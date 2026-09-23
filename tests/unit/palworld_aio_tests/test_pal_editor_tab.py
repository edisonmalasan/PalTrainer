"""Pal Editor player-context shell and WorkspaceContext contracts."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

tab_mod = import_from('palworld_aio.ui.tabs.pal_editor_tab')
i18n_mod = import_from('i18n')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture(scope='session')
def app():
    return _app_instance()


@pytest.fixture
def tab(app):
    widget = tab_mod.PalEditorTab(None)
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_pal_editor_uses_workspace_player_context_without_page_ribbon(tab):
    assert tab.context_bar.objectName() == 'editorContextBar'
    assert tab.player_select_btn.objectName() == 'workspacePlayerSelector'
    assert tab.player_select_btn.property('controlRole') == 'chip'
    assert tab.player_select_btn.property('contextKind') == 'player'
    assert tab.context_label.text() == 'Player'
    assert not tab.findChildren(tab_mod.QFrame, 'pageRibbon')


def test_pal_editor_player_context_has_chevron_and_accessible_copy(tab):
    chevron = tab_mod.app_icons.get_qicon(
        'chevron_down', role='text_secondary')
    assert not tab.player_select_btn.icon().pixmap(32, 32).isNull()
    assert (tab.player_select_btn.icon().pixmap(32, 32).toImage()
            == chevron.pixmap(32, 32).toImage())
    assert tab.player_select_btn.accessibleName() == i18n_mod.t(
        'inventory.select_player', default='Select Player...')
    assert tab.context_summary.text() == (
        'Party, Palbox, and inspector edits apply to this player.')


def test_workspace_context_switches_pal_editor_player(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    tab._player_list = [
        {'uid': 'p1', 'name': 'Hathaway', 'level': 55,
         'display': 'Hathaway (Lv.55)'},
        {'uid': 'p2', 'name': 'Juniper', 'level': 47,
         'display': 'Juniper (Lv.47)'},
    ]
    selected = []

    def select_player(uid, name, display):
        selected.append((uid, name, display))
        tab.current_player_uid = uid
        tab.current_player_name = name
        tab._set_selector_copy(uid, name, display)

    monkeypatch.setattr(tab, 'select_player', select_player)
    tab.bind_workspace_context(context)

    context.set_player(context_mod.ContextSelection('p2', 'Juniper'))

    assert selected == [('p2', 'Juniper', 'Juniper (Lv.47)')]
    assert tab.player_select_btn.text() == 'Juniper (Lv.47)'
    assert tab.player_select_btn.accessibleName() == 'Selected player: Juniper'
    assert tab.context_summary.text() == 'Editing party and Palbox for Juniper.'


def test_single_player_becomes_pal_editor_smart_default(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    tab._player_list = [{
        'uid': 'p1', 'name': 'Hathaway', 'level': 55,
        'display': 'Hathaway (Lv.55)',
    }]
    selected = []
    def select_player(uid, name, display):
        selected.append((uid, name, display))
        tab.current_player_uid = uid
        tab.current_player_name = name

    monkeypatch.setattr(tab, 'select_player', select_player)

    tab.bind_workspace_context(context)
    tab._reconcile_player_context()

    assert context.snapshot.player == context_mod.ContextSelection(
        'p1', 'Hathaway')
    assert selected == [('p1', 'Hathaway', 'Hathaway (Lv.55)')]
