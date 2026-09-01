from __future__ import annotations

from tests.dynamic_importer import import_from

constants = import_from('palworld_aio.constants')
save_manager_module = import_from('palworld_aio.managers.save_manager')
player_manager_module = import_from('palworld_aio.managers.player_manager')


GUILD_ID = '11111111-1111-1111-1111-111111111111'
PLAYER_UID = '22222222-2222-2222-2222-222222222222'


def _loaded_document() -> dict:
    return {
        'properties': {
            'worldSaveData': {
                'value': {
                    'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 1000000000}}},
                    'GroupSaveDataMap': {'value': [{
                        'key': GUILD_ID,
                        'value': {
                            'GroupType': {'value': {'value': 'EPalGroupType::Guild'}},
                            'RawData': {'value': {
                                'guild_name': 'Test Guild',
                                'base_camp_level': 3,
                                'admin_player_uid': PLAYER_UID,
                                'players': [{
                                    'player_uid': PLAYER_UID,
                                    'player_info': {
                                        'player_name': 'Alice',
                                        'last_online_real_time': 900000000,
                                    },
                                }],
                            }},
                        },
                    }]},
                    'BaseCampSaveData': {'value': [{}]},
                    'CharacterSaveParameterMap': {'value': [
                        {
                            'value': {'RawData': {'value': {'object': {'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {'IsPlayer': {'value': True}},
                            }}}}},
                        },
                        {
                            'value': {'RawData': {'value': {'object': {'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {'IsPlayer': {'value': False}},
                            }}}}},
                        },
                    ]},
                },
            },
        },
    }


def test_save_manager_query_contracts_use_world_projections():
    old_document = constants.loaded_level_json
    old_player_levels = constants.player_levels
    try:
        constants.loaded_level_json = _loaded_document()
        constants.player_levels = {PLAYER_UID.replace('-', ''): 7}
        manager = save_manager_module.save_manager

        assert manager.get_current_stats() == {
            'Players': 1,
            'Guilds': 1,
            'Bases': 1,
            'Pals': 1,
        }
        assert manager.get_players() == [
            (PLAYER_UID, 'Alice', GUILD_ID, '10s ago', 7, 10.0),
        ]
        assert manager.get_guild_name_by_id(GUILD_ID) == 'Test Guild'
        assert manager.get_guild_name_by_id('missing') == 'No Guild'
        assert manager.get_guild_level_by_id(GUILD_ID) == 3
        assert manager.is_player_guild_leader(GUILD_ID, PLAYER_UID)
    finally:
        constants.loaded_level_json = old_document
        constants.player_levels = old_player_levels


def test_player_manager_info_preserves_legacy_display_contract():
    old_document = constants.loaded_level_json
    old_player_levels = constants.player_levels
    old_pal_counts = constants.PLAYER_PAL_COUNTS
    try:
        constants.loaded_level_json = _loaded_document()
        constants.player_levels = {PLAYER_UID.replace('-', ''): 7}
        constants.PLAYER_PAL_COUNTS = {PLAYER_UID.replace('-', ''): 3}

        assert player_manager_module.get_player_info(PLAYER_UID) == {
            'uid': PLAYER_UID,
            'name': 'Alice',
            'level': 7,
            'pals': 3,
            'lastseen': '10s ago',
            'guild_id': GUILD_ID,
            'guild_name': 'Test Guild',
        }
        assert player_manager_module.get_player_info('missing') is None
    finally:
        constants.loaded_level_json = old_document
        constants.player_levels = old_player_levels
        constants.PLAYER_PAL_COUNTS = old_pal_counts
