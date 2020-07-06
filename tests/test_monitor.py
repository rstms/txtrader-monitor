#!/bin/env python

import pytest

from txtrader_monitor import Monitor
import time

import os


@pytest.fixture
def monitor():
    yield Monitor()


def test_init(monitor):
    assert monitor

@pytest.mark.skip
def test_run(monitor):
    monitor.run()
    assert monitor

def _execution(data):
    print(f'RX: {data}')
    count += 1
    return count <= 3

def _status(data):

    if '.Authorized' in data:
        m.send('help')
    return True

count = 0


@pytest.mark.skip
def test_module():
    m = Monitor()
    m.set_callback('execution', _execution) 
    m.set_callback('status', _status) 
    m.run()
    assert count == 3
