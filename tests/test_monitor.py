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

def test_run(monitor):
    monitor.run()
    assert monitor


def _execution(self, data):
    print(f'RX: {data}')
    count += 1
    return count <= 3


count=0

def test_module():
    Monitor(callbacks={'execution':_execution}).run()
    assert count == 3
