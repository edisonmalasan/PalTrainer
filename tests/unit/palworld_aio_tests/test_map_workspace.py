"""Focused contracts for the map-first World workspace."""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QApplication, QWidget

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

map_tab_mod = import_from('palworld_aio.ui.tabs.map_tab')
router_mod = import_from('palworld_aio.ui.router')
context_mod = import_from('palworld_aio.ui.workspace_context')
workspace_shell_mod = import_from('palworld_aio.ui.chrome.workspace_shell')
i18n_mod = import_from('i18n')

PROJECT_ROOT = Path(__file__).resolve().parents[3]

_app = None


def test_map_player_delete_cancel_keeps_save_unchanged(monkeypatch):
    from types import SimpleNamespace

    data_manager = import_from('palworld_aio.managers.data_manager')
    calls = []
    monkeypatch.setattr(data_manager, 'load_exclusions', lambda: None)
    monkeypatch.setattr(data_manager, 'delete_player',
                        lambda uid: calls.append(('delete', uid)))
    monkeypatch.setattr(map_tab_mod.constants, 'exclusions', {'players': []})
    monkeypatch.setattr(map_tab_mod, 'show_question',
                        lambda _parent, _title, message:
                        calls.append(('confirm', message)) or False)

    map_tab_mod.MapTab._delete_player(
        SimpleNamespace(), {'player_uid': 'uid', 'player_name': 'Player A'})

    assert len(calls) == 1
    assert '1 player' in calls[0][1]


@pytest.fixture(scope='session')
def app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    i18n_mod.load_resources('en_US')
    return _app


@pytest.fixture
def tab(app):
    widget = map_tab_mod.MapTab(None)
    widget.set_loaded(True)
    widget.resize(1180, 700)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()


def _base(identifier='base-001'):
    return {
        'base_id': identifier,
        'guild_id': 'guild-001',
        'guild_name': 'Lamplight Guild',
        'leader_name': 'Ada',
        'guild_level': 8,
        'member_count': 3,
        'total_bases': 2,
        'base_position': 1,
        'pal_count': 11,
        'coords': (120.2, -75.8),
        'map_type': 'world',
        'img_coords': (1024, 1024),
    }


def test_clear_zones_confirms_affected_count_before_write(monkeypatch):
    from types import SimpleNamespace
    zone_manager = import_from('palworld_aio.managers.zone_manager')

    i18n_mod.load_resources('en_US')
    zones = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]
    prompts = []
    writes = []
    monkeypatch.setattr(zone_manager, 'get_zones', lambda: zones)
    monkeypatch.setattr(zone_manager, 'clear_all_zones',
                        lambda: writes.append('cleared'))
    monkeypatch.setattr(map_tab_mod, 'show_question',
                        lambda _parent, _title, detail:
                        prompts.append(detail) or False)
    tab = SimpleNamespace(_update_zone_items=lambda: None)

    map_tab_mod.MapTab._clear_zones(tab)
    assert prompts == ['Delete all 3 protection zones? This cannot be undone.']
    assert writes == []

    monkeypatch.setattr(map_tab_mod, 'show_question',
                        lambda *_args: True)
    monkeypatch.setattr(map_tab_mod, 'run_with_loading',
                        lambda on_finished, task: on_finished(task()))
    map_tab_mod.MapTab._clear_zones(tab)
    assert writes == ['cleared']


def _player(identifier='player-001'):
    return {
        'player_uid': identifier,
        'player_name': 'Mara',
        'guild_id': 'guild-001',
        'guild_name': 'Lamplight Guild',
        'level': 44,
        'last_seen': '5m',
        'pal_count': 27,
        'coords': (12.0, 30.0),
        'map_type': 'world',
        'img_coords': (1100, 980),
    }


def test_map_uses_workspace_panes_and_labeled_layer_controls(tab):
    assert tab.findChild(QWidget, 'pageRibbon') is None
    assert tab.map_splitter.widget(0) is tab._sidebar_widget
    assert tab.map_splitter.widget(1) is tab._map_widget
    assert tab.map_splitter.widget(2) is tab.inspector_host
    assert tab.map_splitter.sizes()[1] > 0
    assert [button.text() for button in (
        tab.toggle_map_bases,
        tab.toggle_map_players,
        tab.toggle_base_radius_rings,
        tab.toggle_map_zones,
    )] == ['Bases', 'Players', 'Radius', 'Zones']
    for button in (
        tab.toggle_map_bases,
        tab.toggle_map_players,
        tab.toggle_base_radius_rings,
        tab.toggle_map_zones,
    ):
        assert button.toolTip()
        assert button.accessibleName()


def test_map_distinguishes_no_save_loading_empty_no_result_and_error(tab, app):
    tab.set_loaded(False)
    assert tab.map_content_stack.currentWidget() is tab.no_save_state
    assert not tab.center_selection_button.isEnabled()
    assert not tab.open_entity_button.isEnabled()
    assert not tab.open_guild_button.isEnabled()
    tab.set_loading()
    assert tab.map_content_stack.currentWidget() is tab.loading_state
    tab.set_error('Safe map failure.')
    assert tab.map_content_stack.currentWidget() is tab.error_state
    assert tab.error_state.message_label.text() == 'Safe map failure.'

    tab.guilds_data = {}
    tab.filtered_guilds = {}
    tab.players_data = []
    tab.filtered_players_data = []
    tab._update_tree()
    tab.set_loaded(True)
    app.processEvents()
    assert tab.map_content_stack.currentWidget() is tab.map_splitter
    assert not tab._explorer_empty_states['bases'].isHidden()

    base = _base()
    tab.guilds_data = {
        base['guild_id']: {
            'guild_name': base['guild_name'],
            'leader_name': base['leader_name'],
            'last_seen': '5m',
            'last_seen_sort': 5.0,
            'bases': [base],
        },
    }
    tab.filtered_guilds = tab.guilds_data
    tab._update_tree()
    tab.search_input.setText('missing')
    app.processEvents()
    assert not tab._explorer_no_result_states['bases'].isHidden()
    tab._explorer_no_result_states['bases'].action_button.click()
    assert tab.search_input.text() == ''


def test_layer_toggles_and_plus_minus_controls_remain_operable(tab):
    assert tab.toggle_map_bases.isChecked()
    tab.toggle_map_bases.click()
    assert not tab.toggle_map_bases.isChecked()
    tab.toggle_map_players.click()
    assert tab.toggle_map_players.isChecked()

    tab.view.current_zoom = 1.0
    tab.view.resetTransform()
    tab.view.zoom_in_btn.click()
    assert tab.view.current_zoom > 1.0
    tab.view.zoom_out_btn.click()
    assert tab.view.current_zoom == pytest.approx(1.0)
    assert tab.view.navigation_bar.objectName() == 'mapNavigationBar'
    assert tab.view.coords_label.accessibleName()
    assert tab.view.zoom_label.accessibleName()


def test_explorer_headers_count_and_selection_drive_structured_inspector(tab):
    base = _base()
    tab.guilds_data = {
        base['guild_id']: {
            'guild_name': base['guild_name'],
            'leader_name': base['leader_name'],
            'last_seen': '5m',
            'last_seen_sort': 5.0,
            'bases': [base],
        },
    }
    tab.filtered_guilds = tab.guilds_data
    tab._update_tree()
    headers = [tab.base_tree.headerItem().text(index) for index in range(5)]
    assert headers == ['Guild Name', 'Leader', 'Last Seen', 'Bases', 'Base Pals']
    assert tab.explorer_count_label.text() == '1 of 1'

    item = tab.base_tree.topLevelItem(0).child(0)
    tab._on_tree_item_clicked(item, 0)
    assert tab._selected_entity_id == base['base_id']
    assert tab.inspector._title.text() == 'Base 1'
    assert tab.open_entity_button.text() == 'Open Base'
    assert tab.open_guild_button.isEnabled()


def test_marker_entity_links_emit_selected_world_records(tab):
    base = _base()
    base_spy = QSignalSpy(tab.openBaseRequested)
    guild_spy = QSignalSpy(tab.openGuildRequested)
    tab._update_info(base)
    tab.open_entity_button.click()
    tab.open_guild_button.click()
    assert len(base_spy) == 1
    assert base_spy[0][0]['base_id'] == base['base_id']
    assert len(guild_spy) == 1
    assert guild_spy[0][0] == {
        'guild_id': base['guild_id'],
        'guild_name': base['guild_name'],
    }

    player = _player()
    player_spy = QSignalSpy(tab.openPlayerRequested)
    tab._update_player_info(player)
    tab.open_entity_button.click()
    assert len(player_spy) == 1
    assert player_spy[0][0]['player_uid'] == player['player_uid']


def test_minimum_width_keeps_map_primary_and_moves_inspector_to_drawer(tab, app):
    tab.resize(1024, 700)
    app.processEvents()
    assert tab._compact_inspector
    assert not tab.inspector_host.isVisible()
    assert tab.details_button.isVisible()
    sizes = tab.map_splitter.sizes()
    assert sizes[1] > sizes[0]

    tab._update_player_info(_player())
    app.processEvents()
    assert tab.inspector_drawer.isVisible()
    assert tab.inspector_drawer.geometry().right() <= tab.rect().right()
    assert tab.inspector_drawer.geometry().bottom() <= tab.rect().bottom()


def test_map_remains_primary_inside_minimum_width_workspace_shell(app):
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'fixture', 'Fixture World', 'C:/Fixture/Level.sav'))
    shell = workspace_shell_mod.WorkspaceShell(context)
    map_page = map_tab_mod.MapTab(shell.page_host)
    shell.register_page('map', map_page)
    shell.navigate('map')
    shell.resize(1024, 700)
    shell.show()
    app.processEvents()

    assert map_page.width() < 1024
    assert map_page._compact_inspector
    assert not map_page.inspector_host.isVisible()
    explorer_width, map_width, inspector_width = map_page.map_splitter.sizes()
    assert map_width > explorer_width
    assert inspector_width == 0
    assert map_page.details_button.geometry().right() <= (
        map_page.map_control_bar.contentsRect().right())

    shell.close()


def test_router_history_restores_map_search_layers_zoom_and_selection(tab, app):
    player = _player()
    tab.players_data = [player]
    tab.filtered_players_data = [player]
    tab._update_tree()
    context = context_mod.WorkspaceContext()
    router = router_mod.WorkspaceRouter(context)
    router.register_page('map', tab)
    router.navigate('map')

    tab.search_input.setText('Mara')
    tab._switch_map_tab(1)
    tab.toggle_map_bases.setChecked(False)
    tab.toggle_map_players.setChecked(True)
    tab.view.zoom_by_step(1)
    item = tab.player_tree.topLevelItem(0)
    tab._on_tree_item_clicked(item, 0)
    expected_zoom = tab.view.current_zoom
    json.dumps(tab.capture_view_state())

    router.navigate('overview')
    tab.search_input.clear()
    tab._switch_map_tab(0)
    tab.toggle_map_bases.setChecked(True)
    tab.toggle_map_players.setChecked(False)
    tab.view.current_zoom = 1.0
    assert router.back() is not None
    app.processEvents()

    assert tab.search_input.text() == 'Mara'
    assert tab.map_tab_stack.currentIndex() == 1
    assert not tab.toggle_map_bases.isChecked()
    assert tab.toggle_map_players.isChecked()
    assert tab.view.current_zoom == pytest.approx(expected_zoom)
    assert tab._selected_entity_id == player['player_uid']


def test_map_base_transfer_actions_keep_callbacks_behind_shared_review():
    source_path = PROJECT_ROOT / 'src' / 'palworld_aio' / 'ui' / 'tabs' / 'map_tab.py'
    tree = ast.parse(source_path.read_text(encoding='utf-8-sig'))
    map_tab = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == 'MapTab')
    methods = {
        node.name: node for node in map_tab.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        '_import_base_to_guild': {'load_base_file', 'import_base_json'},
        '_export_bases_for_guild': {'export_base_json'},
        '_export_base': {'export_base_json'},
        '_clone_base': {'clone_base_complete'},
    }

    for method_name, callback_names in expected.items():
        calls = {
            node.func.id
            for node in ast.walk(methods[method_name])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        attributes = {
            node.func.attr
            for node in ast.walk(methods[method_name])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert callback_names <= calls
        assert '_run_transfer_workflow' in attributes
