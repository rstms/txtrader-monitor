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
        return name.lower()


class Channel(AutoName):
    STATUS = auto()
    ERROR = auto()
    TIME = auto()
    ORDER = auto()
    ORDER_DATA = auto()
    ORDERS = auto()
    TICKET = auto()
    TICKET_DATA = auto()
    EXECUTION = auto()
    EXECUTION_DATA = auto()
    EXECUTIONS = auto()
    QUOTE = auto()
    TRADE = auto()
    TICK = auto()
    CONNECTION = auto()
    SYMBOL = auto()
    SYMBOL_DATA = auto()
    SHUTDOWN = auto()


ALL_CHANNELS = [v for v in dir(Channel) if v[:2] != '__']
