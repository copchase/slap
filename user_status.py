from __future__ import annotations

import os

import requests


def get_user_info(channel: str, user: str) -> dict[str]:
    user_status_endpoint = os.environ.get("USER_STATUS_ENDPOINT")
    if not user_status_endpoint:
        return None

    params = {"channel": channel, "user": user}
    response = requests.get(user_status_endpoint, params=params)
    if not response.ok:
        return None

    return response.json()
