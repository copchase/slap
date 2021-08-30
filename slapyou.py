from typing import Union
import random
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

    if roll(get_chance_from_currency(caller_currency)):
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


def steal(caller_obj: dict, target_obj: dict, channel_id: str, critical: bool) -> (int, bool):
    caller_currency = get_user_currency(caller_obj, channel_id)
    target_currency = get_user_currency(target_obj, channel_id)
    percentage = random.uniform(0.05 + critical * 0.245, 0.35 + critical * 0.35)
    stolen_amount = max(1, round(percentage * target_currency))
    set_user_currency(caller_obj, channel_id, caller_currency + stolen_amount)

    target_died = target_currency - stolen_amount < 1
    if target_died:
        set_user_currency(target_obj, channel_id, 1)
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


def get_user_currency(user_obj: dict, channel_id: str) -> int:
    return user_obj.get("currency", {}).get(channel_id, 1)


def set_user_currency(user_obj: dict, channel_id: str, currency: int) -> None:
    if "currency" not in user_obj:
        user_obj["currency"] = {}

    user_obj["currency"][channel_id] = currency


def get_chance_from_currency(currency: int) -> float:
    a = 0.333 # Increase to elevate rate of failure growth
    # 0.333 means failure is close to 100% around 1 million currency
    b = 0.0 # Increase to reduce fail rate for all people
    c = -20.0  # Increase to move function towards third quadrant
    # aka increases the "poor person threshold from 1 to 5"
    d = 0.0  # Increase to give more fail chance for poor people
    x = float(currency)
    chance = ((x**a - c) + (d / (x - c))) - b
    return 1 - (chance / 100)


def roll(chance: Union[float, str]) -> bool:
    return random.random() < chance
