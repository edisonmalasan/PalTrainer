"""Focused tests for shell status/typography chrome (uiux-audit-remediation 2.1-2.5).

Covers: status strip message policy (design D3), warning button tri-state
(design D4), save path truncation + copy (design D6), monospace token class
(design D5), and context indicator visibility. Widgets are constructed
standalone offscreen — no MainWindow boot required.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

main_window_mod = import_from('palworld_aio.ui.main_window')
app_bar_mod = import_from('palworld_aio.ui.chrome.app_bar')
constants_mod = import_from('palworld_aio.constants')
tools_mod = import_from('palworld_aio.ui.tabs.tools_tab')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    """Runtime parity: the app boots with en_US resources loaded; without
    this, t(key) returns the raw key and strip summaries diverge."""
    i18n_mod = import_from('i18n')
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture
def app():
    return _app_instance()


# ------------------------------------------------- 2.1 status message policy

PRESENT = main_window_mod._present_status
RAW = main_window_mod._STATUS_SHOW_RAW
DEMOTE = main_window_mod._STATUS_DEMOTE


@pytest.mark.parametrize('payload,expected', [
    ('Decompression successful, decompressed size: 26,429 bytes', ('status.ready', 'Ready')),
    ('Update check error: HTTP Error 404: Not Found', DEMOTE),
    ('Update check callback error: boom', DEMOTE),
    ('Traceback (most recent call last):', DEMOTE),
    ('  File "C:\\x\\y.py", line 1, in <module>', DEMOTE),
    ('urllib.error.HTTPError: HTTP Error 404: Not Found', DEMOTE),
    ('Level.sav loaded', ('status.loaded', 'Save loaded successfully')),
    ('Save completed', ('status.saved', 'Save completed')),
    ('Failed to load save', ('status.load_failed', 'Failed to load save')),
    ('conversion finished: 3 files written', RAW),
    ('', RAW),
])
def test_present_status_policy(payload, expected):
    assert PRESENT(payload) == expected


def test_demoted_update_check_leaves_neutral_ready_message(app):
    from PyQt6.QtWidgets import QStatusBar
    stream = main_window_mod.StatusBarStream(QStatusBar())
    stream.write('Update check error: HTTP Error 404: Not Found')
    stream._drain_pending()
    assert stream.status_bar.currentMessage() == 'Ready'
    # still visible in the log/console path (detached stream)
    class _Win:
        messages: list[str] = []
        def append_message(self, text):
            self.messages.append(text)
    stream.detach_window = _Win()
    stream.detached = True
    stream.write('Update check error: HTTP Error 404: Not Found')
    stream._drain_pending()
    assert stream.detach_window.messages == [
        'Update check error: HTTP Error 404: Not Found']


def test_decompression_stats_replaced_by_ready(app):
    from PyQt6.QtWidgets import QStatusBar
    stream = main_window_mod.StatusBarStream(QStatusBar())
    stream.write('Decompression successful, decompressed size: 26,429 bytes')
    stream._drain_pending()
    assert stream.status_bar.currentMessage() == 'Ready'


def test_raw_payloads_still_reach_strip_verbatim(app):
    from PyQt6.QtWidgets import QStatusBar
    stream = main_window_mod.StatusBarStream(QStatusBar())
    stream.write('conversion finished: 3 files written')
    stream._drain_pending()
    assert stream.status_bar.currentMessage() == 'conversion finished: 3 files written'


# ------------------------------------------------- 2.2 warning tri-state

@pytest.fixture
def bar(app):
    return app_bar_mod.AppBar()


def test_warning_starts_hidden(bar):
    assert bar.warn_state() == 'none'
    assert not bar.warn_btn.isVisibleTo(bar)


def test_warning_lifecycle_none_unread_acknowledged_none(bar):
    bar.raise_warning('Update check failed')
    assert bar.warn_state() == 'unread'
    assert bar.warn_btn.isVisibleTo(bar)
    assert bar.warn_btn.property('warnState') == 'unread'
    assert bar.warn_detail() == 'Update check failed'
    bar._noop_warn()  # click: reveal + acknowledge
    assert bar.warn_state() == 'acknowledged'
    assert bar.warn_btn.isVisibleTo(bar)  # dimmed but visible while unresolved
    bar.resolve_warning()
    assert bar.warn_state() == 'none'
    assert not bar.warn_btn.isVisibleTo(bar)
    assert bar.warn_detail() == ''


def test_warning_reraise_returns_to_unread(bar):
    bar.raise_warning('first')
    bar._noop_warn()
    assert bar.warn_state() == 'acknowledged'
    bar.raise_warning('second')
    assert bar.warn_state() == 'unread'
    assert bar.warn_detail() == 'second'


def test_warning_slot_still_invoked_on_click(bar):
    seen = []
    bar.set_warning_slot(lambda: seen.append(True))
    bar.raise_warning('detail')
    bar._noop_warn()
    assert seen == [True]


def test_legacy_show_warning_false_resolves_condition(bar):
    bar.raise_warning('detail')
    bar.show_warning(False)
    assert bar.warn_state() == 'none'
    assert not bar.warn_btn.isVisibleTo(bar)


# ------------------------- _on_update_checked resolution contract (2.2)

class _FakeStatus:
    def showMessage(self, text, timeout=0):
        pass


class _FakeAppBar:
    """Records tri-state calls without booting the full MainWindow."""

    def __init__(self):
        self.resolved = 0
        self.raised = []
        self.pulses = []

    def set_update_pulse(self, on):
        self.pulses.append(bool(on))

    def resolve_warning(self):
        self.resolved += 1

    def raise_warning(self, detail=''):
        self.raised.append(detail)


def _run_update_callback(ok, latest, branch=None):
    window = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    app_bar = _FakeAppBar()
    window.app_bar = app_bar
    window.status_bar = _FakeStatus()
    original = main_window_mod.MainWindow._on_update_checked
    # _on_update_checked only touches app_bar/status_bar + t(); bind it to
    # the stub
    original(window, ok, latest, branch)
    return app_bar


def test_update_available_resolves_previous_failure(app):
    _run_update_callback(False, None)  # check itself failed
    result = _run_update_callback(False, '1.2.3', 'stable')  # update available
    assert result.resolved == 1
    assert result.raised == []
    assert result.pulses[-1] is True


def test_up_to_date_resolves_previous_failure(app):
    _run_update_callback(False, None)
    result = _run_update_callback(True, None)
    assert result.resolved == 1
    assert result.pulses[-1] is False


def test_failed_check_raises_warning_with_detail(app):
    result = _run_update_callback(False, None)
    assert result.resolved == 0
    assert len(result.raised) == 1
    assert 'Update check failed' in result.raised[0]


# ----------------------------------------- 2.3 save path truncation + copy

@pytest.fixture
def tools_tab(app, monkeypatch):
    tab = tools_mod.ToolsTab()
    yield tab
    constants_mod.current_save_path = ''


def test_save_path_truncated_with_full_tooltip(tools_tab, monkeypatch):
    long_path = 'C:/Users/ediso/AppData/Local/Pal/Saved/SaveGames/76561199438892270/B7D8465740F80E0E7AC081991A033220'
    monkeypatch.setattr(constants_mod, 'current_save_path', long_path, raising=False)
    tools_tab._save_path_label.resize(400, 24)
    tools_tab._apply_save_path_display()
    text = tools_tab._save_path_label.text()
    assert text != long_path
    assert '…' in text
    assert len(text) < len(long_path)
    assert tools_tab._save_path_label.toolTip() == long_path


def test_save_path_copied_with_feedback(tools_tab, monkeypatch):
    path = 'C:/saves/my world'
    monkeypatch.setattr(constants_mod, 'current_save_path', path, raising=False)
    tools_tab._on_copy_path_clicked()
    assert tools_tab._copy_path_btn.toolTip() == 'Copied'
    from PyQt6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == path


def test_copy_hidden_when_no_save(tools_tab):
    constants_mod.current_save_path = ''
    tools_tab._apply_save_path_display()
    assert tools_tab._copy_path_btn.isVisibleTo(tools_tab) is False
    assert tools_tab._save_path_label.text() == 'No save loaded'


# ----------------------------------------------- 2.4 monospace token class

def test_monospace_class_in_built_qss(app):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    qss = qss_mod.build_qss('dark')
    assert 'QPushButton[class="mono"]' in qss
    assert "QPushButton#opsSavePath" in qss  # path stays monospace
    # mono stack includes the bundled family + system fallback
    assert "font-family: 'Cascadia Mono'" in qss


def test_save_path_label_uses_mono_object_name(tools_tab):
    assert tools_tab._save_path_label.objectName() == 'opsSavePath'


# ------------------------------------------ 2.5 context indicator visibility

def test_context_indicator_hidden_without_save(bar):
    assert bar.context.isVisibleTo(bar) is False


def test_context_indicator_visibility_toggle(bar):
    bar.context.setVisible(True)
    assert bar.context.isVisibleTo(bar) is True
    bar.context.setVisible(False)
    assert bar.context.isVisibleTo(bar) is False
