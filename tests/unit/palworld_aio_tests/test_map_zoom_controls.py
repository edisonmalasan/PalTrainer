"""Focused tests for Map overlay discoverability and zoom controls
(uiux-audit-remediation 8.1-8.2 / design D13). MapTab is constructed
standalone offscreen; no save data is required.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

map_tab_mod = import_from('palworld_aio.ui.tabs.map_tab')
map_view_mod = import_from('palworld_aio.ui.map_view.map_view')
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


@pytest.fixture(scope='session')
def tab(app):
    return map_tab_mod.MapTab(None)


# --------------------------------------------------- 8.1 zoom controls

def test_zoom_by_step_matches_wheel_math(tab):
    view = tab.view
    view.resetTransform()
    view.current_zoom = 1.0
    # one wheel-notch in: factor = zoom_factor, no clamp hit
    view._apply_zoom_step(True)
    assert view.current_zoom == pytest.approx(view.zoom_factor)
    # one wheel-notch out returns to 1.0
    view._apply_zoom_step(False)
    assert view.current_zoom == pytest.approx(1.0)
    assert view.zoom_label.text() == 'Zoom: 100%'


def test_zoom_by_step_clamps_at_bounds(tab):
    view = tab.view
    assert view.min_zoom == 1.0
    for _ in range(60):
        view.zoom_by_step(-1)
    assert view.current_zoom == view.min_zoom
    for _ in range(60):
        view.zoom_by_step(1)
    assert view.current_zoom == view.max_zoom


def test_zoom_buttons_exist_with_accessible_names(tab):
    view = tab.view
    assert view.zoom_in_btn.objectName() == 'mapZoomBtn'
    assert view.zoom_out_btn.objectName() == 'mapZoomBtn'
    assert view.zoom_in_btn.accessibleName() == 'Zoom In'
    assert view.zoom_out_btn.accessibleName() == 'Zoom Out'
    assert view.zoom_in_btn.toolTip() == 'Zoom In'
    assert view.zoom_out_btn.toolTip() == 'Zoom Out'
    assert view.zoom_in_btn.parent() is view
    assert view.zoom_out_btn.parent() is view


def test_zoom_buttons_click_call_zoom_by_step_path(tab):
    view = tab.view
    view.resetTransform()
    view.current_zoom = 1.0
    view.zoom_out_btn.click()
    assert view.current_zoom == view.min_zoom  # clamped at min already
    view.zoom_in_btn.click()
    assert view.current_zoom == pytest.approx(view.zoom_factor)
    assert view.zoom_label.text() == f'Zoom: {int(view.zoom_factor * 100)}%'


def test_zoom_buttons_disable_at_bounds(tab):
    view = tab.view
    for _ in range(60):
        view.zoom_by_step(-1)
    assert not view.zoom_out_btn.isEnabled()
    assert view.zoom_in_btn.isEnabled()
    for _ in range(60):
        view.zoom_by_step(1)
    assert not view.zoom_in_btn.isEnabled()
    assert view.zoom_out_btn.isEnabled()


def test_zoom_buttons_stay_clear_of_legend_card(tab):
    view = tab.view
    legend = tab._sidebar_widget
    btn_right = max(view.zoom_in_btn.geometry().right(),
                    view.zoom_out_btn.geometry().right())
    btn_bottom = max(view.zoom_in_btn.geometry().bottom(),
                     view.zoom_out_btn.geometry().bottom())
    # bottom-right corner placement, below the top overlay row (y >= 30)
    assert view.zoom_in_btn.y() >= 30
    assert btn_right <= view.width()
    assert btn_bottom <= view.height()
    # no overlap with the floating legend card (top-left)
    legend_rect = legend.geometry()
    for b in (view.zoom_in_btn, view.zoom_out_btn):
        assert not b.geometry().intersects(legend_rect)


def test_map_zoom_btn_rule_in_built_qss(tab):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    built = qss_mod.build_qss('dark')
    assert 'QPushButton#mapZoomBtn' in built
    # disabled state is part of the shared rule family (bounds UX)
    assert 'QPushButton#mapZoomBtn:disabled' in built
    # no inline colour stylesheets on the new buttons
    assert tab.view.zoom_in_btn.styleSheet() == ''
    assert tab.view.zoom_out_btn.styleSheet() == ''


def test_zoom_i18n_keys_present():
    assert i18n_mod.t('map.zoom_in') == 'Zoom In'
    assert i18n_mod.t('map.zoom_out') == 'Zoom Out'


# ------------------------------------- 8.1 accessible names on toggles

def test_overlay_toggles_accessible_names_match_tooltips(tab):
    toggles = [
        tab.toggle_map_bases,
        tab.toggle_map_players,
        tab.toggle_base_radius_rings,
        tab.toggle_map_zones,
        tab.toggle_map_type,
        tab.btn_calibrate,
        tab.btn_calibrate_tree,
    ]
    for toggle in toggles:
        assert toggle.toolTip(), 'tooltip missing (tooltips are the contract)'
        assert toggle.accessibleName() == toggle.toolTip()


def test_map_type_toggle_keeps_accessible_name_after_swap(tab):
    tab.toggle_map_type.setChecked(True)
    tab._on_map_type_toggle(True)
    assert tab.toggle_map_type.toolTip() == 'World Map'
    assert tab.toggle_map_type.accessibleName() == 'World Map'
    tab.toggle_map_type.setChecked(False)
    tab._on_map_type_toggle(False)
    assert tab.toggle_map_type.accessibleName() == 'Tree Map'


def test_refresh_labels_keeps_accessible_names_synced(tab):
    tab.refresh_labels()
    for name in ('toggle_map_bases', 'toggle_map_players',
                 'toggle_base_radius_rings', 'toggle_map_zones',
                 'toggle_map_type', 'btn_calibrate', 'btn_calibrate_tree'):
        btn = getattr(tab, name)
        assert btn.accessibleName() == btn.toolTip()


# ------------------------------------------- 8.2 browser columns

def test_base_tree_headers_fit_sidebar_at_min_width(tab):
    headers = [tab.base_tree.headerItem().text(i) for i in range(5)]
    assert headers == ['Guild Name', 'Leader', 'Last Seen', 'Bases', 'Base Pals']
    widths = [tab.base_tree.columnWidth(i) for i in range(5)]
    # sidebar floor is 360px (floating card margins included); the four fixed
    # columns plus the stretched last section must fit without header truncation
    sidebar_min = tab._sidebar_widget.minimumWidth() + 16  # card margins
    fixed_total = sum(widths[:4])
    assert tab.base_tree.header().stretchLastSection()
    assert fixed_total + widths[4] <= sidebar_min


def test_tree_items_carry_full_value_tooltips(tab):
    tab.guilds_data = {
        'gid': {
            'guild_name': 'A Very Long Guild Name That Must Elide',
            'leader_name': 'A Very Long Leader Name Indeed',
            'last_seen': '3d 2h',
            'last_seen_sort': 100.0,
            'bases': [{
                'base_id': '0123456789abcdef0123456789abcdef',
                'coords': (123.4, -987.6),
                'pal_count': 7,
            }],
        },
    }
    tab.filtered_guilds = tab.guilds_data
    tab._update_tree()
    guild_item = tab.base_tree.topLevelItem(0)
    assert guild_item.toolTip(0) == tab.guilds_data['gid']['guild_name']
    assert guild_item.toolTip(1) == tab.guilds_data['gid']['leader_name']
    base_item = guild_item.child(0)
    # displayed id is truncated; tooltip keeps the full value
    assert len(base_item.text(1)) < 32
    assert base_item.toolTip(1) == tab.guilds_data['gid']['bases'][0]['base_id']
    assert base_item.toolTip(0) == 'X:123 Y:-987'


def test_player_tree_items_carry_full_value_tooltips(tab):
    tab.players_data = [{
        'player_name': 'A Very Long Player Name That Must Elide',
        'level': 42,
        'last_seen': '5m',
        'last_seen_sort': 10.0,
        'pal_count': 3,
        'coords': (10.0, 20.0),
        'guild_name': 'g',
    }]
    tab.filtered_players_data = tab.players_data
    tab._update_tree()
    player_item = tab.player_tree.topLevelItem(0)
    assert player_item.toolTip(0) == tab.players_data[0]['player_name']
    assert player_item.toolTip(1) == '42'
    assert player_item.toolTip(2) == '5m'
    assert player_item.toolTip(3) == '3'
