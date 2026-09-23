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
