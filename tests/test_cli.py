import pytest
from subprocess import check_output, CalledProcessError
import json
import re
from pprint import pprint, pformat
import time


def _cmd(cmdline):
    try:
        ret = check_output(cmdline, shell=True).decode().strip()
    except CalledProcessError as cpe:
        print(repr(cpe))
        print(f'output={cpe.output}')
        raise(cpe)
    return ret


def test_cli_help()
    out = _cmd('txtrader_monitor --help')
    assert out == 'true'


def test_cli_run()
    out = _cmd('txtrader_monitor')
    assert out == 'true'
