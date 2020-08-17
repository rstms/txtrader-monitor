txtrader-monitor
----------------

This module is a stand-alone package for the monitor component of the txtrader trading api manager

## Installation
```
pip install txtrader-monitor
```

## Configuration
The following configuration variables are required:
```
TXTRADER_HOST
TXTRADER_USERNAME
TXTRADER_PASSWORD
TXTRADER_TCP_PORT
TXTRADER_API_ACCOUNT
```
There are 2 ways to provide the variables:
### passed as a python dict into the constructor `API(config={'TXTRADER_HOST': 'localhost', ...})` 
### set as environment variables

## Example Code
```

from txtrader_monitor import Monitor
import json
from sys import stderr

# print status channel messages to stderr
def status_callback(channel, data):
    stderr.write(f"{channel} {data}\n")
    return True

# print json execution to stdout
def execution_data_callback(channel, message):
    print(message)
    return False 

# init with execution-notification and execution-data options enabled
# attach callback funcitions to channels
# and run until a callback returns False

Monitor(
    options={'execution-data':1},
    callbacks={
        '*': None, 
        'STATUS': status_callback, 
        'EXECUTION_DATA': execution_data_callback
    }
).run()
```

## Example Use:
```
(txtrader-monitor) mkrueger@vesta:~/src/txtrader-monitor$ python examples/example.py 2>/dev/null | jq .
{
  "ORDER_ID": "9b94c305-b9-001a-3",
  "ORIGINAL_ORDER_ID": "9b94c305-b9-001a",
  "AVG_PRICE": 125.08,
  "BUYORSELL": "Buy",
  "CURRENCY": "USD",
  "CURRENT_STATUS": "COMPLETED",
  "DISP_NAME": "IBM",
  "EXCHANGE": "NYS",
  "EXIT_VEHICLE": "DEMOEUR",
  "FILL_ID": "1549-1323056",
  "ORDER_RESIDUAL": 25,
  "ORIGINAL_PRICE": 0,
  "ORIGINAL_VOLUME": 100,
  "PRICE": 125.08,
  "PRICE_TYPE": "Market",
  "TIME_STAMP": "202008171148032300",
  "TIME_ZONE": "America/New_York",
  "MARKET_TRD_DATE": "2020-08-17",
  "TRD_TIME": "11:48:02",
  "VOLUME": 75,
  "VOLUME_TRADED": 75,
  "CUSIP": "459200101",
  "ACCOUNT": "REALTICKDEMO.REALTICK.DEMO31.TRADING"
}
```
