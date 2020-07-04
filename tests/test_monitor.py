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
