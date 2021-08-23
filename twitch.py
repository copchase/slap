import requests
from logzero import logger

BASE_ENDPOINT = "https://api.twitch.tv/helix"


def get_user_id(username: str) -> str:
    path = "/users"
    response = requests.get(BASE_ENDPOINT + path, params={"login": username})
    response.raise_for_status()
    data = response.json()["data"]
    if not data:
        logger.warning(f"User {username} not found")
        return None

    return data["id"]
