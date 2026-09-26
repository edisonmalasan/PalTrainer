import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _run_isolated(script):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(
        [
            str(PROJECT_ROOT / 'src' / 'palsav'),
            str(PROJECT_ROOT / 'src'),
            env.get('PYTHONPATH', ''),
        ]
    )
    return subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
    )


def test_import_does_not_override_qt_lifecycle_methods():
    result = _run_isolated("""
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QDialog

from palworld_aio.ui.main_window import MainWindow  # noqa: F401

assert callable(QObject.deleteLater)
# PyQt6 exposes ``exec`` as a fresh wrapper on each class lookup, so
# identity comparison is not stable across imports.
assert callable(QDialog.exec)
assert not hasattr(QDialog, 'exec_')
""")

    assert result.returncode == 0, result.stderr


def test_pending_journal_survives_save_failure_and_clears_on_success():
    result = _run_isolated(r"""
from types import SimpleNamespace
from palworld_aio.shell_state import ShellState, ShellStateModel
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal
from palworld_aio.ui.workspace_context import SaveIdentity, WorkspaceContext

context = WorkspaceContext()
context.finish_load(SaveIdentity('world', 'Island', 'C:/saves/Level.sav'))
journal = PendingChangeJournal()
journal.changed.connect(context.set_pending_changes)
activities = []
window = SimpleNamespace(
    workspace_context=context,
    pending_journal=journal,
    shell_state=ShellStateModel(),
    _record_activity=lambda *args, **kwargs: activities.append((args, kwargs)),
)
MainWindow._set_dirty(window, True)
MainWindow._set_dirty(window, True)
assert context.snapshot.save_state is ShellState.DIRTY
assert context.snapshot.pending_changes.count == 1
assert len(journal.changes) == 1
context.begin_save()
MainWindow._on_save_failed(window, 'disk error')
assert context.snapshot.save_state is ShellState.ERROR
assert context.snapshot.pending_changes.count == 1
assert len(journal.changes) == 1
context.finish_save(True)
MainWindow._set_dirty(window, False)
assert context.snapshot.save_state is ShellState.LOADED
assert not journal.changes
assert context.snapshot.pending_changes.count == 0
""")
    assert result.returncode == 0, result.stderr


def test_pending_review_discloses_context_count_and_risk():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from types import SimpleNamespace
from PyQt6.QtWidgets import QApplication
import palworld_aio.ui.main_window as main_window
from palworld_aio.ui.chrome.workspace_header import PendingChangesButton
from palworld_aio.ui.pending_changes import PendingChangeJournal

app = QApplication.instance() or QApplication([])
button = PendingChangesButton()
journal = PendingChangeJournal()
journal.record('Removed Pals', context='Player A', affected_count=3,
               high_risk=True)

class Action:
    def __init__(self, text):
        self.text = text
        self.tooltip = ''
        self.enabled = True
        self.triggered = SimpleNamespace(connect=lambda callback: setattr(
            self, 'callback', callback))
    def setToolTip(self, value):
        self.tooltip = value
    def setEnabled(self, value):
        self.enabled = value

class Menu:
    last = None
    def __init__(self, parent):
        self.actions = []
        Menu.last = self
    def setObjectName(self, value):
        self.object_name = value
    def setAccessibleName(self, value):
        self.accessible_name = value
    def addSection(self, value):
        self.section = value
    def addAction(self, value):
        action = Action(value)
        self.actions.append(action)
        return action
    def exec(self, position):
        pass

main_window.QMenu = Menu
window = SimpleNamespace(
    workspace_shell=SimpleNamespace(
        header=SimpleNamespace(pending_changes=button)),
    pending_journal=journal,
    _save_changes=lambda: None,
    _reload_from_disk=lambda: None,
)
main_window.MainWindow._show_pending_changes(window)
assert Menu.last.object_name == 'appContextMenu'
assert Menu.last.actions[0].text == 'High risk · Removed Pals (3)'
assert Menu.last.actions[0].tooltip == 'Player A'
assert not Menu.last.actions[0].enabled

journal.clear()
calls = []
journal.record('Editable', undo=lambda: calls.append('undo'),
               redo=lambda: calls.append('redo'))
window._undo_pending_change = lambda: main_window.MainWindow._undo_pending_change(window)
window._redo_pending_change = lambda: main_window.MainWindow._redo_pending_change(window)
main_window.MainWindow._show_pending_changes(window)
assert [action.text for action in Menu.last.actions] == [
    'Editable', 'Save Changes', 'Reload from Disk', 'Undo last change']
Menu.last.actions[-1].callback()
assert calls == ['undo']
main_window.MainWindow._show_pending_changes(window)
assert [action.text for action in Menu.last.actions] == [
    'No pending changes', 'Redo last change']
Menu.last.actions[-1].callback()
assert calls == ['undo', 'redo']
""")
    assert result.returncode == 0, result.stderr


def test_legacy_dirty_flag_is_reflected_in_pending_journal():
    result = _run_isolated(r"""
from types import SimpleNamespace
from palworld_aio import constants
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal
from palworld_aio.ui.workspace_context import SaveIdentity, WorkspaceContext

context = WorkspaceContext()
context.finish_load(SaveIdentity('world', 'Island', 'C:/saves/Level.sav'))
journal = PendingChangeJournal()
journal.changed.connect(context.set_pending_changes)
window = SimpleNamespace(
    workspace_context=context, pending_journal=journal,
    _record_activity=lambda *args, **kwargs: None,
)
window._set_dirty = lambda dirty: MainWindow._set_dirty(window, dirty)
constants.dirty = True
MainWindow._sync_dirty_from_runtime(window)
MainWindow._sync_dirty_from_runtime(window)
assert journal.summary.count == 1
assert context.snapshot.pending_changes.count == 1
constants.dirty = False
""")
    assert result.returncode == 0, result.stderr


def test_close_guard_preserves_pending_work_until_save_succeeds():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from types import SimpleNamespace
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal
import palworld_aio.ui.main_window as module
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal
from palworld_aio.ui.workspace_context import SaveIdentity, WorkspaceContext

app = QCoreApplication.instance() or QCoreApplication([])
context = WorkspaceContext()
context.finish_load(SaveIdentity('world', 'Island', 'C:/saves/Level.sav'))
journal = PendingChangeJournal()
journal.changed.connect(context.set_pending_changes)
journal.record('Edited player level', context='Player A')

class Manager(QObject):
    save_finished = pyqtSignal(float)
    save_failed = pyqtSignal(str)
    outcome = 'cancel'
    def save_changes(self, parent=None):
        if self.outcome == 'cancel':
            return False
        if self.outcome == 'exception':
            raise RuntimeError('preflight error')
        if self.outcome == 'failure':
            self.save_failed.emit('disk error')
        else:
            self.save_finished.emit(0.1)
        return True

manager = Manager()
module.save_manager = manager
errors = []
window = SimpleNamespace(
    workspace_context=context, pending_journal=journal,
    _sync_dirty_from_runtime=lambda: None,
    _save_before_close=lambda: MainWindow._save_before_close(window),
    _show_error=lambda title, detail: errors.append((title, detail)),
)

class Message:
    choice = 'cancel'
    def __init__(self, parent):
        self.buttons = {}
    def setWindowTitle(self, value):
        pass
    def setText(self, value):
        self.detail = value
        assert '1 pending changes' in value
        assert 'Edited player level' in value
    def addButton(self, label, role):
        button = object()
        self.buttons[{0: 'save', 1: 'discard', 2: 'cancel'}[role]] = button
        return button
    def setIcon(self, value):
        pass
    def setDefaultButton(self, value):
        pass
    def exec(self):
        pass
    def clickedButton(self):
        return self.buttons[Message.choice]

Message.AcceptRole = 0
Message.DestructiveRole = 1
Message.RejectRole = 2
Message.Question = 3
module.QMessageBox = Message
for choice, outcome, expected in [
    ('cancel', 'cancel', False),
    ('discard', 'cancel', True),
    ('save', 'cancel', False),
    ('save', 'failure', False),
    ('save', 'exception', False),
    ('save', 'success', True),
]:
    Message.choice = choice
    manager.outcome = outcome
    assert MainWindow._confirm_close_with_pending_changes(window) is expected
    assert len(journal.changes) == 1
assert errors == [('Save failed', 'preflight error')]
""")
    assert result.returncode == 0, result.stderr


def test_recent_save_replacement_requires_save_discard_or_cancel():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal
import palworld_aio.ui.main_window as module
from palworld_aio import constants
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal
from palworld_aio.ui.workspace_context import SaveIdentity, WorkspaceContext

app = QCoreApplication.instance() or QCoreApplication([])
context = WorkspaceContext()
context.finish_load(SaveIdentity('old', 'Old world', 'C:/old/Level.sav'))
journal = PendingChangeJournal()
journal.changed.connect(context.set_pending_changes)
journal.record('Edited inventory')
constants.dirty = True

class Manager(QObject):
    save_finished = pyqtSignal(float)
    save_failed = pyqtSignal(str)
    outcome = 'cancel'
    def __init__(self):
        super().__init__()
        self.loads = []
    def save_changes(self, parent=None):
        if self.outcome == 'cancel':
            return False
        if self.outcome == 'failure':
            self.save_failed.emit('disk error')
        else:
            self.save_finished.emit(0.1)
        return True
    def load_save(self, path=None, parent=None):
        self.loads.append(path)

manager = Manager()
module.save_manager = manager
class Message:
    choice = 'cancel'
    def __init__(self, parent):
        self.buttons = {}
    def setWindowTitle(self, value):
        pass
    def setText(self, value):
        assert '1 pending changes' in value
        assert 'Level.sav' in value
    def addButton(self, label, role):
        button = object()
        self.buttons[{0: 'save', 1: 'discard', 2: 'cancel'}[role]] = button
        return button
    def setIcon(self, value):
        pass
    def setDefaultButton(self, value):
        pass
    def exec(self):
        pass
    def clickedButton(self):
        return self.buttons[Message.choice]
Message.AcceptRole = 0
Message.DestructiveRole = 1
Message.RejectRole = 2
Message.Warning = 3
module.QMessageBox = Message

window = SimpleNamespace(
    workspace_context=context, pending_journal=journal,
    _sync_dirty_from_runtime=lambda: None,
    _save_before_close=lambda: MainWindow._save_before_close(window),
    _confirm_replace_pending_changes=lambda target:
        MainWindow._confirm_replace_pending_changes(window, target),
)
with TemporaryDirectory() as temp:
    folder = Path(temp)
    (folder / 'Players').mkdir()
    (folder / 'Level.sav').touch()
    for choice, outcome, should_load in [
        ('cancel', 'cancel', False),
        ('save', 'cancel', False),
        ('save', 'failure', False),
        ('discard', 'cancel', True),
        ('save', 'success', True),
    ]:
        Message.choice = choice
        manager.outcome = outcome
        before = len(manager.loads)
        MainWindow._load_recent_save(window, str(folder))
        assert len(manager.loads) == before + int(should_load)
        assert len(journal.changes) == 1
    assert all(path == str(folder / 'Level.sav') for path in manager.loads)
constants.dirty = False
""")
    assert result.returncode == 0, result.stderr


def test_file_folder_and_drop_loads_respect_pending_guard():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import palworld_aio.ui.main_window as module
from palworld_aio.ui.main_window import MainWindow

loads = []
module.save_manager = SimpleNamespace(
    load_save=lambda path=None, parent=None: loads.append(path))
class Picker:
    chosen = ''
    @staticmethod
    def getOpenFileName(*args):
        return Picker.chosen, ''
    @staticmethod
    def getExistingDirectory(*args):
        return str(Path(Picker.chosen).parent)
module.QFileDialog = Picker
decision = {'allow': False}
window = SimpleNamespace(
    _confirm_replace_pending_changes=lambda target: decision['allow'],
    _show_warning=lambda *args: None,
    _drop_overlay=SimpleNamespace(setVisible=lambda value: None),
)

class Event:
    def __init__(self, path):
        self.path = path
        self.accepted = False
        self.ignored = False
    def mimeData(self):
        return SimpleNamespace(
            hasUrls=lambda: True,
            urls=lambda: [SimpleNamespace(toLocalFile=lambda: self.path)])
    def acceptProposedAction(self):
        self.accepted = True
    def ignore(self):
        self.ignored = True

with TemporaryDirectory() as temp:
    folder = Path(temp)
    (folder / 'Players').mkdir()
    level = folder / 'Level.sav'
    level.touch()
    Picker.chosen = str(level)
    MainWindow._load_save(window)
    MainWindow._load_save_folder(window)
    event = Event(str(level))
    MainWindow.dropEvent(window, event)
    assert event.ignored and not event.accepted
    assert loads == []

    decision['allow'] = True
    MainWindow._load_save(window)
    MainWindow._load_save_folder(window)
    event = Event(str(level))
    MainWindow.dropEvent(window, event)
    assert event.accepted
    assert loads == [str(level)] * 3
""")
    assert result.returncode == 0, result.stderr


def test_reload_from_disk_keeps_pending_changes_on_cancel_or_failure():
    result = _run_isolated(r"""
from types import SimpleNamespace
import palworld_aio.ui.main_window as module
from palworld_aio import constants
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal

old_path = constants.current_save_path
old_doc = constants.loaded_level_json
constants.current_save_path = 'C:/old'
constants.loaded_level_json = {'loaded': True}
constants.dirty = True
journal = PendingChangeJournal()
journal.record('Changed inventory')
state = {'allow': False, 'fail': False, 'reloads': 0, 'refreshes': 0}
errors = []
def reload():
    state['reloads'] += 1
    if state['fail']:
        raise RuntimeError('parse error')
module.save_manager = SimpleNamespace(reload_current_save=reload)
window = SimpleNamespace(
    _confirm_replace_pending_changes=lambda target: state['allow'],
    refresh_all=lambda: state.__setitem__('refreshes', state['refreshes'] + 1),
    _refresh_global_search_index=lambda: None,
    _set_dirty=lambda dirty: journal.clear() if not dirty else None,
    _populate_loaded_overview=lambda: None,
    _show_error=lambda title, detail: errors.append((title, detail)),
)
try:
    MainWindow._reload_from_disk(window)
    assert state['reloads'] == 0 and journal.summary.count == 1
    state['allow'] = True
    state['fail'] = True
    MainWindow._reload_from_disk(window)
    assert state['reloads'] == 1 and journal.summary.count == 1
    assert constants.dirty
    assert errors == [('Reload failed', 'parse error')]
    state['fail'] = False
    MainWindow._reload_from_disk(window)
    assert state['reloads'] == 2 and state['refreshes'] == 1
    assert journal.summary.count == 0 and not constants.dirty
finally:
    constants.current_save_path = old_path
    constants.loaded_level_json = old_doc
    constants.dirty = False
""")
    assert result.returncode == 0, result.stderr


def test_backup_restore_never_starts_after_pending_guard_cancel():
    result = _run_isolated(r"""
from types import SimpleNamespace
from palworld_aio import constants
from palworld_aio.ui.main_window import MainWindow

old_path = constants.current_save_path
old_doc = constants.loaded_level_json
old_xgp = constants.xgp_loaded
old_dirty = constants.dirty
constants.current_save_path = 'C:/old'
constants.loaded_level_json = {'loaded': True}
constants.xgp_loaded = False
constants.dirty = True
decisions = []
window = SimpleNamespace(
    _confirm_replace_pending_changes=lambda target:
        decisions.append(target) or False,
    _confirm_backup_restore=lambda backup:
        (_ for _ in ()).throw(AssertionError('restore must not start')),
)
try:
    MainWindow._restore_backup_record(window, SimpleNamespace())
    assert decisions == ['Restore this backup?']
finally:
    constants.current_save_path = old_path
    constants.loaded_level_json = old_doc
    constants.xgp_loaded = old_xgp
    constants.dirty = old_dirty
""")
    assert result.returncode == 0, result.stderr


def test_player_level_change_has_real_in_memory_undo_and_redo():
    result = _run_isolated(r"""
from types import SimpleNamespace
import palworld_aio.ui.main_window as module
import palworld_aio.managers.player_manager as player_manager
from palworld_aio import constants
from palworld_aio.ui.main_window import MainWindow
from palworld_aio.ui.pending_changes import PendingChangeJournal

uid = 'TESTPLAYER'
old_levels = constants.player_levels
constants.player_levels = {uid: 5}
module.LevelInputDialog.get_level = lambda *args: 7
applied = []
def adjust(player_uid, level):
    applied.append((player_uid, level))
    constants.player_levels[uid] = level
    return True
player_manager.adjust_player_level = adjust
journal = PendingChangeJournal()
refreshes = []
window = SimpleNamespace(
    refresh_all=lambda: refreshes.append(window._suppress_dirty_refresh),
    record_pending_change=lambda label, **kwargs:
        journal.record(label, **kwargs),
    _show_info=lambda *args: None,
)
try:
    MainWindow._set_player_level(window, uid)
    assert applied == [(uid, 7)]
    assert journal.summary.count == 1
    assert journal.changes[0].label == 'Player level changed from 5 to 7'
    assert journal.can_undo and not journal.can_redo
    assert journal.undo_last()
    assert applied[-1] == (uid, 5)
    assert journal.can_redo
    assert journal.redo_last()
    assert applied[-1] == (uid, 7)
    assert refreshes == [True, True, True]
    assert window._suppress_dirty_refresh is False
finally:
    constants.player_levels = old_levels
""")
    assert result.returncode == 0, result.stderr


def test_leaf_ui_import_does_not_create_editor_import_cycle():
    result = _run_isolated("""
from palworld_aio.editor.pal_editor.widgets import SkillSlotFrame
from palworld_aio.ui import MainWindow

assert SkillSlotFrame.__name__ == 'SkillSlotFrame'
assert MainWindow.__name__ == 'MainWindow'
""")

    assert result.returncode == 0, result.stderr


def test_reference_and_breeding_editor_links_route_then_select():
    result = _run_isolated(r"""
from palworld_aio.ui.main_window import MainWindow

class Target:
    def __init__(self):
        self.calls = []
    def open_reference(self, category, identifier):
        self.calls.append((category, identifier))
        return True
    def select_pal(self, asset):
        self.calls.append(asset)
        return True

class WindowDouble:
    _LEGACY_PAGE_INDEX = {'docs': 10, 'breeding': 11}
    def __init__(self):
        self.docs_tab = Target()
        self.breeding_tab = Target()
        self.activated = []
        self.ensured = []
    def _activate_nav(self, route):
        self.activated.append(route)
    def _ensure_tab(self, index):
        self.ensured.append(index)

window = WindowDouble()
assert MainWindow.open_reference(window, 'items', 'Item_A')
assert MainWindow.open_breeding(window, 'SheepBall')
assert window.activated == ['docs', 'breeding']
assert window.ensured == [10, 11]
assert window.docs_tab.calls == [('items', 'Item_A')]
assert window.breeding_tab.calls == ['SheepBall']
""")

    assert result.returncode == 0, result.stderr


def test_live_main_window_uses_workspace_shell_and_preserves_legacy_routes():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication
import palworld_aio.ui.main_window as main_window
from palworld_aio.ui.chrome.app_bar import AppBar
from palworld_aio.ui.chrome.nav_strip import NavStrip
from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
from palworld_aio.ui.pages.overview_page import OverviewPage
from palworld_aio.ui.pages.activity_page import ActivityPage
from palworld_aio.ui.pages.about_page import AboutPage
from palworld_aio.ui.pages.backups_page import BackupsPage
from palworld_aio.ui.pages.bases_page import BasesPage
from palworld_aio.ui.pages.exclusions_page import ExclusionsPage
from palworld_aio.ui.pages.diagnostics_page import DiagnosticsPage
from palworld_aio.ui.pages.guilds_page import GuildsPage
from palworld_aio.ui.pages.players_page import PlayersPage
from palworld_aio.ui.pages.settings_page import SettingsPage
from palworld_aio.ui.pages.tool_center_page import ToolCenterPage
from palworld_aio.ui.tabs.map_tab import MapTab
from palworld_aio.ui.routes import ROUTES
from palworld_aio.ui.workspace_context import SaveIdentity, SavePlatform

app = QApplication.instance() or QApplication([])
main_window.load_exclusions = lambda: None
main_window.MainWindow._check_update = lambda self: None
main_window.MainWindow._save_user_settings = lambda self: None
main_window.MainWindow._load_user_settings = lambda self: setattr(self, 'user_settings', {
    'language': 'en_US',
    'show_icons': True,
    'boot_preference': 'menu',
    'console_detached': False,
    'console_window_geometry': None,
    'loading_screen_mode': 'overlay',
    'tray_expanded': False,
})

window = main_window.MainWindow()
assert isinstance(window.workspace_shell, WorkspaceShell)
assert isinstance(window.overview_page, OverviewPage)
assert isinstance(window.activity_page, ActivityPage)
assert isinstance(window.about_page, AboutPage)
assert isinstance(window.backups_page, BackupsPage)
assert isinstance(window.diagnostics_page, DiagnosticsPage)
assert isinstance(window.bases_page, BasesPage)
assert isinstance(window.exclusions_page, ExclusionsPage)
assert isinstance(window.guilds_page, GuildsPage)
assert isinstance(window.players_page, PlayersPage)
assert isinstance(window.settings_page, SettingsPage)
assert isinstance(window.map_tab, MapTab)
assert isinstance(window.tool_center_page, ToolCenterPage)
assert window.workspace_shell._route_pages['overview'] is window.overview_page
assert window.workspace_shell._route_pages['activity'] is window.activity_page
assert window.workspace_shell._route_pages['about'] is window.about_page
assert window.workspace_shell._route_pages['backups'] is window.backups_page
assert window.workspace_shell._route_pages['diagnostics'] is window.diagnostics_page
assert window.workspace_shell._route_pages['bases'] is window.bases_page
assert window.workspace_shell._route_pages['exclusions'] is window.exclusions_page
assert window.workspace_shell._route_pages['guilds'] is window.guilds_page
assert window.workspace_shell._route_pages['players'] is window.players_page
assert window.workspace_shell._route_pages['map'] is window.map_tab
assert window.workspace_shell._route_pages['tools'] is window.tool_center_page
assert window.workspace_shell._route_pages['settings'] is window.settings_page
assert set(window.workspace_shell._route_pages) == set(ROUTES.ids)
assert 'app_bar' not in window.__dict__
assert 'nav_strip' not in window.__dict__
assert window.findChild(AppBar) is None
assert window.findChild(NavStrip) is None
assert window.minimumWidth() == 1024
assert window.minimumHeight() == 700
assert window.workspace_shell.router.current_route_id == 'overview'
assert window.workspace_shell.page_host.currentWidget() is window.overview_page
assert window.overview_page.stack.currentWidget() is window.overview_page.no_save_view
assert window.stacked_widget.currentIndex() == 0

for descriptor in ROUTES:
    if not descriptor.requires_save:
        continue
    window._activate_nav(descriptor.route_id)
    assert window.workspace_shell.router.current_route_id == descriptor.route_id
    assert (window.workspace_shell.page_host.currentWidget()
            is window.workspace_shell._prerequisite_state)

window._activate_nav('tools')
assert window.workspace_shell.page_host.currentWidget() is window.tool_center_page
assert len(window.tool_center_page.cards) == 7

window._activate_nav('settings')
assert window.workspace_shell.page_host.currentWidget() is window.settings_page
window._show_about()
assert window.workspace_shell.page_host.currentWidget() is window.about_page
window._activate_nav('diagnostics')
assert window.workspace_shell.page_host.currentWidget() is window.diagnostics_page

window.workspace_shell.sidebar.route_buttons['players'].click()
assert window.workspace_shell.router.current_route_id == 'players'
assert window.workspace_shell.page_host.currentWidget() is window.workspace_shell._prerequisite_state
window.workspace_context.finish_load(SaveIdentity(
    'fixture', 'Fixture World', 'C:/Fixture', SavePlatform.STEAM))
window._activate_nav('overview')
window._activate_nav('players')
assert window.workspace_shell.page_host.currentWidget() is window.players_page
window._activate_nav('bases')
assert window.workspace_shell.page_host.currentWidget() is window.bases_page
window._activate_nav('guilds')
assert window.workspace_shell.page_host.currentWidget() is window.guilds_page
window._activate_nav('map')
assert window.workspace_shell.page_host.currentWidget() is window.map_tab
window.map_tab.openBaseRequested.emit({
    'base_id': 'base-001', 'base_position': 1,
    'guild_id': 'guild-001', 'guild_name': 'Lamplight Guild',
})
assert window.workspace_shell.router.current_route_id == 'bases'
assert window.workspace_context.snapshot.base.identifier == 'base-001'
assert window.bases_page.browser.search_input.text() == 'base-001'
window.map_tab.openPlayerRequested.emit({
    'player_uid': 'player-001', 'player_name': 'Mara',
    'guild_id': 'guild-001', 'guild_name': 'Lamplight Guild',
})
assert window.workspace_shell.router.current_route_id == 'players'
assert window.workspace_context.snapshot.player.identifier == 'player-001'
assert window.players_page.browser.search_input.text() == 'player-001'
window.map_tab.openGuildRequested.emit({
    'guild_id': 'guild-001', 'guild_name': 'Lamplight Guild',
})
assert window.workspace_shell.router.current_route_id == 'guilds'
assert window.workspace_context.snapshot.guild.identifier == 'guild-001'
assert window.guilds_page.browser.search_input.text() == 'guild-001'
window.workspace_shell.go_back()
assert window.workspace_shell.router.current_route_id == 'players'
assert window.workspace_context.snapshot.player.identifier == 'player-001'
assert window.players_page.browser.search_input.text() == 'player-001'
window.workspace_shell.go_back()
assert window.workspace_shell.router.current_route_id == 'bases'
assert window.workspace_context.snapshot.base.identifier == 'base-001'
assert window.bases_page.browser.search_input.text() == 'base-001'
window.workspace_shell.go_forward()
assert window.workspace_shell.router.current_route_id == 'players'
assert window.workspace_context.snapshot.player.identifier == 'player-001'
window._activate_nav('exclusions')
assert window.workspace_shell.page_host.currentWidget() is window.exclusions_page
window._activate_nav('docs')
assert window.workspace_shell.router.current_route_id == 'docs'
assert window.stacked_widget.currentIndex() == 10
assert all(ribbon.isHidden() for ribbon in window.findChildren(
    main_window.QFrame, 'pageRibbon'))
assert len(window._page_shortcuts) == 12
assert {shortcut.key().toString() for shortcut in window._command_shortcuts} == {
    'Ctrl+K', 'Ctrl+P',
}
assert window._global_search_shortcut.key().toString() == 'Ctrl+Shift+F'
assert window._shell_search_button.isEnabled()
assert not ({shortcut.key().toString() for shortcut in window._page_shortcuts}
            & {shortcut.key().toString() for shortcut in window._command_shortcuts})
window._show_command_palette()
assert len(window._command_palette._commands) == 20
assert {command.command_id for command in window._command_palette._commands} >= {
    'app:load_save', 'app:save_changes', 'route:overview', 'route:diagnostics',
}
window._command_palette.reject()
assert window._window_controls is window.workspace_shell.title_bar.window_controls

window.close()
""")

    assert result.returncode == 0, result.stderr


def test_backup_restore_confirmation_and_main_window_flow_are_guarded():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from datetime import datetime
from pathlib import Path
import tempfile
from PyQt6.QtWidgets import QApplication, QDialog, QLabel

import palworld_aio.ui.main_window as main_window
from palworld_aio import constants
from palworld_aio.application import backup_catalog as catalog
from palworld_aio.managers.save_manager import save_manager
from palworld_aio.ui.chrome.components import BaseDialog

app = QApplication.instance() or QApplication([])
main_window.load_exclusions = lambda: None
main_window.MainWindow._check_update = lambda self: None
main_window.MainWindow._save_user_settings = lambda self: None
main_window.MainWindow._load_user_settings = lambda self: setattr(self, 'user_settings', {
    'language': 'en_US', 'show_icons': True, 'boot_preference': 'menu',
    'console_detached': False, 'console_window_geometry': None,
    'loading_screen_mode': 'header', 'tray_expanded': False,
})
window = main_window.MainWindow()

root = Path(tempfile.mkdtemp(prefix='paltrainer_backup_flow_'))
current = root / 'current'
backup_path = root / 'backup'
for folder, marker in ((current, b'current'), (backup_path, b'backup')):
    folder.mkdir()
    (folder / 'Level.sav').write_bytes(marker)
    (folder / 'Players').mkdir()
    (folder / 'Players' / f'{marker.decode()}.sav').write_bytes(marker)
record = catalog.BackupRecord(
    'fixture', backup_path, datetime(2026, 9, 9, 13, 45),
    'Before Player Inventory Edit', 'Local World', 42)

def accept_confirmation(dialog):
    labels = [label.text() for label in dialog.findChildren(QLabel)]
    assert dialog.title_label.text() == 'Restore this backup?'
    assert 'Current save will be backed up before restoration.' in labels
    assert any(text.startswith('Backup date: Sep 09, 2026') for text in labels)
    return QDialog.DialogCode.Accepted

BaseDialog.exec = accept_confirmation
assert window._confirm_backup_restore(record)

constants.current_save_path = str(current)
constants.loaded_level_json = {'loaded': True}
constants.xgp_loaded = False
constants.dirty = False
catalog.default_backups_root = lambda: root
main_window.run_with_loading = (
    lambda callback, func, *args, **kwargs: callback(func(*args)))
save_manager.reload_current_save = lambda: True
window.refresh_all = lambda: None
window._refresh_global_search_index = lambda: None
window._populate_loaded_overview = lambda: None
window._refresh_backups = lambda: None
window._confirm_backup_restore = lambda _backup: True

window._restore_backup_record(record)

assert (current / 'Level.sav').read_bytes() == b'backup'
assert (current / 'Players' / 'backup.sav').is_file()
assert not (current / 'Players' / 'current.sav').exists()
safety = tuple((root / 'Restore Safety').glob('PalworldSave_backup_*'))
assert len(safety) == 1
assert (safety[0] / 'Level.sav').read_bytes() == b'current'
assert window.backups_page.result_banner is not None
assert 'previous save is preserved' in (
    window.backups_page.result_banner.message_label.text())
assert window.operation_journal.events[-1].title == 'Backup restored'

window.close()
""")

    assert result.returncode == 0, result.stderr


def test_diagnostics_copy_export_and_update_state_use_safe_page_contract():
    result = _run_isolated(r"""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from pathlib import Path
import tempfile
from PyQt6.QtWidgets import QApplication
import palworld_aio.ui.main_window as main_window

app = QApplication.instance() or QApplication([])
main_window.load_exclusions = lambda: None
main_window.MainWindow._check_update = lambda self: None
main_window.MainWindow._save_user_settings = lambda self: None
main_window.MainWindow._load_user_settings = lambda self: setattr(self, 'user_settings', {
    'language': 'en_US', 'show_icons': True, 'boot_preference': 'menu',
    'console_detached': False, 'console_window_geometry': None,
    'loading_screen_mode': 'header', 'tray_expanded': False,
})
window = main_window.MainWindow()
report = window.diagnostics_page.report_text()
window._copy_diagnostics_report(report)
assert QApplication.clipboard().text() == report
assert window.diagnostics_page.result_label.text().startswith('Support report copied')

target = Path(tempfile.mkdtemp(prefix='paltrainer_diagnostics_')) / 'report.txt'
main_window.QFileDialog.getSaveFileName = staticmethod(
    lambda *_args, **_kwargs: (str(target), 'Text Files (*.txt)'))
window._export_diagnostics_report(report)
assert target.read_text(encoding='utf-8') == report
assert 'exported to' in window.diagnostics_page.result_label.text()

window._on_update_checked(False, '2.5.0', 'stable')
assert window.about_page.update_banner.property('status') == 'available'
assert '2.5.0' in window.about_page.update_label.text()
assert window.diagnostics_page.result_label.property('status') == 'warning'
window.close()
""")

    assert result.returncode == 0, result.stderr


def test_repair_actions_keep_manager_callbacks_behind_shared_review():
    import ast

    source_path = PROJECT_ROOT / 'src' / 'palworld_aio' / 'ui' / 'main_window.py'
    tree = ast.parse(source_path.read_text(encoding='utf-8-sig'))
    main_window = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == 'MainWindow')
    methods = {
        node.name: node for node in main_window.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        '_remove_invalid_items': 'remove_invalid_items_from_save',
        '_remove_invalid_structures': 'delete_invalid_structure_map_objects',
        '_repair_structures': 'repair_structures',
        '_repair_items': 'repair_items',
        '_remove_invalid_pals': 'remove_invalid_pals_from_save',
        '_remove_invalid_passives': 'remove_invalid_passives_from_save',
        '_fix_all_pals': 'fix_all_pals_combined',
        '_reset_missions': 'fix_missions',
        '_reset_anti_air': 'reset_anti_air_turrets',
        '_reset_dungeons': 'reset_dungeons',
        '_reset_oilrig': 'reset_oilrig',
        '_reset_invader': 'reset_invader',
        '_reset_supply': 'reset_supply',
        '_reset_lock_gimmick': 'reset_lock_gimmick',
        '_fix_invalid_active_skills': 'fix_invalid_pal_active_skills',
        '_fix_all_timestamps': 'fix_all_negative_timestamps',
        '_reset_player_timestamp': 'reset_selected_player_timestamp',
        '_rebuild_all_guilds': 'rebuild_all_guilds',
        '_trim_overfilled_inventories': 'detect_and_trim_overfilled_inventories',
    }

    for method_name, callback_name in expected.items():
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
        references = {
            node.id for node in ast.walk(methods[method_name])
            if isinstance(node, ast.Name)
        }
        assert callback_name in calls | references
        assert '_run_loaded_save_repair' in attributes

    illegal_pal_source = ast.unparse(methods['_fix_illegal_pals'])
    illegal_player_source = ast.unparse(methods['_fix_illegal_players'])
    assert 'fix_illegal_pals_in_save(self, selected_uids=selected_uids, result_details=True)' in illegal_pal_source
    assert 'fix_illegal_player_stats(self, selected_uids=selected_uids)' in illegal_player_source


def test_base_transfer_actions_keep_manager_callbacks_behind_shared_review():
    import ast

    source_path = PROJECT_ROOT / 'src' / 'palworld_aio' / 'ui' / 'main_window.py'
    tree = ast.parse(source_path.read_text(encoding='utf-8-sig'))
    main_window = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == 'MainWindow')
    methods = {
        node.name: node for node in main_window.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        '_import_base_to_guild': {'load_base_file', 'import_base_json'},
        '_export_all_bases': {'export_base_json'},
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


"""Cancel and journal boundaries for destructive editor actions."""

from types import SimpleNamespace

from tests.dynamic_importer import import_from

base_inventory = import_from('palworld_aio.ui.tabs.base_inventory_tab')
player_inventory = import_from('palworld_aio.ui.tabs.inventory_tab')
main_window = import_from('palworld_aio.ui.main_window')


def test_bulk_quantity_clear_cancel_does_not_mutate(monkeypatch):
    calls = []
    item = {'slot_index': 4, 'container_type': 'main'}
    tab = SimpleNamespace(
        inventory=SimpleNamespace(update_quantity=lambda *args: calls.append(args)),
        _themed_message_box=lambda *args: calls.append(('confirm', args[2])) or 0,
    )

    player_inventory.PlayerInventoryTab._on_bulk_clear_qty(tab, [item])

    assert len(calls) == 1
    assert '1' in calls[0][1]


def test_bulk_quantity_clear_records_only_pending_world_items():
    calls = []
    inventory = SimpleNamespace(
        set_effigy_count=lambda *args: calls.append(('effigy', args)),
        update_quantity=lambda *args: calls.append(('world', args)) or True,
    )
    tab = SimpleNamespace(
        inventory=inventory,
        current_player_uid='uid',
        parent_window=SimpleNamespace(record_pending_change=lambda *a, **k:
                                      calls.append(('journal', a, k))),
        _themed_message_box=lambda *args: player_inventory.QMessageBox.Yes,
        selected_item=None,
        _refresh_display=lambda: calls.append(('refresh',)),
    )
    items = [
        {'slot_index': 1, 'container_type': 'main'},
        {'slot_index': 2, 'is_effigy': True, 'item_id': 'Effigy',
         'relic_type': 'Fire'},
    ]

    player_inventory.PlayerInventoryTab._on_bulk_clear_qty(tab, items)

    assert ('world', ('main', 1, 0)) in calls
    assert ('effigy', ('Fire', 0)) in calls
    assert ('journal', ('Clear player inventory quantities',), {
        'context': 'uid', 'affected_count': 1, 'high_risk': True,
    }) in calls


def test_base_container_clear_cancel_preserves_booth_and_journal(monkeypatch):
    calls = []
    booth = {'id': 'c1', 'booth_type': 'PalMapObjectItemBoothModel',
             'booth_trade_infos': [{'item': 'A'}]}
    manager = SimpleNamespace(
        inventory_container=object(), current_container=booth,
        get_items_count=lambda: 2,
        clear_container=lambda _id: calls.append('clear'),
    )
    tab = SimpleNamespace(
        manager=manager,
        _pal_booth_affected_count=lambda info: 0,
        _main_window=SimpleNamespace(record_pending_change=lambda *a, **k: calls.append('journal')),
    )
    monkeypatch.setattr(base_inventory, 'show_question',
                        lambda _parent, _title, message: calls.append(message) or False)

    base_inventory.BaseInventoryTab._clear_container(tab)

    assert calls == [calls[0]]
    assert '2' in calls[0] and '1 trade' in calls[0]
    assert booth['booth_trade_infos'] == [{'item': 'A'}]


def test_base_container_clear_records_actual_impact_without_undo(monkeypatch):
    calls = []
    booth = {'id': 'c1', 'booth_type': 'PalMapObjectItemBoothModel',
             'booth_trade_infos': [{'item': 'A'}]}
    tab = SimpleNamespace(
        manager=SimpleNamespace(
            inventory_container=object(), current_container=booth,
            get_items_count=lambda: 2,
            clear_container=lambda _id: calls.append('clear') or True),
        _pal_booth_affected_count=lambda info: 0,
        _main_window=SimpleNamespace(record_pending_change=lambda *a, **k:
                                     calls.append(('journal', a, k))),
        _current_base_name='Coastal Base', _current_guild_name='Guild',
        _on_container_selected=lambda _id: None,
    )
    monkeypatch.setattr(base_inventory, 'show_question', lambda *_args: True)
    monkeypatch.setattr(base_inventory.QTimer, 'singleShot', lambda *_args: None)

    base_inventory.BaseInventoryTab._clear_container(tab)

    assert booth['booth_trade_infos'] == []
    assert ('journal', ('Clear base container',), {
        'context': 'Coastal Base', 'affected_count': 3,
        'high_risk': True,
    }) in calls
    assert 'undo' not in calls[-1][2]


def test_single_player_delete_cancel_and_success_journal(monkeypatch):
    calls = []
    monkeypatch.setattr(main_window.constants, 'exclusions', {'players': []})
    monkeypatch.setattr(main_window, 'show_question',
                        lambda _parent, _title, message: calls.append(('confirm', message)) or False)
    monkeypatch.setattr(main_window, 'delete_player',
                        lambda uid: calls.append(('delete', uid)) or True)
    window = SimpleNamespace(
        _get_player_name=lambda uid: 'Player A',
        record_pending_change=lambda *a, **k: calls.append(('journal', k)),
        refresh_all=lambda: calls.append(('refresh',)),
        _show_info=lambda *a: None,
    )

    main_window.MainWindow._delete_player(window, 'uid')
    assert len(calls) == 1 and '1 player' in calls[0][1]

    monkeypatch.setattr(main_window, 'show_question', lambda *_args: True)
    main_window.MainWindow._delete_player(window, 'uid')
    assert ('delete', 'uid') in calls
    assert ('journal', {'context': 'Player A', 'affected_count': 1,
                        'high_risk': True}) in calls


def test_imported_pal_preview_is_read_only_and_matches_world_gate(monkeypatch, tmp_path):
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'player_dps.sav').write_bytes(b'fixture')
    imported = {
        'key': {'InstanceId': {'value': 'pal-1'}},
        'value': {'RawData': {'value': {'object': {'SaveParameter': {
            'struct_type': 'PalIndividualCharacterSaveParameter',
            'value': {'bImportedCharacter': {'value': True}},
        }}}}},
    }
    entries = [imported]
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', {
        'properties': {'worldSaveData': {'value': {
            'CharacterSaveParameterMap': {'value': entries},
        }}}
    })
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _path: SimpleNamespace(
        properties={'SaveParameterArray': {'value': {'values': [
            {'SaveParameter': {'value': {'bImportedCharacter': {'value': True}}}},
        ]}}},
    ))

    assert func_manager.count_imported_pals() == 2
    assert entries == [imported]
    entries.clear()
    assert func_manager.count_imported_pals() == 0


def test_guild_assignment_cancel_does_not_dirty_or_refresh(monkeypatch):
    calls = []
    monkeypatch.setattr(main_window.constants, 'loaded_level_json', {'properties': {}})
    monkeypatch.setattr(main_window, 'GuildAssignDialog',
                        lambda *a, **k: SimpleNamespace(exec=lambda: None))
    window = SimpleNamespace(
        record_pending_change=lambda *a, **k: calls.append('journal'),
        refresh_all=lambda: calls.append('refresh'),
    )

    main_window.MainWindow._open_guild_assign_dialog(window)

    assert calls == []


def test_non_base_map_preview_and_cancel_leave_world_unchanged(monkeypatch):
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'BaseCampSaveData': {'value': [{'key': 'base-1'}]},
        'MapObjectSaveData': {'value': {'values': [
            {'Model': {'value': {'RawData': {'value': {
                'base_camp_id_belong_to': 'base-1'}}}}},
            {'Model': {'value': {'RawData': {'value': {}}}}},
        ]}},
    }}}}
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager, 'is_death_bag', lambda _obj: False)
    monkeypatch.setattr(func_manager, 'is_entity_in_exclusion_zones',
                        lambda _obj: False)
    assert func_manager.count_non_base_map_objects() == 1

    calls = []
    monkeypatch.setattr(main_window, 'show_question',
                        lambda _parent, _title, message:
                        calls.append(message) or False)
    window = SimpleNamespace(_show_warning=lambda *a: None)
    main_window.MainWindow._delete_non_base_map_objs(window)
    assert len(calls) == 1 and '1 non-base map' in calls[0]
    assert len(world['properties']['worldSaveData']['value'][
        'MapObjectSaveData']['value']['values']) == 2


def test_private_chest_preview_does_not_change_lock_fields(monkeypatch):
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'MapObjectSaveData': {'value': {'values': [
            {'ConcreteModel': {'value': {'RawData': {'value': {
                'concrete_model_type': 'PalMapObjectItemBoothModel',
                'is_private_lock': 1,
            }}}}},
        ]}},
        'other': {'private_lock_player_uid': 'uid'},
    }}}}
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)

    assert func_manager.count_private_chest_unlocks() == 2
    assert world['properties']['worldSaveData']['value']['other'][
        'private_lock_player_uid'] == 'uid'


def test_guild_chest_slot_preview_does_not_resize_container(monkeypatch):
    func_manager = import_from('palworld_aio.managers.func_manager')
    container = {
        'key': {'ID': {'value': 'chest-id'}},
        'value': {
            'SlotNum': {'value': 10},
            'Slots': {'value': {'values': []}},
        },
    }
    world = {'properties': {'worldSaveData': {'value': {
        'GuildExtraSaveDataMap': {'value': [{
            'value': {'GuildItemStorage': {'value': {'RawData': {
                'value': {'container_id': 'chest-id'},
            }}}},
        }]},
        'ItemContainerSaveData': {'value': [container]},
    }}}}
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)

    assert func_manager.modify_all_guild_chest_slots(20, preview_only=True) == 1
    assert container['value']['SlotNum']['value'] == 10
    assert container['value']['Slots']['value']['values'] == []


def test_global_guild_chest_resize_cancel_never_runs_mutation(monkeypatch):
    calls = []
    monkeypatch.setattr(main_window.constants, 'loaded_level_json', {'properties': {}})
    monkeypatch.setattr(main_window.QInputDialog, 'getInt',
                        lambda *a, **k: (20, True))
    monkeypatch.setattr(main_window, 'modify_all_guild_chest_slots',
                        lambda size, *a, **k:
                        calls.append(('preview' if k.get('preview_only') else 'mutate', size)) or 2)
    monkeypatch.setattr(main_window, 'show_question',
                        lambda _parent, _title, message:
                        calls.append(('confirm', message)) or False)
    window = SimpleNamespace(_show_warning=lambda *a: None)

    main_window.MainWindow._modify_all_guild_chest_slots(window)

    assert [entry[0] for entry in calls] == ['preview', 'confirm']
    assert '2 eligible guild chests' in calls[1][1]


def test_max_pal_preview_counts_level_and_dps_without_writes(monkeypatch, tmp_path):
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'owner_dps.sav').write_bytes(b'fixture')
    world = {'properties': {'worldSaveData': {'value': {
        'CharacterSaveParameterMap': {'value': [
            {'value': {'RawData': {'value': {'object': {
                'SaveParameter': {'value': {'CharacterID': {'value': 'SheepBall'}}},
            }}}}},
        ]},
    }}}}
    dps = SimpleNamespace(properties={'SaveParameterArray': {'value': {
        'values': [{'SaveParameter': {'value': {
            'CharacterID': {'value': 'ChickenPal'},
        }}}],
    }}})
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _path: dps)
    monkeypatch.setattr(func_manager, 'gvasfile_to_sav',
                        lambda *args: (_ for _ in ()).throw(AssertionError('wrote DPS')))

    assert func_manager.count_pals_for_max() == (1, 1)
    assert func_manager.count_pals_for_fix_all() == (1, 1)
    assert dps.properties['SaveParameterArray']['value']['values'][0][
        'SaveParameter']['value']['CharacterID']['value'] == 'ChickenPal'


def test_repair_completion_journals_only_real_mutation(monkeypatch):
    calls = []
    state = {'result': 0}

    class FakeDialog:
        def __init__(self, spec, operation, result_message, parent):
            self.completed = SimpleNamespace(connect=lambda callback:
                                             setattr(self, 'on_completed', callback))

        def exec(self):
            self.on_completed(state['result'])

    monkeypatch.setattr(main_window.constants, 'loaded_level_json', {'properties': {}})
    monkeypatch.setattr(main_window, 'RepairWorkflowDialog', FakeDialog)
    window = SimpleNamespace(
        record_pending_change=lambda *a, **k: calls.append(('journal', a, k)),
        refresh_all=lambda: calls.append(('refresh',)),
        _record_activity=lambda *a, **k: calls.append(('activity',)),
        _show_warning=lambda *a: None,
    )

    main_window.MainWindow._run_loaded_save_repair(
        window, title='Repair', affected='Items', review='Repair items',
        operation=lambda: 0, result_message=str)
    assert calls == [('activity',)]

    state['result'] = 3
    main_window.MainWindow._run_loaded_save_repair(
        window, title='Repair', affected='Items', review='Repair items',
        operation=lambda: 3, result_message=str)
    assert ('journal', ('Repair',), {'affected_count': 3, 'high_risk': True}) in calls
    assert ('refresh',) in calls

    calls.clear()
    state['result'] = {'fixed_files': 1, 'level_removed': 0}
    main_window.MainWindow._run_loaded_save_repair(
        window, title='Repair', affected='Items', review='Repair items',
        operation=lambda: state['result'], result_message=str,
        pending_count=lambda result: result['level_removed'])
    assert calls == [('activity',)]

    state['result'] = {'fixed_files': 0, 'level_removed': 2}
    main_window.MainWindow._run_loaded_save_repair(
        window, title='Repair', affected='Items', review='Repair items',
        operation=lambda: state['result'], result_message=str,
        pending_count=lambda result: result['level_removed'])
    assert ('journal', ('Repair',), {'affected_count': 2, 'high_risk': True}) in calls


def test_reset_preview_counts_records_without_mutating_world(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')

    world = {'properties': {'worldSaveData': {'value': {
        'FixedWeaponDestroySaveData': {'value': [1, 2]},
        'DungeonPointMarkerSaveData': {'value': {'values': [3]}},
        'DungeonSaveData': {'value': []},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)

    assert func_manager.count_reset_records('FixedWeaponDestroySaveData') == 2
    assert func_manager.count_reset_records(
        'DungeonPointMarkerSaveData', 'DungeonSaveData') == 2
    assert func_manager.count_reset_records('OilrigSaveData') == 0
    assert world == before


def test_inactive_cleanup_previews_do_not_mutate_world(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')

    guild_id = '11111111-1111-1111-1111-111111111111'
    player_id = '22222222-2222-2222-2222-222222222222'
    world = {'properties': {'worldSaveData': {'value': {
        'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 864000000000 * 10}}},
        'GroupSaveDataMap': {'value': [{
            'key': guild_id,
            'value': {'GroupType': {'value': {'value': 'EPalGroupType::Guild'}},
                      'RawData': {'value': {
                          'players': [{'player_uid': player_id,
                                       'player_info': {'last_online_real_time': 0}}],
                          'admin_player_uid': player_id,
                      }}},
        }]},
        'BaseCampSaveData': {'value': [{
            'key': '33333333-3333-3333-3333-333333333333',
            'value': {'RawData': {'value': {'group_id_belong_to': guild_id}}},
        }]},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'exclusions', {})
    monkeypatch.setattr(func_manager, 'build_player_levels', lambda: None)
    monkeypatch.setattr(func_manager.constants, 'player_levels',
                        {player_id.replace('-', ''): 1})
    filters = {'mode': 0, 'days': 1}

    assert func_manager.delete_inactive_players(
        filters, preview_only=True)['count'] == 1
    assert func_manager.delete_inactive_bases(
        filters, preview_only=True)['count'] == 1
    assert world == before


def test_base_pal_restore_cancel_shows_count_without_mutation(monkeypatch):
    prompts = []
    monkeypatch.setattr(base_inventory, '_get_raw_from_item',
                        lambda entry: entry)
    monkeypatch.setattr(base_inventory, 'show_question',
                        lambda _parent, _title, message:
                        prompts.append(message) or False)
    raw = {'Hp': {'value': 1}}
    widget = SimpleNamespace(_pals=[{'character_entry': raw}, None])

    base_inventory.BasePalsContentWidget._restore_all_pals(widget)

    assert '1' in prompts[0]
    assert raw == {'Hp': {'value': 1}}


def test_skin_preview_counts_both_world_fields_without_mutation(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'Pals': [{'SkinName': 'Fancy', 'SkinAppliedCharacterId': 'Pal'},
                 {'SkinAppliedCharacterId': 'Other'}],
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)

    assert func_manager.count_level_skin_fields() == 3
    assert world == before


def test_invalid_item_preview_is_read_only_across_level_and_player_files(
        monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'ABC.sav').write_bytes(b'placeholder')
    world = {'properties': {'worldSaveData': {'value': {'Items': [
        {'RawData': {'value': {'item': {'static_id': 'UnknownItem'}}}},
    ]}}}}
    player = SimpleNamespace(properties={
        'CraftItemCount': {'value': [{'key': 'UnknownItem'}]},
    })
    before_world = deepcopy(world)
    before_player = deepcopy(player.properties)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager.constants, 'get_base_path', lambda: tmp_path)
    monkeypatch.setattr(func_manager, 'resource_path', lambda *a: tmp_path)
    monkeypatch.setattr(func_manager.json_tools, 'load', lambda _: {'items': []})
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _: player)
    monkeypatch.setattr(func_manager, 'gvasfile_to_sav',
                        lambda *a: (_ for _ in ()).throw(AssertionError('wrote file')))

    assert func_manager.remove_invalid_items_from_save(
        preview_only=True) == {'fixed_files': 1, 'level_removed': 1}
    assert world == before_world
    assert player.properties == before_player


def test_invalid_pal_preview_is_read_only_across_level_and_dps(
        monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'ABC_dps.sav').write_bytes(b'placeholder')
    entry = {'key': {'InstanceId': {'value': 'instance'}},
             'value': {'RawData': {'value': {'object': {
                 'SaveParameter': {'value': {'CharacterID': {'value': 'UnknownPal'}}}
             }}}}}
    world = {'properties': {'worldSaveData': {'value': {
        'CharacterSaveParameterMap': {'value': [entry]},
        'CharacterContainerSaveData': {'value': []},
    }}}}
    dps = SimpleNamespace(properties={'SaveParameterArray': {'value': {'values': [
        {'SaveParameter': {'value': {'CharacterID': {'value': 'UnknownPal'}}}},
    ]}}})
    before_world = deepcopy(world)
    before_dps = deepcopy(dps.properties)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager.constants, 'get_base_path', lambda: tmp_path)
    monkeypatch.setattr(func_manager, 'resource_path', lambda *a: tmp_path)
    monkeypatch.setattr(func_manager.json_tools, 'load',
                        lambda _: {'pals': [], 'npcs': []})
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _: dps)
    monkeypatch.setattr(func_manager, 'gvasfile_to_sav',
                        lambda *a: (_ for _ in ()).throw(AssertionError('wrote DPS')))

    assert func_manager.remove_invalid_pals_from_save(
        preview_only=True) == {'level_removed': 1, 'dps_removed': 1}
    assert world == before_world
    assert dps.properties == before_dps


def test_mission_reset_preview_counts_files_without_writing(monkeypatch, tmp_path):
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'ABC.sav').write_bytes(b'placeholder')
    quests = [1, 2]
    gvas = SimpleNamespace(properties={'SaveData': {'value': {
        'CompletedQuestArray_FullRelease': {'value': {'values': quests}},
    }}})
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _: gvas)
    monkeypatch.setattr(func_manager, 'gvasfile_to_sav',
                        lambda *a: (_ for _ in ()).throw(AssertionError('wrote file')))

    assert func_manager.fix_missions(preview_only=True)['fixed'] == 1
    assert quests == [1, 2]


def test_unreferenced_preview_does_not_change_world_or_deletion_queue(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'GroupSaveDataMap': {'value': []},
        'CharacterSaveParameterMap': {'value': []},
        'CharacterContainerSaveData': {'value': []},
        'MapObjectSaveData': {'value': {'values': [{
            'Model': {'value': {'BuildProcess': {'value': {
                'RawData': {'value': {'state': 0}}}}}},
        }]}},
    }}}}
    before = deepcopy(world)
    queue = {'existing'}
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'files_to_delete', queue)
    monkeypatch.setattr(func_manager, 'build_player_levels', lambda: None)
    monkeypatch.setattr(func_manager, 'is_entity_in_exclusion_zones',
                        lambda _entity: False)

    preview = func_manager.delete_unreferenced_data(preview_only=True)

    assert preview['broken_objects'] == 1
    assert world == before
    assert queue == {'existing'}


def test_unreferenced_cleanup_cancel_does_not_run_mutator(monkeypatch):
    prompts = []
    monkeypatch.setattr(main_window.constants, 'loaded_level_json', {'properties': {}})
    monkeypatch.setattr(main_window, 'delete_unreferenced_data',
                        lambda _parent=None, *, preview_only=False:
                        {'broken_objects': 2} if preview_only else
                        (_ for _ in ()).throw(AssertionError('mutated')))
    monkeypatch.setattr(main_window, 'run_with_loading',
                        lambda done, task: done(task()))
    monkeypatch.setattr(main_window, 'show_question',
                        lambda _parent, _title, message:
                        prompts.append(message) or False)
    window = SimpleNamespace(
        record_pending_change=lambda *a, **k: (_ for _ in ()).throw(
            AssertionError('journaled')),
        refresh_all=lambda: (_ for _ in ()).throw(AssertionError('refreshed')),
    )

    main_window.MainWindow._delete_unreferenced(window)

    assert '2' in prompts[0]


def test_structure_and_item_repair_previews_are_read_only(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    dynamic_items = import_from('palworld_aio.inventory.dynamic_item_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'MapObjectSaveData': {'value': {'values': [{
            'Model': {'value': {'RawData': {'value': {
                'hp': {'current': 1, 'max': 10},
            }}}},
        }]}},
        'ItemContainerSaveData': {'value': [{
            'value': {'Slots': {'value': {'values': [{
                'RawData': {'value': {'item': {
                    'static_id': 'TestWeapon', 'dynamic_id': {},
                }}},
            }]}}},
        }]},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(dynamic_items, 'get_item_type', lambda _: 'weapon')

    assert func_manager.repair_structures(preview_only=True)['repaired'] == 1
    assert func_manager.repair_items(preview_only=True)['repaired'] == 1
    assert world == before


def test_invalid_structure_preview_does_not_delete_map_object(monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'MapObjectSaveData': {'value': {'values': [
            {'MapObjectId': {'value': 'UnknownStructure'}},
        ]}},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'get_base_path', lambda: tmp_path)
    monkeypatch.setattr(func_manager, 'resource_path', lambda *a: tmp_path)
    monkeypatch.setattr(func_manager.json_tools, 'load',
                        lambda _: {'structures': []})
    monkeypatch.setattr(func_manager, 'is_entity_in_exclusion_zones',
                        lambda _entity: False)
    monkeypatch.setattr(func_manager, 'is_death_bag', lambda _entity: False)

    assert func_manager.delete_invalid_structure_map_objects(
        preview_only=True) == 1
    assert world == before


def test_timestamp_preview_and_noop_result_reflect_real_changes(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    uid = '11111111-1111-1111-1111-111111111111'
    raw = {'last_online_real_time': 200}
    world = {'properties': {'worldSaveData': {'value': {
        'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 100}}},
        'CharacterSaveParameterMap': {'value': [{
            'key': {'PlayerUId': {'value': uid}},
            'value': {'RawData': {'value': raw}},
        }]},
        'GroupSaveDataMap': {'value': []},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)

    assert func_manager.fix_all_negative_timestamps(preview_only=True) == 1
    assert world == before
    assert func_manager.reset_selected_player_timestamp(
        uid, result_details=True) == {'changed': 1}
    assert func_manager.reset_selected_player_timestamp(
        uid, result_details=True) == {'changed': 0}


def test_invalid_passive_preview_keeps_level_and_files_unchanged(
        monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'ABC.sav').write_bytes(b'placeholder')
    (players / 'ABC_dps.sav').write_bytes(b'placeholder')
    world = {'properties': {'worldSaveData': {'value': {
        'CharacterSaveParameterMap': {'value': [{
            'value': {'RawData': {'value': {'object': {'SaveParameter': {
                'value': {'PassiveSkillList': {'value': {'values': ['BadSkill']}}}
            }}}}},
        }]},
    }}}}
    player = SimpleNamespace(properties={'PassiveSkills': {
        'value': [{'value': 'BadSkill'}]}})
    dps = SimpleNamespace(properties={'SaveParameterArray': {'value': {'values': [
        {'SaveParameter': {'value': {'PassiveSkillList': {
            'value': {'values': ['BadSkill']}}}}},
    ]}}})
    before = deepcopy((world, player.properties, dps.properties))
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager.constants, 'get_base_path', lambda: tmp_path)
    monkeypatch.setattr(func_manager, 'resource_path', lambda *a: tmp_path)
    monkeypatch.setattr(func_manager.json_tools, 'load', lambda _: {'passives': []})
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile',
                        lambda path: dps if '_dps' in str(path) else player)
    monkeypatch.setattr(func_manager, 'gvasfile_to_sav',
                        lambda *a: (_ for _ in ()).throw(AssertionError('wrote file')))

    assert func_manager.remove_invalid_passives_from_save(
        preview_only=True) == {
            'level_removed': 1, 'player_removed': 1, 'dps_removed': 1}
    assert (world, player.properties, dps.properties) == before


def test_invalid_active_skill_preview_does_not_edit_pal_or_write_log(monkeypatch):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'CharacterSaveParameterMap': {'value': [{
            'key': {'InstanceId': {'value': 'instance'}},
            'value': {'RawData': {'value': {'object': {'SaveParameter': {
                'value': {'CharacterID': {'value': 'TestPal'},
                          'EquipWaza': {'value': {'values': ['InvalidSkill']}}}
            }}}}},
        }]},
    }}}}
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'get_base_path', lambda: '')
    monkeypatch.setattr(func_manager, 'resource_path', lambda *a: '')
    monkeypatch.setattr(func_manager.json_tools, 'load', lambda _: {})
    monkeypatch.setattr(func_manager, 'load_game_data_map', lambda *a: {})
    monkeypatch.setattr(func_manager, '_build_skill_name_map', lambda: {})
    monkeypatch.setattr(func_manager, '_is_skill_invalid_for_pal',
                        lambda *a: True)

    assert func_manager.fix_invalid_pal_active_skills(
        preview_only=True)['removed'] == 1
    assert world == before


def test_fix_all_pals_reports_pending_level_and_direct_dps_separately(monkeypatch):
    func_manager = import_from('palworld_aio.managers.func_manager')
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', {
        'properties': {'worldSaveData': {'value': {}}}})
    monkeypatch.setattr(func_manager.constants, 'current_save_path', 'fixture')
    monkeypatch.setattr(func_manager, '_fix_all_pals_core',
                        lambda _wsd, _path, *, include_dps: 2
                        if not include_dps else 99)
    monkeypatch.setattr(func_manager, '_apply_to_dps_files',
                        lambda _transform, _path: 3)

    assert func_manager.fix_all_pals_combined(
        result_details=True) == {'level_fixed': 2, 'dps_fixed': 3}


def test_container_trim_preview_does_not_resize_or_touch_registry(
        monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    players = tmp_path / 'Players'
    players.mkdir()
    (players / 'ABC.sav').write_bytes(b'placeholder')
    world = {'properties': {'worldSaveData': {'value': {
        'ItemContainerSaveData': {'value': [{
            'key': {'ID': {'value': 'main'}},
            'value': {'Slots': {'value': {'values': []}},
                      'SlotNum': {'value': 1}},
        }]},
        'CharacterContainerSaveData': {'value': [{
            'value': {'Slots': {'value': {'values': [1, 2]}},
                      'SlotNum': {'value': 1}},
        }]},
    }}}}
    gvas = SimpleNamespace(properties={'SaveData': {'value': {
        'InventoryInfo': {'value': {
            'CommonContainerId': {'value': {'ID': {'value': 'main'}}},
            'EssentialContainerId': {'value': {'ID': {'value': 'key'}}},
        }},
    }}})
    before = deepcopy(world)
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager, 'sav_to_gvasfile', lambda _: gvas)

    assert func_manager.detect_and_trim_overfilled_inventories(
        preview_only=True) == 2
    assert world == before


def test_guild_item_removal_preview_does_not_change_container(monkeypatch):
    from copy import deepcopy
    manager = import_from('palworld_aio.inventory.base_inventory_manager')
    container = {'value': {'Slots': {'value': {'values': [{
        'RawData': {'type': 'ArrayProperty', 'value': {
            'item': {'static_id': 'TestItem'}, 'count': 5,
        }},
    }]}}}}
    world = {'properties': {'worldSaveData': {'value': {
        'MapObjectSaveData': {'value': {'values': []}},
    }}}}
    before = deepcopy((container, world))
    monkeypatch.setattr(manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(manager.constants, 'get_container_lookup',
                        lambda: {'container': container})
    monkeypatch.setattr(manager, 'find_item_locations_efficient',
                        lambda _item: {'guild': {'base': ['container']}})

    assert manager.remove_item_from_guilds(
        'TestItem', 50, ['guild'], preview_only=True) == {
            'removed': 5, 'containers_affected': 1}
    assert (container, world) == before


def test_guild_item_bulk_cancel_never_runs_removal(monkeypatch):
    manager = import_from('palworld_aio.inventory.base_inventory_manager')
    prompts = []
    monkeypatch.setattr(manager, 'remove_item_from_guilds',
                        lambda _item, _pct, _guilds, *, preview_only=False:
                        {'removed': 5, 'containers_affected': 1}
                        if preview_only else
                        (_ for _ in ()).throw(AssertionError('mutated')))
    monkeypatch.setattr(base_inventory, 'show_question',
                        lambda _parent, _title, message:
                        prompts.append(message) or False)
    tab = SimpleNamespace(_get_item_name=lambda _item: 'Test Item')

    base_inventory.BaseInventoryTab._on_item_action_selected(
        tab, 'TestItem', 'remove_pct:50', ['guild'])

    assert '5' in prompts[0]


def test_structure_removal_count_matches_selected_guild(monkeypatch):
    manager = import_from('palworld_aio.inventory.base_inventory_manager')
    world = {'properties': {'worldSaveData': {'value': {
        'MapObjectSaveData': {'value': {'values': [
            {'MapObjectId': {'value': 'TestStructure'},
             'Model': {'value': {
                 'BuildProcess': {'value': {'RawData': {'value': {'state': 1}}}},
                 'RawData': {'value': {'base_camp_id_belong_to': 'base'}},
             }}},
        ]}},
    }}}}
    monkeypatch.setattr(manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(manager.constants, 'base_guild_lookup', {
        'base': {'GuildID': 'guild'}})

    assert manager.count_structures_for_removal(
        'TestStructure', ['guild']) == 1
    assert manager.count_structures_for_removal(
        'TestStructure', ['other']) == 0


def test_viewing_cage_cancel_does_not_write_player_file(monkeypatch):
    prompts = []
    monkeypatch.setattr(main_window, 'show_question',
                        lambda _parent, _title, message:
                        prompts.append(message) or False)
    monkeypatch.setattr(main_window, 'unlock_viewing_cage_for_player',
                        lambda *a: (_ for _ in ()).throw(AssertionError('wrote')))

    main_window.MainWindow._unlock_viewing_cage(SimpleNamespace(), 'player')

    assert '1' in prompts[0]


def test_base_clone_journals_only_success(monkeypatch):
    calls = []
    window = SimpleNamespace(
        _run_transfer_workflow=lambda **kwargs: kwargs,
        record_pending_change=lambda *a, **k: calls.append(('journal', a, k)),
        refresh_all=lambda: calls.append(('refresh',)),
    )

    workflow = main_window.MainWindow._clone_base(window, 'base', 'guild')
    workflow['on_completed'](False)
    assert calls == []

    workflow['on_completed'](True)
    assert ('journal', ('Clone base',), {
        'context': 'base', 'affected_count': 1, 'high_risk': True}) in calls
    assert ('refresh',) in calls


def test_duplicate_player_preview_does_not_mutate_world_or_deletion_queue(
        monkeypatch, tmp_path):
    from copy import deepcopy
    func_manager = import_from('palworld_aio.managers.func_manager')
    uid = '11111111-1111-1111-1111-111111111111'
    player = {'player_uid': uid, 'player_info': {
        'player_name': 'Player', 'last_online_real_time': 1}}
    guild = {'key': 'guild', 'value': {
        'GroupType': {'value': {'value': 'EPalGroupType::Guild'}},
        'RawData': {'value': {'players': [deepcopy(player), deepcopy(player)],
                              'admin_player_uid': uid}}}}
    world = {'properties': {'worldSaveData': {'value': {
        'GameTimeSaveData': {'value': {'RealDateTimeTicks': {'value': 100}}},
        'GroupSaveDataMap': {'value': [guild]},
        'CharacterSaveParameterMap': {'value': []},
    }}}}
    before = deepcopy(world)
    queue = {'existing'}
    monkeypatch.setattr(func_manager.constants, 'loaded_level_json', world)
    monkeypatch.setattr(func_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(func_manager.constants, 'files_to_delete', queue)
    monkeypatch.setattr(func_manager, 'delete_player_pals', lambda *a: 0)
    monkeypatch.setattr(func_manager, 'canonical_player_entries',
                        lambda *a: ({}, {}))

    assert func_manager.delete_duplicated_players(preview_only=True) == 1
    assert world == before
    assert queue == {'existing'}


def test_bulk_ability_result_separates_written_player_from_pending_level(
        monkeypatch, tmp_path):
    player_manager = import_from('palworld_aio.managers.player_manager')
    players_dir = tmp_path / 'Players'
    players_dir.mkdir()
    (players_dir / 'ABC.sav').write_bytes(b'fixture')
    save_parameter = {'GotStatusPointList': {'value': {'values': [
        {'StatusName': {'value': 'Capture'},
         'StatusPoint': {'value': 3}},
    ]}}}
    gvas = SimpleNamespace(properties={'SaveData': {'value': {
        'RecordData': {'value': {}}}}})
    written = []
    monkeypatch.setattr(player_manager.constants, 'loaded_level_json',
                        {'properties': {'worldSaveData': {'value': {}}}})
    monkeypatch.setattr(player_manager.constants, 'current_save_path', str(tmp_path))
    monkeypatch.setattr(player_manager.constants, 'player_character_cache', {
        'abc': {'value': {'RawData': {'value': {'object': {
            'SaveParameter': {'value': save_parameter}}}}}}})
    monkeypatch.setattr(player_manager, 'RELIC_TO_STATUS_NAME',
                        {'Relic': 'Capture'})
    monkeypatch.setattr(player_manager, 'RELIC_MAX_RANK', {'Relic': 3})
    monkeypatch.setattr(player_manager, 'RELIC_CUMULATIVE_MAX', {'Relic': 3})
    utils = import_from('palworld_aio.utils')
    monkeypatch.setattr(utils, 'sav_to_gvasfile', lambda _path: gvas)
    monkeypatch.setattr(utils, 'gvasfile_to_sav',
                        lambda _gvas, path: written.append(path))

    assert player_manager.max_all_abilities(
        ['ABC'], result_details=True) == {
            'player_files': 1, 'level_players': 0}
    assert len(written) == 1

    assert player_manager.set_ability_values(
        ['ABC'], {'Relic': 2}, result_details=True) == {
            'player_files': 1, 'level_players': 1}


def test_guild_rebuild_review_counts_records_and_noop_has_no_pending_result(
        monkeypatch):
    world = {'properties': {'worldSaveData': {'value': {
        'GroupSaveDataMap': {'value': [{
            'value': {'GroupType': {'value': {
                'value': 'EPalGroupType::Guild'}}}}]},
        'CharacterSaveParameterMap': {'value': [{
            'value': {'RawData': {'value': {'object': {
                'SaveParameter': {'value': {'IsPlayer': {'value': False}}}
            }}}}}]},
    }}}}
    monkeypatch.setattr(main_window.constants, 'loaded_level_json', world)
    monkeypatch.setattr(main_window, 'rebuild_all_guilds', lambda: True)
    window = SimpleNamespace(_run_loaded_save_repair=lambda **kwargs: kwargs)

    workflow = main_window.MainWindow._rebuild_all_guilds(window)

    assert workflow['affected_count'] == 2
    assert workflow['operation']() == {'count': 0}
