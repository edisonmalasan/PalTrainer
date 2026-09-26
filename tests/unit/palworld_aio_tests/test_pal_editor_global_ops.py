from __future__ import annotations

import inspect

from tests.dynamic_importer import import_from

global_ops = import_from(
    'palworld_aio.editor.pal_editor.pal_editor_global_ops')
bulk_ops = import_from(
    'palworld_aio.editor.pal_editor.pal_editor_bulk_ops')
constants = import_from('palworld_aio.constants')


def _pal_entry(
    instance_id: str,
    character_id: str,
    *,
    container_id: str = '',
    owner_uid: str = '',
    group_id: str = '',
    active: tuple[str, ...] = (),
    mastered: tuple[str, ...] = (),
    passive: tuple[str, ...] = (),
):
    save_parameter = {
        'CharacterID': {'value': character_id},
        'OwnerPlayerUId': {'value': owner_uid},
        'SlotId': {
            'value': {
                'ContainerId': {'value': {'ID': {'value': container_id}}},
            },
        },
        'EquipWaza': {'value': {'values': list(active)}},
        'MasteredWaza': {'value': {'values': list(mastered)}},
        'PassiveSkillList': {'value': {'values': list(passive)}},
    }
    return {
        'key': {'InstanceId': {'value': instance_id}},
        'value': {
            'RawData': {
                'value': {
                    'group_id': group_id,
                    'object': {
                        'SaveParameter': {'value': save_parameter},
                    },
                },
            },
        },
    }


def _world(entries, groups=()):
    return {
        'properties': {
            'worldSaveData': {
                'value': {
                    'CharacterSaveParameterMap': {'value': entries},
                    'GroupSaveDataMap': {'value': list(groups)},
                },
            },
        },
    }


def _container(*instance_ids):
    return {
        'value': {
            'Slots': {
                'value': {
                    'values': [
                        {'RawData': {'instance_id': instance_id}}
                        for instance_id in instance_ids
                    ],
                },
            },
        },
    }


def test_delete_preview_counts_only_removable_loaded_pals(monkeypatch):
    removable = _pal_entry('one', 'SheepBall')
    another = _pal_entry('two', 'sheepball')
    player = _pal_entry('player', 'SheepBall')
    player['value']['RawData']['value']['object']['SaveParameter']['value'][
        'IsPlayer'] = {'value': True}
    missing_instance = _pal_entry('', 'SheepBall')
    other = _pal_entry('other', 'ChickenPal')
    monkeypatch.setattr(constants, 'loaded_level_json', _world([
        removable, another, player, missing_instance, other]))

    assert global_ops.count_pals_for_deletion('SheepBall') == 2
    assert global_ops.count_pals_for_deletion('ChickenPal') == 1


def test_delete_pal_removes_each_fixture_from_its_own_container(
        monkeypatch, tmp_path):
    player_pal = _pal_entry(
        'player-pal', 'SheepBall',
        container_id='container-player', owner_uid='player-1')
    base_pal = _pal_entry(
        'base-pal', 'SheepBall',
        container_id='container-base', group_id='base-group')
    survivor = _pal_entry(
        'survivor', 'ChickenPal',
        container_id='container-player', owner_uid='player-1')
    group = {
        'value': {
            'RawData': {
                'value': {
                    'group_id': 'base-group',
                    'individual_character_handle_ids': [
                        {'instance_id': 'base-pal'},
                        {'instance_id': 'other-base-pal'},
                    ],
                },
            },
        },
    }
    player_container = _container('player-pal', 'survivor')
    base_container = _container('base-pal', 'other-base-pal')
    lookup = {
        'containerplayer': player_container,
        'containerbase': base_container,
    }
    world = _world([player_pal, base_pal, survivor], [group])
    monkeypatch.setattr(constants, 'loaded_level_json', world)
    monkeypatch.setattr(constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(constants, 'gps_gvas', None)
    monkeypatch.setattr(constants, 'get_container_lookup', lambda: lookup)
    monkeypatch.setattr(constants, 'invalidate_container_lookup', lambda: None)

    result = global_ops.delete_pal_from_all('SheepBall')

    remaining = world['properties']['worldSaveData']['value'][
        'CharacterSaveParameterMap']['value']
    assert remaining == [survivor]
    assert player_container['value']['Slots']['value']['values'] == [
        {'RawData': {'instance_id': 'survivor'}},
    ]
    assert base_container['value']['Slots']['value']['values'] == [
        {'RawData': {'instance_id': 'other-base-pal'}},
    ]
    handles = group['value']['RawData']['value'][
        'individual_character_handle_ids']
    assert handles == [{'instance_id': 'other-base-pal'}]
    assert result == {'pals_removed': 2, 'affected_count': 2}


def test_remove_skill_respects_fixture_scope_and_mutates_existing_lists(
        monkeypatch, tmp_path):
    active_id = 'EPalWazaID::FireBall'
    player_pal = _pal_entry(
        'player-pal', 'SheepBall',
        container_id='container-player', owner_uid='player-1',
        active=(active_id, 'EPalWazaID::WaterGun'),
        mastered=(active_id,),
        passive=('Runner', 'Swift'))
    base_pal = _pal_entry(
        'base-pal', 'SheepBall', group_id='base-group',
        active=(active_id,), mastered=(active_id,), passive=('Runner',))
    world = _world([player_pal, base_pal])
    monkeypatch.setattr(constants, 'loaded_level_json', world)
    monkeypatch.setattr(constants, 'current_save_path', str(tmp_path))

    result = global_ops.remove_skill_from_all_pals(
        active_skill_id='FireBall',
        passive_skill_id='Runner',
        scope='player',
    )

    player_raw = player_pal['value']['RawData']['value']['object'][
        'SaveParameter']['value']
    base_raw = base_pal['value']['RawData']['value']['object'][
        'SaveParameter']['value']
    assert player_raw['EquipWaza']['value']['values'] == [
        'EPalWazaID::WaterGun']
    assert player_raw['MasteredWaza']['value']['values'] == []
    assert player_raw['PassiveSkillList']['value']['values'] == ['Swift']
    assert base_raw['EquipWaza']['value']['values'] == [active_id]
    assert base_raw['PassiveSkillList']['value']['values'] == ['Runner']
    assert result == {'skills_removed': 3, 'pals_affected': 1}


def test_skill_preview_matches_scope_without_mutating_lists(monkeypatch, tmp_path):
    player_pal = _pal_entry(
        'player-pal', 'SheepBall', container_id='player-container',
        active=('EPalWazaID::FireBall',))
    base_pal = _pal_entry(
        'base-pal', 'SheepBall', group_id='base-group', passive=('Runner',))
    world = _world([player_pal, base_pal])
    monkeypatch.setattr(constants, 'loaded_level_json', world)
    monkeypatch.setattr(constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(constants, 'gps_gvas', None)

    assert global_ops.count_pals_with_skills('FireBall', 'Runner',
                                              'player', include_external=False) == 1
    assert global_ops.count_pals_with_skills('FireBall', 'Runner',
                                              'base', include_external=False) == 1
    assert global_ops.count_pals_with_skills('FireBall', 'Runner',
                                              'all', include_external=False) == 2
    assert player_pal['value']['RawData']['value']['object'][
        'SaveParameter']['value']['EquipWaza']['value']['values'] == [
            'EPalWazaID::FireBall']
    assert base_pal['value']['RawData']['value']['object'][
        'SaveParameter']['value']['PassiveSkillList']['value']['values'] == [
            'Runner']


def test_delete_preview_includes_dps_and_gps_records(monkeypatch, tmp_path):
    from types import SimpleNamespace

    utils = import_from('palworld_aio.utils')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'owner_dps.sav').write_bytes(b'fixture')
    dps_entry = {'SaveParameter': {'value': {
        'CharacterID': {'value': 'SheepBall'}}}}
    gps_entry = {'SaveParameter': {'value': {
        'CharacterID': {'value': 'sheepball'}}}}
    monkeypatch.setattr(constants, 'loaded_level_json', _world([
        _pal_entry('world-pal', 'SheepBall')]))
    monkeypatch.setattr(constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(constants, 'gps_gvas', SimpleNamespace(
        properties={'SaveParameterArray': {'value': {'values': [gps_entry]}}}))
    monkeypatch.setattr(utils, 'sav_to_gvasfile', lambda _path: SimpleNamespace(
        properties={'SaveParameterArray': {'value': {'values': [dps_entry]}}}))

    assert global_ops.count_world_pals_for_deletion('SheepBall') == 1
    assert global_ops.count_pals_for_deletion('SheepBall') == 3
    assert dps_entry['SaveParameter']['value']['CharacterID']['value'] == 'SheepBall'
    assert gps_entry['SaveParameter']['value']['CharacterID']['value'] == 'sheepball'


def test_inventoried_inline_bulk_flows_expose_review_progress_and_results():
    source = inspect.getsource(bulk_ops.BulkOperationMixin)

    assert source.count('BulkWorkflowReview(') == 3
    assert source.count('workflow_review.set_progress') >= 6
    assert source.count('workflow_review.set_result') == 3
