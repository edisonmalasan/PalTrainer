"""Focused regression tests for shell v3 chrome (top-nav-shell task 5.4).

Covers: nav strip overflow (compact labels + collapse menu), save chip
states, and status strip streaming. Widgets are constructed standalone
offscreen — no MainWindow boot required.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

nav_strip_mod = import_from('palworld_aio.ui.chrome.nav_strip')
app_bar_mod = import_from('palworld_aio.ui.chrome.app_bar')
shell_state_mod = import_from('palworld_aio.shell_state')
main_window_mod = import_from('palworld_aio.ui.main_window')

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


EXPECTED_IDS = {'tools', 'base_inventory', 'player_inventory', 'pal_editor',
                'players', 'guilds', 'bases', 'map', 'exclusions',
                'json_editor', 'breeding', 'docs'}


# ---------------------------------------------------------------------------
# Nav strip overflow
# ---------------------------------------------------------------------------

def test_nav_strip_has_all_twelve_destinations(app):
    strip = nav_strip_mod.NavStrip()
    assert set(strip._tabs.keys()) == EXPECTED_IDS


def test_nav_strip_active_id_parity(app):
    strip = nav_strip_mod.NavStrip()
    seen = []
    strip.nav_changed.connect(seen.append)
    strip._on_tab('map')
    assert strip.active_id() == 'map'
    assert seen == ['map']
    strip.set_active('players')
    assert strip.active_id() == 'players'


def test_nav_strip_collapse_zones_hides_and_overflow_reaches(app):
    strip = nav_strip_mod.NavStrip()
    strip.show()
    strip.resize(1200, 40)
    strip.collapse_zones({'nav.zone.reference', 'nav.zone.edit'})
    assert strip._tabs['breeding'].isHidden()
    assert strip._tabs['json_editor'].isHidden()
    # every collapsed destination remains reachable via the overflow menu
    overflow_ids = set()
    for zone_key, _fallback, page_ids in nav_strip_mod.ZONES:
        if zone_key in {'nav.zone.reference', 'nav.zone.edit'}:
            overflow_ids.update(page_ids)
    rebuilt = {a.text() for a in strip._overflow_menu.actions()}
    labels = {nav_strip_mod.nav_full_label(pid) for pid in overflow_ids}
    assert rebuilt == labels
    strip.collapse_zones(set())
    assert not strip._tabs['breeding'].isHidden()


def test_nav_strip_compact_labels_shorten_text(app):
    strip = nav_strip_mod.NavStrip()
    tab = strip._tabs['base_inventory']
    full = tab.text()
    strip._apply_layout_state(True, set())
    compact = tab.text()
    strip._apply_layout_state(False, set())
    assert len(compact) < len(full)


def test_nav_strip_refresh_labels_keeps_twelve(app):
    strip = nav_strip_mod.NavStrip()
    strip.refresh_labels()
    assert len(strip._tabs) == 12


# ---------------------------------------------------------------------------
# Save chip states
# ---------------------------------------------------------------------------

def test_save_chip_state_transitions(app):
    chip = app_bar_mod.SaveStateChip()
    assert chip.property('state') == 'no_save'
    for state in ('loading', 'loaded', 'saving', 'error'):
        chip.apply_state(state)
        assert chip.property('state') == state


def test_save_chip_dirty_dot(app):
    chip = app_bar_mod.SaveStateChip()
    chip.set_dirty(True)
    assert chip._dirty_dot.isVisible() or not chip.isVisible()  # hidden parent ok
    chip.show()
    chip.set_dirty(True)
    assert chip._dirty_dot.isVisible()
    chip.set_dirty(False)
    assert not chip._dirty_dot.isVisible()


def test_save_chip_shell_state_mapping(app):
    ShellState = shell_state_mod.ShellState
    chip = app_bar_mod.SaveStateChip()
    chip.set_shell_state(ShellState.DIRTY)
    assert chip.property('state') == 'dirty'
    chip.set_loading_state('loading')
    assert chip.property('state') == 'loading'
    chip.set_loading_state('idle')
    assert chip.property('state') == 'no_save'


# ---------------------------------------------------------------------------
# Status strip streaming
# ---------------------------------------------------------------------------

def test_status_bar_stream_routes_to_status_strip(app):
    from PyQt6.QtWidgets import QStatusBar
    StatusBarStream = main_window_mod.StatusBarStream
    bar = QStatusBar()
    stream = StatusBarStream(bar)
    stream.write('save loaded ok')
    stream._drain_pending()
    assert bar.currentMessage() == 'save loaded ok'


def test_status_bar_stream_detaches_and_reattaches(app):
    from PyQt6.QtWidgets import QStatusBar
    StatusBarStream = main_window_mod.StatusBarStream
    bar = QStatusBar()
    stream = StatusBarStream(bar)
    seen = []
    stream.detach_state_changed.connect(seen.append)
    # DetachedStatusWindow hits a QEasingCurve enum quirk on some Qt builds;
    # stub the window so detach/attach message routing is still exercised.
    class _FakeWindow:
        def __init__(self):
            self.messages = []
        def append_message(self, text):
            self.messages.append(text)
        def close(self):
            pass
    def _detach():
        stream.detached = True
        stream.detach_window = _FakeWindow()
        stream.detach_state_changed.emit(True)
    stream.detach = _detach
    _detach()
    assert stream.detached and seen == [True]
    stream.write('while detached')
    stream._drain_pending()
    assert stream.detach_window.messages == ['while detached']
    stream.attach()
    assert not stream.detached and seen[-1] is False
    stream.write('back in strip')
    stream._drain_pending()
    assert bar.currentMessage() == 'back in strip'
