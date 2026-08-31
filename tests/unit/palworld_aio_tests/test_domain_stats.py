from __future__ import annotations
from tests.dynamic_importer import import_from

_utils = import_from('palworld_aio.domain.stats')

calculate_max_hp = _utils.calculate_max_hp
calculate_shot_attack = _utils.calculate_shot_attack
calculate_attack = _utils.calculate_attack
calculate_defense = _utils.calculate_defense
calculate_work_speed = _utils.calculate_work_speed
get_friendship_rank = _utils.get_friendship_rank

# Sample pal data matching the characters.json structure used in-game.
PAL_DATA = {
    'scaling': {'hp': 90, 'attack': 90, 'defense': 90},
    'stats': {'shot_attack': 75, 'defense': 90, 'craft_speed': 100},
    'friendship_hp': 4.5,
    'friendship_shotattack': 3.5,
    'friendship_defense': 2.9,
}


def test_get_friendship_rank_thresholds():
    thr = [0, 6000, 13000, 21000, 30000, 40000, 55000, 80000, 110000, 150000, 200000]
    for i, t in enumerate(thr):
        assert get_friendship_rank(t) == i, f'Expected {i} at {t}'


def test_calculate_max_hp_zero_without_data():
    assert calculate_max_hp(None, 50) == 0


def test_calculate_max_hp_base_grows_with_level():
    low = calculate_max_hp(PAL_DATA, 1, 0, 0)
    high = calculate_max_hp(PAL_DATA, 80, 0, 0)
    assert low > 0
    assert high > low


def test_calculate_max_hp_scales_with_iv_and_soul():
    base = calculate_max_hp(PAL_DATA, 50, 0, 0)
    with_iv = calculate_max_hp(PAL_DATA, 50, 100, 0)
    with_soul = calculate_max_hp(PAL_DATA, 50, 0, 20)
    assert with_iv > base
    assert with_soul > base


def test_calculate_max_hp_awake_bonus():
    base = calculate_max_hp(PAL_DATA, 50, 0, 0, is_awake=False)
    awake = calculate_max_hp(PAL_DATA, 50, 0, 0, is_awake=True)
    assert awake > base


def test_calculate_shot_attack_zero_without_data():
    assert calculate_shot_attack(None, 50) == 0


def test_calculate_shot_attack_grows_with_level():
    low = calculate_shot_attack(PAL_DATA, 1)
    high = calculate_shot_attack(PAL_DATA, 80)
    assert low > 0
    assert high > low


def test_calculate_shot_attack_iv_and_condenser():
    base = calculate_shot_attack(PAL_DATA, 50, 0, 0, condenser_rank=1)
    with_iv = calculate_shot_attack(PAL_DATA, 50, 100, 0, condenser_rank=1)
    with_cond = calculate_shot_attack(PAL_DATA, 50, 0, 0, condenser_rank=5)
    assert with_iv > base
    assert with_cond > base


def test_calculate_attack_delegates():
    assert calculate_attack(PAL_DATA, 50, 10, 2) == calculate_shot_attack(PAL_DATA, 50, 10, 2)


def test_calculate_defense_zero_without_data():
    assert calculate_defense(None, 50) == 0


def test_calculate_defense_grows_with_level():
    low = calculate_defense(PAL_DATA, 1)
    high = calculate_defense(PAL_DATA, 80)
    assert low > 0
    assert high > low


def test_calculate_work_speed_zero_without_data():
    assert calculate_work_speed(None, 50) == 0


def test_calculate_work_speed_condenser_bonus():
    base = calculate_work_speed(PAL_DATA, 50, 0, condenser_rank=1)
    with_cond = calculate_work_speed(PAL_DATA, 50, 0, condenser_rank=5)
    assert with_cond >= base
