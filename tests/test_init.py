#!/bin/env python

import pytest

from txtrader_monitor import Monitor


def test_init():
    assert Monitor()
