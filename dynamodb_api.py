from typing import Any, Iterable

import boto3

import twitch
from decimal import Decimal

# DDB_CLIENT = boto3.client("dynamodb")


def get_item(key: Any) -> dict:
    key_dict = convert_to_ddbav(key)



def update_item(key: Any, attributes: dict) -> bool:
    return True


# Convert basic Python types to DynamoDB compatible types
# Complex types should be broken down in their own modules
# before coming here to be converted
def convert_to_ddbav(object: Any) -> dict:
    try:
        key, conversion = DDBAV_DICT[type(object)]
        return {
            key: conversion(object)
        }
    except KeyError:
        raise RuntimeError(f"Attempted to convert complex Python type {type(object)} to DynamoDB type") from None

# Needs to be defined last because dictionary definitions require
# that the values exist
DDBAV_DICT = {
    **dict.fromkeys([int, float], ("N", str)),
    **dict.fromkeys([bytes, bytearray], ("B", bytes)),
    str: ("S", str),
    dict: ("M", lambda x: {k: convert_to_ddbav(x[k]) for k in x}),
    list: ("L", lambda x: [convert_to_ddbav(ele) for ele in x]),
    type(None): ("NULL", lambda x: True),
    bool: ("BOOL", bool)
}
