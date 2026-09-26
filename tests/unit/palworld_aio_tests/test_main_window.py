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
assert context.snapshot.pending_changes.count == 2
assert len(journal.changes) == 2
context.begin_save()
MainWindow._on_save_failed(window, 'disk error')
assert context.snapshot.save_state is ShellState.ERROR
assert context.snapshot.pending_changes.count == 2
assert len(journal.changes) == 2
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
    'Editable', 'Undo last change']
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
    assert 'fix_illegal_pals_in_save(self, selected_uids=selected_uids)' in illegal_pal_source
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
