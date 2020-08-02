from txtrader_monitor import Monitor
import json
from pprint import pprint

m = Monitor(log_level='WARNING')


def status(channel, data):
    print(f"{channel}: {data}")
    if data.startswith('.Authorized'):
        pass
    return True


def ticker(channel, data):
    print(f"{channel}: {data}")
    return True


def timer(channel, data):
    print(f"{channel}: {data}")
    return True


def main():
    m.set_callbacks(callbacks={
        '*': None,
        'TICK': ticker,
        'TIME': timer,
        'STATUS': status,
    })
    m.set_tick_interval(5)
    m.run()


if __name__ == '__main__':
    main()
