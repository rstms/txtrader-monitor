from txtrader_monitor import Monitor
import json
from pprint import pprint


def main():

    m = Monitor()

    def execution(channel, data):
        print(f"{channel} {data}")
        return True

    def executions(channel, data):
        for xid, x in json.loads(data).items():
            pprint(x)
        return True

    def execution_data(channel, data):
        pprint(json.loads(data))
        return True

    def status(channel, data):
        if data.startswith('.Authorized'):
            m.send('executions')
        return True

            #'*': None,
    m.set_callbacks(
        callbacks={
            'STATUS': status,
            'EXECUTION': execution,
            'EXECUTIONS': executions,
            'EXECUTION_DATA': execution_data,
        }
    )
    m.run()


if __name__ == '__main__':
    main()
