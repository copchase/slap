import util
import twitch
import slapyou

def lambda_handler(event: dict, context):
    print(event)
    response_url, channel_info, caller_info, target_name = get_operating_info(event)

    if target_name is None:
        response_message = "A target was not specified"
        twitch.send_message(response_url, response_message)
        return

    caller_id = caller_info["providerId"]
    target_info = twitch.get_user_info(target_name)
    target_id = target_info["providerId"]
    channel_id = channel_info["providerId"]

    if not twitch.is_user_online(channel_id, target_name):
        response_message = f"User {target_name} is currently not in chat"
        twitch.send_message(response_url, response_message)
        return

    slap_result = slapyou.slap(caller_id, target_id, channel_id)
    for msg in slap_result:
        twitch.send_message(response_url, msg)


def get_operating_info(event: dict) -> (str, str, str, str):
    response_url = event["headers"]["nightbot-response-url"]
    channel_info = util.header_to_dict(event["headers"]["nightbot-channel"])
    caller_info = util.header_to_dict(event["headers"]["nightbot-user"])
    target = event["queryStringParameters"].get("target")
    return response_url, channel_info, caller_info, target
