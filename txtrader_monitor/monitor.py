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
import sys
import click
import time
import json
import logging
from typing import IO
from enum import Enum, unique

from signal import signal, Signals, SIG_IGN, SIG_DFL, SIGINT, SIGHUP, SIGQUIT, SIGTERM

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.error import ReactorNotRunning
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import NetstringReceiver

from txtrader_monitor.version import VERSION

from txtrader_monitor.channel import ALL_CHANNELS, Channel
from txtrader_monitor.connection_state import ConnectionState

CHANNELS = ALL_CHANNELS


class Monitor(object):

    def __init__(
        self,
        host: str = '',
        port: str = '',
        username: str = '',
        password: str = '',
        options: dict = {},
        callbacks: dict = {},
        log_level: str = 'WARNING',
    ):
        """Initialize Monitor:
          connection parameters: host, port, username, password, 
          options: a dict of connection parameters transmitted to the server in the 'auth' message
          callbacks: {'channel': function ...}  
            where channel is one of CHANNELS
            use '*' as a channel name to set a new default callback function 
            and function is the callback function that will receive (channel, message)
            callbacks must return True to continue the monitor.run() loop
            by default, all callbacks will print to stdout; to override this, pass callbacks={}
          log_level: select filter for log: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        """

        logging.basicConfig(
            stream=sys.stderr, level=log_level, format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
        )
        logger = logging.getLogger(self.__class__.__name__)

        logging.info(f"{self} __init__({host}, {port}, {username}, XXXXXXXX, {options}, {callbacks}, {log_level})")

        if not isinstance(options, dict):
            raise ValueError(f'options: expected dict type, got {type(options)}')

        self.host = host or os.environ['TXTRADER_HOST']
        self.port = int(port or os.environ['TXTRADER_TCP_PORT'])
        self.username = username or os.environ['TXTRADER_USERNAME']
        self.password = password or os.environ['TXTRADER_PASSWORD']

        self.options = options

        # setup callback map
        self.set_callbacks(callbacks)

        # store LoopingCall if client calls set_tick_interval
        self.tickers = set()

        self.shutdown_pending = False

        reactor.addSystemEventTrigger('after', 'startup', self.startup_event)
        reactor.addSystemEventTrigger('before', 'shutdown', self.shutdown_event)

        # create the factory singleton
        self.factory = StatusClientFactory(self)

        self.connection_state = ConnectionState.INITIALIZING
        self.connection_wanted = False
        self.connection = None
        self.connector = None

    def __del__(self):
        logging.info(f'{self} __del__()')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}<{hex(id(self))}>"

    def set_callbacks(self, callbacks: dict = {}):
        """Set all callback functions with a dict; supports '*' for default, and None values to disable"""
        if '*' in callbacks:
            default = callbacks['*']
            callbacks.pop('*')
        else:
            default = self._cb_default
        self.callbacks = {label: default for label in CHANNELS}
        if callbacks:
            self.callbacks.update(callbacks)

    def set_callback(self, channel, function):
        """Set a callback function (or None) for a message type"""
        if channel in CHANNELS:
            self.callbacks[channel] = function
        else:
            raise ValueError

    def startup_event(self):
        logging.info(f'{self} startup_event()')
        self._callback(Channel.STATUS, 'reactor startup')

    def shutdown_event(self):
        logging.info(f'{self} shutdown_event()')
        self.set_connection_state(ConnectionState.SHUTDOWN)
        self._callback(Channel.SHUTDOWN, 'reactor shutdown detected')
        self.shutdown_pending = True

    def set_connection_state(self, state):
        if self.connection_state != state:
            self.connection_state = state
            self._callback(Channel.CONNECTION, state.name)

    def connect(self):
        logging.info(f'{self} connect()')
        if self.connection_state == ConnectionState.CONNECTED:
            logging.error('connect: already connected')
        else:
            connection_wanted = True
            if not self.connection:
                self.set_connection_state(ConnectionState.CONNECTING)
                self.connector = reactor.connectTCP(self.host.encode(), self.port, self.factory)

    def _connecting(self, connector):
        logging.info(f'{self} _connecting(connector={hex(id(connector))})')
        self.connector == connector
        self.set_connection_state(ConnectionState.CONNECT_PENDING)

    def _connected(self, connection):
        logging.info(f'{self} _connected(connection={hex(id(connection))})')
        self.connection = connection
        self.set_connection_state(ConnectionState.CONNECTED)

    def _connection_failed(self):
        logging.info(f'{self} _connection_failed()')
        self.set_connection_state(ConnectionState.CONNECT_FAILED)

    def disconnect(self):
        logging.info(f'{self} disconnect()')
        connection_wanted = False
        if self.connection_state == ConnectionState.DISCONNECTED:
            logging.error('disconnect: already disconnected')
        else:
            self.set_connection_state(ConnectionState.DISCONNECT_PENDING)
            if self.connection_state in [ConnectionState.CONNECTING, ConnectionState.CONNECT_PENDING]:
                self.factory.stopTrying()
            if self.connector:
                self.connector.disconnect()

    def _disconnected(self, reason):
        logging.info(f'{self} _disconnected({reason.getErrorMessage()})')
        self.connection = None
        self.connector = None
        self.set_connection_state(ConnectionState.DISCONNECTED)

    def set_tick_interval(self, interval_seconds):
        looper = LoopingCall(self.ticker)
        looper.start(interval_seconds)
        self.tickers.add(looper)
        return looper

    def stop_ticker(self, ticker_looper):
        ticker_looper.stop()
        self.tickers.discard(looper)

    def ticker(self):
        self._callback(Channel.TICK, time.time())

    def _callback(self, channel: Channel, data: str):
        if isinstance(channel, Channel):
            channel = channel.name
        func = self.callbacks[channel]
        if func:
            if not func(channel, data):
                self.shutdown(f'client requested shutdown')

    def shutdown(self, reason):
        self.shutdown_pending = True
        logging.info(f'{self} shutdown(reason={reason})')
        while self.tickers:
            self.tickers.pop().stop()
        if self.connection:
            self.connection.send(f'exit {reason}')
            self.disconnect()

    def _cb_default(self, channel, msg):
        #if not self.shutdown_pending:
        print(f'{channel}: {msg}')
        return True

    def send(self, command):
        self.connection.send(command)

    def signal_handler(self, sig, frame):
        signame = Signals(sig).name
        logging.warning(f'{signame} received; attempting graceful shutdown...')
        # reset all signals back to the default
        self.set_handler(SIG_DFL)
        self.shutdown(f'received {signame}')
        self.stop()

    def set_handler(self, handler):
        for s in [SIGINT, SIGHUP, SIGQUIT, SIGTERM]:
            signal(s, handler)

    def run(self):
        """React to gateway events, returning data via callback functions."""
        logging.info(f'{self} run()')
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
    # set 256MB line buffer                                                                                                                                       MAX_LENGTH = 0x10000000
    def __init__(self, controller):
        logging.info(f'{self} __init__({hex(id(controller))})')
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
        logging.info(f'{self} __del__()')

    def connectionMade(self):
        logging.info(f"{self} connectionMade()")
        self.controller._connected(self)

    def connectionLost(self, reason):
        logging.info(f"{self} connectionLost({reason.getErrorMessage()})")
        self.controller._disconnected(reason=reason)

    def send(self, data, mask_password=None):
        if mask_password:
            log_data = data.replace(mask_password, 'XXXXXXXX')
        else:
            log_data = data
        logging.info(str(f"{self} send(data={log_data})"))
        logging.debug(f"TX: {log_data}")
        self.sendString(data.encode())

    def stringReceived(self, data):
        data = data.decode()
        logging.debug(f"RX: {data}")
        if data.startswith('.'):
            self.controller._callback(Channel.STATUS, data)
            if data.lower().startswith('.connected'):
                self.send(
                    f"auth {self.controller.username} {self.controller.password} {json.dumps(self.controller.options)}",
                    mask_password=self.controller.password
                )
            elif data.lower().startswith('.authorized'):
                dummy, self.channel = data.split()[:2]
                # setup channel map now that we have the channel name
                self.channel_map = {
                    '%s.time: ' % self.channel: Channel.TIME,
                    '%s.error: ' % self.channel: Channel.ERROR,
                    '%s.order.' % self.channel: Channel.ORDER,
                    '%s.order-data ' % self.channel: Channel.ORDER_DATA,
                    '%s.orders: ' % self.channel: Channel.ORDERS,
                    '%s.ticket.' % self.channel: Channel.TICKET,
                    '%s.ticket-data ' % self.channel: Channel.TICKET_DATA,
                    '%s.open-order.' % self.channel: Channel.ORDER,
                    '%s.execution.' % self.channel: Channel.EXECUTION,
                    '%s.executions: ' % self.channel: Channel.EXECUTIONS,
                    '%s.execution-data ' % self.channel: Channel.EXECUTION_DATA,
                    '%s.symbol: ' % self.channel: Channel.SYMBOL,
                    '%s.symbol-data: ' % self.channel: Channel.SYMBOL_DATA,
                    '%s.quote.' % self.channel: Channel.QUOTE,
                    '%s.trade.' % self.channel: Channel.TRADE
                }
                self.account_channel = '%s.current-account' % self.channel
        else:
            handled = False
            for channel, callback_channel in self.channel_map.items():
                if data.startswith(channel):
                    handled = True
                    return self.controller._callback(callback_channel, data[len(channel):])
            # only return current_account message if different from last one
            if data.startswith(self.account_channel):
                if self.last_account == data:
                    return
                else:
                    self.last_account = data
            self.controller._callback(Channel.STATUS, data)


class StatusClientFactory(ReconnectingClientFactory):
    initialDelay = 1
    maxDelay = 15

    def __init__(self, controller):
        logging.info(f"{self} __init__({hex(id(controller))})")
        self.controller = controller

    def __del__(self):
        logging.info(f'{self} __del__()')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}<{hex(id(self))}>"

    def startedConnecting(self, connector):
        logging.info(f"{self} startedConnecting(connector={hex(id(connector))})")
        self.controller._connecting(connector)

    def buildProtocol(self, addr):
        logging.info(f"{self} buildProtocol(addr={addr}) (connected)")
        self.resetDelay()
        return StatusClient(self.controller)

    def clientConnectionFailed(self, connector, reason):
        logging.info(f"{self} clientConnectionFailed(connector={hex(id(connector))} msg={reason.getErrorMessage()})")
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        logging.info(f"{self} clientConnectionLost(connector={hex(id(connector))} msg={reason.getErrorMessage()})")
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def startFactory(self):
        logging.info(f"{self} startFactory()")

    def stopFactory(self):
        logging.info(f"{self} stopFactory()")
        if self.controller.shutdown_pending:
            self.controller.stop()


@click.command('txtrader_monitor', short_help='monitor txtrader update channel')
@click.option('-h', '--host', default='localhost', envvar='TXTRADER_HOST')
@click.option('-p', '--port', type=int, default=50090, envvar='TXTRADER_TCP_PORT')
@click.option('-u', '--username', default='txtrader_user', envvar='TXTRADER_USERNAME')
@click.option('-P', '--password', default='change_this_password', envvar='TXTRADER_PASSWORD')
@click.option('--options', type=str, default='{"order-notification":1,"execution-notification":1}', envvar='TXTRADER_OPTIONS')
@click.option('--version', type=str, default='{}', envvar='TXTRADER_OPTIONS')
@click.option(
    '-l',
    '--log_level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
    default='WARNING',
    envvar='TXTRADER_LOG_LEVEL'
)
@click.version_option(VERSION)
def txtrader_monitor(host, port, username, password, options, log_level, version):
    options = json.loads(options)
    Monitor(host, port, username, password, options=options, callbacks={}, log_level=log_level).run()
