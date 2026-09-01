from __future__ import annotations
from tests.dynamic_importer import import_from

SaveProjections = import_from('palworld_aio.read_models').SaveProjections


def _wsd():
    return {
        'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 1000000000}}},
        'WorldSaveParameter': {'value': {'WorldName': {'value': 'My World'}}},
        'GroupSaveDataMap': {'value': [
            {
                'key': '11111111-1111-1111-1111-111111111111',
                'value': {
                    'GroupType': {'value': {'value': 'EPalGroupType::Guild'}},
                    'RawData': {'value': {
                        'guild_name': 'Test Guild',
                        'base_camp_level': 2,
                        'admin_player_uid': '22222222-2222-2222-2222-222222222222',
                        'base_ids': ['33333333-3333-3333-3333-333333333333'],
                        'players': [{
                            'player_uid': '22222222-2222-2222-2222-222222222222',
                            'role': 1,
                            'player_info': {
                                'player_name': 'Alice',
                                'last_online_real_time': 900000000,
                            },
                        }],
                    }},
                },
            },
            {
                'key': '44444444-4444-4444-4444-444444444444',
                'value': {
                    'GroupType': {'value': {'value': 'EPalGroupType::NonGuild'}},
                    'RawData': {'value': {'guild_name': 'Not a guild'}},
                },
            },
        ]},
        'BaseCampSaveData': {'value': [
            {
                'key': '33333333-3333-3333-3333-333333333333',
                'value': {
                    'RawData': {'value': {
                        'group_id_belong_to': '11111111-1111-1111-1111-111111111111',
                        'base_camp_level': 3,
                        'base_camp_area_radius': 2000,
                        'transform': {'translation': {'x': 100, 'y': 200, 'z': 300}},
                    }},
                },
            },
        ]},
        'CharacterSaveParameterMap': {'value': [
            {
                'key': {'PlayerUId': {'value': '22222222-2222-2222-2222-222222222222'}},
                'value': {
                    'RawData': {'value': {
                        'object': {
                            'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {'IsPlayer': {'value': True}, 'Level': {'value': 5}},
                            },
                        },
                    }},
                },
            },
            {
                'key': {'InstanceId': {'value': '55555555-5555-5555-5555-555555555555'}},
                'value': {
                    'RawData': {'value': {
                        'object': {
                            'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {'IsPlayer': {'value': False}, 'Level': {'value': 10}},
                            },
                        },
                    }},
                },
            },
        ]},
        'ItemContainerSaveData': {'value': [
            {
                'key': {'ID': {'value': '66666666-6666-6666-6666-666666666666'}},
                'value': {'Slots': {'value': {'values': [{'slot': 0}, {'slot': 1}]}}},
            },
        ]},
        'CharacterContainerSaveData': {'value': [
            {'key': {'ID': {'value': '77777777-7777-7777-7777-777777777777'}}},
        ]},
        'MapObjectSaveData': {'value': {'values': [{'Model': {}}]}},
    }


def test_get_tick():
    assert SaveProjections.get_tick(_wsd()) == 1000000000


def test_get_world_name():
    assert SaveProjections.get_world_name(_wsd()) == 'My World'
    assert SaveProjections.get_world_name({'WorldSaveParameter': {}}) == 'World'


def test_get_guilds_filters_non_guild():
    guilds = SaveProjections.get_guilds(_wsd())
    assert len(guilds) == 1
    g = guilds[0]
    assert g['id'] == '11111111-1111-1111-1111-111111111111'
    assert g['name'] == 'Test Guild'
    assert g['level'] == 2
    assert g['member_count'] == 1
    assert g['base_ids'] == ['33333333-3333-3333-3333-333333333333']


def test_get_guild_members():
    members = SaveProjections.get_guild_members(_wsd(), '11111111-1111-1111-1111-111111111111')
    assert len(members) == 1
    assert members[0]['name'] == 'Alice'
    assert members[0]['role'] == 1
    assert members[0]['elapsed'] == 10.0
    assert members[0]['is_leader'] is True
    assert SaveProjections.get_guild_members(_wsd(), '00000000-0000-0000-0000-000000000000') == []


def test_get_guild_id_for_player():
    gid = SaveProjections.get_guild_id_for_player(_wsd(), '22222222-2222-2222-2222-222222222222')
    assert gid == '11111111-1111-1111-1111-111111111111'
    assert SaveProjections.get_guild_id_for_player(_wsd(), 'nobody') is None


def test_get_guild_name():
    assert SaveProjections.get_guild_name(_wsd(), '11111111-1111-1111-1111-111111111111') == 'Test Guild'
    assert SaveProjections.get_guild_name(_wsd(), 'zzz') == 'Unknown Guild'


def test_get_guild_entry_and_leadership():
    guild = SaveProjections.get_guild_entry(_wsd(), '11111111-1111-1111-1111-111111111111')
    assert guild is not None
    assert SaveProjections.is_guild_leader(
        _wsd(),
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
    )
    assert not SaveProjections.is_guild_leader(_wsd(), 'zzz', '22222222-2222-2222-2222-222222222222')


def test_get_player_rows():
    rows = SaveProjections.get_player_rows(
        _wsd(),
        player_levels={'22222222222222222222222222222222': 7},
    )
    assert rows == [{
        'uid': '22222222-2222-2222-2222-222222222222',
        'name': 'Alice',
        'guild_id': '11111111-1111-1111-1111-111111111111',
        'elapsed': 10.0,
        'level': 7,
    }]


def test_get_player_info():
    info = SaveProjections.get_player_info(_wsd(), '22222222-2222-2222-2222-222222222222',
                                           player_levels={'22222222222222222222222222222222': 7},
                                           pal_counts={'22222222222222222222222222222222': 3})
    assert info is not None
    assert info['name'] == 'Alice'
    assert info['level'] == 7
    assert info['pals'] == 3
    assert info['guild_name'] == 'Test Guild'
    assert info['lastseen'] == 10.0


def test_get_player_info_missing():
    assert SaveProjections.get_player_info(_wsd(), 'nobody') is None


def test_get_player_char_entries():
    entries = SaveProjections.get_player_char_entries(_wsd())
    assert len(entries) == 1
    assert SaveProjections.get_save_param(entries[0])['IsPlayer']['value'] is True


def test_get_pal_char_entries():
    entries = SaveProjections.get_pal_char_entries(_wsd())
    assert len(entries) == 1
    assert SaveProjections.get_save_param(entries[0])['Level']['value'] == 10


def test_get_player_save_param():
    sp = SaveProjections.get_player_save_param(_wsd(), '22222222-2222-2222-2222-222222222222')
    assert sp is not None
    assert sp['Level']['value'] == 5


def test_get_world_stats():
    assert SaveProjections.get_world_stats(_wsd()) == {
        'Players': 1,
        'Guilds': 1,
        'Bases': 1,
        'Pals': 1,
    }


def test_get_bases():
    bases = SaveProjections.get_bases(_wsd())
    assert len(bases) == 1
    b = bases[0]
    assert b['id'] == '33333333-3333-3333-3333-333333333333'
    assert b['x'] == 100 and b['y'] == 200 and b['z'] == 300
    assert b['area_radius'] == 2000


def test_get_base_by_id():
    b = SaveProjections.get_base_by_id(_wsd(), '33333333-3333-3333-3333-333333333333')
    assert b is not None and b['level'] == 3
    assert SaveProjections.get_base_by_id(_wsd(), 'zzz') is None


def test_get_base_coords():
    coords = SaveProjections.get_base_coords(_wsd(), '33333333-3333-3333-3333-333333333333')
    assert coords == (100, 200, 300)
    assert SaveProjections.get_base_coords(_wsd(), 'zzz') is None


def test_get_container_by_id():
    cont = SaveProjections.get_container_by_id(_wsd(), '66666666-6666-6666-6666-666666666666')
    assert cont is not None
    assert SaveProjections.get_container_by_id(_wsd(), 'zzz') is None


def test_get_container_slot_count():
    assert SaveProjections.get_container_slot_count(_wsd(), '66666666-6666-6666-6666-666666666666') == 2
    assert SaveProjections.get_container_slot_count(_wsd(), 'zzz') == 0


def test_get_container_contents():
    contents = SaveProjections.get_container_contents(_wsd(), '66666666-6666-6666-6666-666666666666')
    assert len(contents) == 2
    assert contents[0] == {'slot': 0}
