from __future__ import annotations

import string
import time
from datetime import datetime

from logzero import logger

import slapyou2
import twitch
import user_status
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

    target_name = target_name.strip(f"{string.whitespace}@,")
    caller_id = caller_info["providerId"]
    user_online = False
    channel_name = channel_info["name"]
    target_info = user_status.get_user_info(channel_name, target_name)
    target_id = target_info["providerId"]
    channel_id = channel_info["providerId"]

    if target_info is None:
        target_info = twitch.get_user_info(target_name)
        user_online = twitch.is_user_online(channel_name, target_name)
    else:
        user_online = target_info["online"]

    if not user_online:
        response_message = f"User {target_name} is currently not in chat"
        twitch.send_message(response_url, response_message)
        return None

    target_name = target_name.lower()
    if target_name == "nightbot" and caller_info["userLevel"] != "owner":
        response_message = "You can't slap me :)"
        twitch.send_message(response_url, response_message)
        return None

    logger.info(f"""{caller_info["displayName"]} is trying to slap {target_name}""")

    if util.is_target_self(caller_id, target_id):
        response_message = (
            "ERROR: You cannot attempt to intentionally slap yourself PepeLaugh"
        )
        twitch.send_message(response_url, response_message)
        return None
    elif util.is_target_channel_owner(target_info, channel_info):
        response_message = "ERROR: You cannot slap the streamer PepeLaugh"
        twitch.send_message(response_url, response_message)
        return None

    slap_info = {
        "caller": {"id": caller_id, "name": caller_info["displayName"]},
        "target": {"id": target_id, "name": target_info["displayName"]},
        "channelId": channel_id,
        "output": [],
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
