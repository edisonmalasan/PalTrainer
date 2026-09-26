"""Characterization contracts captured before the AUDIT.md workspace rehaul.

These tests protect public wiring while the presentation is replaced. They do
not require a real Palworld save and intentionally avoid asserting legacy
geometry or styling that the new workspace is expected to remove.
"""
from __future__ import annotations

import ast
import inspect
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_INVENTORY = (
    PROJECT_ROOT
    / 'openspec'
    / 'changes'
    / 'implement-audit-uiux-rehaul'
    / 'migration-inventory.md'
)

main_window_mod = import_from('palworld_aio.ui.main_window')
tools_mod = import_from('palworld_aio.ui.tabs.tools_tab')
constants = import_from('palworld_aio.constants')

_app = None


@pytest.fixture
def app():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication

        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


class _FakeStack:
    def __init__(self):
        self.current_index = None

    def setCurrentIndex(self, index):
        self.current_index = index


class _FakeNav:
    def __init__(self):
        self.current = None

    def active_id(self):
        return self.current

    def set_active(self, page_id):
        self.current = page_id


def test_all_existing_page_ids_keep_their_activation_indices():
    expected = {
        'tools': 0,
        'base_inventory': 1,
        'player_inventory': 2,
        'pal_editor': 3,
        'players': 4,
        'guilds': 5,
        'bases': 6,
        'map': 7,
        'exclusions': 8,
        'json_editor': 9,
        'docs': 10,
        'breeding': 11,
    }
    window = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    window._tab_created = set(expected.values())
    window.stacked_widget = _FakeStack()
    window.nav_strip = _FakeNav()

    for page_id, index in expected.items():
        window._on_nav_changed(page_id)
        assert window.stacked_widget.current_index == index
        assert window.nav_strip.current == page_id


def test_programmatic_navigation_keeps_string_page_id_contract():
    window = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    window.nav_strip = _FakeNav()
    seen = []
    window._on_nav_changed = seen.append

    window._activate_nav('base_inventory')

    assert window.nav_strip.current == 'base_inventory'
    assert seen == ['base_inventory']


def test_load_and_save_entry_points_delegate_to_save_manager(monkeypatch):
    calls = []
    manager = SimpleNamespace(
        load_save=lambda *args, **kwargs: calls.append(('load', args, kwargs)),
        save_changes=lambda *args, **kwargs: calls.append(('save', args, kwargs)),
    )
    monkeypatch.setattr(main_window_mod, 'save_manager', manager)
    monkeypatch.setattr(main_window_mod, 'QFileDialog', SimpleNamespace(
        getOpenFileName=lambda *_args: ('C:/fixture/Level.sav', '')))
    monkeypatch.setattr(constants, 'loaded_level_json', {'loaded': True})
    window = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    window._confirm_replace_pending_changes = lambda target: True

    window._load_save()
    window._save_changes()

    assert calls == [
        ('load', (), {'path': 'C:/fixture/Level.sav', 'parent': window}),
        ('save', (), {'parent': window}),
    ]


def test_entity_selection_propagates_to_the_shared_context(monkeypatch):
    context_calls = []

    class _Context:
        def set_player(self, value):
            context_calls.append(('player', value))

        def set_guild(self, value):
            context_calls.append(('guild', value))

        def set_base(self, value):
            context_calls.append(('base', value))

    class _Members:
        def clear(self):
            pass

        def add_item(self, *args, **kwargs):
            raise AssertionError('empty member fixture should not add rows')

    window = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    window.app_bar = SimpleNamespace(context=_Context())
    window.guild_members_panel = _Members()
    window._populate_players_inspector = lambda data: None
    window._populate_guilds_inspector = lambda data: None
    window._populate_bases_inspector = lambda data: None
    monkeypatch.setattr(main_window_mod, 'get_guild_members', lambda guild_id: [])

    window._on_player_selected(['Player A', '', '', '', 'p1', 'Guild A'])
    window._on_guild_selected(['Guild A', 'g1', '', ''])
    window._on_guild_member_selected(['[L]Player B'])
    window._on_base_selected(['Base A', 'g1', 'Guild A'])

    assert context_calls == [
        ('player', 'Player A'),
        ('guild', 'Guild A'),
        ('guild', 'Guild A'),
        ('player', 'Player B'),
        ('base', 'Base A'),
        ('guild', 'Guild A'),
    ]


def test_all_seven_tool_rows_dispatch_the_preserved_handler_and_index(app):
    tab = tools_mod.ToolsTab()
    calls = []
    tab._run_converting_tool = lambda index: calls.append(('conversion', index))
    tab._run_management_tool = lambda index: calls.append(('management', index))

    expected = []
    for _zone, rows in tab.MISSION_ZONES:
        for _tool_key, handler, index in rows:
            expected.append(
                ('conversion' if handler == '_run_converting_tool' else 'management', index)
            )
    assert len(tab._mission_rows) == len(expected) == 7

    for (button, *_rest), dispatch in zip(tab._mission_rows, expected):
        button.click()

    assert calls == expected
    tab.deleteLater()


def test_main_window_dialog_launchers_keep_constructor_contracts():
    contracts = {
        '_open_bulk_player_item_dialog': 'PlayerItemActionDialog',
        '_open_bulk_player_pal_dialog': 'PlayerPalActionDialog',
        '_open_bulk_technology_dialog': 'PlayerTechnologyActionDialog',
        '_open_guild_assign_dialog': 'GuildAssignDialog',
        '_load_backup_save': 'BaseDialog',
        '_open_pal_name_settings': 'BaseDialog',
    }

    for method_name, dialog_name in contracts.items():
        source = inspect.getsource(getattr(main_window_mod.MainWindow, method_name))
        assert f'{dialog_name}(' in source
        assert '.exec()' in source


def test_every_current_dialog_class_is_owned_by_the_migration_inventory():
    """New dialog classes must also be added to the inventory until closure."""
    inventory = MIGRATION_INVENTORY.read_text(encoding='utf-8')
    source_root = PROJECT_ROOT / 'src' / 'palworld_aio'
    class_bases = {}

    for path in source_root.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {
                base.id
                for base in node.bases
                if isinstance(base, ast.Name)
            }
            class_bases[node.name] = bases

    dialog_bases = {'QDialog', 'BaseDialog', 'FramelessDialog', 'ThemedDialog'}
    changed = True
    while changed:
        changed = False
        for name, bases in class_bases.items():
            if name not in dialog_bases and bases & dialog_bases:
                dialog_bases.add(name)
                changed = True

    owned = sorted(dialog_bases - {'QDialog'})
    missing = [name for name in owned if f'`{name}`' not in inventory]
    assert not missing, f'Dialog classes missing inventory ownership: {missing}'
