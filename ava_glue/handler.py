# pyright: basic
# ruff: noqa

import json

def handle(event, _):
    print(event)
    return {
        "statusCode": 200,
        "body": json.dumps(event)
    }
