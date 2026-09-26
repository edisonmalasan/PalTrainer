from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


sidebar_mod = import_from('palworld_aio.ui.chrome.sidebar')
routes = import_from('palworld_aio.ui.routes')
tokens = import_from('palworld_aio.ui.chrome.tokens')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_sidebar_is_generated_from_all_registry_groups_and_routes(app):
    sidebar = sidebar_mod.WorkspaceSidebar()
    assert tuple(sidebar.route_buttons) == routes.ROUTES.ids
    assert tuple(sidebar._group_labels) == tuple(routes.RouteGroup)
    assert sidebar.route_buttons['tools'].text() == 'Tool Center'
    assert all(button.accessibleName() for button in sidebar.route_buttons.values())
    assert all(not button.icon().isNull() for button in sidebar.route_buttons.values())


def test_active_route_and_activation_signal_use_stable_id(app):
    sidebar = sidebar_mod.WorkspaceSidebar()
    observed = []
    sidebar.routeActivated.connect(observed.append)
    sidebar.set_active('players')
    assert sidebar.active_route == 'players'
    assert sidebar.route_buttons['players'].isChecked()
    assert sidebar.route_buttons['players'].property('active') is True
    sidebar.route_buttons['guilds'].click()
    assert observed == ['guilds']


def test_prerequisites_are_explained_without_hiding_or_disabling_routes(app):
    sidebar = sidebar_mod.WorkspaceSidebar()
    sidebar.set_route_availability({
        'player_inventory': {routes.ContextKind.SAVE, routes.ContextKind.PLAYER},
    })
    button = sidebar.route_buttons['player_inventory']
    assert button.isEnabled()
    assert button.property('prerequisiteMissing') is True
    assert 'Requires: Save, Player' in button.toolTip()
    assert 'Requires: Save, Player' in button.accessibleDescription()


def test_collapse_and_width_settings_round_trip_with_safe_defaults(app):
    sidebar = sidebar_mod.WorkspaceSidebar()
    observed = []
    sidebar.collapsedChanged.connect(observed.append)
    sidebar.set_expanded_width(276)
    sidebar.set_collapsed(True)
    assert sidebar.width() == tokens.LAYOUT['sidebar_collapsed']
    assert all(not button.text() for button in sidebar.route_buttons.values())
    assert all(button.toolTip() for button in sidebar.route_buttons.values())
    settings = sidebar.export_settings()

    restored = sidebar_mod.WorkspaceSidebar()
    restored.restore_settings(settings)
    assert restored.collapsed
    restored.set_collapsed(False)
    assert restored.width() == 276
    assert restored.route_buttons['overview'].text() == 'Overview'
    assert observed == [True]

    restored.restore_settings({'expanded_width': 'wide', 'collapsed': 'yes'})
    assert not restored.collapsed
    assert restored.width() == tokens.LAYOUT['sidebar_expanded']


def test_arrow_home_and_end_keys_follow_route_order(app):
    sidebar = sidebar_mod.WorkspaceSidebar()
    sidebar.show()
    sidebar.activateWindow()
    app.processEvents()
    first = sidebar.route_buttons['overview']
    first.setFocus()
    app.processEvents()
    QTest.keyClick(first, Qt.Key.Key_Down)
    assert sidebar.route_buttons['activity'].hasFocus()
    QTest.keyClick(sidebar.route_buttons['activity'], Qt.Key.Key_End)
    assert sidebar.route_buttons['diagnostics'].hasFocus()
    QTest.keyClick(sidebar.route_buttons['diagnostics'], Qt.Key.Key_Home)
    assert first.hasFocus()


@pytest.mark.parametrize('width,height', [(1024, 700), (1450, 800)])
def test_every_route_remains_reachable_at_supported_window_sizes(app, width, height):
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    sidebar = sidebar_mod.WorkspaceSidebar()
    layout.addWidget(sidebar)
    layout.addStretch(1)
    host.resize(width, height)
    host.show()
    app.processEvents()

    assert sidebar.height() == height
    assert set(sidebar.route_buttons) == set(routes.ROUTES.ids)
    for button in sidebar.route_buttons.values():
        assert not button.isHidden()
        sidebar.scroll_area.ensureWidgetVisible(button)
        app.processEvents()
        assert button.isVisibleTo(sidebar.scroll_area.viewport())
