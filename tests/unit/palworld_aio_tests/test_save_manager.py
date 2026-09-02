from __future__ import annotations

from tests.dynamic_importer import import_from

constants = import_from('palworld_aio.constants')
save_manager_module = import_from('palworld_aio.managers.save_manager')
player_manager_module = import_from('palworld_aio.managers.player_manager')
data_manager_module = import_from('palworld_aio.managers.data_manager')


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


def test_data_manager_guild_members_preserve_display_contract():
    old_document = constants.loaded_level_json
    old_player_levels = constants.player_levels
    old_pal_counts = constants.PLAYER_PAL_COUNTS
    try:
        constants.loaded_level_json = _loaded_document()
        constants.player_levels = {PLAYER_UID.replace('-', ''): 7}
        constants.PLAYER_PAL_COUNTS = {PLAYER_UID.replace('-', ''): 3}

        assert data_manager_module.get_guild_members(GUILD_ID) == [{
            'uid': PLAYER_UID,
            'name': 'Alice',
            'lastseen': '10s ago',
            'last_sort': 10.0,
            'level': 7,
            'pals': 3,
            'is_leader': True,
            'role': 3,
            'role_label': 'Member',
        }]
    finally:
        constants.loaded_level_json = old_document
        constants.player_levels = old_player_levels
        constants.PLAYER_PAL_COUNTS = old_pal_counts


ZERO_UUID = '00000000-0000-0000-0000-000000000000'


def _dps_entry(inst_id: str, char_id: str = 'SheepBall') -> dict:
    return {
        'SaveParameter': {'value': {'CharacterID': {'value': char_id}}},
        'InstanceId': {'value': {'InstanceId': {'value': {'ID': {'value': inst_id}}}}},
    }


def test_dps_entry_instance_id_reads_entry_level_guid():
    entry = _dps_entry('9e03be9f-4537-f66d-f914-a99977f681e3')
    assert save_manager_module._dps_entry_instance_id(entry) == '9e03be9f-4537-f66d-f914-a99977f681e3'


def test_dps_entry_instance_id_handles_missing_or_malformed():
    assert save_manager_module._dps_entry_instance_id({}) == ''
    assert save_manager_module._dps_entry_instance_id({'InstanceId': {'value': {}}}) == ''
    assert save_manager_module._dps_entry_instance_id({'InstanceId': {'value': {'InstanceId': {'value': None}}}}) == ''
    assert save_manager_module._dps_entry_instance_id({'InstanceId': 7}) == ''


def test_dps_scan_dedupes_placeholder_entries(monkeypatch, tmp_path):
    """Glitched files pad the array with thousands of all-zero placeholders.

    The scan must collapse them so the worker stays O(unique pals); the save
    file itself is never touched by this path.
    """
    entries = (
        [_dps_entry(ZERO_UUID, 'None')] * 8000
        + [_dps_entry(f'{i + 1:08x}-0000-0000-0000-000000000000') for i in range(50)]
        + [_dps_entry('0000000a-0000-0000-0000-000000000000')]
    )
    monkeypatch.setattr(save_manager_module, 'sav_to_gvasfile', lambda path: type(
        'FakeGvas', (), {'properties': {'SaveParameterArray': {'value': {'values': entries}}}})())
    monkeypatch.setattr(save_manager_module, 'load_game_data_map', lambda fname, key: {})

    uid, pname, formatted, illegal = save_manager_module._process_dps_scan_worker(
        ('uid-1', 'Tester', str(tmp_path / 'dps.sav'), str(tmp_path)))

    # 8000 zero placeholders collapse to 1 + 50 unique pals; 'None' CharacterID
    # entries are skipped for the log, so 50 formatted pals remain.
    assert len(formatted) == 50
    assert illegal == []
