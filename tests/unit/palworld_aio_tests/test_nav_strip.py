"""Focused tests for the two-tier nav strip (uiux-audit-remediation 1.5).

Covers: all 12 destinations reachable via the tiers, the unchanged
`nav_changed(str)` page-ID contract, zone switching swapping the secondary
row, last-visited-per-zone navigation with first-child fallback, overflow
reachability per tier, and the Base Inventory / Bases icon distinction.
Widgets are constructed standalone offscreen.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

nav_strip_mod = import_from('palworld_aio.ui.chrome.nav_strip')
icons_mod = import_from('palworld_aio.ui.chrome.icons')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture
def app():
    return _app_instance()


@pytest.fixture
def strip(app):
    widget = nav_strip_mod.NavStrip()
    widget.resize(1400, 72)
    return widget


EXPECTED_IDS = {'tools', 'base_inventory', 'player_inventory', 'pal_editor',
                'players', 'guilds', 'bases', 'map', 'exclusions',
                'json_editor', 'breeding', 'docs'}

ZONE_CHILDREN = {zk: pids for zk, _fb, pids in nav_strip_mod.ZONES}
START_ZONE = nav_strip_mod.START_ZONE
ZONE_KEYS = {'nav.zone.world', 'nav.zone.edit', 'nav.zone.reference'}


def _secondary_visible_ids(widget) -> set[str]:
    return {
        pid for pid, zone in widget._tab_zone.items()
        if zone != START_ZONE and widget._tabs[pid].isVisibleTo(widget)
    }


# ------------------------------------------------------------- structure

def test_nav_strip_keeps_all_twelve_destinations(app):
    widget = nav_strip_mod.NavStrip()
    assert set(widget._tabs.keys()) == EXPECTED_IDS


def test_primary_tier_shows_zones_only(app):
    widget = nav_strip_mod.NavStrip()
    assert widget._tabs['tools'].parent() is widget._primary_row
    for zone_tab in widget._zone_tabs.values():
        assert zone_tab.parent() is widget._primary_row
    assert set(widget._zone_tabs) == ZONE_KEYS
    # no secondary child is shown before a zone is active
    assert _secondary_visible_ids(widget) == set()


def test_nav_strip_height_stays_compact(app):
    widget = nav_strip_mod.NavStrip()
    assert widget.height() == 72


# ------------------------------------------------------ reachability

def test_all_destinations_reachable_via_tiers(app):
    widget = nav_strip_mod.NavStrip()
    seen: list[str] = []
    widget.nav_changed.connect(seen.append)
    for zone_key, _fb, page_ids in nav_strip_mod.ZONES:
        widget._on_zone_tab(zone_key)
        assert widget.active_id() == page_ids[0]
        for pid in page_ids:
            widget._on_tab(pid)
            assert widget.active_id() == pid
    assert set(seen) == EXPECTED_IDS


def test_nav_changed_signal_contract_unchanged(app):
    widget = nav_strip_mod.NavStrip()
    seen: list[str] = []
    widget.nav_changed.connect(seen.append)
    widget._on_tab('map')
    widget._on_tab('pal_editor')
    widget._on_tab('breeding')
    widget._on_tab('tools')
    assert seen == ['map', 'pal_editor', 'breeding', 'tools']
    assert all(isinstance(pid, str) for pid in seen)
    widget.set_active('docs')  # programmatic activation emits nothing
    assert seen == ['map', 'pal_editor', 'breeding', 'tools']
    assert widget.active_id() == 'docs'


def test_zone_activation_falls_back_to_first_child(app):
    widget = nav_strip_mod.NavStrip()
    widget._on_zone_tab('nav.zone.world')
    assert widget.active_id() == 'map'
    widget._on_zone_tab('nav.zone.edit')
    assert widget.active_id() == 'player_inventory'
    widget._on_zone_tab('nav.zone.reference')
    assert widget.active_id() == 'breeding'


def test_zone_activation_prefers_last_visited(app):
    widget = nav_strip_mod.NavStrip()
    widget._on_tab('guilds')
    widget._on_zone_tab('nav.zone.edit')
    assert widget.active_id() == 'player_inventory'
    widget._on_tab('json_editor')
    widget._on_zone_tab('nav.zone.world')
    assert widget.active_id() == 'guilds'
    widget._on_zone_tab('nav.zone.edit')
    assert widget.active_id() == 'json_editor'


def test_tools_primary_navigates_directly(app):
    widget = nav_strip_mod.NavStrip()
    widget._on_tab('bases')
    widget._on_tab('tools')
    assert widget.active_id() == 'tools'
    widget._on_zone_tab(START_ZONE)
    assert widget.active_id() == 'tools'


def test_set_active_unknown_id_is_ignored(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('map')
    widget.set_active('not_a_page')
    assert widget.active_id() == 'map'


# --------------------------------------------- secondary tier swapping

def test_zone_switching_swaps_secondary_row(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('map')
    assert _secondary_visible_ids(widget) == set(ZONE_CHILDREN['nav.zone.world'])
    widget.set_active('pal_editor')
    assert _secondary_visible_ids(widget) == set(ZONE_CHILDREN['nav.zone.edit'])
    widget.set_active('docs')
    assert _secondary_visible_ids(widget) == set(ZONE_CHILDREN['nav.zone.reference'])
    widget.set_active('tools')
    assert _secondary_visible_ids(widget) == set()  # Start zone: no children


def test_primary_active_zone_treatment(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('map')
    assert widget._zone_tabs['nav.zone.world'].isChecked()
    assert not widget._zone_tabs['nav.zone.edit'].isChecked()
    assert not widget._zone_tabs['nav.zone.reference'].isChecked()
    assert widget._tabs['map'].isChecked()
    assert not widget._tabs['tools'].isChecked()
    widget.set_active('tools')
    assert widget._tabs['tools'].isChecked()
    for zone_tab in widget._zone_tabs.values():
        assert not zone_tab.isChecked()


def test_active_destination_tab_gains_accent_icon(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('bases')
    accent = icons_mod.get_qicon('bases', role='accent').pixmap(64, 64).toImage()
    muted = icons_mod.get_qicon('bases', role='text_secondary').pixmap(64, 64).toImage()
    assert widget._tabs['bases'].icon().pixmap(64, 64).toImage() == accent
    assert widget._tabs['bases'].icon().pixmap(64, 64).toImage() != muted


# ---------------------------------------------------------- overflow

def test_primary_collapse_keeps_zones_reachable_via_overflow(app):
    widget = nav_strip_mod.NavStrip()
    widget.collapse_zones({'nav.zone.reference', 'nav.zone.edit'})
    assert widget._zone_tabs['nav.zone.reference'].isHidden()
    assert widget._zone_tabs['nav.zone.edit'].isHidden()
    assert not widget._zone_tabs['nav.zone.world'].isHidden()
    assert widget._overflow_btn.isVisibleTo(widget)
    assert set(widget._overflow_zone_actions) == {
        'nav.zone.reference', 'nav.zone.edit'}
    seen: list[str] = []
    widget.nav_changed.connect(seen.append)
    widget._overflow_zone_actions['nav.zone.reference'].trigger()
    assert widget.active_id() == 'breeding'  # first-child fallback
    assert seen == ['breeding']
    widget.collapse_zones(set())
    assert not widget._zone_tabs['nav.zone.reference'].isHidden()


def test_active_zone_primary_tab_is_never_collapsed(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('breeding')  # Reference becomes the active zone
    widget.show()
    widget.resize(240, 72)
    assert 'nav.zone.reference' not in widget._primary_collapsed
    assert 'nav.zone.start' not in widget._primary_collapsed


def test_secondary_overflow_keeps_children_reachable(app):
    widget = nav_strip_mod.NavStrip()
    seen: list[str] = []
    widget.nav_changed.connect(seen.append)
    widget.set_active('map')
    widget._apply_layout_state(True, set(), {'players', 'guilds', 'exclusions'})
    assert widget._overflow_btn.isVisibleTo(widget)
    assert set(widget._overflow_page_actions) == {
        'players', 'guilds', 'exclusions'}
    widget._overflow_page_actions['guilds'].trigger()
    assert widget.active_id() == 'guilds'
    assert seen[-1] == 'guilds'
    reachable = _secondary_visible_ids(widget) | set(widget._overflow_page_actions)
    assert set(ZONE_CHILDREN['nav.zone.world']) <= reachable


def test_narrow_window_overflow_keeps_every_destination_reachable(app):
    widget = nav_strip_mod.NavStrip()
    widget.set_active('map')
    widget.show()
    widget.resize(320, 72)
    # World children stay reachable through the secondary row or the menu
    reachable = _secondary_visible_ids(widget) | set(widget._overflow_page_actions)
    assert set(ZONE_CHILDREN['nav.zone.world']) <= reachable
    # Zone destinations stay reachable through the primary row or the menu
    primary_reachable = (
        {'nav.zone.world', 'nav.zone.edit', 'nav.zone.reference'}
        <= (set(widget._overflow_zone_actions)
            | {zk for zk, tab in widget._zone_tabs.items() if not tab.isHidden()}))
    assert primary_reachable
    # Start/Tools never collapses
    assert not widget._tabs['tools'].isHidden()
    assert widget._tabs['tools'].isVisibleTo(widget)


def test_overflow_menu_uses_existing_labels(app):
    widget = nav_strip_mod.NavStrip()
    widget.collapse_zones({'nav.zone.world'})
    widget.set_active('player_inventory')
    widget._apply_layout_state(False, {'nav.zone.world'}, {'pal_editor'})
    assert widget._overflow_zone_actions['nav.zone.world'].text() == \
        nav_strip_mod.nav_zone_caption('nav.zone.world', 'World')
    assert widget._overflow_page_actions['pal_editor'].text() == \
        nav_strip_mod.nav_full_label('pal_editor')


# ---------------------------------------------------- icon distinction

def test_base_inventory_nav_icon_distinct_from_bases(app):
    _app_instance()
    widget = nav_strip_mod.NavStrip()
    bases_img = widget._tabs['bases'].icon().pixmap(64, 64).toImage()
    inv_img = widget._tabs['base_inventory'].icon().pixmap(64, 64).toImage()
    assert not bases_img.isNull() and not inv_img.isNull()
    assert bases_img != inv_img


def test_base_inventory_reuses_container_glyph(app):
    _app_instance()
    assert icons_mod.has_vector_icon('base_inventory')
    assert icons_mod._svg_source('base_inventory') == \
        icons_mod._svg_source('container')


# ------------------------------------------------------ i18n / labels

def test_refresh_labels_keeps_twelve_and_zone_tabs(app):
    widget = nav_strip_mod.NavStrip()
    widget.refresh_labels()
    assert len(widget._tabs) == 12
    assert len(widget._zone_tabs) == 3
    assert widget._zone_tabs['nav.zone.world'].accessibleName()
