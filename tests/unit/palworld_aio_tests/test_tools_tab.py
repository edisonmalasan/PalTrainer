"""Focused tests for the Tools page (uiux-audit-remediation 3.1-3.3).

Covers: segmented platform control (exclusivity, handler mapping, i18n
labels), live activity log panel (stream mirroring, bounded height,
auto-scroll buffer, clear empties only the panel), and preserved metric
chip navigation wiring. Widgets are constructed standalone offscreen.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

tools_mod = import_from('palworld_aio.ui.tabs.tools_tab')
main_window_mod = import_from('palworld_aio.ui.main_window')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod = import_from('i18n')
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture
def app():
    return _app_instance()


@pytest.fixture
def tools(app):
    tab = tools_mod.ToolsTab()
    yield tab
    import_from('palworld_aio.constants').current_save_path = ''


# --------------------------------------------------- 3.1 segmented control

def test_segmented_control_exclusive_selection(app):
    steam_calls, gp_calls = [], []
    seg = tools_mod.PlatformSegmentedControl(
        lambda: steam_calls.append(True), lambda: gp_calls.append(True))
    seg.select('gamepass')
    assert seg.selected() == 'gamepass'
    assert seg._segments['gamepass'].isChecked()
    assert not seg._segments['steam'].isChecked()
    seg.select('steam')
    assert seg.selected() == 'steam'
    assert seg._segments['steam'].isChecked()
    assert not seg._segments['gamepass'].isChecked()


def test_segmented_control_handler_mapping(app):
    """Steam segment fires the Steam (Save) flow, GamePass segment the XGP
    flow — the mapping the standalone buttons used."""
    steam_calls, gp_calls = [], []
    seg = tools_mod.PlatformSegmentedControl(
        lambda: steam_calls.append('steam'), lambda: gp_calls.append('xgp'))
    seg._segments['steam'].click()
    seg._segments['gamepass'].click()
    assert steam_calls == ['steam']
    assert gp_calls == ['xgp']


def test_segmented_control_click_restarts_same_flow(app):
    steam_calls, gp_calls = [], []
    seg = tools_mod.PlatformSegmentedControl(
        lambda: steam_calls.append(1), lambda: gp_calls.append(1))
    seg._segments['gamepass'].click()
    seg._segments['gamepass'].click()
    assert gp_calls == [1, 1]
    assert steam_calls == []


def test_tools_tab_routes_segment_to_parent_flows(app):
    tab = tools_mod.ToolsTab()
    calls = []

    class _Win:
        def _load_save(self):
            calls.append('steam')
        def _load_xgp_save(self):
            calls.append('xgp')
    tab.parent_window = _Win()
    tab._platform_segment._segments['steam'].click()
    tab._platform_segment._segments['gamepass'].click()
    assert calls == ['steam', 'xgp']


def test_segmented_control_accessible_names(app):
    seg = tools_mod.PlatformSegmentedControl(lambda: None, lambda: None)
    names = {k: btn.accessibleName() for k, btn in seg._segments.items()}
    assert names['steam'] == 'Steam'
    assert names['gamepass'] == 'GamePass'


def test_segmented_control_single_widget_in_masthead(tools):
    """One connected control replaces the two standalone load buttons."""
    assert hasattr(tools, '_platform_segment')
    assert not hasattr(tools, '_load_steam_btn')
    assert not hasattr(tools, '_load_xgp_btn')
    assert tools._platform_segment.parent() is not None


# ------------------------------------------------- 3.2 activity log panel

def test_log_panel_receives_streamed_message(app):
    panel = tools_mod.ActivityLogPanel()
    panel.append_entry('Save loaded successfully')
    assert 'Save loaded successfully' in panel._view.toPlainText()


def test_log_panel_ignores_blank_chunks(app):
    panel = tools_mod.ActivityLogPanel()
    panel.append_entry('   ')
    panel.append_entry('')
    assert panel.entry_count() == 0


def test_log_panel_clear_empties_only_panel(app):
    panel = tools_mod.ActivityLogPanel()
    seen = []
    stream = main_window_mod.StatusBarStream(
        __import__('PyQt6.QtWidgets', fromlist=['QStatusBar']).QStatusBar())
    stream.text_written.connect(seen.append)
    stream.text_written.connect(panel.append_entry)
    stream.write('conversion finished: 3 files written')
    stream._drain_pending()
    assert panel.entry_count() == 1
    panel.clear()
    assert panel.entry_count() == 0
    # the underlying stream routing is untouched: strip message + signal
    # history are independent of the panel's view
    assert stream.status_bar.currentMessage() == 'conversion finished: 3 files written'
    assert seen == ['conversion finished: 3 files written']


def test_log_panel_bounded_height_and_buffer(app):
    panel = tools_mod.ActivityLogPanel()
    assert 180 <= panel.height() <= 240
    for i in range(tools_mod.ActivityLogPanel.MAX_ENTRIES + 50):
        panel.append_entry(f'entry {i}')
    assert panel.entry_count() <= tools_mod.ActivityLogPanel.MAX_ENTRIES
    assert panel._view.toPlainText().strip().splitlines()[-1] == \
        f'entry {tools_mod.ActivityLogPanel.MAX_ENTRIES + 49}'


def test_tools_tab_subscribes_to_parent_stream(app):
    tab = tools_mod.ToolsTab()
    assert hasattr(tab, '_activity_log')

    class _Win:
        pass
    win = _Win()
    tab.parent_window = win
    from PyQt6.QtWidgets import QStatusBar
    stream = main_window_mod.StatusBarStream(QStatusBar())
    win.status_stream = stream
    tab._setup_log_stream()
    stream.write('loading Level.sav')
    stream._drain_pending()
    assert 'loading Level.sav' in tab._activity_log._view.toPlainText()


# ------------------------------------- preserved wiring (hard constraints)

def test_metric_chips_keep_navigation_handlers(tools):
    assert hasattr(tools, '_stat_cards')
    assert hasattr(tools, '_make_nav_release')
    handler = tools._make_nav_release('players')
    assert callable(handler)


def test_masthead_path_and_copy_untouched(tools):
    assert tools._save_path_label.objectName() == 'opsSavePath'
    assert tools._copy_path_btn.objectName() == 'opsCopyPathBtn'
