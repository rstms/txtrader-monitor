from txtrader_monitor import Monitor
import json
from pprint import pprint
import os

m = Monitor(log_level=os.environ.get('TXTRADER_LOG_LEVEL', 'WARNING'))


def status(channel, data):
    trigger = 'rtx.positions:'
    if data.startswith('.Authorized'):
        m.send(f"positions")
    elif data.startswith(trigger):
        print(data[len(trigger) + 1:])
        return False
    return True


def main():
    m.set_callbacks(callbacks={
        '*': None,
        'STATUS': status,
    })
    m.run()


if __name__ == '__main__':
    main()
