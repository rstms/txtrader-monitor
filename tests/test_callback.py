#!/bin/env python

import pytest

from txtrader_monitor import Monitor

monitor = Monitor()


def _status(channel, msg):
    global monitor
    print(f'{channel}: {msg}')
    print(f'connection_state is {monitor.connection_state.name}')
    return not msg.startswith('.Authorized')


def test_send_error():
    global monitor
    monitor.send('test')


def test_callback():
    global monitor
    # override single callback, leaving others to print
    monitor.set_callback('STATUS', _status)
    monitor.run()
