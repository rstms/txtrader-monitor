#!/bin/env python

import pytest
import ujson as json
from pprint import pprint

from txtrader_monitor import Monitor

m = Monitor(log_level='WARNING')

ex = None


def _executions(channel, data):
    global ex
    #print(f'{channel}: {data}')
    ex = (json.loads(data))
    return False


def _status(channel, msg):
    print(f'{channel}: {msg}')
    if msg.startswith('.Authorized'):
        m.send('executions')
    return True


def test_run_query_executions():
    global ex
    m.set_callback('STATUS', _status)
    m.set_callback('EXECUTIONS', _executions)
    m.run()
    assert ex != None
    pprint(ex)
