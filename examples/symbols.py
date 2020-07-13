from txtrader_monitor import Monitor
import json
from pprint import pprint

options = {'symbol': 'MSFT', 'query_sent': False, 'querydata_sent': False}

m = Monitor(log_level='WARNING')


def symbol(channel, data):
    result = json.loads(data)
    pprint(json.loads(data))
    symbol = options['symbol']
    if not options['query_sent']:
        options['query_sent'] = True
        m.send(f"query {symbol}")
    elif not options['querydata_sent']:
        options['querydata_sent'] = True
        m.send(f"querydata {symbol}")
    return True


def symbol_data(channel, data):
    pprint(json.loads(data))
    return False 

def status(channel, data):
    print(f"{channel}: {data}")
    if data.startswith('.Authorized'):
        options['query_sent'] = False
        options['querydata_sent'] = False
        m.send(f"add {options['symbol']}")
    return True


def main():
    m.set_callbacks(callbacks={
        '*': None,
        'STATUS': status,
        'SYMBOL': symbol,
        'SYMBOL_DATA': symbol_data,
    })
    m.run()


if __name__ == '__main__':
    main()
