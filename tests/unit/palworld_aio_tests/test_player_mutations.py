from __future__ import annotations

from tests.dynamic_importer import import_from


player_mutations = import_from('palworld_aio.world.player_mutations')

PLAYER_UID = '22222222-2222-2222-2222-222222222222'


def _property(value):
    return {'value': value}


def _player_save_parameter():
    return {
        'IsPlayer': _property(True),
        'GotStatusPointList': {
            'value': {
                'values': [
                    {'StatusName': _property('Health'), 'StatusPoint': _property(1)},
                    {'StatusName': _property('Stamina'), 'StatusPoint': _property(2)},
                ],
            },
        },
        'GotExStatusPointList': {
            'value': {
                'values': [
                    {'StatusName': _property('Attack'), 'StatusPoint': _property(3)},
                ],
            },
        },
        'UnusedStatusPoint': _property(4),
    }


def _world_save_data():
    save_parameter = _player_save_parameter()
    return {
        'GroupSaveDataMap': {
            'value': [{
                'key': 'guild-id',
                'value': {
                    'RawData': {
                        'value': {
                            'players': [{
                                'player_uid': PLAYER_UID,
                                'player_info': {'player_name': 'Before'},
                            }],
                        },
                    },
                },
            }],
        },
        'CharacterSaveParameterMap': {
            'value': [{
                'key': {'PlayerUId': _property(PLAYER_UID)},
                'value': {
                    'RawData': {
                        'value': {
                            'object': {
                                'SaveParameter': {
                                    'struct_type': 'PalIndividualCharacterSaveParameter',
                                    'value': save_parameter,
                                },
                            },
                        },
                    },
                },
            }],
        },
    }


def _save_parameter(world_save_data):
    return (
        world_save_data['CharacterSaveParameterMap']['value'][0]['value']['RawData']
        ['value']['object']['SaveParameter']['value']
    )


def test_rename_player_updates_guild_and_character_body():
    world_save_data = _world_save_data()

    assert player_mutations.rename_player(world_save_data, PLAYER_UID, 'After') is True

    player = world_save_data['GroupSaveDataMap']['value'][0]['value']['RawData']['value']['players'][0]
    assert player['player_info']['player_name'] == 'After'
    assert _save_parameter(world_save_data)['NickName'] == {
        'id': None,
        'type': 'StrProperty',
        'value': 'After',
    }


def test_set_player_level_adds_missing_properties_and_returns_normalized_uid():
    world_save_data = _world_save_data()

    changed, normalized_uid = player_mutations.set_player_level(
        world_save_data,
        PLAYER_UID,
        6,
        {'6': {'TotalEXP': 600}},
    )

    save_parameter = _save_parameter(world_save_data)
    assert changed is True
    assert normalized_uid == PLAYER_UID.replace('-', '')
    assert save_parameter['Level']['value']['value'] == 6
    assert save_parameter['Exp']['value'] == 600
    assert player_mutations.set_player_level(world_save_data, PLAYER_UID, 81, {}) == (False, '')


def test_set_player_stats_updates_both_status_lists_and_unused_points():
    world_save_data = _world_save_data()

    assert player_mutations.set_player_stats(
        world_save_data,
        PLAYER_UID,
        {'Health': 9, 'Attack': 8},
    ) is True

    save_parameter = _save_parameter(world_save_data)
    base_values = save_parameter['GotStatusPointList']['value']['values']
    extra_values = save_parameter['GotExStatusPointList']['value']['values']
    assert base_values[0]['StatusPoint']['value'] == 9
    assert base_values[1]['StatusPoint']['value'] == 2
    assert extra_values[0]['StatusPoint']['value'] == 8
    assert save_parameter['UnusedStatusPoint']['value'] == 0
