import time

import slapyou
import twitch
import util


def lambda_handler(event: dict, context):
    if "warmup" in event:
        return

    response_url, channel_info, caller_info, target_name = get_operating_info(event)

    if target_name is None or target_name == "null":
        response_message = "A target was not specified"
        twitch.send_message(response_url, response_message)
        return

    caller_id = caller_info["providerId"]
    target_info = twitch.get_user_info(target_name)
    target_id = target_info["providerId"]
    channel_id = channel_info["providerId"]
    channel_name = channel_info["name"]

    if not twitch.is_user_online(channel_name, target_name):
        response_message = f"User {target_name} is currently not in chat"
        twitch.send_message(response_url, response_message)
        return

    slap_result = slapyou.slap(caller_info, target_info, channel_id)
    for msg in slap_result:
        twitch.send_message(response_url, msg)
        time.sleep(5.5)


def get_operating_info(event: dict) -> (str, str, str, str):
    response_url = event["headers"]["Nightbot-Response-Url"]
    channel_info = util.header_to_dict(event["headers"]["Nightbot-Channel"])
    caller_info = util.header_to_dict(event["headers"]["Nightbot-User"])
    target = event["queryStringParameters"].get("target")
    return response_url, channel_info, caller_info, target
