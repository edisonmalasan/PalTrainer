from __future__ import annotations
from tests.dynamic_importer import import_from

ops = import_from('palworld_aio.managers.operations')

OperationResult = ops.OperationResult


def _wsd():
    return {
        'MapObjectSaveData': {'value': {'values': [
            {
                'MapObjectId': {'value': 'DroppedCharacter'},
                'ConcreteModel': {'value': {'RawData': {'value': {
                    'instance_id': '11111111-1111-1111-1111-111111111111',
                    'stored_parameter_id': '22222222-2222-2222-2222-222222222222',
                }}}},
            },
            {
                'MapObjectId': {'value': 'DeathPenaltyChest'},
                'ConcreteModel': {'value': {'RawData': {'value': {
                    'instance_id': '33333333-3333-3333-3333-333333333333',
                }}, 'ModuleMap': {'value': [
                    {'key': 'EPalMapObjectConcreteModelModuleType::ItemContainer',
                     'value': {'RawData': {'value': {
                         'target_container_id': '44444444-4444-4444-4444-444444444444',
                     }}}},
                ]}}},
            },
            {
                'MapObjectId': {'value': 'SomeOtherObject'},
                'ConcreteModel': {'value': {'RawData': {'value': {}}}},
            },
        ]}},
        'CharacterSaveParameterMap': {'value': [
            {
                'key': {'InstanceId': {'value': '55555555-5555-5555-5555-555555555555'}},
                'value': {
                    'RawData': {'value': {
                        'object': {
                            'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {
                                    'OwnerPlayerUId': {'value': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'},
                                    'IsPlayer': {'value': False},
                                },
                            },
                        },
                    }},
                },
            },
            {
                'key': {'InstanceId': {'value': '66666666-6666-6666-6666-666666666666'}},
                'value': {
                    'RawData': {'value': {
                        'object': {
                            'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {
                                    'OwnerPlayerUId': {'value': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'},
                                    'IsPlayer': {'value': False},
                                },
                            },
                        },
                    }},
                },
            },
            {
                'key': {'InstanceId': {'value': '77777777-7777-7777-7777-777777777777'}},
                'value': {
                    'RawData': {'value': {
                        'object': {
                            'SaveParameter': {
                                'struct_type': 'PalIndividualCharacterSaveParameter',
                                'value': {
                                    'OwnerPlayerUId': {'value': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'},
                                    'IsPlayer': {'value': False},
                                },
                            },
                        },
                    }},
                },
            },
        ]},
        'CharacterContainerSaveData': {'value': [
            {'key': {'ID': {'value': 'cccccccc-cccc-cccc-cccc-cccccccccccc'}},
             'value': {'Slots': {'value': {'values': []}}}},
        ]},
    }


# ---------------------------------------------------------------------------
# OperationResult
# ---------------------------------------------------------------------------

def test_operation_result_defaults():
    r = OperationResult()
    assert r.changed_entities == 0
    assert r.warnings == []
    assert r.deleted_files == []
    assert r.confirmation_required is False
    assert r.ok is True


def test_operation_result_merge():
    a = OperationResult(changed_entities=2, warnings=['w1'], confirmation_required=True)
    b = OperationResult(changed_entities=3, deleted_files=['f1'], ok=False)
    a.merge(b)
    assert a.changed_entities == 5
    assert a.warnings == ['w1']
    assert a.deleted_files == ['f1']
    assert a.confirmation_required is True
    assert a.ok is False


# ---------------------------------------------------------------------------
# Death-bag helpers
# ---------------------------------------------------------------------------

def test_is_dropped_character():
    assert ops.is_dropped_character({'MapObjectId': {'value': 'DroppedCharacter'}}) is True
    assert ops.is_dropped_character({'MapObjectId': {'value': 'DeathPenaltyChest'}}) is False
    assert ops.is_dropped_character({}) is False


def test_is_death_penalty_chest_obj():
    assert ops.is_death_penalty_chest_obj({'MapObjectId': {'value': 'DeathPenaltyChest'}}) is True
    assert ops.is_death_penalty_chest_obj({'MapObjectId': {'value': 'DroppedCharacter'}}) is False


def test_is_death_bag():
    assert ops.is_death_bag({'MapObjectId': {'value': 'DroppedCharacter'}}) is True
    assert ops.is_death_bag({'MapObjectId': {'value': 'DeathPenaltyChest'}}) is True
    assert ops.is_death_bag({'MapObjectId': {'value': 'Other'}}) is False


def test_collect_death_bag_ids():
    wsd = _wsd()
    result = ops.collect_death_bag_ids(wsd)
    assert '11111111111111111111111111111111' in result.protected_instance_ids
    assert '22222222222222222222222222222222' in result.protected_instance_ids
    assert '33333333333333333333333333333333' in result.protected_instance_ids
    assert '44444444444444444444444444444444' in result.protected_container_ids
    assert result.changed_entities == 2


def test_collect_death_bag_ids_empty_wsd():
    result = ops.collect_death_bag_ids({'MapObjectSaveData': {'value': {'values': []}}})
    assert result.protected_instance_ids == set()
    assert result.protected_container_ids == set()
    assert result.changed_entities == 0


# ---------------------------------------------------------------------------
# Character map operations
# ---------------------------------------------------------------------------

def test_delete_player_pals_removes_owned_entries():
    wsd = _wsd()
    result = ops.delete_player_pals(wsd, ['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'])
    assert result.changed_entities == 2
    remaining = wsd['CharacterSaveParameterMap']['value']
    assert len(remaining) == 1
    uid = remaining[0]['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value']
    assert uid == 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'


def test_delete_player_pals_no_matches():
    wsd = _wsd()
    original_count = len(wsd['CharacterSaveParameterMap']['value'])
    result = ops.delete_player_pals(wsd, ['zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz'])
    assert result.changed_entities == 0
    assert len(wsd['CharacterSaveParameterMap']['value']) == original_count


def test_clean_character_save_parameter_map():
    wsd = _wsd()
    valid = {'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}
    result = ops.clean_character_save_parameter_map(wsd, valid)
    assert result.changed_entities == 1
    remaining = wsd['CharacterSaveParameterMap']['value']
    assert len(remaining) == 2


def test_cleanup_player_references_clears_world_links():
    deleted_uid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    wsd = {
        'MapObjectSaveData': {
            'value': {
                'values': [{
                    'Model': {
                        'value': {
                            'RawData': {
                                'value': {
                                    'build_player_uid': deleted_uid,
                                    'stage_instance_id_belong_to': {'id': deleted_uid},
                                },
                            },
                        },
                    },
                }],
            },
        },
        'CharacterContainerSaveData': {
            'value': [{
                'value': {
                    'Slots': {
                        'value': {
                            'values': [{
                                'RawData': {'value': {'player_uid': deleted_uid}},
                            }],
                        },
                    },
                },
            }],
        },
        'GroupSaveDataMap': {
            'value': [{
                'value': {
                    'RawData': {
                        'value': {
                            'individual_character_handle_ids': [
                                {'guid': deleted_uid},
                                {'guid': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'},
                                'legacy-handle',
                            ],
                        },
                    },
                },
            }],
        },
    }

    ops.cleanup_player_references(wsd, [deleted_uid])

    raw_map_object = wsd['MapObjectSaveData']['value']['values'][0]['Model']['value']['RawData']['value']
    assert raw_map_object['build_player_uid'] == '00000000-0000-0000-0000-000000000000'
    assert raw_map_object['stage_instance_id_belong_to']['id'] == '00000000-0000-0000-0000-000000000000'
    slot = wsd['CharacterContainerSaveData']['value'][0]['value']['Slots']['value']['values'][0]
    assert slot['RawData']['value']['player_uid'] == '00000000-0000-0000-0000-000000000000'
    handles = wsd['GroupSaveDataMap']['value'][0]['value']['RawData']['value']['individual_character_handle_ids']
    assert handles == [{'guid': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'}, 'legacy-handle']
