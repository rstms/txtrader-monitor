#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
  monitor.py
  ----------

  TxTrader Monitor class - Instantiate in client to receive event notifications.

  Copyright (c) 2015 Reliance Systems Inc. <mkrueger@rstms.net>
  Licensed under the MIT license.  See LICENSE for details.

"""

import os
import click
import time
import json

from signal import signal, Signals, SIG_IGN, SIG_DFL, SIGINT, SIGHUP, SIGQUIT, SIGTERM

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.error import ReactorNotRunning
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.python.log import PythonLoggingObserver

from txtrader_monitor.version import VERSION

import logging


class Monitor(object):
    def __init__(self,
                 host=None,
                 port=None,
                 username=None,
                 password=None,
                 callbacks=None,
                 options=None,
                 log_level='WARNING'):
        """Initialize Monitor:
          connection parameters: host, port, username, password, 
          callbacks: {'name':function ...}  
            where name is one of ['status', 'error', 'time', 'order', 'execution', 'quote', 'trade', 'tick', 'shutdown']
            and function(data) is the callback that will receive event data
            callbacks must return True to continue monitor.run() loop
            by default, all callbacks will print to stdout; to override this, pass callbacks={}
          options: a dict of connection parameters transmitted to the server in the 'auth' message
        """

        observer = PythonLoggingObserver()
        observer.start()

        logging.basicConfig(level=log_level)
        logging.debug(f"{self} init")

        # store connection args for Factory
        self.args = {
            'host': host or os.environ['TXTRADER_HOST'],
            'port': int(port or os.environ['TXTRADER_TCP_PORT']),
            'username': username or os.environ['TXTRADER_USERNAME'],
            'password': password or os.environ['TXTRADER_PASSWORD'],
            'options': options or {}
        }

        # store LoopingCall if client calls set_tick_interval
        self.tickers = set()

        # setup callback map
        self.callbacks = {
            label: None
            for label in ('status', 'error', 'time', 'order', 'execution',
                          'quote', 'trade', 'tick', 'connection', 'shutdown')
        }
        if callbacks == None:
            self.callbacks = {
                label: self._cb_print
                for label in self.callbacks.keys()
            }
        else:
            self.callbacks.update(**callbacks)

        self.shutdown_pending = False

        reactor.addSystemEventTrigger('after', 'startup', self.startup_event)
        reactor.addSystemEventTrigger('before', 'shutdown',
                                      self.shutdown_event)

        self.factory = StatusClientFactory(self)
        self.connection_state = 'initializing'
        self.connection = None
        self.connector = None

    def __del__(self):
        logging.debug(f'{self} __del__')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}<{hex(id(self))}>"

    def startup_event(self):
        logging.debug(f'{self} startup_event')
        self._callback('status', 'reactor startup')

    def shutdown_event(self):
        logging.debug(f'{self} shutdown_event')
        self.set_connection_state('shutdown')
        self._callback('shutdown', 'reactor shutdown detected')
        self.shutdown_pending = True
        #self.disconnect()

    def set_connection_state(self, state):
        if self.connection_state != state:
            self.connection_state = state
            self._callback('connection', state)

    def connect(self):
        logging.debug(f'{self} connect')
        if not self.connection:
            self.set_connection_state('connecting...')
            self.connector = reactor.connectTCP(self.args['host'].encode(),
                                                self.args['port'],
                                                self.factory)

    def _connecting(self, connector):
        logging.debug(f'{self} _connecting connector={hex(id(connector))}')
        self.connector == connector
        self.set_connection_state('connection_pending...')

    def _connected(self, connection):
        logging.debug(f'{self} _connected connection={hex(id(connection))}')
        self.connection = connection
        self.set_connection_state('connected')

    def _connection_failed(self):
        logging.debug(f'{self} _connection_failed')
        self.set_connection_state('connection failed')

    def disconnect(self):
        logging.debug(f'{self} disconnect')
        self.shutdown_pending = True
        self.set_connection_state('disconnecting...')
        if self.factory:
            self.factory.stopTrying()
        if self.connector:
            self.connector.disconnect()

    def _disconnected(self, reason):
        logging.debug(f'{self} _disconnected {reason.getErrorMessage()}')
        self.connection = None
        self.set_connection_state('disconnected')

    def set_callback(self, cb_type, cb_func):
        """Set a callback function (or None) for a message type"""
        self.callbacks[cb_type] = cb_func

    def set_tick_interval(self, interval_seconds):
        looper = LoopingCall(self.ticker)
        looper.start(interval_seconds)
        self.tickers.add(looper)
        return looper

    def stop_ticker(self, ticker_looper):
        ticker_looper.stop()
        self.tickers.discard(looper)

    def ticker(self):
        self._callback('tick', time.time())

    def _callback(self, cb_type, cb_data):
        if cb_type in self.callbacks:
            if not self.callbacks[cb_type](cb_type, cb_data):
                self.shutdown(f'client request')

    def shutdown(self, reason):
        logging.debug(f'{self} shutdown reason={reason}')
        while self.tickers:
            self.tickers.pop().stop()
        if self.connection:
            self.connection.send(f'exit {reason}')
        self.shutdown_pending = True
        self.disconnect()

    def _cb_print(self, label, msg):
        print('%s: %s' % (label, repr(msg)))
        return True

    def signal_handler(self, sig, frame):
        signame = Signals(sig).name
        print(f'{signame} received; attempting graceful shutdown...')
        # reset all signals back to the default
        self.set_handler(SIG_DFL)
        self.shutdown(f'received {signame}')
        self.stop()

    def set_handler(self, handler):
        for s in [SIGINT, SIGHUP, SIGQUIT, SIGTERM]:
            signal(s, handler)

    def run(self):
        """React to gateway events, returning data via callback functions."""
        logging.debug(f'{self} run')
        self.set_handler(self.signal_handler)
        reactor.callWhenRunning(self.connect)
        reactor.run()

    def stop(self):
        try:
            if reactor.running:
                reactor.stop()
        except ReactorNotRunning:
            pass


class StatusClient(NetstringReceiver):
    def __init__(self, controller):
        logging.debug(f'{self} __init__({hex(id(controller))})')
        self.MAX_LENGTH = 0x1000000
        self.channel = ''
        self.message_types = []
        self.channel_map = {}
        self.last_account = ''
        self.controller = controller

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}<{hex(id(self))}>"

    def __del__(self):
        logging.debug(f'{self} __del__')

    def connectionMade(self):
        logging.debug(f"{self} connectionMade")
        self.controller._connected(self)

    def connectionLost(self, reason):
        logging.debug(f"{self} connectionLost {reason.getErrorMessage()}")
        self.controller._disconnected(reason=reason)

    def send(self, data):
        logging.debug(f"{self} send data={data}")
        logging.info(f"TX: {data}")
        self.sendString(data.encode())

    def stringReceived(self, data):
        data = data.decode()
        logging.info(f"RX: {data}")
        if data.startswith('.'):
            self.controller._callback('status', data)
            if data.startswith('.connected'):
                args = self.controller.args
                self.send(
                    f"auth {args['username']} {args['password']} {json.dumps(args['options'])}"
                )
            elif data.startswith('.Authorized'):
                dummy, self.channel = data.split()[:2]
                # setup channel map now that we have the channel name
                self.channel_map = {
                    '%s.time: ' % self.channel: 'time',
                    '%s.error:' % self.channel: 'error',
                    '%s.order.' % self.channel: 'order',
                    '%s.ticket.' % self.channel: 'ticket',
                    '%s.open-order.' % self.channel: 'order',
                    '%s.execution.' % self.channel: 'execution',
                    '%s.quote.' % self.channel: 'quote',
                    '%s.trade.' % self.channel: 'trade'
                }
                self.account_channel = '%s.current-account' % self.channel
        else:
            for channel, callback in self.channel_map.items():
                if data.startswith(channel):
                    return self.controller._callback(callback,
                                                     data[len(channel):])
            # only return current_account message if different from last one
            if data.startswith(self.account_channel):
                if self.last_account == data:
                    return
                else:
                    self.last_account = data
            self.controller._callback('status', data)


class StatusClientFactory(ReconnectingClientFactory):
    initialDelay = 15
    maxDelay = 60

    def __init__(self, controller):
        logging.debug(f"{self} __init__({hex(id(controller))})")
        self.controller = controller

    def __del__(self):
        logging.debug(f'{self} __del__')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}<{hex(id(self))}>"

    def startedConnecting(self, connector):
        logging.debug(f"{self} startedConnecting:  connector={hex(id(connector))}")
        self.controller._connecting(connector)

    def buildProtocol(self, addr):
        logging.debug(f"{self} buildProtocol (connected) addr={addr}")
        self.resetDelay()
        return StatusClient(self.controller)

    def clientConnectionFailed(self, connector, reason):
        logging.debug(f"{self} clientConnectionFailed connector={hex(id(connector))} msg={reason.getErrorMessage()}")
        ReconnectingClientFactory.clientConnectionFailed(
            self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        logging.debug(f"{self} clientConnectionLost connector={hex(id(connector))} msg={reason.getErrorMessage()}"
        )
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def startFactory(self):
        logging.debug(f"{self} startFactory")

    def stopFactory(self):
        logging.debug(f"{self} stopFactory")
        if self.controller.shutdown_pending:
            self.controller.stop()


@click.command('txtrader_monitor', short_help='output txtrader updates')
@click.option('--host', default=None, envvar='TXTRADER_HOST')
@click.option('--port', type=int, default=None, envvar='TXTRADER_TCP_PORT')
@click.option('--username', default=None, envvar='TXTRADER_USERNAME')
@click.option('--password', default=None, envvar='TXTRADER_PASSWORD')
@click.option('-l', '--log_level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False), default='WARNING', envvar='LOG_LEVEL')
def txtrader_monitor(host, port, username, password, log_level):
    Monitor(host, port, username, password, log_level=log_level).run()
