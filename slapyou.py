from __future__ import annotations

import random
from typing import Union

from logzero import logger

import dynamodb_api
import emote

# How can she slap?


def slap(caller_info: dict, target_info: dict, channel_id: str) -> list:
    output_str = []

    caller_name = caller_info["displayName"]
    caller_id = caller_info["providerId"]
    target_name = target_info["displayName"]
    target_id = target_info["providerId"]

    caller_obj = dynamodb_api.get_item(caller_id)
    target_obj = None

    caller_currency = get_user_currency(caller_obj, channel_id)
    critical = roll(0.0625)

    logger.info(f"critical status is {critical}")
    if roll(get_chance_from_currency(caller_currency)):
        logger.info("slap attempt successful")
        target_obj = dynamodb_api.get_item(target_id)
        target_currency = get_user_currency(target_obj, channel_id)
        stolen_amount, target_died = steal(caller_obj, target_obj, channel_id, critical)
        dynamodb_api.update_item(target_id, target_obj)
        if critical:
            output_str.append(f"{caller_name} ({caller_currency} HP) slaps {target_name} ({target_currency} HP) and critically hits, taking {stolen_amount} HP {emote.get_positive_emote()} !")
        else:
            output_str.append(f"{caller_name} ({caller_currency} HP) slaps {target_name} ({target_currency} HP) and took {stolen_amount} HP.")

        if target_died:
            output_str[0] += (f" {target_name} has died from the battle PepeHands")
            output_str.append(f"{target_name} has respawned with 1 HP FeelsGoodMan")
    elif critical:
        output_str.append(f"{caller_name} slaps themselves in confusion and dies {emote.get_negative_emote()} !")
        output_str.append(f"{caller_name}, you have respawned with 1 HP AngelThump")
        set_user_currency(caller_obj, channel_id, 1)
    else:
        loss_amount = loss(caller_obj, channel_id)
        if loss_amount == 0:
            output_str.append(f"{caller_name} tripped and died trying to slap {target_name} {emote.get_negative_emote()}")
            output_str.append(f"{caller_name} has respawned with 1 HP AngelThump Try aiming better next time PepeLaugh")
        else:
            output_str.append(f"{caller_name} ({caller_currency}) fails to slap {target_name} and loses {loss_amount} HP")

    dynamodb_api.update_item(caller_id, caller_obj)
    return output_str


def slap_success(caller_obj: dict, target_id: str, channel_id: str, output_str: list):
    logger.debug("slap success")
    target_obj = dynamodb_api.get_item(target_id)
    target_currency = get_user_currency(target_obj, channel_id)

    if roll_for_crit():
        if roll_one_percent_crit():
            slap_damage = 100 * target_currency * random.normalvariate
    stolen_amount, target_died = steal(caller_obj, target_obj, channel_id, roll_for_crit())
    dynamodb_api.update_item(target_id, target_obj)


def steal(caller_obj: dict, target_obj: dict, channel_id: str, critical: bool):
    caller_currency = get_user_currency(caller_obj, channel_id)
    target_currency = get_user_currency(target_obj, channel_id)
    percentage = random.uniform(1 + critical * 4, 5 + critical * 10)
    stolen_amount = max(1, round(percentage * target_currency))
    set_user_currency(caller_obj, channel_id, caller_currency + stolen_amount)

    target_died = target_currency - stolen_amount < 1
    if target_died:
        respawn_player(target_obj, channel_id)
    else:
        set_user_currency(target_obj, channel_id, target_currency - stolen_amount)

    return stolen_amount, target_died


def loss(caller_obj: dict, channel_id: str) -> int:
    caller_currency = get_user_currency(caller_obj, channel_id)
    if caller_currency == 1:
        return 0
    percentage = random.uniform(0.1, 0.4)
    loss_amount = max(1, round(percentage * caller_currency))
    set_user_currency(caller_obj, channel_id, caller_currency - loss_amount)
    return loss_amount


def respawn_player(user_obj: dict, channel_id: str) -> None:
    initial_hp = 10
    set_user_currency(user_obj, channel_id, initial_hp)


def get_user_currency(user_obj: dict, channel_id: str) -> int:
    return user_obj.get("currency", {}).get(channel_id, 1)


def set_user_currency(user_obj: dict, channel_id: str, currency: int) -> None:
    if "currency" not in user_obj:
        user_obj["currency"] = {}

    user_obj["currency"][channel_id] = currency


def get_chance_from_currency(currency: int) -> float:
    a = 0.839 # Increase to elevate rate of failure growth
    b = 27.0 # Increase to reduce fail rate for all people
    c = -20.0  # Increase to move function towards third quadrant
    # aka increases the "poor person threshold from 1 to 5"
    d = 590.0  # Increase to give more fail chance for poor people
    # increase d to push inflection point towards +inf
    x = float(currency)
    chance = ((x**a - c) + (d / (x - c))) - b
    return 1 - (chance / 100)


def roll(chance: Union[float, str]) -> bool:
    return random.random() < chance


def roll_for_crit() -> int:
    return roll(0.0625)


def roll_one_percent_crit() -> bool:
    return roll(0.01)

# slap_info should be like
# {
#   "caller": "123"
#   "target": "456"
#   "channel": "123"
# }
def slapyou_v2(slap_info: dict) -> list[str]:
    return []