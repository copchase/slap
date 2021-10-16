from __future__ import annotations

import time
from datetime import datetime

from logzero import logger

import slapyou2
import twitch
import util


def lambda_handler(event: dict, context):
    if "warmup" in event:
        return

    logger.info(f"current time is {datetime.utcnow()}Z")
    logger.info(f"incoming event: {event}")
    response_url, channel_info, caller_info, target_name = get_operating_info(event)

    if target_name is None or target_name == "null":
        response_message = "A target was not specified"
        twitch.send_message(response_url, response_message)
        return None

    caller_id = caller_info["providerId"]
    target_info = twitch.get_user_info(target_name)
    target_id = target_info["providerId"]
    channel_id = channel_info["providerId"]
    channel_name = channel_info["name"]

    target_name = target_name.lower()
    if target_name == "nightbot" and caller_info["userLevel"] != "owner":
        response_message = "You can't slap me :)"
        twitch.send_message(response_url, response_message)
        return None

    logger.info(f"""{caller_info["displayName"]} is trying to slap {target_name}""")

    if util.is_target_self(caller_id, target_id):
        response_message = "ERROR: You cannot attempt to intentionally slap yourself PepeLaugh"
        twitch.send_message(response_url, response_message)
        return None
    elif util.is_target_channel_owner(target_info, channel_info):
        response_message = "ERROR: You cannot slap the streamer PepeLaugh"
        twitch.send_message(response_url, response_message)
        return None
    elif not twitch.is_user_online(channel_name, target_name):
        response_message = f"User {target_name} is currently not in chat"
        twitch.send_message(response_url, response_message)
        return None

    slap_info = {
        "caller": {
            "id": caller_id,
            "name": caller_info["displayName"]
        },
        "target": {
            "id": target_id,
            "name": target_info["displayName"]
        },
        "channelId": channel_id,
        "output": []
    }

    slapyou2.slap(slap_info)
    msgs_to_send = slap_info["output"]
    while len(msgs_to_send) > 0:
        msg = msgs_to_send.pop(0)
        twitch.send_message(response_url, msg)
        time.sleep(5.5)

    return None


def get_operating_info(event: dict) -> tuple[str, str, str, str]:
    response_url = event["headers"]["Nightbot-Response-Url"]
    channel_info = util.header_to_dict(event["headers"]["Nightbot-Channel"])
    caller_info = util.header_to_dict(event["headers"]["Nightbot-User"])
    target = event["queryStringParameters"].get("target")
    return response_url, channel_info, caller_info, target
