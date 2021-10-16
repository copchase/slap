from __future__ import annotations
import json

import os
import random
from decimal import ROUND_HALF_DOWN, Decimal

from logzero import logger

import dynamodb_api
import emote


# slap_info
# caller
#   name, id, ddb
# target
#   name, id, ddb
# channelId
def slap(slap_info: dict):
    # Read in DDB objects, quick GetItem actions
    logger.info(
        f"incoming slap event: {json.dumps(slap_info, default=json_dumps_helper)}"
    )
    slap_info["caller"]["ddb"] = dynamodb_api.get_item(slap_info["caller"]["id"])
    slap_info["target"]["ddb"] = dynamodb_api.get_item(slap_info["target"]["id"])
    logger.debug("read from ddb")
    write_needed = True
    if is_miss():
        write_needed = miss(slap_info)
    else:
        hit(slap_info)

    # Write to disk
    if write_needed:
        dynamodb_api.update_item(slap_info["caller"]["id"], slap_info["caller"]["ddb"])
        dynamodb_api.update_item(slap_info["target"]["id"], slap_info["target"]["ddb"])
        logger.debug("wrote to ddb")

    logger.info(
        f"Slap event completed: {json.dumps(slap_info, default=json_dumps_helper)}"
    )


def miss(slap_info: dict):
    if is_crit():
        # Critical miss means instant death
        compensation_percent = Decimal(os.environ.get("CRIT_MISS_COMP_PERCENT", "0.5"))
        caller_hp = slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]]
        compensation = (caller_hp * compensation_percent).to_integral_value(
            rounding=ROUND_HALF_DOWN
        )
        slap_info["target"]["ddb"]["currency"][slap_info["channelId"]] += compensation
        revive_msg = revive(slap_info["caller"], slap_info["channelId"])
        slap_info["output"].append(get_crit_miss_msg(slap_info, compensation))
        slap_info["output"].append(revive_msg)
        return True
    else:
        # Should misses be gains for the target? Maybe add a feature flag?
        slap_info["output"].append(get_miss_msg(slap_info))
        return False


def hit(slap_info: dict):
    base_damage = get_base_damage()
    caller_hp = slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]]
    target_hp = slap_info["target"]["ddb"]["currency"][slap_info["channelId"]]
    damage = min(target_hp, base_damage)
    if is_crit():
        damage = min(target_hp, damage + get_crit_damage(slap_info))
        slap_info["output"].append(get_crit_hit_msg(slap_info, damage))
    else:
        slap_info["output"].append(get_hit_msg(slap_info, damage))

    caller_hp += damage
    target_hp -= damage

    # Reassign on objects
    slap_info["caller"]["ddb"]["currency"][slap_info["channelId"]] = caller_hp
    slap_info["target"]["ddb"]["currency"][slap_info["channelId"]] = target_hp

    if target_hp <= Decimal(0):
        # target is dead
        revive(slap_info["target"], slap_info["channelId"])


def is_miss():
    return random.random() <= float(os.environ.get("MISS_CHANCE", "0.2"))


def is_crit():
    return random.random() <= float(os.environ.get("CRIT_CHANCE", "0.0625"))


# User refers to caller or target
def revive(user_info: dict, channel_id: str):
    revive_hp = os.environ.get("REVIVE_HP", "10")
    user_info["ddb"]["currency"][channel_id] = Decimal(revive_hp)
    return get_revive_msg(user_info["name"], revive_hp)


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


def get_base_damage() -> Decimal:
    damage = random.randint(1, int(os.environ.get("REVIVE_HP", "10")))
    return Decimal(damage)


def get_crit_damage(slap_info: dict) -> Decimal:
    min_crit_dmg_percent = float(os.environ.get("MIN_CRIT_DMG_PERCENT", "0.5"))
    max_crit_dmg_percent = float(os.environ.get("MAX_CRIT_DMG_PERCENT", "0.75"))
    crit_dmg_percent = Decimal(
        random.uniform(min_crit_dmg_percent, max_crit_dmg_percent)
    )
    target_hp = slap_info["target"]["ddb"]["currency"][slap_info["channelId"]]
    crit_dmg = (target_hp * crit_dmg_percent).to_integral_value(
        rounding=ROUND_HALF_DOWN
    )

    return crit_dmg


def json_dumps_helper(x):
    if isinstance(x, Decimal):
        return str(x)

    raise TypeError(f"Object of type {type(x)} is not JSON serializable")
