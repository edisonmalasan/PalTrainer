from __future__ import annotations

from tests.dynamic_importer import import_from


check_is_illegal_pal = import_from(
    'palworld_aio.world.diagnostics',
).check_is_illegal_pal


def _property(value):
    return {'value': value}


def _pal_entry(save_parameter):
    return {
        'value': {
            'RawData': {
                'value': {
                    'object': {
                        'SaveParameter': {
                            'value': save_parameter,
                        },
                    },
                },
            },
        },
    }


def test_illegal_pal_diagnostic_reports_each_supported_limit():
    save_parameter = {
        'Level': _property(81),
        'Talent_HP': _property(101),
        'Talent_Shot': _property(101),
        'Talent_Defense': _property(101),
        'Rank_HP': _property(21),
        'Rank_Attack': _property(21),
        'Rank_Defence': _property(21),
        'Rank_CraftSpeed': _property(21),
        'PassiveSkillList': {'value': {'values': ['A', 'A', 'B', 'C', 'D']}},
        'EquipWaza': {'value': {'values': ['A', 'B', 'C', 'D']}},
        'Rank': _property(6),
    }

    is_illegal, markers = check_is_illegal_pal(_pal_entry(save_parameter))

    assert is_illegal is True
    assert markers == [
        'Level',
        'HP IV',
        'ATK IV',
        'DEF IV',
        'HP Soul',
        'ATK Soul',
        'DEF Soul',
        'Craft Soul',
        '>4 Passives',
        'Duplicate Passives',
        '>3 Active Skills',
        '>4 Stars',
    ]


def test_illegal_pal_diagnostic_accepts_player_storage_shape_and_malformed_entries():
    legal_save_parameter = {
        'Level': _property(80),
        'Talent_HP': _property(100),
        'PassiveSkillList': {'value': ['A', 'B', 'C', 'D']},
        'EquipWaza': {'value': ['A', 'B', 'C']},
        'Rank': _property(5),
    }

    assert check_is_illegal_pal({'SaveParameter': {'value': legal_save_parameter}}) == (False, [])
    assert check_is_illegal_pal({}) == (False, [])
