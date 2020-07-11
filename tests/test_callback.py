#!/bin/env python

import pytest


def _status(channel, msg):
    print(f"{channel}: {msg}")
    return not msg.startswith('.Authorized')


def test_callback():
    from txtrader_monitor import Monitor
    monitor = Monitor()
    # override single callback, leaving others to print
    monitor.set_callback('STATUS', _status)
    monitor.run()
