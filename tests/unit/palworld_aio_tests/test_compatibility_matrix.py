from __future__ import annotations
from tests.dynamic_importer import import_from

SaveProjections = import_from('palworld_aio.read_models').SaveProjections
operations = import_from('palworld_aio.managers.operations')
domain_stats = import_from('palworld_aio.domain.stats')
container_types = import_from('palworld_xgp_import.container_types')
shell_state = import_from('palworld_aio.shell_state')


def _wsd():
    return {
        'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 1000000000}}},
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
                            'player_info': {'player_name': 'Alice', 'last_online_real_time': 900000000},
                        }],
                    }},
                },
            },
        ]},
        'BaseCampSaveData': {'value': [
            {
                'key': '33333333-3333-3333-3333-333333333333',
                'value': {
                    'RawData': {'value': {
                        'group_id_belong_to': '11111111-1111-1111-1111-111111111111',
                        'transform': {'translation': {'x': 1, 'y': 2, 'z': 3}},
                    }},
                },
            },
        ]},
        'MapObjectSaveData': {'value': {'values': [
            {
                'MapObjectId': {'value': 'DroppedCharacter'},
                'ConcreteModel': {'value': {'RawData': {'value': {
                    'instance_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                    'stored_parameter_id': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
                }}}},
            },
        ]}},
        'CharacterSaveParameterMap': {'value': [
            {
                'key': {'InstanceId': {'value': 'cccccccc-cccc-cccc-cccc-cccccccccccc'}},
                'value': {
                    'RawData': {'value': {'object': {'SaveParameter': {
                        'struct_type': 'PalIndividualCharacterSaveParameter',
                        'value': {
                            'OwnerPlayerUId': {'value': '22222222-2222-2222-2222-222222222222'},
                            'IsPlayer': {'value': False},
                        },
                    }}}},
                },
            },
        ]},
        'CharacterContainerSaveData': {'value': []},
        'ItemContainerSaveData': {'value': []},
    }


# ---------------------------------------------------------------------------
# Compatibility matrix: the refactored read/operation/domain layers agree
# with each other on the same save document (plan 012 regression gate).
# ---------------------------------------------------------------------------

def test_projections_and_operations_agree_on_guilds():
    wsd = _wsd()
    guilds = SaveProjections.get_guilds(wsd)
    assert len(guilds) == 1
    assert guilds[0]['member_count'] == 1
    members = SaveProjections.get_guild_members(wsd, '11111111-1111-1111-1111-111111111111')
    assert len(members) == 1
    assert members[0]['name'] == 'Alice'
    assert members[0]['elapsed'] == 10.0


def test_projection_tick_matches_container_time_scale():
    wsd = _wsd()
    assert SaveProjections.get_tick(wsd) == 1000000000


def test_death_bag_collection_feeds_protection_semantics():
    wsd = _wsd()
    result = operations.collect_death_bag_ids(wsd)
    assert 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' in result.protected_instance_ids
    assert 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' in result.protected_instance_ids
    assert operations.is_dropped_character({'MapObjectId': {'value': 'DroppedCharacter'}})
    assert operations.is_death_bag({'MapObjectId': {'value': 'DeathPenaltyChest'}})


def test_character_operations_preserve_player_bodies():
    wsd = _wsd()
    result = operations.delete_player_pals(wsd, ['22222222-2222-2222-2222-222222222222'])
    assert result.changed_entities == 1
    assert len(wsd['CharacterSaveParameterMap']['value']) == 0


def test_domain_stats_are_positive_on_valid_pal_data():
    pal = {
        'scaling': {'hp': 90, 'attack': 90, 'defense': 90},
        'stats': {'shot_attack': 75, 'defense': 90, 'craft_speed': 100},
        'friendship_hp': 4.5,
    }
    assert domain_stats.calculate_max_hp(pal, 50, 0, 0) > 0
    assert domain_stats.calculate_shot_attack(pal, 50, 0, 0) > 0
    assert domain_stats.calculate_defense(pal, 50, 0, 0) > 0
    assert domain_stats.get_friendship_rank(200000) == 10


def test_container_types_roundtrip_and_shell_state_agree_on_loaded_lifecycle():
    ft = container_types.FILETIME.from_timestamp(1700000000.0)
    idx = container_types.ContainerIndex(
        flag1=0, package_name='Test', mtime=ft, flag2=0,
        index_uuid='idx', unknown=0, containers=[],
    )
    assert idx.get_save_containers('Missing') == {}

    m = shell_state.ShellStateModel()
    m.begin_load()
    m.finish_load(True)
    assert m.state == shell_state.ShellState.LOADED
    assert m.state.can_save
