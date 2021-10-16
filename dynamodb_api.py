from __future__ import annotations

import os
from typing import Any, Tuple

import boto3
from logzero import logger

import twitch


DDB_RESOURCE = None
SLAPYOU_TABLE_NAME = None
SLAPYOU_TABLE = None

if os.environ.get("ENV", "local").lower() != "local":
    DDB_RESOURCE = boto3.resource("dynamodb")
    SLAPYOU_TABLE_NAME = os.environ.get("SLAPYOU_TABLE")
    SLAPYOU_TABLE = DDB_RESOURCE.Table(SLAPYOU_TABLE_NAME)


def get_item(key: Any) -> dict:
    result = SLAPYOU_TABLE.get_item(Key={"userId": key})
    logger.info(f"DDB.GetItem response: {result}")
    return result.get("Item")


def update_item(key: Any, attr: dict) -> bool:
    attr.pop("userId", None)
    update_exp, ean, eav = make_update_item_assets(attr)
    result = SLAPYOU_TABLE.update_item(
        Key={"userId": key},
        UpdateExpression=update_exp,
        ExpressionAttributeNames=ean,
        ExpressionAttributeValues=eav,
    )
    logger.info(f"DDB.UpdateItem response: {result}")


# UpdateItem requires explicit setting of attributes
# No need to pass back iteration history
# Iteration on a dict is insertion order based
# Returns of tuple of update expression, EAN, and EAV
# EAN = Expression Attribute Names
# EAV = Expression Attribute Values
def make_update_item_assets(attributes: dict) -> Tuple[str, dict, dict]:
    if len(attributes) == 0:
        logger.warn("UpdateItem was passed an empty attribute dict")
        return "", {}, {}

    counter = 1
    update_exp_frags = []
    ean = {}
    eav = {}
    for key in attributes:
        if type(key) != str:
            continue

        update_exp_frags.append(f"#{counter} = :{counter}")
        ean[f"#{counter}"] = key
        eav[f":{counter}"] = attributes[key]
        counter += 1

    update_exp = ", ".join(update_exp_frags)
    return (f"SET {update_exp}", ean, eav)
