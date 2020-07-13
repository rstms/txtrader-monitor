#!/bin/env python

import pytest
from pprint import pprint
import ujson as json

from txtrader_monitor import Monitor

ret = None
m = Monitor()


def _orders(channel, data):
    global ret
    print(f'{channel}: {data}')
    ret = json.loads(data)
    return False


def _status(channel, msg):
    print(f'{channel}: {msg}')
    if msg.startswith('.Authorized'):
        m.send('orders')
    return True


def test_orders():
    m.set_callback('STATUS', _status)
    m.set_callback('ORDERS', _orders)
    m.run()
    assert ret != None
    pprint(ret)
