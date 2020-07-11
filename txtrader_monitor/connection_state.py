#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  connection_state.py
  -------------------

  TxTrader ConnectionState

  Copyright (c) 2015 Reliance Systems Inc. <mkrueger@rstms.net>
  Licensed under the MIT license.  See LICENSE for details.

"""

from enum import Enum, auto


class AutoName(Enum):

    def _generate_next_value_(name, start, count, last_values):
        return name


class ConnectionState(AutoName):
    INITIALIZING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    CONNECT_PENDING = auto()
    FAILED = auto()
    DISCONNECT_PENDING = auto()
    DISCONNECTED = auto()
    SHUTDOWN = auto()
