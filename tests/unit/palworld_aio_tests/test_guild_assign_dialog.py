from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


dialog_mod = import_from('palworld_aio.ui.dialogs.guild_assign_dialog')
constants = import_from('palworld_aio.constants')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    import_from('i18n').load_resources('en_US')


def _group(guild_id, name, players):
    return {
        'key': guild_id,
        'value': {
            'GroupType': {'value': {'value': 'EPalGroupType::Guild'}},
            'RawData': {'value': {
                'guild_name': name,
                'base_camp_level': 10,
                'players': players,
            }},
        },
    }


def _player(uid, name, role=3):
    return {
        'player_uid': uid,
        'player_info': {'player_name': name},
        'role': role,
    }


@pytest.fixture
def loaded_world(monkeypatch):
    world = {
        'properties': {'worldSaveData': {'value': {
            'GroupSaveDataMap': {'value': [
                _group('GUILD-1', 'Guild One', [
                    _player('PLAYER-1', 'Ada', 1),
                ]),
                _group('GUILD-2', 'Guild Two', [
                    _player('PLAYER-2', 'Ben'),
                ]),
            ]},
        }}},
    }
    monkeypatch.setattr(constants, 'loaded_level_json', world)
    monkeypatch.setattr(constants, 'player_levels', {
        'player1': 55, 'player2': 40,
    })
    return world


def _guild_item(dialog, guild_id):
    return next(
        item for item in dialog.guild_panel._all_items
        if item.data(0, Qt.ItemDataRole.UserRole) == guild_id)


def test_source_target_review_skips_players_already_in_target(
        app, loaded_world, monkeypatch):
    calls = []
    invalidations = []
    monkeypatch.setattr(
        dialog_mod, 'move_player_to_guild',
        lambda uid, gid: calls.append((uid, gid)) or True)
    monkeypatch.setattr(
        constants, 'invalidate_container_lookup',
        lambda: invalidations.append(None))
    dialog = dialog_mod.GuildAssignDialog(
        selected_player_uids=('PLAYER-1', 'PLAYER-2'))

    assert len(dialog._selected_players()) == 2
    assert dialog.workflow.currentIndex() == 0
    assert dialog.next_btn.isEnabled()
    dialog._go_next()
    dialog.guild_panel.tree.setCurrentItem(_guild_item(dialog, 'GUILD-1'))
    dialog._go_next()

    assert dialog.workflow.currentIndex() == 2
    assert '1 of 2 selected' in dialog.review_summary.text()
    assert '1 already in the target guild' in dialog.review_players.text()
    assert dialog.assign_btn.isEnabled()
    dialog._assign()

    assert calls == [('PLAYER-2', 'GUILD-1')]
    assert invalidations == [None]
    assert dialog.progress.maximum() == 1
    assert dialog.progress.value() == 1
    assert dialog.result_label.property('resultState') == 'success'
    assert dialog._completed
    assert dialog.moved_count == 1
    assert dialog.cancel_btn.text() == 'Close'


def test_cancel_before_review_never_mutates(
        app, loaded_world, monkeypatch):
    calls = []
    monkeypatch.setattr(
        dialog_mod, 'move_player_to_guild',
        lambda uid, gid: calls.append((uid, gid)) or True)
    dialog = dialog_mod.GuildAssignDialog(
        selected_player_uids=('PLAYER-2',))
    dialog.reject()
    assert calls == []
    assert getattr(dialog, 'moved_count', 0) == 0


def test_failed_assignment_reports_warning_result(
        app, loaded_world, monkeypatch):
    monkeypatch.setattr(
        dialog_mod, 'move_player_to_guild', lambda uid, gid: False)
    monkeypatch.setattr(
        constants, 'invalidate_container_lookup', lambda: None)
    dialog = dialog_mod.GuildAssignDialog(
        selected_player_uids=('PLAYER-2',))
    dialog._go_next()
    dialog.guild_panel.tree.setCurrentItem(_guild_item(dialog, 'GUILD-1'))
    dialog._go_next()
    dialog._assign()
    assert dialog.moved_count == 0
    assert dialog.result_label.property('resultState') == 'warning'
    assert '1 failed' in dialog.result_label.text()
