import os
from decimal import Decimal

import pytest

import slapyou2

START_HP = Decimal(os.environ.get("REVIVE_HP", "10"))
ZERO_HP = Decimal(0)


@pytest.fixture
def test_data():
    sample_caller_ddb = {"userId": "callerId", "currency": {"channelId": Decimal(10)}}

    sample_target_ddb = {"userId": "targetId", "currency": {"channelId": Decimal(10)}}

    sample_slap_info = {
        "caller": {"name": "callerName", "id": "callerId", "ddb": sample_caller_ddb},
        "target": {"name": "targetName", "id": "targetId", "ddb": sample_target_ddb},
        "channelId": "channelId",
        "output": [],
    }

    return sample_slap_info


def test_slap_new_players(mocker, test_data):
    mocker.patch("dynamodb_api.get_item", return_value=None)
    mocker.patch("dynamodb_api.update_item")
    test_data["caller"].pop("ddb", None)
    test_data["target"].pop("ddb", None)

    slapyou2.slap(test_data)

    assert test_data["caller"]["ddb"] is not None
    assert test_data["target"]["ddb"] is not None


def test_slap_new_caller(mocker, test_data):
    mocker.patch("dynamodb_api.get_item", return_value=None)
    mocker.patch("dynamodb_api.update_item")
    test_data["caller"].pop("ddb", None)

    slapyou2.slap(test_data)

    assert test_data["caller"]["ddb"] is not None
    assert test_data["target"]["ddb"] is not None


def test_slap_new_target(mocker, test_data):
    mocker.patch("dynamodb_api.get_item", return_value=None)
    mocker.patch("dynamodb_api.update_item")
    test_data["target"].pop("ddb", None)

    slapyou2.slap(test_data)

    assert test_data["caller"]["ddb"] is not None
    assert test_data["target"]["ddb"] is not None


def test_hit(mocker, test_data):
    mocker.patch("slapyou2.is_crit", return_value=False)

    slapyou2.hit(test_data)

    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp > START_HP
    assert target_hp > ZERO_HP


def test_crit_hit(mocker, test_data):
    mocker.patch("slapyou2.is_crit", return_value=True)
    min_crit_dmg_percent = Decimal(os.environ.get("MIN_CRIT_DMG_PERCENT", "0.5"))

    slapyou2.hit(test_data)

    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp >= START_HP + Decimal(1) + (START_HP * min_crit_dmg_percent)
    assert target_hp > ZERO_HP


def test_miss(mocker, test_data):
    mocker.patch("slapyou2.is_crit", return_value=False)

    slapyou2.miss(test_data)

    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp == START_HP
    assert target_hp == START_HP


def test_crit_miss(mocker, test_data):
    mocker.patch("slapyou2.is_crit", return_value=True)
    crit_miss_comp_percent = Decimal(os.environ.get("CRIT_MISS_COMP_PERCENT", "0.5"))

    slapyou2.miss(test_data)

    caller_hp, target_hp = get_hp_helper(test_data)
    assert caller_hp == START_HP
    assert target_hp == START_HP + (crit_miss_comp_percent * START_HP)
    assert (caller_hp + target_hp) > 2 * START_HP


def get_hp_helper(data):
    caller_hp = data["caller"]["ddb"]["currency"]["channelId"]
    target_hp = data["target"]["ddb"]["currency"]["channelId"]
    return caller_hp, target_hp
