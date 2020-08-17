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

# init monitor with execution-notification and execution-data options enabled
# attach our callback funcitions to the desired channels
# and run it until a callback returns False
Monitor(
    options={'execution-data':1 },
    callbacks={
        '*': None, 
        'STATUS': status_callback,
        'EXECUTION_DATA': execution_data_callback
    }
).run()
