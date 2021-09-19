import bisect
import json
import os

import boto3


def header_to_dict(header: str) -> dict:
    output = {}
    kv_pairs = header.split("&")
    for pair in kv_pairs:
        pair_array = pair.split("=")
        output[pair_array[0]] = pair_array[1]

    return output


def is_target_channel_owner(target_info: dict, channel_info: dict) -> bool:
    return target_info["providerId"] == channel_info["providerId"]


def is_target_self(caller_id: str, target_id: str) -> bool:
    return caller_id == target_id


def is_target_bot(target_id: str) -> bool:
    bot_set = set([
        "anotherttvviewer",
        "commanderroot",
        "hnlbot",
        "moobot",
        "nightbot",
        "phantombot"
        "spireinfo",
        "stay_hydrated_bot",
        "streamelements",
        "streamlabs",
        "xanbot",
    ])

    return target_id.lower() in bot_set

def get_access_token() -> str:
    lambda_client = boto3.client("lambda")
    env = os.environ.get("ENV")
    response = lambda_client.invoke(
        FunctionName=f"{env}-twitch-oauth",
        InvocationType="RequestResponse",
        LogType="None",
    )

    token = response["Payload"].read().decode("utf-8")
    if not token:
        raise RuntimeError("Could not retrieve access token")

    return token


def find_idx(lst: list, value) -> int:
    idx = bisect.bisect_left(lst, value)
    if idx < len(lst) and lst[idx] == value:
        return idx
    return -1
