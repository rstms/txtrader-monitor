from txtrader_monitor import Monitor
import json
from pprint import pprint

m = Monitor()


def status(channel, data):
    trigger = '.accounts:'
    #print(f"{channel}: {data}")
    if data.startswith('.Authorized'):
        m.send(f"accounts")
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
