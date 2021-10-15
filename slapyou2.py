from __future__ import annotations

import os
import random

from logzero import logger

import dynamodb_api
import emote
from decimal import Decimal, ROUND_HALF_DOWN

# slap_info
# caller
#   name, id, ddb
# target
#   name, id, ddb
# channelId
def slap(slap_info: dict):
    # Read in DDB objects, quick GetItem actions
    slap_info["output"] = []
    slap_info["caller"]["ddb"] = dynamodb_api.get_item(slap_info["caller"]["id"])
    slap_info["target"]["ddb"] = dynamodb_api.get_item(slap_info["target"]["id"])

    if is_miss():
        miss(slap_info)
    else:
        hit(slap_info)


def miss(slap_info: dict):
    if is_crit():
        # Critical miss means instant death
        compensation_percent = Decimal(os.environ("CRIT_MISS_COMP_PERCENT", "0.5"))
        caller_hp = slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]]
        compensation_for_target = (caller_hp * compensation_percent).to_integral_value(
            rounding=ROUND_HALF_DOWN
        )
        slap_info["target"]["ddb"]["currency"][
            slap_info["channelId"]
        ] += compensation_for_target
        revive(slap_info["caller"], slap_info["channelId"])

    else:
        # Should misses be gains for the target? Maybe add a feature flag?
        pass


def hit(slap_info: dict):
    pass


def is_miss():
    return random.random() <= float(os.environ.get("MISS_CHANCE", "0.2"))


def is_crit():
    return random.random() <= float(os.environ.get("CRIT_CHANCE", "0.0625"))


# User refers to caller or target
def revive(user_info: dict, channel_id: str):
    revive_hp = os.environ.get("REVIVE_HP", "10")
    user_info["currency"][channel_id] = Decimal(revive_hp)


def get_miss_msg(slap_info: dict) -> str:
    templates = ["{} tries to slap {} but misses"]

    template = random.choice(templates).format(
        slap_info["caller"]["name"], slap_info["target"]["name"]
    )
    return template + f" {emote.get_negative_emote()} !"


def get_crit_miss_msg(slap_info: dict, compensation: str) -> str:
    caller_templates = ["{} ({} HP) slaps themselves in confusion and dies"]
    caller_template = random.choice(caller_templates).format(
        slap_info["caller"]["name"],
        slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]],
    )
    caller_template += f" {emote.get_negative_emote()} "

    target_templates = ["{} ({} HP) yoinks {} HP from the corpse"]
    target_template = random.choice(target_templates).format(
        slap_info["target"]["name"],
        slap_info["target"]["ddb"]["currency"][slap_info["channelId"]],
        compensation,
    )
    target_template += f" {emote.get_positive_emote()} "
    return caller_template + target_template


def get_hit_msg(slap_info: str, damage: Decimal) -> str:
    templates = ["{} ({} HP) slaps {} ({} HP) and takes {} HP"]

    template = random.choice(templates).format(
        slap_info["caller"]["name"],
        slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]],
        slap_info["target"]["name"],
        slap_info["target"]["ddb"]["currency"][slap_info["channelId"]],
        damage,
    )
    return template


def get_crit_hit_msg(slap_info: str, damage: Decimal) -> str:
    templates = ["{} ({} HP) critically slaps {} ({} HP) and takes {} HP"]

    template = random.choice(templates).format(
        slap_info["caller"]["name"],
        slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]],
        slap_info["target"]["name"],
        slap_info["target"]["ddb"]["currency"][slap_info["channelId"]],
        damage,
    )
    return template + f" {emote.get_positive_emote()} !"


def get_revive_msg(user_name: str, hp: str) -> str:
    templates = ["{} has respawned with {} HP"]

    template = random.choice(templates).format(user_name, hp)
    return template
