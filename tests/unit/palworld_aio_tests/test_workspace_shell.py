from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


shell_mod = import_from('palworld_aio.ui.chrome.workspace_shell')
context_mod = import_from('palworld_aio.ui.workspace_context')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _loaded_context():
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'world-1', 'Island', 'C:/Level.sav', context_mod.SavePlatform.STEAM))
    return context


def test_shell_composes_sidebar_title_header_page_and_notification_hosts(app):
    shell = shell_mod.WorkspaceShell(context_mod.WorkspaceContext())
    assert shell.sidebar.parent() is shell
    assert shell.title_bar.window_controls.parent() is shell.title_bar
    assert shell.header.notifications.parent() is shell.header
    assert shell.page_host.parent() is shell.splitter
    assert shell.findChild(type(shell.sidebar), 'sideBar') is shell.sidebar
    assert shell.findChild(type(shell.title_bar.drag_region), 'windowDragRegion') is shell.title_bar.drag_region


def test_registered_pages_follow_router_and_header_identity(app):
    shell = shell_mod.WorkspaceShell(_loaded_context())
    players = QLabel('Players page')
    shell.register_page('players', players)
    observed = []
    shell.routeChanged.connect(observed.append)
    result = shell.navigate('players')
    assert result.ready
    assert shell.page_host.currentWidget() is players
    assert shell.sidebar.active_route == 'players'
    assert shell.header.title_label.text() == 'Players'
    assert observed == ['players']


def test_missing_context_uses_prerequisite_surface_without_disabling_route(app):
    shell = shell_mod.WorkspaceShell(_loaded_context())
    shell.register_page('player_inventory', QLabel('Inventory'))
    result = shell.navigate('player_inventory')
    assert not result.ready
    assert shell.page_host.currentWidget() is shell._prerequisite_state
    assert 'Player' in shell._prerequisite_state.message_label.text()
    assert shell.sidebar.route_buttons['player_inventory'].isEnabled()


def test_context_snapshot_updates_save_pending_and_breadcrumbs(app):
    context = _loaded_context()
    shell = shell_mod.WorkspaceShell(context)
    context.set_player(context_mod.ContextSelection('player-1', 'Ada'))
    context.set_pending_changes(context_mod.PendingChangesSummary(2, 'Inventory'))
    assert shell.header.save_context.state == 'dirty'
    assert shell.header.save_context._title == 'Island'
    assert shell.header.pending_changes.count == 2
    assert [item.label for item in shell.header.context_bar.items][-1] == 'Ada'


def test_failed_load_has_explicit_header_state_without_a_save(app):
    context = context_mod.WorkspaceContext()
    shell = shell_mod.WorkspaceShell(context)
    context.finish_load(None, success=False)

    assert shell.header.save_context.state == 'error'
    assert shell.header.save_context._title == 'Save load failed'
    assert 'try again' in shell.header.save_context._detail


def test_only_dedicated_drag_region_starts_shell_drag(app):
    shell = shell_mod.WorkspaceShell(context_mod.WorkspaceContext())
    shell.resize(1024, 700)
    shell.show()
    app.processEvents()
    drags = []
    minimizes = []
    shell.title_bar.drag_region.dragStarted.connect(lambda: drags.append(True))
    shell.minimizeRequested.connect(lambda: minimizes.append(True))

    QTest.mouseClick(shell.title_bar.drag_region, Qt.MouseButton.LeftButton)
    assert drags == [True]
    QTest.mouseClick(
        shell.title_bar.window_controls.minimize_btn,
        Qt.MouseButton.LeftButton,
    )
    assert minimizes == [True]
    assert drags == [True]


@pytest.mark.parametrize('width,mode', [(1024, 'drawer'), (1450, 'side')])
def test_inspector_switches_between_drawer_and_side_host(app, width, mode):
    shell = shell_mod.WorkspaceShell(_loaded_context())
    inspector = QLabel('Entity details')
    shell.set_inspector(inspector, title='Player details')
    shell.resize(width, 700)
    shell.show()
    app.processEvents()
    assert shell.property('inspectorMode') == mode
    if mode == 'drawer':
        assert shell.inspector_side.isHidden()
        shell.open_inspector(shell.sidebar.route_buttons['players'])
        app.processEvents()
        assert shell.inspector_drawer.isVisibleTo(shell)
        assert inspector.parent() is shell.inspector_drawer
    else:
        assert shell.inspector_side.isVisibleTo(shell)
        assert inspector.parent() is shell.inspector_side


def test_title_bar_history_buttons_track_router(app):
    shell = shell_mod.WorkspaceShell(_loaded_context())
    assert not shell.title_bar.back_button.isEnabled()
    shell.navigate('players')
    assert shell.title_bar.back_button.isEnabled()
    shell.go_back()
    assert shell.router.current_route_id == 'overview'
    assert shell.title_bar.forward_button.isEnabled()


def test_replacing_one_route_keeps_a_widget_shared_by_other_routes(app):
    shell = shell_mod.WorkspaceShell(_loaded_context())
    shared = QLabel('Legacy pages')
    shell.register_page('players', shared)
    shell.register_page('tools', shared)
    replacement = QLabel('Tool Center')
    shell.register_page('tools', replacement)
    shell.navigate('players')
    assert shell.page_host.currentWidget() is shared
    shell.navigate('tools')
    assert shell.page_host.currentWidget() is replacement
