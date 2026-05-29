# pyright: basic
# ruff: noqa

import json

def handler(event, _):
    print(event)
    return {
        "statusCode": 200,
        "body": json.dumps(event)
    }
