from __future__ import annotations

from tests.dynamic_importer import import_from

indexes = import_from('palworld_aio.world.indexes')
save_manager = import_from('palworld_aio.managers.save_manager')


OWNER_A = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
OWNER_B = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'


def _character_entry(
    instance_id: str,
    *,
    player_uid: str | None = None,
    owner_uid: str | None = None,
    is_player: bool = False,
    level: int = 1,
    exp: int = 0,
) -> dict:
    save_parameter = {
        'struct_type': 'PalIndividualCharacterSaveParameter',
        'value': {
            'IsPlayer': {'value': is_player},
            'Level': {'value': level},
            'Exp': {'value': exp},
            'LastOnlineRealTime': {'value': 0},
        },
    }
    if owner_uid is not None:
        save_parameter['value']['OwnerPlayerUId'] = {'value': owner_uid}
    key = {'InstanceId': {'value': instance_id}}
    if player_uid is not None:
        key['PlayerUId'] = {'value': player_uid}
    return {
        'key': key,
        'value': {'RawData': {'value': {'object': {'SaveParameter': save_parameter}}}},
    }


def _world_save_data() -> dict:
    return {
        'CharacterSaveParameterMap': {
            'value': [
                _character_entry(
                    '11111111-1111-1111-1111-111111111111',
                    player_uid=OWNER_A,
                    is_player=True,
                    level=17,
                    exp=100,
                ),
                _character_entry(
                    '22222222-2222-2222-2222-222222222222',
                    player_uid=OWNER_A,
                    is_player=True,
                    level=42,
                    exp=200,
                ),
                _character_entry(
                    '33333333-3333-3333-3333-333333333333',
                    owner_uid=OWNER_A,
                ),
                _character_entry(
                    '44444444-4444-4444-4444-444444444444',
                    owner_uid=OWNER_A,
                ),
                _character_entry(
                    '55555555-5555-5555-5555-555555555555',
                    owner_uid=OWNER_B,
                ),
            ],
        },
        'CharacterContainerSaveData': {'value': []},
    }


def test_build_player_index_selects_canonical_player_body():
    index = indexes.build_player_index(_world_save_data())
    owner_a = OWNER_A.replace('-', '')

    assert index.levels == {owner_a: 42}
    assert index.entries[owner_a]['key']['InstanceId']['value'].startswith('2222')
    assert len(index.duplicates[owner_a]) == 1


def test_count_owned_pals_uses_normalized_effective_owners():
    counts = indexes.count_owned_pals(_world_save_data())

    assert counts == {
        OWNER_A.replace('-', ''): 2,
        OWNER_B.replace('-', ''): 1,
    }


def test_count_owned_pals_returns_empty_for_malformed_world_data():
    assert indexes.count_owned_pals({}) == {}


def test_legacy_save_manager_count_delegates_to_world_index():
    document = {'properties': {'worldSaveData': {'value': _world_save_data()}}}

    assert save_manager.count_owned_pals(document) == indexes.count_owned_pals(
        document['properties']['worldSaveData']['value'],
    )
    assert save_manager.count_owned_pals({}) == {}
