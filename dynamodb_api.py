import os
from typing import Any

import boto3

import twitch

DDB_CLIENT = boto3.client("dynamodb")
DDB_TABLE = os.environ.get("SLAPYOU_TABLE")

def get_item(key: Any) -> dict:
    key_dict = {"userId": convert_to_ddbav(key)}
    result = DDB_CLIENT.get_item(TableName=DDB_TABLE, Key=key_dict)
    ddbav_attr = result.get("Item", {})
    python_attr = {}

    for key in ddbav_attr:
        python_attr[key] = convert_from_ddbav(ddbav_attr[key])

    return python_attr


def update_item(key: Any, attributes: dict) -> bool:
    counter = 1
    key_dict = {"userId": convert_to_ddbav(key)}
    attr_dict = {}
    for k in attributes:
        attr_dict[k] = convert_to_ddbav(attributes[k])

    update_exp, ean, eav = make_update_item_assets(attributes)
    DDB_CLIENT.update_item(
        TableName=DDB_TABLE,
        Key=key_dict,
        ReturnValues="NONE",
        UpdateExpression=update_exp,
        ExpressionAttributeNames=ean,
        ExpressionAttributeValues=eav
    )


# UpdateItem requires explicit setting of attributes
# No need to pass back iteration history
# Iteration on a dict is insertion order based
# Returns of tuple of update expression, EAN, and EAV
# EAN = Expression Attribute Names
# EAV = xpression Attribute Values
def make_update_item_assets(attributes: dict) -> (str, dict, dict):
    counter = 1
    exp_frag = []
    ean = {}
    eav = {}
    for key in attributes:
        if type(key) != str:
            continue

        exp_frag.append(f"#{counter} = :{counter}")
        ean[f"#{counter}"] = key
        eav[f":{counter}"] = convert_to_ddbav(attributes[key])
        counter += 1

    update_exp = ", ".join(exp_frag)
    return (f"SET {update_exp}", ean, eav)


# Convert basic Python types to DynamoDB compatible types
# Complex types should be broken down in their own modules
# before coming here to be converted
def convert_to_ddbav(object: Any) -> dict:
    try:
        key, conversion = TO_DDBAV_DICT[type(object)]
        return {
            key: conversion(object)
        }
    except KeyError:
        raise RuntimeError(f"Attempted to convert complex Python type {type(object)} to DynamoDB type") from None


def convert_from_ddbav(ddbav: dict) -> Any:
    for key in ddbav:
        conversion = FROM_DDBAV_DICT[key]
        return conversion(ddbav[key])

# Needs to be defined last because dictionary definitions require
# that the values exist
TO_DDBAV_DICT = {
    **dict.fromkeys([int, float], ("N", str)),
    **dict.fromkeys([bytes, bytearray], ("B", bytes)),
    str: ("S", str),
    dict: ("M", lambda x: {k: convert_to_ddbav(x[k]) for k in x}),
    list: ("L", lambda x: [convert_to_ddbav(ele) for ele in x]),
    type(None): ("NULL", lambda x: True),
    bool: ("BOOL", bool)
}

FROM_DDBAV_DICT = {
    "N": lambda x: float(x) if "." in x else int(x),
    "B": bytes,
    "S": str,
    "M": lambda x: {k: convert_from_ddbav(x[k]) for k in x},
    "L": lambda x: [convert_from_ddbav[ele] for ele in x],
    "NULL": lambda x: None,
    "BOOL": bool
}
