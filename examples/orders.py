from txtrader_monitor import Monitor
import json
from pprint import pprint

options = {'order-notification': 1, 'order-data': 1}
m = Monitor(options=options, log_level='WARNING')


def status(channel, data):
    print(f"{channel}: {data}")
    if data.startswith('.Authorized'):
        m.send(f"orders")
    return True


def orders(channel, data):
    print(f"{channel}: {data}")
    return True


def order(channel, data):
    print(f"{channel}: {data}")
    return True


def order_data(channel, data):
    print(f"{channel}: {data}")
    return True


def main():
    m.set_callbacks(
        callbacks={
            '*': None,
            'STATUS': status,
            'ORDER': order,
            'ORDERS': orders,
            'ORDER_DATA': order_data,
        }
    )
    m.run()


if __name__ == '__main__':
    main()
