import json
from decimal import Decimal
import os
import pytest
from logzero import logger

import slapyou2

START_HP = Decimal(os.environ.get("REVIVE_HP", "10"))


@pytest.fixture
def test_data():
    sample_caller_ddb = {
    "userId": "callerId",
    "currency": {
        "channelId": Decimal(10)
    }
}

    sample_target_ddb = {
        "userId": "targetId",
        "currency": {
            "channelId": Decimal(10)
        }
    }

    sample_slap_info = {
        "caller": {
            "name": "callerName",
            "id": "callerId",
            "ddb": sample_caller_ddb
        },
        "target": {
            "name": "targetName",
            "id": "targetId",
            "ddb": sample_target_ddb
        },
        "channelId": "channelId",
        "output": []
    }

    return sample_slap_info


def test_hit(test_data):
    slapyou2.hit(test_data)
    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp > START_HP
    assert target_hp < START_HP
    assert (caller_hp + target_hp) == 2 * START_HP


def test_miss(mocker, test_data):
    mocker.patch("slapyou2.is_crit", return_value=False)
    slapyou2.miss(test_data)
    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp == START_HP
    assert target_hp == START_HP
    assert (caller_hp + target_hp) == 2 * START_HP


def get_hp_helper(data):
    caller_hp = data["caller"]["ddb"]["currency"]["channelId"]
    target_hp = data["target"]["ddb"]["currency"]["channelId"]
    return caller_hp, target_hp
