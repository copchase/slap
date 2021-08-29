import json
import os

import requests
from logzero import logger

import util

HELIX_ENDPOINT = "https://api.twitch.tv/helix"
TMI_ENDPOINT = "https://tmi.twitch.tv"


def get_user_info(username: str) -> dict:
    path = "/users"
    token = util.get_access_token().strip("\"")
    params = {"login": username}
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": os.environ.get("CLIENT_ID")
    }
    response = requests.get(HELIX_ENDPOINT + path, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()["data"][0]
    if not data:
        logger.warning(f"User {username} not found")
        return None

    data["displayName"] = data.pop("display_name")
    data["providerId"] = data.pop("id")
    data["name"] = data.pop("login")
    return data


def send_message(response_url: str, message: str) -> None:
    request_body = {"message": message}
    requests.post(response_url, None, request_body)


def is_user_online(channel: str, username: str) -> bool:
    endpoint = f"{TMI_ENDPOINT}/group/user/{channel}/chatters"
    response = requests.get(endpoint)
    response.raise_for_status()
    chat_info = response.json()["chatters"]

    for v in chat_info.values():
        found_idx = util.find_idx(v, username)
        if found_idx != -1:
            return True

    return False
