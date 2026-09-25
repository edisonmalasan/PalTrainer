import os
from palsav import json_tools
import webbrowser
import urllib.request
import re
import io
import sys
import collections
import threading
from functools import partial
import logging
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMenuBar, QMenu, QStatusBar, QSplitter, QFileDialog, QDialog, QComboBox, QApplication, QStackedWidget, QTextEdit, QLineEdit
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint, QPropertyAnimation, QEasingCurve, QByteArray, QThread

from PyQt6.QtGui import QIcon, QFont, QAction, QPixmap, QCloseEvent, QTextCursor, QCursor
from i18n import t, set_language, load_resources, get_native_lang_name
from common import get_versions, get_current_version, get_display_version, is_standalone
from import_libs import run_with_loading
from loading_manager import show_question
from .tabs.tools_tab import center_on_parent, DropOverlay
GITHUB_LATEST_ZIP = 'https://github.com/edisonmalasan/PalTrainer/releases/latest'
from palworld_aio import constants
from palworld_aio.shell_state import ShellStateModel
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from palworld_aio.utils import as_uuid
from palworld_aio.managers.save_manager import save_manager
from palworld_aio.managers.data_manager import get_guilds, get_guild_members, get_bases, delete_guild, delete_player, load_exclusions, save_exclusions, delete_base_camp
from palworld_aio.managers.func_manager import delete_empty_guilds, delete_inactive_players, delete_inactive_bases, delete_duplicated_players, delete_imported_pals, delete_unreferenced_data, delete_non_base_map_objects, delete_invalid_structure_map_objects, delete_all_skins, unlock_all_private_chests, remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, fix_missions, reset_anti_air_turrets, reset_dungeons, reset_oilrig, reset_invader, reset_supply, reset_lock_gimmick, unlock_viewing_cage_for_player, fix_all_negative_timestamps, reset_selected_player_timestamp, detect_and_trim_overfilled_inventories, unlock_all_technologies_for_player, unlock_all_lab_research_for_guild, modify_container_slots, modify_all_player_slots, modify_all_guild_chest_slots, fix_unassigned_pals, restore_all_pals, fix_all_pals_combined, max_all_pals, fix_illegal_pals_in_save, fix_illegal_player_stats, repair_structures, repair_items, edit_game_days, scan_illegal_pals_by_owner, scan_illegal_players_by_stats, fix_invalid_pal_active_skills
from palworld_aio.managers.guild_manager import move_player_to_guild, rebuild_all_guilds, make_member_leader, rename_guild, set_guild_level
from palworld_aio.managers.base_manager import export_base_json, import_base_json, clone_base_complete, update_base_area_range, get_last_import_audit
from palworld_aio.managers.backup_manager import export_base_backup, load_base_file, compress_to_pst3
from palworld_aio.managers.player_manager import rename_player
from palworld_aio.map.map_generator import generate_world_map
from palworld_aio.editor.dialogs import InputDialog, DaysInputDialog, LevelInputDialog, RadiusInputDialog, PalDefenderDialog, GameDaysInputDialog, InactiveFilterDialog
from palworld_aio.widgets import SearchPanel, StatsPanel, ScrollableContextMenu
from palworld_aio.widgets.empty_state import EmptyState
from resource_resolver import resource_path
from palworld_aio.ui.dialogs.player_item_dialog import PlayerItemActionDialog
from palworld_aio.ui.dialogs.player_pal_dialog import PlayerPalActionDialog
from palworld_aio.ui.dialogs.player_technology_dialog import PlayerTechnologyActionDialog
from palworld_aio.ui.dialogs.guild_assign_dialog import GuildAssignDialog
from palworld_aio.ui.dialogs.repair_workflow_dialog import (
    RepairWorkflowDialog,
    loaded_save_repair_spec,
    require_repair_success,
)
from palworld_aio.ui.dialogs.transfer_workflow_dialog import (
    TransferWorkflowDialog,
    TransferWorkflowSpec,
)
from palworld_aio.ui.chrome.components import (
    BaseDialog,
    InputPromptDialog as QInputDialog,
    MessageDialog as QMessageBox,
)
def _short_guid(value):
    """modernize-tab-ui 5.2: first 8 chars + ellipsis for GUID display text."""
    s = str(value or '')
    return s[:8] + '…' if len(s) > 12 else s
def _item_value(item, col):
    """modernize-tab-ui 5.2: full column value (GUID role) with text fallback."""
    value = item.data(col, SearchPanel.GUID_ROLE)
    return value if value not in (None, '') else item.text(col)
# uiux-audit-remediation 5.1: role used by _populate_players_inspector to
# read the full Guild ID from the players table (search_panel.GUID_ROLE).
from palworld_aio.widgets.search_panel import GUID_ROLE as _PLAYER_GUILD_ID_ROLE
class DetachedStatusWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self._main_window = parent
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(600, 400)
        self._drag_pos = QPoint()
        self.is_dark = True
        self._load_theme()
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName('mainContainer')
        self.main_layout.addWidget(self.container)
        self.inner = QVBoxLayout(self.container)
        self.inner.setContentsMargins(10, 5, 10, 10)
        self.setup_status_ui()
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_animation = QPropertyAnimation(self, b'windowOpacity')
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if sys.platform == 'linux':
                self.windowHandle().startSystemMove()
            else:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if sys.platform != 'linux' and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def save_geometry(self):
        geo = self.saveGeometry()
        return bytes(geo.toBase64()).decode()
    def load_geometry(self, geo_str):
        if geo_str:
            geo = QByteArray.fromBase64(bytes(geo_str, 'utf-8'))
            self.restoreGeometry(geo)
    def _load_theme(self):
        ThemeManager.apply_to_widget(self)
    def setup_status_ui(self):
        head = QHBoxLayout()
        self.title_label = QLabel(t('console.title'))
        self.title_label.setObjectName('consoleTitleLabel')
        head.addWidget(self.title_label)
        head.addStretch()
        self.close_btn = QPushButton('✕')
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setObjectName('consoleCloseBtn')
        head.addWidget(self.close_btn)
        self.inner.addLayout(head)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setObjectName('consoleTextEdit')
        self.inner.addWidget(self.text_edit)
    def update_theme(self, is_dark):
        self.is_dark = is_dark
        self._load_theme()
    def refresh_title(self):
        self.title_label.setText(t('console.title'))
    def append_message(self, text):
        self.text_edit.append(text)
        document = self.text_edit.document()
        if document.blockCount() > 500:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, document.blockCount() - 500)
            cursor.removeSelectedText()
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
    def closeEvent(self, event):
        if self._main_window and hasattr(self._main_window, 'user_settings'):
            try:
                self._main_window.user_settings['console_window_geometry'] = self.save_geometry()
                if hasattr(self._main_window, '_save_user_settings'):
                    self._main_window._save_user_settings()
            except (RuntimeError, AttributeError):
                pass
        if self._main_window and hasattr(self._main_window, 'status_stream'):
            try:
                self._main_window.status_stream.detach_window = None
                self._main_window.status_stream.detached = False
                self._main_window.status_stream.detach_state_changed.emit(False)
            except (RuntimeError, AttributeError):
                pass
        event.accept()
class StatusBarStream(QObject):
    text_written = pyqtSignal(str)
    detach_state_changed = pyqtSignal(bool)
    def __init__(self, status_bar, parent=None):
        QObject.__init__(self)
        self.status_bar = status_bar
        self._main_window = parent
        self.stringio = io.StringIO()
        self._stream_lock = threading.Lock()
        self.detached = False
        self.detach_window = None
        self.text_written.connect(self._handle_text)
        self._pending = collections.deque()
        self._pending_lock = threading.Lock()
        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(100)
        self._drain_timer.timeout.connect(self._drain_pending)
        self._drain_timer.start()
    def _handle_text(self, text):
        if self.detached and self.detach_window:
            self.detach_window.append_message(text)
        else:
            presented = _present_status(text)
            if presented is _STATUS_SHOW_RAW:
                self.status_bar.showMessage(text)
            elif presented is _STATUS_DEMOTE:
                # demoted to the log/console; keep the last human message,
                # or leave the neutral ready message instead of stale text
                if not self.status_bar.currentMessage():
                    self.status_bar.showMessage(t('status.ready') if t else 'Ready')
            else:
                key, fallback = presented  # type: ignore[misc]
                self.status_bar.showMessage(t(key) if t else fallback)
    def write(self, text):
        with self._stream_lock:
            self.stringio.write(text)
        if text.strip():
            # Never touch Qt from a producer thread: queue and let the GUI
            # thread drain. Cross-thread widget writes here were a source of
            # heap corruption under concurrent worker logging.
            with self._pending_lock:
                self._pending.append(text.strip())
    def _drain_pending(self):
        if not self._pending:
            return
        with self._pending_lock:
            batch = list(self._pending)
            self._pending.clear()
        for text in batch:
            self.text_written.emit(text)
    def flush(self):
        pass
    def detach(self):
        if not self.detached:
            self.detached = True
            self.detach_window = DetachedStatusWindow(self._main_window)
            self.detach_window.setWindowOpacity(0.0)
            saved_geo = self._main_window.user_settings.get('console_window_geometry') if self._main_window and hasattr(self._main_window, 'user_settings') else None
            if saved_geo:
                self.detach_window.load_geometry(saved_geo)
            self.detach_window.show()
            self.detach_window.activateWindow()
            self.detach_window.raise_()
            self.detach_window.fade_animation = QPropertyAnimation(self.detach_window, b'windowOpacity')
            self.detach_window.fade_animation.setDuration(300)
            self.detach_window.fade_animation.setStartValue(0.0)
            self.detach_window.fade_animation.setEndValue(1.0)
            self.detach_window.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.detach_window.fade_animation.start()
            self.detach_state_changed.emit(True)
    def attach(self):
        if self.detached and self.detach_window:
            self.detached = False
            self.detach_state_changed.emit(False)
            self.detach_window.close()
            self.detach_window = None
    def __getattr__(self, name):
        return getattr(self.stringio, name)
class UpdateChecker(QThread):
    update_checked = pyqtSignal(bool, object, object)
    def __init__(self, force_test=False, branch=None):
        super().__init__()
        self.force_test = force_test
        self.branch = branch or 'stable'
    def run(self):
        try:
            import ssl, json
            context = ssl.create_default_context()
            req = urllib.request.Request(
                'https://api.github.com/repos/edisonmalasan/PalTrainer/releases/latest',
                headers={
                    'User-Agent': 'PalTrainer/2.0',
                    'Accept': 'application/vnd.github.v3+json',
                },
            )
            with urllib.request.urlopen(req, timeout=10, context=context) as r:
                data = json.loads(r.read().decode('utf-8'))
            tag = data.get('tag_name', '') or ''
            latest = tag.lstrip('v') or None
            local, _ = get_versions()
            available = False
            if latest:
                local_tuple = tuple((int(x) for x in local.split('.')))
                latest_tuple = tuple((int(x) for x in latest.split('.')))
                available = latest_tuple > local_tuple
            if self.force_test:
                available = True
            self.update_checked.emit(not available, latest, self.branch)
        except Exception as e:
            print(f'Update check error: {e}')
            self.update_checked.emit(False, None, None)
# Status strip presentation policy (uiux-audit-remediation 2.1 / design D3):
# the strip shows one short human-readable message; raw technical payloads
# are demoted to the log/console stream (StatusBarStream still routes every
# payload verbatim when detached). Patterns match the producers:
# - decompression stats: palsav compressor logger lines
# - update-check failures: UpdateChecker.print in run(); they surface through
#   the app-bar warning affordance (2.2) instead of strip text
# - exception text / HTTP status codes: traceback blocks and HTTPError reprs
_STATUS_SHOW_RAW = object()
_STATUS_DEMOTE = object()
_STATUS_SUMMARIZERS = (
    (re.compile(r'Decompression successful', re.IGNORECASE), ('status.ready', 'Ready')),
    (re.compile(r'^(?:Save )?load(?:ed| complete| successful)\b|Level\.sav loaded', re.IGNORECASE), ('status.loaded', 'Save loaded successfully')),
    (re.compile(r'^Save (?:completed|saved)', re.IGNORECASE), ('status.saved', 'Save completed')),
    (re.compile(r'load (?:failed|error)|failed to load', re.IGNORECASE), ('status.load_failed', 'Failed to load save')),
    (re.compile(r'^Update check (?:error|callback error):'), _STATUS_DEMOTE),
    (re.compile(r'^Traceback \(most recent call last\):'), _STATUS_DEMOTE),
    (re.compile(r'^File "'), _STATUS_DEMOTE),
    (re.compile(r'HTTP Error \d{3}'), _STATUS_DEMOTE),
)
def _present_status(text):
    """Map a streamed payload to its strip presentation (design D3).

    Returns _STATUS_DEMOTE (log/console only), (key, fallback) for a human
    summary, or _STATUS_SHOW_RAW to display the payload unchanged."""
    stripped = (text or '').strip()
    if not stripped:
        return _STATUS_SHOW_RAW
    for pattern, presentation in _STATUS_SUMMARIZERS:
        if pattern.search(stripped):
            return presentation
    return _STATUS_SHOW_RAW
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = True
        self._is_refreshing = False
        self.shell_state = ShellStateModel()
        self.user_settings = {}
        self.lang_map = {'English': 'en_US', '中文': 'zh_CN', 'Русский': 'ru_RU', 'Français': 'fr_FR', 'Español': 'es_ES', 'Deutsch': 'de_DE', '日本語': 'ja_JP', '한국어': 'ko_KR', 'Português (Brasil)': 'pt_BR', 'Português (Portugal)': 'pt_PT'}
        load_exclusions()
        self._load_user_settings()
        self._setup_ui()
        self._refresh_exclusions()
        self._load_theme()
        initial_route = self.__dict__.get('workspace_settings')
        self._activate_nav(initial_route.current_route if initial_route else 'tools')
        self._setup_menus()
        self._setup_connections()
        QTimer.singleShot(0, self._check_update)
        self.status_stream = StatusBarStream(self.status_bar, self)
        self.status_stream.detach_state_changed.connect(self._on_detach_state_changed)
        self.status_stream.text_written.connect(
            self.diagnostics_page.append_console_message)
        self._sync_diagnostics_console()
        sys.stdout = self.status_stream
        sys.stderr = self.status_stream
        from palsav import setup_logging
        class _StatusBarLogHandler(logging.StreamHandler):
            def __init__(self, stream):
                super().__init__(stream)
            def emit(self, record):
                try:
                    self.stream.write(self.format(record) + '\n')
                except Exception:
                    self.handleError(record)
        handler = _StatusBarLogHandler(self.status_stream)
        handler.setLevel(logging.INFO)
        handler.raiseExceptions = False
        handler.setFormatter(logging.Formatter('{message}', style='{'))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        setup_logging()
        for h in list(root_logger.handlers):
            if h is handler:
                continue
            if isinstance(h, logging.StreamHandler) and (h.stream is None or h.stream is sys.stderr):
                root_logger.removeHandler(h)
                h.close()
        logging.lastResort = None
        if self.user_settings.get('console_detached', False):
            self.status_stream.detach()
            self._set_console_action_state(True)
    def _setup_ui(self):
        self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
        self.setMinimumSize(1024, 700)
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1450, screen.width() - 40)
        h = min(800, screen.height() - 40)
        self.resize(w, h)
        self.setWindowFlags(Qt.FramelessWindowHint)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        central_widget = QWidget()
        central_widget.setObjectName('central')
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._setup_workspace_shell(main_layout)
        # Status strip (top-nav-shell 1.5): visible host for streamed
        # load/save/log messages; detachable console behavior unchanged.
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName('statusStrip')
        self.status_bar.setFixedHeight(24)
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.setAcceptDrops(True)
        self._drop_overlay = DropOverlay(self)
        self._drop_overlay.setVisible(False)
        self._drop_overlay.setGeometry(self.rect())

    def _setup_workspace_shell(self, main_layout):
        from .chrome.stats_drawer import StatsDrawer
        from .chrome.tokens import LAYOUT
        from .chrome.workspace_shell import WorkspaceShell
        from palworld_aio.ui.operation_journal import OperationJournal
        from palworld_aio.ui.pending_changes import PendingChangeJournal
        from palworld_aio.ui.pages.activity_page import ActivityPage
        from palworld_aio.ui.pages.about_page import AboutPage
        from palworld_aio.ui.pages.backups_page import BackupsPage
        from palworld_aio.ui.pages.diagnostics_page import DiagnosticsPage
        from palworld_aio.ui.pages.overview_page import OverviewPage
        from palworld_aio.ui.pages.settings_page import SettingsPage
        from palworld_aio.ui.pages.tool_center_page import ToolCenterPage
        from palworld_aio.ui.workspace_context import WorkspaceContext
        from palworld_aio.ui.workspace_settings import WorkspaceSettings
        self._workspace_shell_live = True
        self.workspace_settings = WorkspaceSettings.from_mapping(
            self.user_settings.get('workspace_ui'))
        self.workspace_context = WorkspaceContext()
        self.operation_journal = OperationJournal(parent=self)
        self.pending_journal = PendingChangeJournal(parent=self)
        self.pending_journal.changed.connect(
            self.workspace_context.set_pending_changes)
        self.workspace_shell = WorkspaceShell(self.workspace_context)
        self.workspace_shell.minimizeRequested.connect(self.showMinimized)
        self.workspace_shell.maximizeRequested.connect(self._toggle_maximize)
        self.workspace_shell.closeRequested.connect(self.close)
        self.workspace_shell.routeChanged.connect(self._show_legacy_route)
        main_layout.addWidget(self.workspace_shell, stretch=1)

        header = self.workspace_shell.header
        header.pending_changes.clicked.connect(self._show_pending_changes)
        self._shell_save_button = header.add_action(
            'save', t('menu.file.save_changes') if t else 'Save Changes',
            self._save_changes, primary=True, icon='save')
        self._shell_menu_button = header.add_action(
            'menu', t('Menu') if t else 'Menu', self._show_menu_popup_v2,
            icon='menu')
        self._shell_search_button = header.add_action(
            'global_search', t('ui.search.global_title') if t else 'Search everything',
            self._show_global_search, icon='search')
        self._shell_stats_button = header.add_action(
            'statistics', t('deletion.stats_panel') if t else 'Statistics',
            lambda: self._set_tray_drawer_visible(True), icon='grid')
        self._shell_console_button = header.add_action(
            'console', t('console.detach') if t else 'Console',
            self._detach_status, icon='console')
        self._shell_guide_button = header.add_action(
            'guide', t('tab_guide.tooltip') if t else 'Tab Usage Guide',
            self._show_tab_guide, icon='toolbox')
        self._shell_warning_button = header.add_action(
            'warnings', t('warning.title') if t else 'Warnings',
            self._show_warnings, icon='warning')
        self._shell_about_button = header.add_action(
            'about', t('about.title') if t else 'About PalTrainer',
            self._show_about, icon='info')

        self.stacked_widget = QStackedWidget()
        self._build_pages()
        for route_id in self._LEGACY_PAGE_INDEX:
            self.workspace_shell.register_page(route_id, self.stacked_widget)
        self._ensure_tab(4)
        players_index = self.stacked_widget.indexOf(self.players_page)
        self.stacked_widget.removeWidget(self.players_page)
        self._players_legacy_placeholder = QWidget()
        self.stacked_widget.insertWidget(
            players_index, self._players_legacy_placeholder)
        self.workspace_shell.register_page('players', self.players_page)
        self._ensure_tab(5)
        guilds_index = self.stacked_widget.indexOf(self.guilds_page)
        self.stacked_widget.removeWidget(self.guilds_page)
        self._guilds_legacy_placeholder = QWidget()
        self.stacked_widget.insertWidget(
            guilds_index, self._guilds_legacy_placeholder)
        self.workspace_shell.register_page('guilds', self.guilds_page)
        self._ensure_tab(6)
        bases_index = self.stacked_widget.indexOf(self.bases_page)
        self.stacked_widget.removeWidget(self.bases_page)
        self._bases_legacy_placeholder = QWidget()
        self.stacked_widget.insertWidget(
            bases_index, self._bases_legacy_placeholder)
        self.workspace_shell.register_page('bases', self.bases_page)
        self._ensure_tab(7)
        map_index = self.stacked_widget.indexOf(self.map_tab)
        self.stacked_widget.removeWidget(self.map_tab)
        self._map_legacy_placeholder = QWidget()
        self.stacked_widget.insertWidget(
            map_index, self._map_legacy_placeholder)
        self.workspace_shell.register_page('map', self.map_tab)
        self._ensure_tab(8)
        exclusions_index = self.stacked_widget.indexOf(self.exclusions_page)
        self.stacked_widget.removeWidget(self.exclusions_page)
        self._exclusions_legacy_placeholder = QWidget()
        self.stacked_widget.insertWidget(
            exclusions_index, self._exclusions_legacy_placeholder)
        self.workspace_shell.register_page('exclusions', self.exclusions_page)
        self.overview_page = OverviewPage()
        self.overview_page.navigateRequested.connect(self._activate_nav)
        self.overview_page.openSaveRequested.connect(self._load_save)
        self.overview_page.openFolderRequested.connect(self._load_save_folder)
        self.overview_page.recentSaveRequested.connect(self._load_recent_save)
        self.overview_page.locateRecentRequested.connect(self._locate_recent_save)
        self.overview_page.removeRecentRequested.connect(self._remove_recent_save)
        self.overview_page.utilityRequested.connect(self._launch_overview_utility)
        self.workspace_shell.register_page('overview', self.overview_page)
        self.activity_page = ActivityPage(self.operation_journal)
        self.workspace_shell.register_page('activity', self.activity_page)
        self.backups_page = BackupsPage()
        self.backups_page.refreshRequested.connect(self._refresh_backups)
        self.backups_page.revealRequested.connect(self._reveal_backup_folder)
        self.backups_page.restoreRequested.connect(self._restore_backup_record)
        self.workspace_shell.register_page('backups', self.backups_page)
        self.tool_center_page = ToolCenterPage(self.workspace_context)
        self.tool_center_page.launchRequested.connect(self._launch_registered_tool)
        self.tool_center_page.prerequisiteRequested.connect(
            self._resolve_tool_prerequisite)
        self.workspace_shell.register_page('tools', self.tool_center_page)
        self.settings_page = SettingsPage(self.user_settings)
        self.settings_page.preferencesChanged.connect(self._apply_preferences)
        self.workspace_shell.register_page('settings', self.settings_page)
        self.about_page = AboutPage()
        self.about_page.projectRequested.connect(webbrowser.open)
        self.about_page.updateCheckRequested.connect(self._check_update)
        self.about_page.diagnosticsRequested.connect(
            lambda: self._activate_nav('diagnostics'))
        self.workspace_shell.register_page('about', self.about_page)
        self.diagnostics_page = DiagnosticsPage()
        self.diagnostics_page.copyRequested.connect(
            self._copy_diagnostics_report)
        self.diagnostics_page.exportRequested.connect(
            self._export_diagnostics_report)
        self.diagnostics_page.revealPathRequested.connect(
            self._reveal_system_path)
        self.diagnostics_page.detachConsoleRequested.connect(self._detach_status)
        self.diagnostics_page.updateCheckRequested.connect(self._check_update)
        self.workspace_shell.register_page('diagnostics', self.diagnostics_page)
        self._unsubscribe_overview_context = self.workspace_context.subscribe(
            self._sync_overview_context)
        self._show_no_save_overview()
        self.workspace_shell.sidebar.restore_settings({
            'collapsed': self.workspace_settings.sidebar_collapsed,
            'expanded_width': self.workspace_settings.sidebar_width,
        })
        self.workspace_shell.restore_splitter_sizes(
            self.workspace_settings.splitter_sizes)
        self.workspace_shell.router.restore_persistent_state(
            current_route=self.workspace_settings.current_route,
            last_routes=self.workspace_settings.last_routes,
            page_view_state=self.workspace_settings.page_view_state,
        )

        self._tray_drawer = StatsDrawer()
        self._tray_drawer.setFixedWidth(LAYOUT['inspector_width'])
        self._tray_drawer.close_requested.connect(self._close_tray_drawer)
        self.workspace_shell.set_inspector(
            self._tray_drawer, title=t('deletion.stats_panel') if t else 'Statistics')
        self.workspace_shell.inspector_side.hide()
        self._window_controls = self.workspace_shell.title_bar.window_controls
        constants.header_loading_widget = self.workspace_shell.header.save_context

    def _show_menu_popup_v2(self):
        from palworld_aio.widgets import MenuPopup
        if getattr(self, '_menu_popup_v2', None) is None:
            self._menu_popup_v2 = MenuPopup(self)
            if getattr(self, '_menu_actions_dict', None):
                self._menu_popup_v2.set_menu_actions(self._menu_actions_dict)
        anchor = getattr(self, '_shell_menu_button', None)
        if anchor is not None:
            gp = anchor.mapToGlobal(anchor.rect().bottomLeft())
            self._menu_popup_v2.show_at(QPoint(gp.x(), gp.y() + 4))
            return

    def _set_tray_drawer_visible(self, visible):
        if not getattr(self, '_workspace_shell_live', False):
            return
        if visible:
            self.workspace_shell.open_inspector(self._shell_stats_button)
        else:
            if self.workspace_shell.inspector_drawer.isVisible():
                self.workspace_shell.inspector_drawer.close_drawer()
            self.workspace_shell.inspector_side.hide()
        self.user_settings['tray_expanded'] = visible
        self._save_user_settings()

    def _close_tray_drawer(self):
        self._set_tray_drawer_visible(False)

    def _build_pages(self):
        self._tab_created = set()
        self._lazy_tab_map = {}
        for idx in range(12):
            placeholder = QWidget()
            self.stacked_widget.addWidget(placeholder)
            self._lazy_tab_map[idx] = placeholder
        self._ensure_tab(0)
        self._ensure_tab(2)
        self._ensure_tab(3)
        self._ensure_tab(4)
        self._ensure_tab(5)
        self._ensure_tab(6)
        self._ensure_tab(8)
        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.currentWidget().update()
        self.stacked_widget.repaint()

    _LEGACY_PAGE_INDEX = {
        'tools': 0,
        'base_inventory': 1,
        'player_inventory': 2,
        'pal_editor': 3,
        'players': 4,
        'guilds': 5,
        'bases': 6,
        'map': 7,
        'exclusions': 8,
        'json_editor': 9,
        'docs': 10,
        'breeding': 11,
    }

    _TAB_SETUP = {
        0: '_setup_tools_tab',
        1: '_setup_base_inventory_tab',
        2: '_setup_inventory_tab',
        3: '_setup_pal_editor_tab',
        4: '_setup_players_tab',
        5: '_setup_guilds_tab',
        6: '_setup_bases_tab',
        7: '_setup_map_tab',
        8: '_setup_exclusions_tab',
        9: '_setup_json_editor_tab',
        10: '_setup_docs_tab',
        11: '_setup_breeding_tab',
    }
    def _ensure_tab(self, index: int):
        method_name = self._TAB_SETUP.get(index)
        if method_name is None:
            return
        placeholder = self._lazy_tab_map.pop(index, None)
        if placeholder is not None:
            idx = self.stacked_widget.indexOf(placeholder)
            self.stacked_widget.removeWidget(placeholder)
            placeholder.setParent(None)
            placeholder.hide()
            getattr(self, method_name)()
            widget = self.stacked_widget.widget(self.stacked_widget.count() - 1)
            self.stacked_widget.removeWidget(widget)
            self.stacked_widget.insertWidget(idx, widget)
            for ribbon in widget.findChildren(QFrame, 'pageRibbon'):
                ribbon.hide()
            self._tab_created.add(index)
    def _setup_players_tab(self):
        from palworld_aio.ui.pages.players_page import PlayersPage
        self.players_page = PlayersPage()
        self.players_panel = self.players_page.browser
        self.players_panel.tree.customContextMenuRequested.connect(self._show_player_context_menu)
        self.players_page.playerSelected.connect(self._on_player_record_selected)
        self.players_page.openInventoryRequested.connect(self._edit_player_inventory)
        self.players_page.openPalEditorRequested.connect(self._open_player_pal_editor)
        self.players_page.openGuildRequested.connect(self._open_player_guild)
        self.players_page.bulkItemsRequested.connect(self._open_bulk_player_item_dialog)
        self.players_page.bulkPalsRequested.connect(self._open_bulk_player_pal_dialog)
        self.players_page.bulkTechnologyRequested.connect(
            self._open_bulk_technology_dialog)
        self.players_page.bulkGuildRequested.connect(
            self._open_guild_assign_dialog)
        self.players_page.stateActionRequested.connect(
            lambda action: self._handle_world_state_action(
                action, self._refresh_players))
        self._players_inspector_column = self.players_page.entity_browser.inspector_host
        self._players_inspector = self.players_page.inspector
        self._players_bulk_frame = self.players_page.bulk_footer
        self.bulk_item_btn = self.players_page.bulk_item_button
        self.bulk_pal_btn = self.players_page.bulk_pal_button
        self.bulk_tech_btn = self.players_page.bulk_technology_button
        self.bulk_guild_btn = self.players_page.bulk_guild_button
        self.bulk_label = self.players_page.bulk_footer.status_label
        self._players_table_cap = 420
        self.stacked_widget.addWidget(self.players_page)
    def _setup_guilds_tab(self):
        from palworld_aio.ui.pages.guilds_page import GuildsPage
        self.guilds_page = GuildsPage()
        self.guilds_panel = self.guilds_page.browser
        self.guild_members_panel = self.guilds_page.members_browser
        self.guilds_panel.tree.customContextMenuRequested.connect(self._show_guild_context_menu)
        self.guild_members_panel.tree.customContextMenuRequested.connect(self._show_guild_member_context_menu)
        self.guilds_page.guildSelected.connect(self._on_guild_record_selected)
        self.guilds_page.memberSelected.connect(self._on_guild_member_record_selected)
        self.guilds_page.openPlayersRequested.connect(self._open_guild_players)
        self.guilds_page.openBasesRequested.connect(self._open_guild_bases)
        self.guilds_page.stateActionRequested.connect(
            lambda action: self._handle_world_state_action(
                action, self._refresh_guilds))
        self._guilds_inspector_column = self.guilds_page.entity_browser.inspector_host
        self._guilds_inspector = self.guilds_page.inspector
        self._guilds_table_cap = 420
        self.stacked_widget.addWidget(self.guilds_page)
    def _setup_bases_tab(self):
        from palworld_aio.ui.pages.bases_page import BasesPage
        self.bases_page = BasesPage()
        self.bases_panel = self.bases_page.browser
        self.bases_panel.tree.customContextMenuRequested.connect(self._show_base_context_menu)
        self.bases_page.baseSelected.connect(self._on_base_record_selected)
        self.bases_page.openInventoryRequested.connect(
            self._open_base_record_inventory)
        self.bases_page.openMapRequested.connect(self._open_base_record_map)
        self.bases_page.openGuildRequested.connect(self._open_base_record_guild)
        self.bases_page.stateActionRequested.connect(
            lambda action: self._handle_world_state_action(
                action, self._refresh_bases))
        self._bases_inspector_column = self.bases_page.entity_browser.inspector_host
        self._bases_inspector = self.bases_page.inspector
        self._bases_open_inventory_btn = self.bases_page.inventory_button
        self._bases_table_cap = 420
        self.stacked_widget.addWidget(self.bases_page)
    def _setup_map_tab(self):
        from .tabs.map_tab import MapTab
        self.map_tab = MapTab(self)
        self.map_tab.openBaseRequested.connect(self._open_map_base)
        self.map_tab.openPlayerRequested.connect(self._open_map_player)
        self.map_tab.openGuildRequested.connect(self._open_map_guild)
        self.map_tab.loadSaveRequested.connect(self._load_save)
        self.map_tab.retryRequested.connect(self._refresh_map)
        self.stacked_widget.addWidget(self.map_tab)
    def _setup_tools_tab(self):
        from .tabs.tools_tab import ToolsTab
        self.tools_tab = ToolsTab(self)
        self.stacked_widget.addWidget(self.tools_tab)
    def _setup_base_inventory_tab(self):
        from .tabs.base_inventory_tab import BaseInventoryTab
        self.base_inventory_tab = BaseInventoryTab(self)
        if 'workspace_context' in self.__dict__:
            self.base_inventory_tab.bind_workspace_context(
                self.workspace_context)
        self.stacked_widget.addWidget(self.base_inventory_tab)
    def _setup_inventory_tab(self):
        from .tabs.inventory_tab import PlayerInventoryTab
        self.inventory_tab = PlayerInventoryTab(self)
        if 'workspace_context' in self.__dict__:
            self.inventory_tab.bind_workspace_context(self.workspace_context)
        self.stacked_widget.addWidget(self.inventory_tab)
        self.inventory_tab.unlock_all_map_requested.connect(self._on_bulk_unlock_all_map)
    def _setup_pal_editor_tab(self):
        from .tabs.pal_editor_tab import PalEditorTab
        self.pal_editor_tab = PalEditorTab(self)
        if 'workspace_context' in self.__dict__:
            self.pal_editor_tab.bind_workspace_context(self.workspace_context)
        self.stacked_widget.addWidget(self.pal_editor_tab)
    def _setup_docs_tab(self):
        from .tabs.docs_tab import DocsTab
        self.docs_tab = DocsTab(self)
        self.stacked_widget.addWidget(self.docs_tab)

    def _setup_json_editor_tab(self):
        from .tabs.json_editor_tab import JsonEditorTab
        self.json_editor_tab = JsonEditorTab(self)
        self.stacked_widget.addWidget(self.json_editor_tab)

    def _setup_breeding_tab(self):
        from .tabs.breeding_tab import BreedingTab
        self.breeding_tab = BreedingTab(self)
        self.stacked_widget.addWidget(self.breeding_tab)

    def _setup_exclusions_tab(self):
        from palworld_aio.ui.pages.exclusions_page import ExclusionsPage
        self.exclusions_page = ExclusionsPage()
        self.exclusions_page.addRequested.connect(self._add_exclusion_via_prompt)
        self.exclusions_page.removeRequested.connect(self._remove_exclusion)
        self.exclusions_page.stateActionRequested.connect(
            lambda action: self._handle_world_state_action(
                action, self._refresh_exclusions))
        self.exclusions_page.browser.tree.customContextMenuRequested.connect(
            lambda pos: self._show_exclusion_context_menu(
                pos, self.exclusions_page.current_kind))
        self.excl_players_panel = self.exclusions_page.browser
        self.excl_guilds_panel = self.exclusions_page.browser
        self.excl_bases_panel = self.exclusions_page.browser
        self._excl_add_buttons = {
            key: self.exclusions_page.add_button
            for key in ('players', 'guilds', 'bases')
        }
        self._excl_btns = self.exclusions_page.segmented._buttons
        self._excl_empty_states = {}
        self.stacked_widget.addWidget(self.exclusions_page)
        self._apply_excl_empty_states()
    def _switch_exclusion_view(self, key):
        self.exclusions_page.switch_view(key)
    def _add_exclusion_via_prompt(self, excl_type):
        """uiux-audit-remediation 7.1: visible '+ Add Exclusion' affordance —
        prompts for the identifier and routes into the existing
        _add_exclusion flow (storage/save/refresh untouched). Empty or
        cancelled input does nothing."""
        prompts = {
            'players': ('deletion.exclusions.add_prompt_players', 'Enter the Player UID to exclude:'),
            'guilds': ('deletion.exclusions.add_prompt_guilds', 'Enter the Guild ID to exclude:'),
            'bases': ('deletion.exclusions.add_prompt_bases', 'Enter the Base ID to exclude:'),
        }
        prompt_key, prompt_fallback = prompts[excl_type]
        text, ok = QInputDialog.getText(
            self,
            t('deletion.exclusions.add_title') if t else 'Add Exclusion',
            t(prompt_key) if t else prompt_fallback)
        if not ok:
            return
        value = text.strip()
        if not value:
            return
        self._add_exclusion(excl_type, value)
    def _setup_menus(self):
        menu_actions = {'file': [(t('menu.file.load_save') if t else 'Load Save', self._load_save), (t('menu.file.load_xgp_save') if t else 'Load GamePass Save', self._load_xgp_save), (t('menu.file.load_backup') if t else 'Load from Backup', self._load_backup_save), (t('menu.file.load_gps') if t else 'Load Global Pal Storage', self._load_gps), (t('menu.file.load_worldoption') if t else 'Load WorldOption', self._load_worldoption), (t('menu.file.save_changes') if t else 'Save Changes', self._save_changes), (t('menu.file.rename_world') if t else 'Rename World', self._rename_world), (t('aio.menu.open_data_folder') if t else 'Open Data Folder', self._open_data_folder)], 'functions': [(t('deletion.menu.submenu.delete') if t else 'Delete', [(t('deletion.menu.delete_empty_guilds') if t else 'Delete Empty Guilds', self._delete_empty_guilds), (t('deletion.menu.delete_inactive_bases') if t else 'Delete Inactive Bases', self._delete_inactive_bases), (t('deletion.menu.delete_duplicate_players') if t else 'Delete Duplicate Players', self._delete_duplicate_players), (t('deletion.menu.delete_inactive_players') if t else 'Delete Inactive Players', self._delete_inactive_players), (t('deletion.menu.delete_unreferenced') if t else 'Delete Unreferenced Data', self._delete_unreferenced), (t('deletion.menu.delete_non_base_map_objs') if t else 'Delete Non-Base Map Objects', self._delete_non_base_map_objs), (t('deletion.menu.delete_all_skins') if t else 'Delete All Skins', self._delete_all_skins), (t('deletion.menu.delete_invalid_items') if t else 'Delete Invalid Items', self._remove_invalid_items), (t('deletion.menu.delete_invalid_structures') if t else 'Delete Invalid Structures', self._remove_invalid_structures), (t('deletion.menu.delete_imported_pals') if t else 'Delete Imported Pals', self._delete_imported_pals), (t('deletion.menu.delete_invalid_pals') if t else 'Delete Invalid Pals', self._remove_invalid_pals), (t('deletion.menu.delete_invalid_passives') if t else 'Delete Invalid Passives', self._remove_invalid_passives)]), (t('deletion.menu.submenu.fix') if t else 'Fix', [(t('deletion.menu.fix_structures') if t else 'Fix All Structures', self._repair_structures), (t('deletion.menu.fix_items') if t else 'Fix All Items', self._repair_items), (t('deletion.menu.fix_all_pals') if t else 'Fix All Pals', self._fix_all_pals), (t('deletion.menu.fix_illegal_pals') if t else 'Fix Illegal Pals', self._fix_illegal_pals), (t('deletion.menu.fix_illegal_players') if t else 'Fix Illegal Players', self._fix_illegal_players), (t('deletion.menu.fix_invalid_active_skills') if t else 'Fix Invalid Active Skills', self._fix_invalid_active_skills), (t('deletion.menu.fix_timestamps') if t else 'Fix All Negative Timestamps', self._fix_all_timestamps), (t('deletion.menu.fix_overfilled_inventories') if t else 'Fix Container Sizes', self._trim_overfilled_inventories), (t('deletion.menu.fix_all_guilds') if t else 'Fix All Guilds', self._rebuild_all_guilds)]), (t('deletion.menu.submenu.reset') if t else 'Reset', [(t('deletion.menu.reset_missions') if t else 'Reset Missions', self._reset_missions), (t('deletion.menu.reset_anti_air') if t else 'Reset Anti-Air Turrets', self._reset_anti_air), (t('deletion.menu.reset_oilrig') if t else 'Reset Oil Rigs', self._reset_oilrig), (t('deletion.menu.reset_invader') if t else 'Reset Invaders', self._reset_invader), (t('deletion.menu.reset_supply') if t else 'Reset Supply', self._reset_supply), (t('deletion.menu.reset_dungeons') if t else 'Reset Dungeons', self._reset_dungeons), (t('deletion.menu.reset_lock_gimmick') if t else 'Reset Mini Game Towers', self._reset_lock_gimmick)]), (t('deletion.menu.submenu.misc') if t else 'Misc', [(t('deletion.menu.unlock_private_chests') if t else 'Unlock Private Chests', self._unlock_private_chests), (t('deletion.menu.max_all_pals') if t else 'Max All Pals', self._max_all_pals), (t('deletion.menu.paldefender') if t else 'PalDefender Commands', self._open_paldefender),         (t('base.export_all') if t else 'Export All Bases', self._export_all_bases), (t('modify_container_slots') if t else 'Modify Container Slots', self._modify_container_slots), (t('deletion.menu.modify_all_player_slots') if t else 'Modify All Player Slots', self._modify_all_player_slots), (t('deletion.menu.modify_all_guild_chest_slots') if t else 'Modify All Guild Chest Slots', self._modify_all_guild_chest_slots), (t('gamedays.menu') if t else 'Edit Game Days', self._edit_game_days)])], 'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)], 'maps': [(t('deletion.menu.show_map') if t else 'Show Map', self._show_map), (t('deletion.menu.generate_map') if t else 'Generate Map', self._generate_map)], 'exclusions': [(t('deletion.menu.save_exclusions') if t else 'Save Exclusions', self._save_exclusions)], 'languages': [(get_native_lang_name(code), partial(self._change_language, code), {'en_US': '🇺🇸', 'zh_CN': '🇨🇳', 'ru_RU': '🇷🇺', 'fr_FR': '🇫🇷', 'es_ES': '🇪🇸', 'de_DE': '🇩🇪', 'ja_JP': '🇯🇵', 'ko_KR': '🇰🇷', 'pt_BR': '🇧🇷', 'pt_PT': '🇵🇹'}[code]) for code in ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR', 'pt_BR', 'pt_PT']]}
        self._set_menu_actions(menu_actions)
    def _open_data_folder(self):
        from resource_resolver import get_user_config_dir
        _p = os.path.dirname(get_user_config_dir())
        self._reveal_system_path(_p)
    def _reveal_system_path(self, path):
        _p = os.path.abspath(str(path))
        if not os.path.exists(_p):
            self._show_error(
                t('error.title') if t else 'Error',
                t('ui.diagnostics.path_missing',
                  default='This path is not available: {path}', path=_p))
            return
        try:
            if sys.platform == 'win32':
                os.startfile(_p)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', _p])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', _p])
        except Exception as _e:
            print(f'Could not open diagnostics path {_p}: {_e}')
            self._show_error(
                t('error.title') if t else 'Error',
                t('ui.diagnostics.open_failed',
                  default='Could not open this application path.'))
    def _copy_diagnostics_report(self, report):
        QApplication.clipboard().setText(str(report))
        page = self.__dict__.get('diagnostics_page')
        if page is not None:
            page.set_result(t(
                'ui.diagnostics.copied',
                default='Support report copied to the clipboard.'))
    def _export_diagnostics_report(self, report):
        from pathlib import Path
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            t('ui.diagnostics.export', default='Export Report'),
            'PalTrainer-diagnostics.txt',
            t('ui.diagnostics.text_files', default='Text Files (*.txt)'))
        if not path:
            return
        page = self.__dict__.get('diagnostics_page')
        try:
            Path(path).write_text(str(report), encoding='utf-8')
        except OSError as error:
            print(f'Failed to export diagnostics report: {error}')
            if page is not None:
                page.set_result(t(
                    'ui.diagnostics.export_failed',
                    default='The report could not be exported.'), 'danger')
            return
        if page is not None:
            page.set_result(t(
                'ui.diagnostics.exported',
                default='Support report exported to {path}.', path=path))
    def _sync_diagnostics_console(self):
        page = self.__dict__.get('diagnostics_page')
        stream = self.__dict__.get('status_stream')
        if page is None:
            return
        if stream is not None:
            page.set_console_text(stream.stringio.getvalue())
            page.set_console_detached(bool(stream.detached))
        warning = self.__dict__.get('_warning_detail', '')
        if warning:
            page.set_update_warning(warning)
    def _create_action(self, text, callback):
        action = QAction(text, self)
        action.triggered.connect(callback)
        return action
    def _setup_connections(self):
        save_manager.load_started.connect(self.shell_state.begin_load)
        save_manager.load_started.connect(self._on_shell_loading)
        save_manager.load_finished.connect(self._on_load_finished)
        save_manager.save_started.connect(self.shell_state.begin_save)
        save_manager.save_started.connect(self._on_shell_saving)
        save_manager.save_finished.connect(self._on_save_finished)
        save_manager.save_failed.connect(self._on_save_failed)
        self._dirty_sync_timer = QTimer(self)
        self._dirty_sync_timer.timeout.connect(self._sync_dirty_from_runtime)
        self._dirty_sync_timer.start(250)
        self._setup_global_shortcuts()

    def _setup_global_shortcuts(self):
        """Plan 024 + top-nav-shell 3.3: Ctrl+1..9/0 for the original ten
        pages, Ctrl+- / Ctrl+= for breeding/docs; Esc closes the tray drawer."""
        from PyQt6.QtGui import QShortcut, QKeySequence
        page_order = ['tools', 'base_inventory', 'player_inventory', 'pal_editor',
                      'players', 'guilds', 'bases', 'map', 'exclusions', 'json_editor']
        for idx, page_id in enumerate(page_order):
            key = idx + 1 if idx < 9 else 0
            shortcut = QShortcut(QKeySequence(f'Ctrl+{key}'), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(lambda pid=page_id: self._activate_nav(pid))
            self._page_shortcuts = getattr(self, '_page_shortcuts', [])
            self._page_shortcuts.append(shortcut)
        extra_pages = [('Ctrl+-', 'breeding'), ('Ctrl+=', 'docs')]
        for seq, page_id in extra_pages:
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(lambda pid=page_id: self._activate_nav(pid))
            self._page_shortcuts.append(shortcut)
        self._command_shortcuts = []
        for sequence in ('Ctrl+K', 'Ctrl+P'):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(self._show_command_palette)
            self._command_shortcuts.append(shortcut)
        self._global_search_shortcut = QShortcut(QKeySequence('Ctrl+Shift+F'), self)
        self._global_search_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._global_search_shortcut.activated.connect(self._show_global_search)
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        esc.activated.connect(self._on_global_escape)
        self._esc_shortcut = esc

    def _show_command_palette(self):
        from palworld_aio.ui.chrome.command_palette import (
            CommandDescriptor, CommandPalette, route_commands,
        )
        palette = self.__dict__.get('_command_palette')
        if palette is None:
            category = t('ui.command.category.application') if t else 'Application'
            commands = list(route_commands(self._activate_nav))
            commands.extend((
                CommandDescriptor(
                    'app:load_save',
                    t('ui.command.load_save') if t else 'Load Save',
                    category,
                    self._load_save,
                    ('open', 'file', 'world'),
                    'Ctrl+O',
                ),
                CommandDescriptor(
                    'app:save_changes',
                    t('ui.command.save_changes') if t else 'Save Changes',
                    category,
                    self._save_changes,
                    ('write', 'pending', 'changes'),
                    'Ctrl+S',
                ),
            ))
            palette = CommandPalette(commands, self)
            self._command_palette = palette
        palette.open_palette()

    def _show_global_search(self):
        from palworld_aio.ui.global_search import GlobalSearchDialog, GlobalSearchIndex
        index = self.__dict__.get('_global_search_index')
        if index is None:
            index = GlobalSearchIndex()
            self._global_search_index = index
        dialog = self.__dict__.get('_global_search_dialog')
        if dialog is None:
            dialog = GlobalSearchDialog(index, self.workspace_shell.router, self)
            self._global_search_dialog = dialog
        dialog.open_search()

    def _refresh_global_search_index(self):
        """Build identifier-only search records from loaded and bundled data."""
        from palworld_aio.ui.global_search import GlobalSearchIndex, build_search_records
        from palworld_aio.world.projections import SaveProjections

        players = [
            {'uid': uid, 'name': name, 'guild_id': guild_id}
            for uid, name, guild_id, *_rest in save_manager.get_players()
        ]
        guilds = get_guilds()
        bases = get_bases()
        pals = []
        level = constants.loaded_level_json
        if level:
            wsd = level['properties']['worldSaveData']['value']
            for entry in SaveProjections.get_pal_char_entries(wsd):
                parameter = SaveProjections.get_save_param(entry)
                instance_id = str(
                    entry.get('key', {}).get('InstanceId', {}).get('value', ''))
                character_id = parameter.get('CharacterID', {}).get('value', '')
                nickname = parameter.get('NickName', {}).get('value', '')
                owner_uid = parameter.get('OwnerPlayerUId', {}).get('value', '')
                if instance_id:
                    pals.append({
                        'instance_id': instance_id,
                        'name': str(nickname or character_id or instance_id),
                        'owner_uid': str(owner_uid or ''),
                        'detail': str(character_id or ''),
                    })

        def game_data(filename, key):
            path = resource_path(constants.get_base_path(), 'game_data', filename)
            try:
                payload = json_tools.load(path)
            except (OSError, ValueError, TypeError):
                return []
            values = payload.get(key, []) if isinstance(payload, dict) else []
            return values if isinstance(values, list) else []

        items = game_data('items.json', 'items')
        skills = game_data('skills.json', 'skills')
        technologies = game_data('world.json', 'technology')
        fast_travel_path = resource_path(
            constants.get_base_path(), 'game_data', 'fast_travel_points.json')
        try:
            fast_travel = json_tools.load(fast_travel_path)
        except (OSError, ValueError, TypeError):
            fast_travel = {}
        world_data = [
            {'id': key, 'name': value.get('localized_name') or value.get('id') or key}
            for key, value in fast_travel.items()
            if isinstance(value, dict)
        ] if isinstance(fast_travel, dict) else []
        records = build_search_records(
            players=players,
            guilds=guilds,
            bases=bases,
            pals=pals,
            items=items,
            skills=skills,
            technologies=technologies,
            world_data=world_data,
        )
        index = self.__dict__.get('_global_search_index')
        if index is None:
            index = GlobalSearchIndex(records)
            self._global_search_index = index
        else:
            index.replace(records)
        self.__dict__.pop('_global_search_dialog', None)

    def _activate_nav(self, page_id: str) -> None:
        """Single keyboard/programmatic nav entry."""
        shell = self.__dict__.get('workspace_shell')
        if shell is not None:
            shell.navigate(page_id)
            return
        nav_strip = self.__dict__.get('nav_strip')
        if nav_strip is not None:
            nav_strip.set_active(page_id)
        self._on_nav_changed(page_id)

    def _activate_contextual_nav(self, page_id: str, **context) -> None:
        """Navigate with target context after the source history entry is saved."""
        shell = self.__dict__.get('workspace_shell')
        if shell is not None:
            shell.router.open_contextual(page_id, **context)
            return
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            for name, selection in context.items():
                setter = getattr(workspace_context, f'set_{name}', None)
                if setter is not None:
                    setter(selection)
        self._activate_nav(page_id)

    def open_reference(self, category: str, identifier: str) -> bool:
        """Navigate from an editor to a bundled-data record."""
        self._activate_nav('docs')
        self._ensure_tab(self._LEGACY_PAGE_INDEX['docs'])
        docs_tab = self.__dict__.get('docs_tab')
        return bool(docs_tab and docs_tab.open_reference(category, identifier))

    def open_breeding(self, pal_asset: str) -> bool:
        """Navigate from a Pal surface to its breeding combinations."""
        self._activate_nav('breeding')
        self._ensure_tab(self._LEGACY_PAGE_INDEX['breeding'])
        breeding_tab = self.__dict__.get('breeding_tab')
        return bool(breeding_tab and breeding_tab.select_pal(pal_asset))

    def _on_global_escape(self):
        active = QApplication.activeModalWidget()
        if active is not None:
            return
        shell = self.__dict__.get('workspace_shell')
        if shell is not None and shell.inspector_drawer.isVisible():
            self._close_tray_drawer()
    def _set_dirty(self, dirty):
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            journal = self.__dict__.get('pending_journal')
            if journal is not None:
                if dirty and workspace_context.snapshot.save is not None:
                    journal.record(t(
                        'ui.activity.change_detail',
                        default='The current save has in-memory changes.'),
                        context=workspace_context.snapshot.current_route)
                    from palworld_aio.ui.operation_journal import (
                        ActivityKind, ActivityStatus,
                    )
                    self._record_activity(
                        ActivityKind.MUTATION,
                        t('ui.activity.change_recorded',
                          default='Unsaved change recorded'),
                        status=ActivityStatus.WARNING,
                        detail=journal.summary.latest_label or '',
                    )
                elif not dirty:
                    journal.clear()
                return
            from palworld_aio.ui.workspace_context import PendingChangesSummary
            current = workspace_context.snapshot.pending_changes
            if dirty and current.count == 0:
                from palworld_aio.ui.operation_journal import (
                    ActivityKind, ActivityStatus,
                )
                self._record_activity(
                    ActivityKind.MUTATION,
                    t('ui.activity.change_recorded', default='Unsaved change recorded'),
                    status=ActivityStatus.WARNING,
                    detail=(current.latest_label or t(
                        'ui.activity.change_detail',
                        default='The current save has in-memory changes.')),
                )
            workspace_context.set_pending_changes(
                PendingChangesSummary(
                    max(1, current.count),
                    current.latest_label or 'Unsaved changes',
                    current.has_high_risk,
                ) if dirty else PendingChangesSummary())
            return
        app_bar = self.__dict__.get('app_bar')
        if app_bar is not None:
            app_bar.save_chip.set_dirty(dirty)

    def _sync_dirty_from_runtime(self):
        context = self.__dict__.get('workspace_context')
        journal = self.__dict__.get('pending_journal')
        if (context is not None and journal is not None
                and context.snapshot.save is not None
                and constants.dirty and not journal.changes):
            self._set_dirty(True)

    def _show_pending_changes(self):
        button = self.workspace_shell.header.pending_changes
        menu = QMenu(button)
        menu.setObjectName('appContextMenu')
        menu.setAccessibleName(t(
            'ui.pending.review', default='Review pending changes'))
        changes = self.pending_journal.changes
        if not changes:
            action = menu.addAction(t(
                'ui.pending.none', default='No pending changes'))
            action.setEnabled(False)
        else:
            menu.addSection(t(
                'ui.pending.review', default='Review pending changes'))
            for change in changes:
                label = change.label
                if change.affected_count is not None:
                    label = f'{label} ({change.affected_count})'
                action = menu.addAction(label)
                action.setToolTip(change.context or change.label)
                action.setEnabled(False)
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _set_menu_actions(self, actions_dict):
        self._menu_actions_dict = actions_dict
        if getattr(self, '_menu_popup_v2', None):
            self._menu_popup_v2.set_menu_actions(actions_dict)

    def _update_stats_all(self, stats):
        self._tray_drawer.stats_panel.update_stats(stats)

    def _record_activity(
        self, kind, title, *, status=None, detail='', context='', undo=None,
    ):
        journal = self.__dict__.get('operation_journal')
        if journal is None:
            return None
        from palworld_aio.ui.operation_journal import ActivityStatus
        if not context:
            snapshot = self.workspace_context.snapshot
            context = snapshot.save.display_name if snapshot.save else ''
        return journal.record(
            kind, title, context=context,
            status=status or ActivityStatus.SUCCESS,
            detail=detail, undo=undo,
        )

    def _refresh_stats_all_before(self):
        from palworld_aio.managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        self._tray_drawer.stats_panel.refresh_stats_before(stats)

    def _refresh_stats_all_after(self):
        from palworld_aio.managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        self._tray_drawer.stats_panel.refresh_stats_after(stats)

    @staticmethod
    def _overview_backup_label(snapshot):
        backup = snapshot.backup
        if backup.latest_label:
            return backup.latest_label
        if backup.count:
            return t('ui.overview.backup.available', default='Backup available')
        if backup.recommended:
            return t('ui.overview.backup.recommended', default='Backup recommended')
        return t('ui.overview.backup.none', default='No backup recorded')

    def _sync_overview_context(self, snapshot):
        overview = self.__dict__.get('overview_page')
        if overview is None:
            return
        if snapshot.save is None:
            self._show_no_save_overview()
            return
        overview.update_context_summary(
            pending_changes=snapshot.pending_changes.count,
            backup_label=self._overview_backup_label(snapshot),
        )

    def _recent_overview_entries(self):
        from pathlib import Path
        from palworld_aio.ui.pages.overview_page import RecentSaveEntry
        entries = []
        for item in self.workspace_settings.recent_saves:
            path = Path(item.path)
            level_path = path if path.name.lower() == 'level.sav' else path / 'Level.sav'
            available = level_path.is_file() and (level_path.parent / 'Players').is_dir()
            entries.append(RecentSaveEntry(
                save_id=item.save_id,
                label=item.display_name,
                path=item.path,
                platform=(
                    'Game Pass' if item.platform == 'xbox' else
                    'Steam' if item.platform == 'steam' else 'Unknown platform'
                ),
                available=available,
            ))
        return tuple(entries)

    def _show_no_save_overview(self):
        overview = self.__dict__.get('overview_page')
        if overview is not None:
            overview.set_no_save(self._recent_overview_entries())

    def _populate_loaded_overview(self):
        from palworld_aio.ui.pages.overview_page import (
            LoadedOverviewModel, OverviewActivityItem,
        )
        snapshot = self.workspace_context.snapshot
        identity = snapshot.save
        if identity is None:
            return
        stats = save_manager.get_current_stats()
        counts = {
            key.lower(): max(0, int(value))
            for key, value in stats.items()
            if key.lower() in {'players', 'guilds', 'bases', 'pals'}
        }
        modified_at = identity.modified_at or t(
            'ui.overview.modified_unknown', default='Unknown')
        platform = (
            'Game Pass' if identity.platform.value == 'xbox' else
            'Steam' if identity.platform.value == 'steam' else
            t('ui.overview.platform_unknown', default='Unknown platform')
        )
        self.overview_page.set_loaded(LoadedOverviewModel(
            save_name=identity.display_name,
            platform=platform,
            modified_at=modified_at,
            backup_label=self._overview_backup_label(snapshot),
            pending_changes=snapshot.pending_changes.count,
            counts=counts,
            activity=(OverviewActivityItem(
                t('ui.overview.activity.loaded', default='Save loaded'),
                f'{platform} • {modified_at}',
                'success',
            ),),
        ))

    def _on_shell_loading(self):
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            workspace_context.begin_load()
            return
        try:
            from palworld_aio.shell_state import ShellState
            self.app_bar.save_chip.set_shell_state(ShellState.LOADING)
        except (RuntimeError, AttributeError, ImportError):
            pass
    def _on_shell_saving(self):
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            workspace_context.begin_save()
            return
        try:
            from palworld_aio.shell_state import ShellState
            self.app_bar.save_chip.set_shell_state(ShellState.SAVING)
        except (RuntimeError, AttributeError, ImportError):
            pass
    def _create_message_box(self, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
        msg_box.setWindowModality(Qt.ApplicationModal)
        msg_box.setIcon(icon)
        return msg_box
    def _show_info(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_warning(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_error(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_question(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_legacy_route(self, button_id):
        if button_id == 'diagnostics':
            self._sync_diagnostics_console()
            return
        if button_id in {'about', 'settings'}:
            return
        if button_id == 'backups':
            self._refresh_backups()
            return
        if (button_id == 'players'
                and self.__dict__.get('players_page') is not None):
            return
        if (button_id == 'guilds'
                and self.__dict__.get('guilds_page') is not None):
            return
        if (button_id == 'bases'
                and self.__dict__.get('bases_page') is not None):
            return
        if (button_id == 'map'
                and self.__dict__.get('map_tab') is not None):
            return
        if (button_id == 'exclusions'
                and self.__dict__.get('exclusions_page') is not None):
            return
        page_index = self._LEGACY_PAGE_INDEX.get(button_id)
        if page_index is None:
            return
        if page_index not in self._tab_created:
            self._ensure_tab(page_index)
            if constants.loaded_level_json:
                self._refresh_tab(page_index)
        self.stacked_widget.setCurrentIndex(page_index)

    def _refresh_backups(self):
        from palworld_aio.application.backup_catalog import discover_backups
        page = self.__dict__.get('backups_page')
        if page is None:
            return
        try:
            page.set_backups(discover_backups())
        except Exception as error:
            page.set_backups(())
            page.set_result(False, t(
                'ui.backups.restore_failed',
                default='Restore failed. {detail}', detail=str(error)))

    def _reveal_backup_folder(self, backup_path):
        path = os.path.abspath(str(backup_path))
        if not os.path.isdir(path):
            self._show_error(
                t('error.title'),
                t('ui.overview.file_not_found', default='File not found'))
            return
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', path])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])
        except Exception as error:
            self._show_error(
                t('error.title'), f'Could not open folder:\n{path}\n{error}')

    def _confirm_backup_restore(self, backup):
        from palworld_aio.ui.chrome.components import BaseDialog
        dialog = BaseDialog(
            t('ui.backups.confirm_title', default='Restore this backup?'),
            self, min_size=(480, 250), danger=True, kicker='Backups')
        message = QLabel(t(
            'ui.backups.confirm_message',
            default='Current save will be backed up before restoration.'), dialog)
        message.setWordWrap(True)
        dialog.content_layout.addWidget(message)
        timestamp = QLabel(t(
            'ui.backups.confirm_date', default='Backup date: {timestamp}',
            timestamp=backup.created_at.strftime('%b %d, %Y %I:%M %p')),
            dialog)
        timestamp.setProperty('class', 'secondary')
        dialog.content_layout.addWidget(timestamp)
        dialog.add_confirm_button(
            t('ui.backups.restore', default='Restore'), danger=True)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _restore_backup_record(self, backup):
        from pathlib import Path
        if not constants.current_save_path or not constants.loaded_level_json:
            self._show_warning(
                t('ui.backups.confirm_title', default='Restore this backup?'),
                t('ui.backups.no_loaded_save',
                  default='Load the save you want to restore before continuing.'))
            return
        if constants.xgp_loaded:
            self._show_warning(
                t('error.title'),
                t('ui.backups.gamepass_unsupported',
                  default='Full-save restore is not available for a loaded Game Pass container.'))
            return
        if constants.dirty:
            self._show_warning(
                t('inventory.unsaved.title', default='Unsaved Changes'),
                t('ui.backups.unsaved_changes',
                  default='Save or discard pending changes before restoring a backup.'))
            return
        if not self._confirm_backup_restore(backup):
            return

        from palworld_aio.application.backup_catalog import (
            default_backups_root, restore_backup,
        )
        page = self.backups_page
        timestamp = backup.created_at.strftime('%b %d, %Y %I:%M %p')
        page.set_loading(t(
            'ui.backups.restoring',
            default='Backing up the current save, then restoring {timestamp}…',
            timestamp=timestamp))
        current_save = Path(constants.current_save_path)
        safety_root = default_backups_root() / 'Restore Safety'

        def task():
            try:
                return restore_backup(backup, current_save, safety_root)
            except Exception as error:
                return error

        def on_finished(result):
            from palworld_aio.ui.operation_journal import (
                ActivityKind, ActivityStatus,
            )
            if isinstance(result, Exception):
                detail = str(result)
                page.set_result(False, t(
                    'ui.backups.restore_failed',
                    default='Restore failed. {detail}', detail=detail))
                self._record_activity(
                    ActivityKind.FAILURE,
                    t('ui.activity.backup_restore_failed',
                      default='Backup restore failed'),
                    status=ActivityStatus.FAILED, detail=detail)
                return
            try:
                save_manager.reload_current_save()
                self.refresh_all(mark_dirty=False)
                self._refresh_global_search_index()
                constants.dirty = False
                self._set_dirty(False)
                self._populate_loaded_overview()
            except Exception as error:
                detail = t(
                    'ui.backups.reload_failed',
                    default='The files were restored, but the save could not be reloaded: {detail}',
                    detail=str(error))
                page.set_result(False, detail)
                self._record_activity(
                    ActivityKind.FAILURE,
                    t('ui.activity.backup_reload_failed',
                      default='Restored save reload failed'),
                    status=ActivityStatus.FAILED, detail=detail)
                return
            self._refresh_backups()
            message = t(
                'ui.backups.restore_result',
                default='Backup restored. The previous save is preserved at {safety_path}.',
                safety_path=str(result.safety_backup_path))
            page.set_result(True, message)
            self._record_activity(
                ActivityKind.BACKUP,
                t('ui.activity.backup_restored', default='Backup restored'),
                detail=message)

        run_with_loading(on_finished, task, parent=self)

    def _on_nav_changed(self, button_id):
        shell = self.__dict__.get('workspace_shell')
        if shell is not None and shell.router.current_route_id != button_id:
            shell.navigate(button_id)
            return
        self._show_legacy_route(button_id)
        # Characterization compatibility for isolated legacy-nav fakes.
        if self.__dict__.get('nav_strip') is not None and self.nav_strip.active_id() != button_id:
            self.nav_strip.set_active(button_id)
    def _load_user_settings(self):
        from boot_paths import CONFIG_DIR, USER_CONFIG_DIR
        from palworld_aio.ui.user_preferences import normalize_user_settings
        user_cfg_path = str(USER_CONFIG_DIR / 'user.cfg')
        if not os.path.exists(user_cfg_path):
            user_cfg_path = os.path.join(str(CONFIG_DIR), 'user.cfg')
        if os.path.exists(user_cfg_path):
            try:
                self.user_settings = normalize_user_settings(
                    json_tools.load(user_cfg_path))
            except Exception as e:
                print(f'Failed to load user settings: {e}')
                self.user_settings = normalize_user_settings(None)
        else:
            self.user_settings = normalize_user_settings(None)
            os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
            self._save_user_settings()
        constants.loading_screen_mode = self.user_settings.get('loading_screen_mode', 'overlay')
        constants.reduced_motion = self.user_settings.get('reduced_motion', False)
        constants.automatic_backup_on_load = self.user_settings.get(
            'automatic_backup_on_load', True)
        constants.warn_unsaved_exit = self.user_settings.get(
            'warn_unsaved_exit', True)
        constants.pal_creation_name_mode = self.user_settings.get('pal_creation_name_mode', 'new')
        constants.bulk_sync_apply_nickname = self.user_settings.get('bulk_sync_apply_nickname', False)
    def _apply_preferences(self, patch):
        from palworld_aio.ui.user_preferences import UserPreferences
        merged = dict(self.user_settings)
        if isinstance(patch, dict):
            merged.update(patch)
        preferences = UserPreferences.from_mapping(merged)
        values = preferences.to_mapping()
        old_language = self.user_settings.get('language', 'en_US')
        language = preferences.language
        values.pop('language')
        self.user_settings.update(values)
        constants.loading_screen_mode = preferences.loading_screen_mode
        constants.reduced_motion = preferences.reduced_motion
        constants.automatic_backup_on_load = preferences.automatic_backup_on_load
        constants.warn_unsaved_exit = preferences.warn_unsaved_exit
        constants.pal_creation_name_mode = preferences.pal_creation_name_mode
        constants.bulk_sync_apply_nickname = preferences.bulk_sync_apply_nickname
        stream = self.__dict__.get('status_stream')
        if stream is not None and preferences.console_detached != stream.detached:
            stream.detach() if preferences.console_detached else stream.attach()
        if old_language != language:
            self._change_language(language)
        else:
            self.user_settings['language'] = language
            self._save_user_settings()
    def _save_user_settings(self):
        from boot_paths import USER_CONFIG_DIR
        shell = self.__dict__.get('workspace_shell')
        workspace_settings = self.__dict__.get('workspace_settings')
        if shell is not None and workspace_settings is not None:
            sidebar = shell.sidebar.export_settings()
            router_state = shell.router.export_persistent_state()
            workspace_settings.sidebar_collapsed = bool(sidebar['collapsed'])
            workspace_settings.sidebar_width = int(sidebar['expanded_width'])
            workspace_settings.splitter_sizes = shell.splitter_sizes()
            workspace_settings.current_route = str(router_state['current_route'])
            workspace_settings.last_routes = dict(router_state['last_routes'])
            workspace_settings.page_view_state = dict(router_state['page_view_state'])
            if self.workspace_context.snapshot.save is not None:
                workspace_settings.capture_context(self.workspace_context)
            self.user_settings['workspace_ui'] = workspace_settings.to_mapping()
        user_cfg_path = str(USER_CONFIG_DIR / 'user.cfg')
        self.user_settings['pal_creation_name_mode'] = constants.pal_creation_name_mode
        self.user_settings['bulk_sync_apply_nickname'] = constants.bulk_sync_apply_nickname
        try:
            os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
            json_tools.dump(self.user_settings, user_cfg_path, indent=2)
        except Exception as e:
            print(f'Failed to save user settings: {e}')
    def _load_theme(self):
        ThemeManager.apply_global()
    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    def _detach_status(self):
        if self.status_stream:
            if self.status_stream.detached:
                self.status_stream.attach()
            else:
                self.status_stream.detach()
        self.user_settings['console_detached'] = self.status_stream.detached if self.status_stream else False
        self._save_user_settings()
    def _on_detach_state_changed(self, detached):
        self._set_console_action_state(detached)
        page = self.__dict__.get('diagnostics_page')
        if page is not None:
            page.set_console_detached(bool(detached))
        if self.user_settings.get('console_detached') != bool(detached):
            self.user_settings['console_detached'] = bool(detached)
            self._save_user_settings()

    def _set_console_action_state(self, detached):
        button = self.__dict__.get('_shell_console_button')
        if button is not None:
            button.setProperty('active', bool(detached))
            button.style().unpolish(button)
            button.style().polish(button)
            return
        app_bar = self.__dict__.get('app_bar')
        if app_bar is not None:
            app_bar.set_console_visible(detached)
    def _check_update(self):
        current = self.__dict__.get('update_checker')
        if current is not None and current.isRunning():
            return
        about = self.__dict__.get('about_page')
        if about is not None:
            about.set_update_state('checking')
        self.update_checker = UpdateChecker()
        self.update_checker.update_checked.connect(self._on_update_checked)
        self.update_checker.start()
    def _on_update_checked(self, ok, latest, branch):
        try:
            if not ok and latest:
                tools_version = get_display_version()
                self._set_update_action_state(True)
                branch_text = f' ({branch})' if branch else ''
                self.status_bar.showMessage(f"{(t('update.current') if t else 'Current')}: {tools_version}{branch_text} | {(t('update.latest') if t else 'Latest')}: {latest} - Click version chip to update", 0)
            else:
                self._set_update_action_state(False)
            about = self.__dict__.get('about_page')
            diagnostics = self.__dict__.get('diagnostics_page')
            if not ok and latest:
                if about is not None:
                    about.set_update_state(
                        'available', current=get_display_version(),
                        latest=str(latest))
                if diagnostics is not None:
                    diagnostics.set_update_warning(t(
                        'ui.about.update_available',
                        default='Update available: {current} → {latest}',
                        current=get_display_version(), latest=str(latest)))
            elif ok:
                if about is not None:
                    about.set_update_state(
                        'current', current=get_display_version())
            else:
                detail = t(
                    'status.update_check_failed',
                    default='Update check failed — open Warnings for details')
                if about is not None:
                    about.set_update_state('error', detail=detail)
                if diagnostics is not None:
                    diagnostics.set_update_warning(detail)
            # uiux-audit-remediation 2.2: a failed update check raises the
            # warning affordance (tri-state) instead of pinning raw error
            # text in the strip; any successful check — up-to-date (ok) or
            # update-available (latest set) — resolves it.
            if ok or latest is not None:
                self._warning_detail = ''
                app_bar = self.__dict__.get('app_bar')
                if app_bar is not None:
                    app_bar.resolve_warning()
            else:
                self._warning_detail = (
                    t('status.update_check_failed') if t
                    else 'Update check failed — open Warnings for details')
                app_bar = self.__dict__.get('app_bar')
                if app_bar is not None:
                    app_bar.raise_warning(self._warning_detail)
        except Exception as e:
            print(f'Update check callback error: {e}')

    def _set_update_action_state(self, available):
        button = self.__dict__.get('_shell_save_button')
        if button is not None:
            button.setProperty('updateAvailable', bool(available))
            button.style().unpolish(button)
            button.style().polish(button)
            return
        app_bar = self.__dict__.get('app_bar')
        if app_bar is not None:
            app_bar.set_update_pulse(available)
    def _lock_ui(self):
        pass
    def _unlock_ui(self):
        pass
    def _on_load_finished(self, success):
        self.shell_state.finish_load(success)
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            from datetime import datetime
            from pathlib import Path
            from palworld_aio.ui.workspace_context import (
                BackupState, SaveIdentity, SavePlatform,
            )
            save_path = str(constants.current_save_path or '')
            identity = None
            if success:
                path = Path(save_path) if save_path else None
                is_level_file = bool(path and path.name.lower() == 'level.sav')
                level_path = path if is_level_file else (path / 'Level.sav' if path else None)
                modified_at = None
                modified_timestamp = constants.loaded_level_mtime
                if modified_timestamp is None and level_path is not None:
                    try:
                        modified_timestamp = level_path.stat().st_mtime
                    except OSError:
                        modified_timestamp = None
                if modified_timestamp is not None:
                    modified_at = datetime.fromtimestamp(modified_timestamp).strftime(
                        '%b %d, %Y %I:%M %p')
                platform = (SavePlatform.XBOX if constants.xgp_loaded
                            else SavePlatform.STEAM)
                display_name = (
                    str(constants.xgp_save_id or 'Game Pass World')
                    if platform is SavePlatform.XBOX else
                    ((path.parent.name if is_level_file else path.name)
                     if path else 'Loaded Save')
                )
                identity = SaveIdentity(
                    save_id=(str(path.parent if is_level_file else path)
                             if path else 'loaded-save'),
                    display_name=display_name,
                    path=save_path,
                    platform=platform,
                    modified_at=modified_at,
                    read_only=bool(level_path and level_path.is_file()
                                   and not os.access(level_path, os.W_OK)),
                )
            backup = None
            if success:
                backup = BackupState(
                    count=0 if constants.xgp_loaded else 1,
                    latest_label=(None if constants.xgp_loaded else t(
                        'ui.overview.backup.created', default='Automatic backup created')),
                    recommended=bool(constants.xgp_loaded),
                )
            workspace_context.finish_load(identity, success=success, backup=backup)
            if success:
                from palworld_aio.ui.operation_journal import ActivityKind
                self.workspace_settings.remember_save(identity)
                self._record_activity(
                    ActivityKind.LOAD,
                    t('ui.activity.save_loaded', default='Save loaded'),
                    detail=identity.path,
                )
                if backup is not None and backup.count:
                    self._record_activity(
                        ActivityKind.BACKUP,
                        t('ui.activity.backup_created', default='Backup created'),
                        detail=(backup.latest_label or ''),
                    )
                self._populate_loaded_overview()
                self.workspace_shell.router.reset_for_save(route_id='overview')
                workspace_settings = self.__dict__.get('workspace_settings')
                if workspace_settings is not None:
                    workspace_settings.restore_context(workspace_context)
        else:
            try:
                from palworld_aio.shell_state import ShellState
                state = ShellState.LOADED if success else ShellState.ERROR
                self.app_bar.save_chip.set_shell_state(state)
            except (RuntimeError, AttributeError, ImportError):
                pass
        if success:
            if 'inventory_tab' in self.__dict__:
                self.inventory_tab.clear_player()
            if 'pal_editor_tab' in self.__dict__:
                self.pal_editor_tab.clear_player()
                self.pal_editor_tab.current_player_uid = None
            if 'base_inventory_tab' in self.__dict__:
                self.base_inventory_tab._clear_guild_selection()
            self.refresh_all(mark_dirty=False)
            self._refresh_global_search_index()
            constants.dirty = False
            self._set_dirty(False)
            app_bar = self.__dict__.get('app_bar')
            if app_bar is not None:
                app_bar.context.clear_selection()
                app_bar.context.setVisible(True)
            self._refresh_stats_all_before()
            self.status_bar.showMessage(t('status.loaded') if t else 'Save loaded successfully', 5000)
        else:
            from palworld_aio.ui.operation_journal import (
                ActivityKind, ActivityStatus,
            )
            self._record_activity(
                ActivityKind.FAILURE,
                t('ui.activity.load_failed', default='Save load failed'),
                status=ActivityStatus.FAILED,
                detail=t('save.load_failed', default='The selected save could not be loaded.'),
            )
            self.status_bar.showMessage(t('status.load_failed') if t else 'Failed to load save', 5000)
            msg_box = self._create_message_box(QMessageBox.Critical)
            msg_box.setWindowTitle(t('error.title'))
            if constants.xgp_loaded:
                msg_box.setText(t('xgp.save_unreadable.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
            else:
                msg_box.setText(t('save.load_failed'))
            msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
            msg_box.exec()
    def _on_save_finished(self, duration):
        self.shell_state.finish_save(True)
        constants.dirty = False
        self._set_dirty(False)
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            workspace_context.finish_save(True)
            from palworld_aio.ui.operation_journal import ActivityKind
            self._record_activity(
                ActivityKind.SAVE,
                t('ui.activity.save_completed', default='Changes saved'),
                detail=t(
                    'ui.activity.save_duration',
                    default='Completed in {duration:.2f}s', duration=duration),
            )
        else:
            try:
                from palworld_aio.shell_state import ShellState
                self.app_bar.save_chip.set_shell_state(ShellState.LOADED)
            except (RuntimeError, AttributeError, ImportError):
                pass
        self.status_bar.showMessage(f"{(t('status.saved') if t else 'Save completed')}({duration:.2f}s)", 5000)
        if constants.xgp_loaded:
            return
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(t('success.title'))
        msg_box.setText(t('Changes saved successfully.'))
        msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
        msg_box.exec()
    def _on_save_failed(self, _detail):
        self.shell_state.finish_save(False)
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is not None:
            workspace_context.finish_save(False)
        from palworld_aio.ui.operation_journal import ActivityKind, ActivityStatus
        self._record_activity(
            ActivityKind.FAILURE,
            t('ui.activity.save_failed', default='Save failed'),
            status=ActivityStatus.FAILED,
            detail=t('ui.activity.save_failed_detail',
                     default='Changes remain in memory. Check Diagnostics before retrying.'),
        )
    _TAB_REFRESH = {
        0: None,
        1: '_refresh_base_inventory',
        2: '_refresh_inventory',
        3: '_refresh_pal_editor',
        4: '_refresh_players',
        5: '_refresh_guilds',
        6: '_refresh_bases',
        7: '_refresh_map',
        8: '_refresh_exclusions',
        9: '_refresh_json_editor',
        10: None,
        11: '_refresh_breeding',
    }
    def _refresh_tab(self, page_index):
        method = self._TAB_REFRESH.get(page_index)
        if method:
            getattr(self, method)()
    def _refresh_pal_editor(self):
        if 'pal_editor_tab' in self.__dict__:
            self.pal_editor_tab.refresh()
    def _refresh_json_editor(self):
        if 'json_editor_tab' in self.__dict__:
            self.json_editor_tab.refresh()
    def _refresh_breeding(self):
        if 'breeding_tab' in self.__dict__:
            self.breeding_tab.refresh()
    def refresh_all(self, *, mark_dirty=True):
        if self._is_refreshing:
            return
        if mark_dirty:
            constants.dirty = True
            self._set_dirty(True)
        self._is_refreshing = True
        try:
            self._refresh_players()
            self._refresh_guilds()
            self._refresh_bases()
            self._refresh_map()
            self._refresh_exclusions()
            self._refresh_inventory()
            self._refresh_base_inventory()
            self._refresh_pal_editor()
            if 'tools_tab' in self.__dict__:
                self.tools_tab.refresh()
            self._refresh_json_editor()
            self._refresh_breeding()
        finally:
            self._is_refreshing = False
    def _refresh_inventory(self):
        if 'inventory_tab' in self.__dict__:
            self.inventory_tab.refresh()
    def _refresh_stats(self):
        stats = save_manager.get_current_stats()
        self._update_stats_all(stats)

    def _handle_world_state_action(self, action, retry):
        if action == 'load_save':
            self._load_save()
        elif action == 'retry':
            retry()

    def _refresh_players(self):
        from palworld_aio.ui.pages.players_page import PlayerRow
        if not constants.loaded_level_json:
            self.players_page.set_loaded(False)
            return
        self.players_page.set_loading()
        try:
            players = save_manager.get_players()
            records = []
            for uid, name, gid, lastseen, level, elapsed in players:
                pals = constants.PLAYER_PAL_COUNTS.get(uid.replace('-', '').lower(), 0)
                gname = save_manager.get_guild_name_by_id(gid)
                glevel = save_manager.get_guild_level_by_id(gid)
                is_leader = save_manager.is_player_guild_leader(gid, uid)
                records.append(PlayerRow(
                    uid=str(uid),
                    name=str(name),
                    last_seen=str(lastseen),
                    level=int(level) if str(level).isdigit() else 0,
                    pals=int(pals) if str(pals).isdigit() else 0,
                    guild_name=str(gname or ''),
                    guild_id=str(gid or ''),
                    guild_level=int(glevel) if str(glevel).isdigit() else 0,
                    is_leader=bool(is_leader),
                    last_seen_sort=(float(elapsed) if elapsed is not None else None),
                ))
            self.players_page.set_players(tuple(records))
        except Exception:
            logging.getLogger(__name__).exception('Could not refresh Players workspace')
            self.players_page.set_error(t(
                'ui.players.error_message',
                default='Player records could not be read from this save.'))
    def _refresh_guilds(self):
        from collections import Counter
        from palworld_aio.ui.pages.guilds_page import GuildRow
        if not constants.loaded_level_json:
            self.guilds_page.set_loaded(False)
            return
        self.guilds_page.set_loading()
        try:
            guilds = get_guilds()
            base_counts = Counter(str(base['guild_id']) for base in get_bases())
            records = []
            for g in guilds:
                guild_id = str(g['id'])
                records.append(GuildRow(
                    guild_id=guild_id,
                    name=str(g['name'] or ''),
                    level=(int(g['level']) if str(g['level']).isdigit() else 0),
                    member_count=int(g['member_count']),
                    base_count=base_counts[guild_id],
                ))
            self.guilds_page.set_guilds(tuple(records))
        except Exception:
            logging.getLogger(__name__).exception('Could not refresh Guilds workspace')
            self.guilds_page.set_error(t(
                'ui.guilds.error_message',
                default='Guild records could not be read from this save.'))
    def _refresh_bases(self):
        from palworld_aio.managers.data_manager import get_base_coords
        from palworld_aio.ui.pages.bases_page import BaseRow
        if not constants.loaded_level_json:
            self.bases_page.set_loaded(False)
            return
        self.bases_page.set_loading()
        try:
            bases = get_bases()
            guild_counts = {}
            records = []
            for b in bases:
                glevel = save_manager.get_guild_level_by_id(b['guild_id'])
                guild_id = str(b['guild_id'])
                guild_counts[guild_id] = guild_counts.get(guild_id, 0) + 1
                base_name = t(
                    'ui.bases.generated_name', default='Base {number}',
                    number=guild_counts[guild_id])
                x_coord, y_coord = get_base_coords(str(b['id']))
                location = ''
                if x_coord is not None and y_coord is not None:
                    location = f'X {float(x_coord):.0f}, Y {float(y_coord):.0f}'
                records.append(BaseRow(
                    base_id=str(b['id']),
                    name=base_name,
                    guild_id=guild_id,
                    guild_name=str(b['guild_name'] or ''),
                    guild_level=(int(glevel) if str(glevel).isdigit() else 0),
                    location=location,
                    status=t('ui.bases.status.in_save', default='In save'),
                ))
            self.bases_page.set_bases(tuple(records))
        except Exception:
            logging.getLogger(__name__).exception('Could not refresh Bases workspace')
            self.bases_page.set_error(t(
                'ui.bases.error_message',
                default='Base records could not be read from this save.'))

    def _cap_search_table_height(self, panel, chrome_attr: str, content_cap: int,
                                 max_rows: int = 10, min_height: int = 180):
        """uiux-audit-remediation 5.2 (design D7): shared content-height cap
        for World-Data table cards (Bases, Players). The card sizes to its
        rows up to ``content_cap`` (rows scroll internally beyond it) so the
        bulk footer hugs the table and the inspector fills the side."""
        tree = panel.tree
        row_h = 26
        if tree.topLevelItemCount():
            measured = tree.visualItemRect(tree.topLevelItem(0)).height()
            if measured > 0:
                row_h = measured
        header_h = tree.header().height() or 28
        visible = min(tree.topLevelItemCount(), max_rows)
        tree_needed = header_h + visible * row_h + 2
        # non-tree chrome of the SearchPanel (search row + hairline + footer),
        # measured once from a laid-out widget (falls back to the QSS sum)
        try:
            chrome = getattr(self, chrome_attr)
        except (AttributeError, RuntimeError):
            chrome = 0
        if not chrome and panel.height() > 200:
            measured = panel.height() - tree.height()
            if measured >= 48:
                setattr(self, chrome_attr, measured)
                chrome = measured
        if not chrome:
            from palworld_aio.ui.chrome.tokens import HEIGHT
            chrome = (HEIGHT['default'] + 18) + 1 + (HEIGHT['compact'] + 8)
        cap = min(tree_needed + chrome, max(content_cap + chrome, 200))
        panel.setMaximumHeight(max(cap, min_height))

    def _cap_bases_table_height(self):
        """uiux-audit-remediation 4.2: bound the bases table container to its
        content height (see _cap_search_table_height)."""
        self._cap_search_table_height(
            self.bases_panel, '_bases_panel_chrome', self._bases_table_cap)
    def _refresh_map(self):
        if 'map_tab' in self.__dict__:
            self.map_tab.refresh()
    def _apply_excl_empty_states(self):
        """modernize-tab-ui 7.1: no-save keeps the plain load-save hint; with a
        save loaded the exclusions panes show the shared EmptyState."""
        page = self.__dict__.get('exclusions_page')
        if page is not None:
            page.set_loaded(bool(constants.loaded_level_json))
            return
        loaded = bool(constants.loaded_level_json)
        for key, empty in getattr(self, '_excl_empty_states', {}).items():
            panel = getattr(self, f'excl_{key}_panel', None)
            if panel is None:
                continue
            if loaded:
                panel.set_empty_state_widget(empty)
                empty.setText(t('deletion.exclusions.empty_title') if t else 'No exclusions configured')
                empty.setHint(t(f'deletion.exclusions.empty_hint_{key}') if t else 'Use the right-click menu to exclude entries.')
            else:
                panel.set_empty_state_widget(None)
    def _refresh_exclusions(self):
        page = self.__dict__.get('exclusions_page')
        if page is not None:
            if not constants.loaded_level_json:
                page.set_loaded(False)
                return
            page.set_loading()
            try:
                page.set_exclusions({
                    key: constants.exclusions.get(key, [])
                    for key in ('players', 'guilds', 'bases')
                })
                self._apply_excl_empty_states()
            except Exception:
                logging.getLogger(__name__).exception(
                    'Could not refresh Exclusions workspace')
                page.set_error(t(
                    'ui.exclusions.error_message',
                    default='Exclusions could not be read from this save.'))
            return
        self.excl_players_panel.clear()
        for uid in constants.exclusions.get('players', []):
            self.excl_players_panel.add_item([uid])
        self.excl_guilds_panel.clear()
        for gid in constants.exclusions.get('guilds', []):
            self.excl_guilds_panel.add_item([gid])
        self.excl_bases_panel.clear()
        for bid in constants.exclusions.get('bases', []):
            self.excl_bases_panel.add_item([bid])
        self._apply_excl_empty_states()
    def _refresh_base_inventory(self):
        if 'base_inventory_tab' in self.__dict__:
            self.base_inventory_tab.refresh()
    def mousePressEvent(self, event):
        # The new shell's dedicated WindowDragRegion owns frameless movement.
        super().mousePressEvent(event)
    def _hit_window_drag_zone(self, event) -> bool:
        return False
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
    def _show_warnings(self):
        # uiux-audit-remediation 2.2 (design D4): click-to-reveal includes
        # the condition that raised the affordance (e.g. a failed update
        # check) ahead of the standing save-safety notices.
        lines = []
        warn_detail = self.__dict__.get('_warning_detail', '')
        app_bar = self.__dict__.get('app_bar')
        if not warn_detail and app_bar is not None:
            warn_detail = app_bar.warn_detail()
        if warn_detail:
            lines.append(warn_detail)
        warnings = [(t('notice.backup') if t else 'WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THESE TOOLS!', {}), (t('notice.patch', game_version=get_versions()[1]) if t else 'MAKE SURE TO UPDATE YOUR SAVES AFTER EVERY GAME PATCH!', {}), (t('notice.errors') if t else 'IF YOU DO NOT UPDATE YOUR SAVES AFTER A PATCH,YOU MAY ENCOUNTER ERRORS!', {})]
        lines.extend((w for w, _ in warnings if w))
        combined = '\n\n'.join(lines)
        if not combined:
            combined = t('notice.none') if t else 'No warnings.'
        msg_box = self._create_message_box(QMessageBox.Warning)
        msg_box.setWindowTitle(t('PalTrainer') if t else 'PalTrainer')
        msg_box.setText(combined)
        msg_box.exec()
    def _show_about(self):
        self._activate_nav('about')
    def _show_tab_guide(self):
        from .dialogs.tab_guide_dialog import TabGuideDialog
        dialog = TabGuideDialog(self)
        if not hasattr(self, '_active_dialogs'):
            self._active_dialogs = []
        self._active_dialogs.append(dialog)
        try:
            dialog.exec()
        finally:
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
    @staticmethod
    def _preselect_dialog_players(dialog, player_uids):
        if not player_uids:
            return
        desired = {str(uid).replace('-', '').upper() for uid in player_uids}
        player_list = getattr(dialog, 'player_list', None)
        if player_list is None:
            return
        for index in range(player_list.count()):
            item = player_list.item(index)
            widget = player_list.itemWidget(item)
            if widget is None:
                continue
            uid = str(widget.property('uid') or '').replace('-', '').upper()
            if hasattr(widget, 'setChecked'):
                widget.setChecked(uid in desired)

    def _open_bulk_player_item_dialog(self, player_uids=None):
        dialog = PlayerItemActionDialog(self)
        dialog.item_action_selected.connect(self._on_player_item_action)
        dialog.add_all_key_items_requested.connect(self._on_bulk_add_all_key_items)
        dialog.add_all_effigies_requested.connect(self._on_bulk_add_all_effigies)
        dialog.edit_abilities_requested.connect(self._on_bulk_edit_abilities)
        dialog.unlock_all_map_requested.connect(self._on_bulk_unlock_all_map)
        dialog.modify_slots_requested.connect(self._on_bulk_modify_slots)
        self._preselect_dialog_players(dialog, player_uids)
        dialog.exec()
    def _open_bulk_player_pal_dialog(self, _player_uids=None):
        dialog = PlayerPalActionDialog(self)
        dialog.pal_action_selected.connect(self._on_player_pal_action)
        dialog.exec()
    def _open_bulk_technology_dialog(self, player_uids=None):
        dialog = PlayerTechnologyActionDialog(self)
        QTimer.singleShot(
            0, lambda: self._preselect_dialog_players(dialog, player_uids))
        if not hasattr(self, '_active_dialogs'):
            self._active_dialogs = []
        self._active_dialogs.append(dialog)
        try:
            dialog.exec()
        finally:
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
    def _on_player_item_action(self, item_id, action, player_uids):
        def task():
            from palworld_aio.inventory.base_inventory_manager import remove_item_from_players, add_item_to_players
            if action == 'remove_all':
                result = remove_item_from_players(item_id, player_uids=player_uids)
                return ('remove_all', result)
            elif action.startswith('remove_pct:'):
                pct = float(action.split(':')[1])
                result = remove_item_from_players(item_id, percentage=pct, player_uids=player_uids)
                return ('remove_pct', result, int(pct))
            elif action.startswith('add:'):
                parts = action.split(':')
                quantity = int(parts[1])
                container_type = parts[2] if len(parts) > 2 else 'key'
                result = add_item_to_players(item_id, quantity=quantity, container_type=container_type, player_uids=player_uids)
                return ('add', result)
            return (None, None)
        def on_finished(result):
            action_type = result[0]
            if action_type is None:
                return
            if action_type == 'remove_all':
                r = result[1]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_from_players').format(count=r.get('removed', 0), players=r.get('players_affected', 0)) if t else f"Removed {r.get('removed', 0)} items from {r.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.no_players_had_item') if t else 'No players had this item.')
            elif action_type == 'remove_pct':
                r, pct = result[1], result[2]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_pct_from_players').format(count=r.get('removed', 0), players=r.get('players_affected', 0), pct=int(pct)) if t else f"Removed {pct}% ({r.get('removed', 0)} items) from {r.get('players_affected', 0)} player(s).")
            elif action_type == 'add':
                r = result[1]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.add_complete') if t else 'Bulk Add Complete', t('player_item.added_to_players').format(count=r.get('added', 0), players=r.get('players_affected', 0)) if t else f"Added {r.get('added', 0)} items to {r.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.could_not_add') if t else 'Could not add items to any players.')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_add_all_effigies(self, player_uids):
        def task():
            from palworld_aio.managers.player_manager import max_all_abilities
            max_all_abilities(player_uids)
            return True
        def on_finished(_):
            self._show_info(t('inventory.max_all_abilities_done', default='Abilities maxed.'), t('inventory.max_all_abilities_done', default='Abilities maxed to maximum rank.'))
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_edit_abilities(self, player_uids, ability_values):
        def task():
            from palworld_aio.managers.player_manager import set_ability_values
            set_ability_values(player_uids, ability_values)
            return True
        def on_finished(_):
            self._show_info(t('inventory.edit_abilities_done', default='Abilities updated.'), t('inventory.edit_abilities_done', default='Ability values applied.'))
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_add_all_key_items(self, player_uids):
        from palworld_aio.inventory.inventory_manager import ItemData, PlayerInventory, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS, ASSET_TO_RELIC_TYPE
        from resource_resolver import resource_path
        import os, json
        all_items = ItemData.get_all_items()
        unlock_assets = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
        boss_map_path = resource_path(constants.get_base_path(), 'game_data', 'boss_mapping.json')
        try:
            boss_map = json.load(open(boss_map_path, encoding='utf-8')).get('boss_defeat_flag_map', {})
        except:
            boss_map = {}
        candidates = [i for i in all_items if i.get('type_a') == 'EPalItemTypeA::Essential' and (i['asset'] not in unlock_assets) and (i.get('sort_id', 0) != 9999) and (i.get('name', '') != i.get('asset', '')) and ('en_text' not in i.get('name', '').lower()) and (not i['asset'].startswith('BossDefeatReward_') or i['asset'] in boss_map)]
        effigy_accepted = False
        effigy_qty = 1
        if ASSET_TO_RELIC_TYPE:
            dlg = QInputDialog(self)
            dlg.setWindowTitle(t('inventory.effigy_add_qty_title', default='Effigy Quantity'))
            dlg.setLabelText(t('inventory.effigy_add_qty_prompt', default='How many of each effigy type to add?'))
            dlg.setIntValue(effigy_qty)
            dlg.setIntRange(1, constants.MAX_QUANTITY)
            dlg.setInputMode(QInputDialog.IntInput)
            if dlg.exec() == QDialog.Accepted:
                effigy_qty = dlg.intValue()
                effigy_accepted = True
        def task():
            nonlocal effigy_accepted, effigy_qty
            from palworld_aio.utils import gvasfile_to_sav
            from palworld_aio.inventory.dynamic_item import sync_dynamic_items_with_registry
            from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            container_lookup = {}
            for c in item_containers:
                cid = c.get('key', {}).get('ID', {}).get('value', '')
                if cid:
                    container_lookup[cid] = c
            total_missing = 0
            players_affected = 0
            for uid in player_uids:
                try:
                    inv = PlayerInventory(uid)
                    if not inv.load():
                        continue
                    key_container = inv.containers.get('key')
                    existing = {s.get('item_id', '') for s in (key_container.slots if key_container else []) if s.get('item_id', '')}
                    existing.update(inv._bounty_tokens.keys())
                    for asset, rtype in ASSET_TO_RELIC_TYPE.items():
                        if inv._effigies.get(rtype, 0) > 0:
                            existing.add(asset)
                    missing = [c['asset'] for c in candidates if c['asset'] not in existing]
                    for item_id in FOOD_POUCH_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    for item_id in ACCESSORY_UNLOCK_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    for item_id in WEAPON_UNLOCK_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    if effigy_accepted:
                        for rtype in set(ASSET_TO_RELIC_TYPE.values()):
                            inv.set_effigy_count(rtype, effigy_qty, _save=False)
                    if not missing:
                        if effigy_accepted:
                            inv._save_player_sav()
                            players_affected += 1
                        continue
                    key_container = inv.containers.get('key')
                    if key_container:
                        std_container = key_container._standardized_container
                        slots_needed = len(key_container.slots) + len(missing)
                        if slots_needed > std_container.max_slots:
                            new_max = slots_needed + 50
                            std_container.expand_capacity(new_max)
                            std_container.container_data['value']['SlotNum']['value'] = new_max
                        for item_id in missing:
                            std_container.add_item(item_id, 1)
                    for ctype, inventory_container in inv.containers.items():
                        cid = str(inventory_container.container_id)
                        if cid in container_lookup:
                            raw_slots = inventory_container._standardized_container.get_raw_slots()
                            container_lookup[cid]['value']['Slots']['value']['values'] = raw_slots
                    sync_dynamic_items_with_registry(inv.containers)
                    gvasfile_to_sav(inv.player_gvas, os.path.join(constants.current_save_path, 'Players', f"{str(uid).replace('-', '').upper()}.sav"))
                    total_missing += len(missing)
                    players_affected += 1
                except Exception as e:
                    print(f'Error processing key items for player {uid}: {e}')
                    continue
            if players_affected > 0:
                constants.invalidate_container_lookup()
            return (total_missing, players_affected)
        def on_finished(result):
            total_missing, players_affected = result
            if total_missing == 0:
                self._show_info(t('player_item.add_complete') if t else 'Add All Key Items', t('inventory.no_new_items') if t else 'All key items already present.')
            else:
                self._show_info(t('player_item.add_complete') if t else 'Bulk Add Complete', f'Added {total_missing} key items to {players_affected} player(s).')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_unlock_all_map(self, player_uids):
        def task():
            import json, os
            from palworld_aio.inventory.inventory_manager import PlayerInventory
            from palworld_aio.utils import gvasfile_to_sav, sav_to_gvasfile
            from boot_paths import ROOT_DIR
            ft_path = resource_path(str(ROOT_DIR), 'game_data', 'fast_travel_points.json')
            ft_data = json.load(open(ft_path, 'r'))
            ft_guids = sorted(ft_data.keys())
            players_affected = 0
            for uid in player_uids:
                try:
                    uid_clean = str(uid).replace('-', '').upper()
                    sav_path = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
                    existing = sav_to_gvasfile(sav_path) if os.path.exists(sav_path) else None
                    if existing:
                        eprops = existing.properties if hasattr(existing, 'properties') else existing.get('properties', {})
                        esave = eprops.get('SaveData', {}).get('value', {})
                        erecord = esave.get('RecordData', {}).get('value', {})
                        eft = erecord.get('FastTravelPointUnlockFlag', {})
                        eentries = eft.get('value', [])
                        eft_set = {e['key'] for e in eentries if e.get('value', False)}
                        if eft_set == set(ft_guids):
                            players_affected += 1
                            continue
                    inv = PlayerInventory(uid)
                    if not inv.load():
                        continue
                    gvas = inv.player_gvas
                    props = gvas.properties if hasattr(gvas, 'properties') else gvas.get('properties', {})
                    save_data = props.get('SaveData', {}).get('value', {})
                    if not save_data:
                        continue
                    record_data = save_data.setdefault('RecordData', {'value': {}, 'type': 'StructProperty'})['value']
                    ft_flag = record_data.setdefault('FastTravelPointUnlockFlag', {'key_type': 'NameProperty', 'value_type': 'BoolProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': [], 'type': 'MapProperty'})
                    ft_flag['value'] = [{'key': g, 'value': True} for g in ft_guids]
                    gvasfile_to_sav(gvas, os.path.join(constants.current_save_path, 'Players', f"{str(uid).replace('-', '').upper()}.sav"))
                    players_affected += 1
                except Exception as e:
                    print(f'Error unlocking map for player {uid}: {e}')
                    continue
            return players_affected
        def on_finished(players_affected):
            self._show_info(t('player_item.add_complete') if t else 'Unlock Complete', t('inventory.unlock_all_map_bulk_success.msg', count=players_affected, default=f'Unlocked fast travel for {players_affected} player(s).'))
        run_with_loading(on_finished, task)
    def _on_bulk_modify_slots(self, player_uids, new_count):
        def task():
            from palworld_aio.inventory.inventory_manager import PlayerInventory
            modified = 0
            for uid in player_uids:
                try:
                    inv = PlayerInventory(uid)
                    if not inv.load():
                        continue
                    if inv.set_max_slots(new_count):
                        modified += 1
                except Exception as e:
                    print(f'Error resizing slots for player {uid}: {e}')
                    continue
            return modified
        def on_finished(modified):
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
            self._show_info(t('player_item.modify_slots_title') if t else 'Modify Player Slots', t('player_item.modify_slots_done', count=modified, slots=new_count) if t else f'Resized {modified} player inventories to {new_count} slots')
        run_with_loading(on_finished, task)
    def _on_player_pal_action(self, item_id, action, player_uids):
        def task():
            from palworld_aio.editor.edit_pals import delete_pal_from_all, remove_skill_from_all_pals
            if action.startswith('delete_pal:'):
                pal_id = action.split(':')[1]
                result = delete_pal_from_all(pal_id)
                return ('delete_pal', result)
            elif action.startswith('remove_all:'):
                parts = action.split(':')
                active_skill_id = parts[1] if len(parts) > 1 and parts[1] else None
                passive_skill_id = parts[2] if len(parts) > 2 and parts[2] else None
                scope = parts[3] if len(parts) > 3 and parts[3] else 'all'
                result = remove_skill_from_all_pals(active_skill_id=active_skill_id, passive_skill_id=passive_skill_id, scope=scope)
                return ('remove_skill', result)
            return (None, None)
        def on_finished(result):
            action_type, r = result
            if action_type is None:
                return
            if action_type == 'delete_pal':
                if r and r.get('pals_removed', 0) > 0:
                    self._show_info(t('player_pal.remove_complete') if t else 'Bulk Pal Remove Complete', t('player_pal.pals_removed_everywhere').format(count=r.get('pals_removed', 0), affected=r.get('affected_count', 0)) if t else f"Removed {r.get('pals_removed', 0)} pals from {r.get('affected_count', 0)} players/bases everywhere.")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_pal') if t else 'No pals of that type were found.')
            elif action_type == 'remove_skill':
                if r and r.get('skills_removed', 0) > 0:
                    self._show_info(t('player_pal.skill_remove_complete') if t else 'Bulk Skill Remove Complete', t('player_pal.skill_removed_from_all').format(count=r.get('skills_removed', 0), pals=r.get('pals_affected', 0)) if t else f"Removed {r.get('skills_removed', 0)} skills from {r.get('pals_affected', 0)} pals (players + bases).")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_skill') if t else 'No pals had the selected skills.')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_player_selected(self, data):
        if data:
            workspace_context = self.__dict__.get('workspace_context')
            if workspace_context is not None:
                from palworld_aio.ui.workspace_context import ContextSelection
                player_id = str(data[4]) if len(data) > 4 else str(data[0])
                workspace_context.set_player(ContextSelection(player_id, str(data[0])))
                if len(data) > 6 and data[6]:
                    workspace_context.set_guild(
                        ContextSelection(str(data[6]), str(data[5])))
            else:
                self.app_bar.context.set_player(data[0])
                self.app_bar.context.set_guild(data[5])
            self._populate_players_inspector(data)

    def _on_player_record_selected(self, player):
        workspace_context = self.__dict__.get('workspace_context')
        if workspace_context is None:
            return
        from palworld_aio.ui.workspace_context import ContextSelection
        workspace_context.set_player(ContextSelection(player.uid, player.name))
        if player.guild_id:
            workspace_context.set_guild(ContextSelection(
                player.guild_id, player.guild_name))

    def _open_player_pal_editor(self, uid, name):
        from palworld_aio.ui.workspace_context import ContextSelection
        self._activate_contextual_nav(
            'pal_editor', player=ContextSelection(str(uid), str(name)))
        if 'pal_editor_tab' in self.__dict__:
            self.pal_editor_tab.select_player(uid, name, name)

    def _open_player_guild(self, guild_id):
        from palworld_aio.ui.workspace_context import ContextSelection
        guild_name = save_manager.get_guild_name_by_id(guild_id)
        guild = ContextSelection(str(guild_id), str(guild_name or guild_id))
        self._activate_contextual_nav('guilds', guild=guild)
        self.guilds_page.browser.search_input.setText(str(guild_id))

    def _populate_players_inspector(self, data):
        """uiux-audit-remediation 5.1: mirror the selected player row into
        the inspector (context wiring and data logic unchanged)."""
        inspector = getattr(self, '_players_inspector', None)
        if inspector is None:
            return
        if not data:
            inspector.show_empty(
                t('players.inspector_empty') if t else 'Select a player to view their details')
            return
        item = self.players_panel.get_selected_item()
        uid = str(item.toolTip(4)) if item is not None and item.toolTip(4) else str(data[4])
        guild_id = str(item.data(6, _PLAYER_GUILD_ID_ROLE)) if item is not None and item.data(6, _PLAYER_GUILD_ID_ROLE) else str(data[6])
        title = str(data[0])
        inspector.show_details(title, {
            0: str(data[2]),
            1: str(data[1]),
            2: str(data[3]),
            3: str(data[5]),
            4: '',
            5: uid,
            6: guild_id,
        })
    def _on_guild_selected(self, data):
        modern_page = self.__dict__.get('guilds_page')
        if modern_page is not None:
            guild = modern_page.selected_guild()
            if guild is not None:
                self._on_guild_record_selected(guild)
            return
        if data:
            workspace_context = self.__dict__.get('workspace_context')
            if workspace_context is not None:
                from palworld_aio.ui.workspace_context import ContextSelection
                workspace_context.set_guild(
                    ContextSelection(str(data[1]), str(data[0])))
            else:
                self.app_bar.context.set_guild(data[0])
            self._populate_guilds_inspector(data)
            self.guild_members_panel.clear()
            members = get_guild_members(data[1])
            for m in members:
                prefix = '[L]' if m['is_leader'] else ''
                last_sort = m.get('last_sort')
                rl = m.get('role_label', '')
                sort_keys = {1: last_sort if last_sort is not None else float('inf'), 2: int(m['level']) if str(m['level']).isdigit() else 0, 3: int(m['pals']) if str(m['pals']).isdigit() else 0, 5: m.get('role', 3)}
                self.guild_members_panel.add_item([prefix + m['name'], m['lastseen'], m['level'], m['pals'], m['uid'], rl], sort_keys=sort_keys)

    def _on_guild_record_selected(self, guild):
        from palworld_aio.ui.pages.guilds_page import GuildMemberRow
        from palworld_aio.ui.workspace_context import ContextSelection
        self.workspace_context.set_guild(ContextSelection(
            guild.guild_id, guild.name))
        members = []
        for member in get_guild_members(guild.guild_id):
            level = member.get('level', 0)
            pals = member.get('pals', 0)
            members.append(GuildMemberRow(
                uid=str(member.get('uid', '')),
                name=str(member.get('name', '')),
                role=str(member.get('role_label', '')),
                level=int(level) if str(level).isdigit() else 0,
                pals=int(pals) if str(pals).isdigit() else 0,
                last_seen=str(member.get('lastseen', '')),
                is_leader=bool(member.get('is_leader', False)),
                role_value=int(member.get('role', 3)),
                last_seen_sort=(
                    float(member['last_sort'])
                    if member.get('last_sort') is not None else None),
            ))
        self.guilds_page.set_members(guild.guild_id, tuple(members))

    def _on_guild_member_record_selected(self, member):
        from palworld_aio.ui.workspace_context import ContextSelection
        self.workspace_context.set_player(ContextSelection(
            member.uid, member.name))

    def _open_guild_players(self, guild):
        from palworld_aio.ui.workspace_context import ContextSelection
        selection = ContextSelection(guild.guild_id, guild.name)
        self._activate_contextual_nav('players', guild=selection)
        self.players_page.browser.search_input.setText(guild.guild_id)

    def _open_guild_bases(self, guild):
        from palworld_aio.ui.workspace_context import ContextSelection
        selection = ContextSelection(guild.guild_id, guild.name)
        self._activate_contextual_nav('bases', guild=selection)
        self.bases_page.browser.search_input.setText(guild.guild_id)

    def _populate_guilds_inspector(self, data):
        """uiux-audit-remediation 6.1: mirror the selected guild row into the
        inspector (context wiring and member population unchanged)."""
        inspector = getattr(self, '_guilds_inspector', None)
        if inspector is None:
            return
        if not data:
            inspector.show_empty(
                t('guilds.inspector_empty') if t else 'Select a guild to view its details')
            return
        item = self.guilds_panel.get_selected_item()
        guild_id = str(item.toolTip(1)) if item is not None and item.toolTip(1) else str(data[1])
        inspector.show_details(str(data[0]), {
            0: str(data[2]),
            1: str(data[3]),
            2: guild_id,
        })
    def _on_guild_member_selected(self, data):
        if data:
            name = data[0].replace('[L]', '')
            workspace_context = self.__dict__.get('workspace_context')
            if workspace_context is not None:
                from palworld_aio.ui.workspace_context import ContextSelection
                player_id = str(data[4]) if len(data) > 4 else name
                workspace_context.set_player(ContextSelection(player_id, name))
            else:
                self.app_bar.context.set_player(name)
    def _on_base_selected(self, data):
        if data:
            workspace_context = self.__dict__.get('workspace_context')
            if workspace_context is not None:
                from palworld_aio.ui.workspace_context import ContextSelection
                if len(data) > 2 and data[1]:
                    workspace_context.set_guild(
                        ContextSelection(str(data[1]), str(data[2])))
                workspace_context.set_base(
                    ContextSelection(str(data[0]), str(data[0])))
            else:
                self.app_bar.context.set_base(data[0])
                self.app_bar.context.set_guild(data[2])
            self._populate_bases_inspector(data)

    def _on_base_record_selected(self, base):
        from palworld_aio.ui.workspace_context import ContextSelection
        self.workspace_context.set_guild(ContextSelection(
            base.guild_id, base.guild_name))
        self.workspace_context.set_base(ContextSelection(
            base.base_id, base.name))

    def _open_base_record_inventory(self, base):
        from palworld_aio.ui.workspace_context import ContextSelection
        self._on_base_record_selected(base)
        self._activate_contextual_nav(
            'base_inventory',
            guild=ContextSelection(base.guild_id, base.guild_name),
            base=ContextSelection(base.base_id, base.name),
        )
        tab = getattr(self, 'base_inventory_tab', None)
        if tab is not None and hasattr(tab, 'select_guild'):
            tab.select_guild(base.guild_id)

    def _open_base_record_map(self, base):
        from palworld_aio.ui.workspace_context import ContextSelection
        self._on_base_record_selected(base)
        self._activate_contextual_nav(
            'map',
            guild=ContextSelection(base.guild_id, base.guild_name),
            base=ContextSelection(base.base_id, base.name),
        )
        self.map_tab.select_base(str(base.base_id))

    def _open_map_base(self, base):
        from palworld_aio.ui.workspace_context import ContextSelection
        base_id = str(base.get('base_id', ''))
        guild_id = str(base.get('guild_id', ''))
        guild_name = str(base.get('guild_name', '') or guild_id)
        context = {
            'base': ContextSelection(
                base_id,
                t('ui.map.base_number', number=base.get('base_position', 1))),
        }
        if guild_id:
            context['guild'] = ContextSelection(guild_id, guild_name)
        self._activate_contextual_nav('bases', **context)
        self.bases_page.browser.search_input.setText(base_id)

    def _open_map_player(self, player):
        from palworld_aio.ui.workspace_context import ContextSelection
        uid = str(player.get('player_uid', ''))
        name = str(player.get('player_name', '') or uid)
        context = {'player': ContextSelection(uid, name)}
        guild_id = str(player.get('guild_id', ''))
        if guild_id:
            guild_name = str(player.get('guild_name', '') or guild_id)
            context['guild'] = ContextSelection(guild_id, guild_name)
        self._activate_contextual_nav('players', **context)
        self.players_page.browser.search_input.setText(uid)

    def _open_map_guild(self, guild):
        from palworld_aio.ui.workspace_context import ContextSelection
        guild_id = str(guild.get('guild_id', ''))
        guild_name = str(guild.get('guild_name', '') or guild_id)
        self._activate_contextual_nav(
            'guilds', guild=ContextSelection(guild_id, guild_name))
        self.guilds_page.browser.search_input.setText(guild_id)

    def _open_base_record_guild(self, base):
        from palworld_aio.ui.workspace_context import ContextSelection
        self._on_base_record_selected(base)
        self._activate_contextual_nav(
            'guilds',
            guild=ContextSelection(base.guild_id, base.guild_name),
            base=ContextSelection(base.base_id, base.name),
        )
        self.guilds_page.browser.search_input.setText(base.guild_id)

    def _populate_bases_inspector(self, data):
        """uiux-audit-remediation 4.2: mirror the selected base row into the
        inspector (selection wiring and data logic unchanged)."""
        inspector = getattr(self, '_bases_inspector', None)
        if inspector is None:
            return
        if not data:
            inspector.show_empty(
                t('bases.inspector_empty') if t else 'Select a base to view its details')
            return
        item = self.bases_panel.get_selected_item()
        base_id = str(item.toolTip(0)) if item is not None and item.toolTip(0) else str(data[0])
        guild_id = str(item.toolTip(1)) if item is not None and item.toolTip(1) else str(data[1])
        # 1-based position of the base within its guild, from get_bases() order
        base_number = 0
        try:
            guild_bases = [b for b in get_bases() if str(b['guild_id']) == guild_id]
            base_number = next(
                (i + 1 for i, b in enumerate(guild_bases) if str(b['id']) == base_id), 0)
        except (TypeError, ValueError, KeyError):
            base_number = 0
        title = f'Base {base_number}' if base_number else (t('bases.inspector_title') if t else 'Base')
        inspector.show_details(title, {
            0: str(data[2]),
            1: str(data[3]),
            2: base_id,
            3: guild_id,
        })

    def _open_base_in_inventory(self):
        """uiux-audit-remediation 4.5: navigate to the Base Inventory page
        and target the selected base's guild there (guild-level targeting —
        the Base Inventory component's selection scope)."""
        bases_page = self.__dict__.get('bases_page')
        if bases_page is not None:
            base = bases_page.selected_base()
            if base is not None:
                self._open_base_record_inventory(base)
            return
        if not getattr(self, '_bases_inspector', None):
            return
        item = self.bases_panel.get_selected_item() if hasattr(self, 'bases_panel') else None
        if item is None:
            return
        guild_id = item.toolTip(1) or item.text(1)
        if not guild_id:
            return
        self._activate_nav('base_inventory')
        tab = getattr(self, 'base_inventory_tab', None)
        if tab is not None and hasattr(tab, 'select_guild'):
            tab.select_guild(guild_id)
    def closeEvent(self, event: QCloseEvent):
        if (constants.dirty and constants.current_save_path
                and self.user_settings.get('warn_unsaved_exit', True)):
            self._set_dirty(False)
            msg = QMessageBox(self)
            msg.setWindowTitle(t('error.unsaved_title', default='Unsaved Changes'))
            msg.setText(t('error.unsaved_msg', default='You have unsaved changes. Save before exiting?'))
            save_btn = msg.addButton(t('button.save', default='Save'), QMessageBox.AcceptRole)
            msg.addButton(t('button.dont_save', default="Don't Save"), QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton(t('button.cancel', default='Cancel'), QMessageBox.RejectRole)
            msg.setIcon(QMessageBox.Question)
            msg.setDefaultButton(cancel_btn)
            msg.exec()
            if msg.clickedButton() == save_btn:
                from PyQt6.QtCore import QEventLoop
                loop = QEventLoop()
                save_manager.save_finished.connect(loop.quit)
                save_manager.save_changes(parent=self)
                loop.exec()
                save_manager.save_finished.disconnect(loop.quit)
            elif msg.clickedButton() == cancel_btn:
                event.ignore()
                return
        if self.status_stream and self.status_stream.detach_window:
            try:
                self.user_settings['console_window_geometry'] = self.status_stream.detach_window.save_geometry()
                self._save_user_settings()
            except (RuntimeError, AttributeError):
                pass
        self._save_user_settings()
        boot_preference = self.user_settings.get('boot_preference', 'menu')
        if boot_preference == 'palworld_aio':
            QApplication.quit()
            event.accept()
        else:
            event.accept()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_drop_overlay'):
            self._drop_overlay.setGeometry(self.rect())
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    self._drop_overlay.setVisible(True)
                    self._drop_overlay.raise_()
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    event.acceptProposedAction()
                    return
        super().dragMoveEvent(event)
    def dragLeaveEvent(self, event):
        self._drop_overlay.setVisible(False)
        super().dragLeaveEvent(event)
    def dropEvent(self, event):
        self._drop_overlay.setVisible(False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    save_manager.load_save(path=file_path, parent=self)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)
    def _show_player_context_menu(self, pos):
        item = self.players_panel.tree.itemAt(pos)
        if not item:
            return
        uid = _item_value(item, 6)
        gid = _item_value(item, 7)
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('players', uid)))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('players', uid)))
        menu.add_action(self._create_action(t('deletion.ctx.delete_player'), lambda: self._delete_player(uid)))
        menu.add_action(self._create_action(t('player.rename.menu'), lambda: self._rename_player(uid, item.text(0))))
        menu.add_action(self._create_action(t('player.viewing_cage.menu'), lambda: self._unlock_viewing_cage(uid)))
        menu.add_action(self._create_action(t('player.reset_timestamp.menu') if t else 'Reset Timestamp', lambda: self._reset_player_timestamp(uid)))
        menu.add_action(self._create_action(t('player.unlock_technologies.menu') if t else 'Unlock All Technologies', lambda: self._unlock_all_technologies_for_player(uid)))
        menu.addSeparator()
        menu.add_action(self._create_action('Set Player Level' if not t else t('player.set_level'), lambda: self._set_player_level(uid)))
        menu.addSeparator()
        menu.add_action(self._create_action(t('guild.ctx.make_leader'), lambda: self._make_leader(gid, uid)))
        menu.add_action(self._create_action(t('deletion.ctx.delete_guild'), lambda: self._delete_guild(gid)))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(gid, item.text(3))))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(gid)))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(gid)))
        menu.add_action(self._create_action(t('button.import'), lambda: self._import_base_to_guild(gid)))
        menu.exec(self.players_panel.tree.viewport().mapToGlobal(pos))
    def _show_guild_context_menu(self, pos):
        item = self.guilds_panel.tree.itemAt(pos)
        if not item:
            return
        gid = _item_value(item, 4)
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('guilds', gid)))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('guilds', gid)))
        menu.add_action(self._create_action(t('deletion.ctx.delete_guild'), lambda: self._delete_guild(gid)))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(gid, item.text(0))))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(gid)))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(gid)))
        menu.add_sep()
        menu.add_action(self._create_action(t('base.export_guild'), lambda: self._export_bases_for_guild(gid)))
        menu.add_action(self._create_action(t('base.import_multi'), lambda: self._import_base_to_guild(gid)))
        menu.exec(self.guilds_panel.tree.viewport().mapToGlobal(pos))
    def _show_guild_member_context_menu(self, pos):
        item = self.guild_members_panel.tree.itemAt(pos)
        if not item:
            return
        guild_data = self.guilds_panel.get_selected_data()
        if not guild_data:
            return
        gid = str(guild_data[5])
        member_uid = _item_value(item, 5)
        member_record = self.guilds_page.selected_member()
        member_name = member_record.name if member_record is not None else item.text(0)
        role = None
        for pdata in (get_guild_members(gid) or []):
            if str(pdata.get('uid', '')).replace('-', '').lower() == str(member_uid).replace('-', '').lower():
                role = pdata.get('role', 3)
                break
        menu = ScrollableContextMenu(self)
        menu.add_label(t('guild.menu.set_role') if t else 'Set Role')
        for rv, rl in [(1, 'guild_master'), (2, 'submaster'), (3, 'member'), (4, 'guest')]:
            rkey = f'guild.role.{rl}'
            label = t(rkey) if t else rl.replace('_', ' ').title()
            chk = '✓ ' if rv == role else '  '
            menu.add_item(f'role_{rv}', f'{chk}{label}')
        menu.add_sep()
        menu.add_action(self._create_action(t('guild.ctx.make_leader'), lambda: self._make_leader(gid, member_uid)))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(gid)))
        menu.add_sep()
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('players', member_uid)))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('players', member_uid)))
        menu.add_action(self._create_action(t('deletion.ctx.delete_player'), lambda: self._delete_player(member_uid)))
        menu.add_action(self._create_action(t('player.rename.menu'), lambda: self._rename_player(member_uid, member_name)))
        menu.add_action(self._create_action(t('player.reset_timestamp.menu') if t else 'Reset Timestamp', lambda: self._reset_player_timestamp(member_uid)))
        menu.add_sep()
        menu.add_action(self._create_action('Set Player Level' if not t else t('player.set_level'), lambda: self._set_player_level(member_uid)))
        result = menu.exec(self.guild_members_panel.tree.viewport().mapToGlobal(pos))
        if result and result.startswith('role_'):
            role_val = int(result.split('_')[1])
            self._set_guild_member_role(gid, member_uid, role_val)
    def _show_base_context_menu(self, pos):
        item = self.bases_panel.tree.itemAt(pos)
        if not item:
            return
        bid = _item_value(item, 5)
        bgid = _item_value(item, 7)
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('bases', bid)))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('bases', bid)))
        menu.add_action(self._create_action(t('deletion.ctx.delete_base'), lambda: self._delete_base(bid, bgid)))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(bgid, item.text(1))))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(bgid)))
        menu.add_action(self._create_action(t('export.base'), lambda: self._export_base(bid)))
        menu.add_action(self._create_action(t('base.radius.menu') if t else 'Adjust Radius', lambda: self._adjust_base_radius(bid)))
        menu.add_action(self._create_action(t('import.base'), lambda: self._import_base(bgid)))
        menu.add_action(self._create_action(t('clone.base'), lambda: self._clone_base(bid, bgid)))
        menu.add_action(self._create_action(t('base.palbox_nudge') if t else 'Nudge Palbox', lambda: self._nudge_palbox(bid)))
        menu.exec(self.bases_panel.tree.viewport().mapToGlobal(pos))
    def _show_exclusion_context_menu(self, pos, excl_type):
        panel = getattr(self, f'excl_{excl_type}_panel')
        item = panel.tree.itemAt(pos)
        if not item:
            return
        val = item.text(0)
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda v=val: self._remove_exclusion(excl_type, v)))
        menu.exec(panel.tree.viewport().mapToGlobal(pos))
    def _load_save(self):
        save_manager.load_save(parent=self)
    def _load_save_folder(self):
        from common import get_preferred_save_path
        folder = QFileDialog.getExistingDirectory(
            self,
            t('ui.overview.open_folder') if t else 'Open Save Folder',
            get_preferred_save_path(),
        )
        if not folder:
            return
        level_path = os.path.join(folder, 'Level.sav')
        players_path = os.path.join(folder, 'Players')
        if not os.path.isfile(level_path) or not os.path.isdir(players_path):
            self._show_warning(
                t('error.title') if t else 'Invalid save folder',
                t('ui.overview.invalid_folder', default=(
                    'Choose a save folder containing Level.sav and a Players folder.')),
            )
            return
        save_manager.load_save(path=level_path, parent=self)
    def _load_recent_save(self, path):
        from pathlib import Path
        candidate = Path(path)
        level_path = candidate if candidate.name.lower() == 'level.sav' else candidate / 'Level.sav'
        if not level_path.is_file() or not (level_path.parent / 'Players').is_dir():
            self._show_no_save_overview()
            return
        save_manager.load_save(path=str(level_path), parent=self)
    def _locate_recent_save(self, save_id):
        from common import get_preferred_save_path
        level_path, _selected = QFileDialog.getOpenFileName(
            self,
            t('ui.overview.locate') if t else 'Locate Save',
            get_preferred_save_path(),
            'Level.sav (Level.sav)',
        )
        if not level_path:
            return
        folder = os.path.dirname(level_path)
        if not os.path.isdir(os.path.join(folder, 'Players')):
            self._show_warning(
                t('error.title') if t else 'Invalid save folder',
                t('ui.overview.invalid_folder', default=(
                    'Choose a save folder containing Level.sav and a Players folder.')),
            )
            return
        self.workspace_settings.relocate_recent_save(save_id, folder)
        self._show_no_save_overview()
        self._save_user_settings()
    def _remove_recent_save(self, save_id):
        if self.workspace_settings.remove_recent_save(save_id):
            self._show_no_save_overview()
            self._save_user_settings()
    def _launch_overview_utility(self, tool_id):
        self._activate_nav('tools')
        self._launch_registered_tool(tool_id)
    def _launch_registered_tool(self, tool_id):
        from palworld_aio.ui.tool_registry import TOOLS
        try:
            tool = TOOLS.resolve(tool_id)
        except KeyError:
            return
        self._ensure_tab(0)
        tool.launch(self.tools_tab)
        from palworld_aio.ui.operation_journal import (
            ActivityKind, ActivityStatus,
        )
        self._record_activity(
            ActivityKind.TOOL,
            t(tool.title_key, default=tool.tool_id.replace('_', ' ').title()),
            status=ActivityStatus.INFO,
            detail=t('ui.activity.tool_opened', default='Tool opened'),
        )
    def _resolve_tool_prerequisite(self, context_kind):
        routes = {
            'player': 'players',
            'guild': 'guilds',
            'base': 'bases',
            'container': 'base_inventory',
        }
        if context_kind == 'save':
            self._load_save()
            return
        route = routes.get(context_kind)
        if route is not None:
            self._activate_nav(route)
    def _load_xgp_save(self):
        from palworld_xgp_import.gamepass_manager import pick_xgp_world
        pick = pick_xgp_world(self, 'Load GamePass Save')
        if not pick:
            return
        cpath, save_id, _ = pick
        save_manager.load_xgp_save(cpath, save_id, parent=self)
    def _load_backup_save(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
        from resource_resolver import get_data_base
        from loading_manager import show_warning
        from palworld_aio.utils import sav_to_gvasfile
        backup_dir = os.path.abspath(os.path.join(get_data_base(), 'Backups', 'AllinOneTools'))
        if not os.path.isdir(backup_dir):
            show_warning(self, t('error.title'), t('backup.no_backups'))
            return
        items = []
        for name in sorted(os.listdir(backup_dir), reverse=True):
            if not name.startswith('PalworldSave_backup_'):
                continue
            folder = os.path.join(backup_dir, name)
            if not os.path.isfile(os.path.join(folder, 'Level.sav')) or not os.path.isdir(os.path.join(folder, 'Players')):
                continue
            ts_raw = name.replace('PalworldSave_backup_', '')
            ts = f'{ts_raw[:4]}-{ts_raw[4:6]}-{ts_raw[6:8]} {ts_raw[9:11]}:{ts_raw[11:13]}:{ts_raw[13:]}'
            world = 'Unknown World'
            meta_path = os.path.join(folder, 'LevelMeta.sav')
            if os.path.isfile(meta_path):
                try:
                    mg = sav_to_gvasfile(meta_path)
                    world = mg.properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'Unknown World')
                except Exception:
                    pass
            player_count = len([f for f in os.listdir(os.path.join(folder, 'Players')) if f.endswith('.sav')])
            items.append((name, ts, world, player_count))
        if not items:
            show_warning(self, t('error.title'), t('backup.no_backups'))
            return
        dlg = BaseDialog(
            t('menu.file.load_backup'), self, min_size=(600, 300),
            kicker=t('ui.backups.kicker', default='Backups'))
        layout = dlg.content_layout
        lst = QListWidget()
        lst.setSpacing(2)
        item_height = 24
        max_visible = 8
        lst.setMinimumHeight(item_height * min(len(items), max_visible) + 10)
        lst.setMaximumHeight(item_height * max_visible + 10)
        for name, ts, world, pcount in items:
            lst.addItem(f'{ts} — {world} ({pcount} players)')
        layout.addWidget(lst)
        ok_btn = dlg.add_confirm_button(t('common.ok'))
        ok_btn.setEnabled(False)
        dlg.cancel_btn.setText(t('common.cancel'))
        lst.itemClicked.connect(lambda: ok_btn.setEnabled(True))
        lst.itemDoubleClicked.connect(lambda: dlg.accept() if lst.currentItem() else None)
        if dlg.exec() != QDialog.Accepted or not lst.currentItem():
            return
        idx = lst.currentRow()
        name = items[idx][0]
        backup_path = os.path.join(backup_dir, name)
        level_path = os.path.join(backup_path, 'Level.sav')
        save_manager.load_save(level_path, parent=self)
    def _restart_program(self):
        import sys
        python = sys.executable
        os.execl(python, python, *sys.argv)
    def _save_changes(self):
        if not constants.loaded_level_json:
            self._show_warning(t('error.title'), t('guild.rebuild.no_save'))
            return
        self._sync_dirty_from_runtime()
        context = self.__dict__.get('workspace_context')
        if (context is not None
                and context.snapshot.save_state.value == 'read_only'):
            self._show_warning(
                t('error.title', default='Cannot save'),
                t('ui.save.read_only_message',
                  default='This save is read only. Choose a writable copy before saving.'))
            return
        save_manager.save_changes(parent=self)
    def _rename_world(self):
        from ..utils import sav_to_gvasfile, gvasfile_to_sav
        if not constants.current_save_path:
            return
        meta_path = os.path.join(constants.current_save_path, 'LevelMeta.sav')
        if not os.path.exists(meta_path):
            return
        meta_gvas = sav_to_gvasfile(meta_path)
        old = meta_gvas.properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'Unknown World')
        new_name = InputDialog.get_text(t('world.rename.title'), t('world.rename.prompt', old=old), self)
        if new_name:
            meta_gvas.properties['SaveData']['value']['WorldName']['value'] = new_name
            gvasfile_to_sav(meta_gvas, meta_path)
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('success.title'))
            msg_box.setText(t('world.rename.done'))
            msg_box.exec()
    def _edit_game_days(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        result = edit_game_days(self)
        if result:
            self.refresh_all()
            self._show_info(t('Done'), t('gamedays.success', old=result['old'], new=result['new']))
    def _load_gps(self):
        box = self._create_message_box(QMessageBox.Question)
        box.setWindowTitle(t('menu.file.load_gps') if t else 'Load Global Pal Storage')
        box.setText(t('menu.file.load_gps.select_source_msg') if t else "Which platform's Global Pal Storage do you want to load?")
        gp_btn = box.addButton(t('menu.file.load_gps.btn_gamepass') if t else 'GamePass', QMessageBox.AcceptRole)
        st_btn = box.addButton(t('menu.file.load_gps.btn_steam') if t else 'Steam', QMessageBox.AcceptRole)
        box.addButton(t('Cancel'), QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is gp_btn:
            self._load_gps_gamepass()
        elif clicked is st_btn:
            self._load_gps_steam()
    def _load_gps_gamepass(self):
        from palworld_aio import constants
        from palworld_xgp_import.gamepass_manager import load_gamepass_gps, GamepassGpsUnavailable
        try:
            res = load_gamepass_gps()
        except GamepassGpsUnavailable:
            self._show_warning(
                t('menu.file.load_gps.gamepass_sync_held_title') if t else 'GamePass GPS Unavailable',
                t('menu.file.load_gps.gamepass_sync_held_msg') if t else 'The Game Pass Global Pal Storage container is currently empty on this PC - cloud sync may be holding it.\n\nLaunch Palworld (Game Pass version) once so sync restores the container, then try again.')
            return
        if not res:
            self._show_warning(
                t('menu.file.load_gps.gamepass_not_found_title') if t else 'GamePass GPS Not Found',
                t('menu.file.load_gps.gamepass_not_found_msg') if t else 'No Global Pal Storage was found for Game Pass on this PC.\n\nPlay Palworld (Game Pass version) and interact with a Global Pal Storage first, then try again.')
            return
        path, cpath = res
        ok = save_manager.load_gps(path, parent=self)
        if not ok:
            return
        constants.gps_xgp_container_path = cpath
        from palworld_aio.editor.gps_editor import GpsEditorDialog
        dlg = GpsEditorDialog(self)
        dlg.exec()
    def _load_gps_steam(self):
        from palworld_aio import constants
        from common import get_preferred_save_path
        path, _ = QFileDialog.getOpenFileName(self, t('menu.file.load_gps') if t else 'Load Global Pal Storage', get_preferred_save_path(), 'GlobalPalStorage.sav (GlobalPalStorage.sav)')
        if not path:
            return
        if not os.path.basename(path).startswith('GlobalPalStorage'):
            self._show_warning(t('error.title') if t else 'Error', 'Please select a GlobalPalStorage.sav file')
            return
        constants.gps_xgp_container_path = None
        ok = save_manager.load_gps(path, parent=self)
        if ok:
            from palworld_aio.editor.gps_editor import GpsEditorDialog
            dlg = GpsEditorDialog(self)
            dlg.exec()

    def _load_worldoption(self):
        from ..utils import sav_to_json
        from common import get_preferred_save_path
        sav_path, _ = QFileDialog.getOpenFileName(self, t('menu.file.load_worldoption') if t else 'Load WorldOption', get_preferred_save_path(), 'WorldOption.sav (WorldOption.sav)')
        if not sav_path:
            return
        if not os.path.basename(sav_path).startswith('WorldOption'):
            self._show_warning(t('error.title') if t else 'Error', 'Please select a WorldOption.sav file')
            return
        try:
            json_data = sav_to_json(sav_path)
            if 'properties' not in json_data or 'OptionWorldData' not in json_data.get('properties', {}):
                self._show_warning(t('error.title') if t else 'Error', 'Invalid WorldOption.sav structure')
                return
            from palworld_aio.editor.worldoption_editor import edit_worldoption_settings
            result = edit_worldoption_settings(json_data, sav_path, self)
            if result:
                self._show_info(t('success.title') if t else 'Success', f'WorldOption settings saved successfully!\n\nLocation: {sav_path}')
        except Exception as e:
            self._show_error(t('error.title') if t else 'Error', f'Failed to load WorldOption.sav:\n{str(e)}')
    def _delete_empty_guilds(self):
        if not constants.loaded_level_json:
            msg_box = self._create_message_box(QMessageBox.Warning)
            msg_box.setWindowTitle(t('error.title') if t else 'Error')
            msg_box.setText(t('error.no_save_loaded') if t else 'No save file loaded.')
            msg_box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
            msg_box.exec()
            return
        def task():
            return delete_empty_guilds(self)
        def on_finished(removed):
            if removed > 0:
                constants.invalidate_container_lookup()
                if 'base_inventory_tab' in self.__dict__:
                    self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('Done'))
            msg_box.setText(t('deletion.empty_guilds_removed', count=removed))
            msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
            msg_box.exec()
        run_with_loading(on_finished, task)
    def _delete_inactive_bases(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        params = InactiveFilterDialog.get_filter(self)
        if params:
            def task():
                return delete_inactive_bases(params, self)
            def on_finished(result):
                if result['count'] > 0:
                    constants.invalidate_container_lookup()
                    if 'base_inventory_tab' in self.__dict__:
                        self.base_inventory_tab.manager.invalidate_cache()
                self.refresh_all()
                if result['details']:
                    from resource_resolver import get_data_base
                    log_dir = os.path.join(get_data_base(), 'Logs', 'DeleteInactive')
                    os.makedirs(log_dir, exist_ok=True)
                    log_path = os.path.join(log_dir, 'inactive_bases.log')
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(result['details']))
                self._show_info(t('Done'), t('inactive_bases_deleted', count=result['count']))
            run_with_loading(on_finished, task)
    def _delete_duplicate_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_duplicated_players(self)
        def on_finished(removed):
            if removed > 0:
                constants.invalidate_container_lookup()
                if 'base_inventory_tab' in self.__dict__:
                    self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.duplicates_removed', count=removed))
        run_with_loading(on_finished, task)
    def _delete_inactive_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        params = InactiveFilterDialog.get_filter(self)
        if params:
            def task():
                return delete_inactive_players(params, self)
            def on_finished(result):
                self.refresh_all()
                if result['details']:
                    from resource_resolver import get_data_base
                    log_dir = os.path.join(get_data_base(), 'Logs', 'DeleteInactive')
                    os.makedirs(log_dir, exist_ok=True)
                    log_path = os.path.join(log_dir, 'inactive_players.log')
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(result['details']))
                self._show_info(t('Done'), t('deletion.inactive_players_removed', count=result['count']))
            run_with_loading(on_finished, task)
    def _delete_unreferenced(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_unreferenced_data(self)
        def on_finished(result):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.unreferenced_result',
                                        characters=result.get('characters', 0),
                                        pals=result.get('pals', 0),
                                        guilds=result.get('guilds', 0),
                                        broken_objects=result.get('broken_objects', 0),
                                        dropped_items=result.get('dropped_items', 0),
                                        treasure_dupes=result.get('treasure_dupes', 0),
                                        orphaned_containers=result.get('orphaned_containers', 0)))
        run_with_loading(on_finished, task)
    def _delete_non_base_map_objs(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_non_base_map_objects(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.non_base_objs_removed', count=removed))
        run_with_loading(on_finished, task)
    def _delete_all_skins(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_all_skins(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.skins_removed', count=removed))
        run_with_loading(on_finished, task)
    def _unlock_private_chests(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return unlock_all_private_chests(self)
        def on_finished(unlocked):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.chests_unlocked', count=unlocked))
        run_with_loading(on_finished, task)
    def _run_loaded_save_repair(
        self,
        *,
        title,
        affected,
        review,
        operation,
        result_message,
        risk='',
        confirm_text='',
    ):
        """Review and run a loaded-save repair with a durable recovery result."""
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return None
        dialog = RepairWorkflowDialog(
            loaded_save_repair_spec(
                title,
                affected,
                review,
                risk=risk,
                confirm_text=confirm_text,
            ),
            operation,
            result_message,
            self,
        )

        def on_completed(result):
            self.refresh_all()
            from palworld_aio.ui.operation_journal import ActivityKind
            dialog_text = result_message(result)
            self._record_activity(
                ActivityKind.MUTATION,
                title,
                detail=dialog_text,
            )

        dialog.completed.connect(on_completed)
        dialog.exec()
        return dialog
    def _run_transfer_workflow(
        self,
        *,
        title,
        source,
        target,
        review,
        operation,
        result_message,
        backup='',
        risk='',
        confirm_text='',
        result_success=None,
        on_completed=None,
    ):
        """Run a contextual import/export/clone callback behind shared review."""
        dialog = TransferWorkflowDialog(
            TransferWorkflowSpec(
                title=title,
                source=source,
                target=target,
                review=review,
                backup=backup,
                risk=risk,
                confirm_text=confirm_text,
            ),
            operation,
            result_message,
            self,
            result_success=result_success,
        )
        if on_completed is not None:
            dialog.completed.connect(on_completed)
        dialog.exec()
        return dialog
    def _remove_invalid_items(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.delete_invalid_items'),
            affected=t(
                'repair.affected.invalid_items',
                default='Invalid item references across the loaded save'),
            review=t(
                'repair.review.invalid_items',
                default='Remove only item records that fail the existing validity checks.'),
            operation=lambda: remove_invalid_items_from_save(self),
            result_message=lambda fixed: t('fixed_files', fixed=fixed),
        )
    def _remove_invalid_structures(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.delete_invalid_structures'),
            affected=t(
                'repair.affected.invalid_structures',
                default='Invalid structure map objects in the loaded world'),
            review=t(
                'repair.review.invalid_structures',
                default='Remove only structures rejected by the existing map-object validity checks.'),
            risk=t(
                'repair.risk.removal',
                default='Records identified as invalid will be removed from the in-memory save.'),
            operation=lambda: delete_invalid_structure_map_objects(self),
            result_message=lambda removed: t(
                'invalid_structures_removed', removed=removed),
            confirm_text=t('repair.workflow.remove', default='Remove invalid data'),
        )
    def _repair_structures(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_structures'),
            affected=t(
                'repair.affected.structures',
                default='All repairable structures in the loaded world'),
            review=t(
                'repair.review.structures',
                default='Restore structure durability using the existing structure repair rules.'),
            operation=lambda: repair_structures(self),
            result_message=lambda result: t(
                'deletion.structures_repaired',
                repaired=result['repaired'], skipped=result['skipped']),
        )
    def _repair_items(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_items'),
            affected=t(
                'repair.affected.items',
                default='All repairable item durability records in the loaded save'),
            review=t(
                'repair.review.items',
                default='Restore item durability using the existing item repair rules.'),
            operation=lambda: repair_items(self),
            result_message=lambda result: t(
                'deletion.items_repaired', repaired=result['repaired']),
        )
    def _remove_invalid_pals(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.delete_invalid_pals'),
            affected=t(
                'repair.affected.invalid_pals',
                default='Invalid Pal records across all owners and containers'),
            review=t(
                'repair.review.invalid_pals',
                default='Remove only Pal records rejected by the existing save validity checks.'),
            risk=t(
                'repair.risk.removal',
                default='Records identified as invalid will be removed from the in-memory save.'),
            operation=lambda: remove_invalid_pals_from_save(self),
            result_message=lambda removed: t('palclean.summary', removed=removed),
            confirm_text=t('repair.workflow.remove', default='Remove invalid data'),
        )
    def _delete_imported_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        reply = show_question(self, t('deletion.delete_imported_pals.title') if t else 'Delete Imported Pals', t('deletion.delete_imported_pals.confirm') if t else 'Delete ALL imported pals (DNA) from every player\'s party, palbox, DPS storage, and all base workers? This cannot be undone. Continue?')
        if not reply:
            return
        def task():
            return delete_imported_pals(self)
        def on_finished(removed):
            if removed > 0:
                constants.invalidate_container_lookup()
                if 'base_inventory_tab' in self.__dict__:
                    self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.imported_pals_removed', count=removed))
        run_with_loading(on_finished, task)
    def _remove_invalid_passives(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.delete_invalid_passives'),
            affected=t(
                'repair.affected.invalid_passives',
                default='Invalid passive-skill references on Pals'),
            review=t(
                'repair.review.invalid_passives',
                default='Remove passive skills rejected by the existing skill validity checks.'),
            operation=lambda: remove_invalid_passives_from_save(self),
            result_message=lambda removed: t(
                'deletion.invalid_passives_removed', count=removed),
        )
    def _fix_all_pals(self):
        return self._run_loaded_save_repair(
            title=t('func_manager.fix_all_pals.title'),
            affected=t(
                'repair.affected.all_pals', default='Every Pal in the loaded save'),
            review=t('func_manager.fix_all_pals.confirm'),
            operation=lambda: fix_all_pals_combined(self),
            result_message=lambda count: t(
                'func_manager.fix_all_pals.success', count=count),
        )
    def _max_all_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.editor.pal_editor.legacy_frame import PalFrame
        cheat_q = show_question(self, t('func_manager.max_all_pals.title') if t else 'Max All Pals', t('func_manager.max_all_pals.cheat_ask') if t else 'Use extreme 255 caps?')
        PalFrame._cheat_mode = cheat_q
        msg = t('func_manager.max_all_pals.confirm_cheat') if cheat_q else (t('func_manager.max_all_pals.confirm') if t else 'This will max all stats (level 80, IVs 100, souls 20, rank 5) for all pals. Continue?')
        reply = show_question(self, t('func_manager.max_all_pals.title') if t else 'Max All Pals', msg)
        if not reply:
            PalFrame._cheat_mode = False
            return
        def task():
            return max_all_pals(self)
        def on_finished(count):
            PalFrame._cheat_mode = False
            self._show_info(t('func_manager.max_all_pals.title') if t else 'Max All Pals', t('func_manager.max_all_pals.success', count=count) if t else f'Maxed {count} pals.')
            QTimer.singleShot(0, self.refresh_all)
        run_with_loading(on_finished, task)
    def _fix_illegal_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.ui.dialogs.fix_illegal_pal_dialog import FixIllegalPalDialog
        def scan_task():
            return scan_illegal_pals_by_owner()
        def on_scan_done(scan_data):
            if not scan_data:
                self._show_info(t('fix_illegal_pal.no_illegals_title') if t else 'No Illegal Pals', t('fix_illegal_pal.no_illegals_msg') if t else 'No illegal pals found in the save.')
                return
            dlg = FixIllegalPalDialog(scan_data, self)
            def start_fix(selected_uids):
                def fix_task():
                    return fix_illegal_pals_in_save(
                        self, selected_uids=selected_uids)
                def on_fix_done(fixed):
                    self.refresh_all()
                    dlg.finish_repair(t(
                        'deletion.illegal_pals_fixed', count=fixed))
                def on_fix_error(error):
                    dlg.fail_repair(str(error))
                run_with_loading(
                    on_fix_done, fix_task, parent=dlg,
                    on_error=on_fix_error, local_state=True)
            dlg.repair_requested.connect(start_fix)
            dlg.exec()
        run_with_loading(on_scan_done, scan_task)
    def _fix_illegal_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.ui.dialogs.fix_illegal_player_dialog import FixIllegalPlayerDialog
        def scan_task():
            return scan_illegal_players_by_stats()
        def on_scan_done(scan_data):
            if not scan_data:
                self._show_info(t('fix_illegal_player.no_illegals_title') if t else 'No Illegal Players', t('fix_illegal_player.no_illegals_msg') if t else 'No players with illegal stats found in the save.')
                return
            dlg = FixIllegalPlayerDialog(scan_data, self)
            def start_fix(selected_uids):
                def fix_task():
                    return fix_illegal_player_stats(
                        self, selected_uids=selected_uids)
                def on_fix_done(fixed):
                    self.refresh_all()
                    dlg.finish_repair(t(
                        'deletion.illegal_players_fixed', count=fixed))
                def on_fix_error(error):
                    dlg.fail_repair(str(error))
                run_with_loading(
                    on_fix_done, fix_task, parent=dlg,
                    on_error=on_fix_error, local_state=True)
            dlg.fix_requested.connect(start_fix)
            dlg.exec()
        run_with_loading(on_scan_done, scan_task)
    def _reset_missions(self):
        return self._run_loaded_save_repair(
            title=t('missions.reset_title'),
            affected=t(
                'repair.affected.missions',
                default='Mission state for every player in the loaded save'),
            review=t(
                'repair.review.missions',
                default='Reset mission state using the existing mission repair rules.'),
            operation=lambda: fix_missions(self),
            result_message=lambda result: t('missions.summary', **result),
        )
    def _reset_anti_air(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_anti_air'),
            affected=t(
                'repair.affected.anti_air',
                default='All anti-air turret reset state in the loaded world'),
            review=t(
                'repair.review.anti_air',
                default='Reset anti-air turret state using the existing manager action.'),
            operation=lambda: reset_anti_air_turrets(self),
            result_message=lambda _count: t('anti_air_reset_all'),
        )
    def _reset_dungeons(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_dungeons'),
            affected=t(
                'repair.affected.dungeons',
                default='All dungeon reset state in the loaded world'),
            review=t(
                'repair.review.dungeons',
                default='Reset dungeon state using the existing manager action.'),
            operation=lambda: reset_dungeons(self),
            result_message=lambda count: t('dungeons_reset_count', count=count),
        )
    def _reset_oilrig(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_oilrig'),
            affected=t(
                'repair.affected.oilrig',
                default='All oil-rig reset state in the loaded world'),
            review=t(
                'repair.review.oilrig',
                default='Reset oil-rig state using the existing manager action.'),
            operation=lambda: reset_oilrig(self),
            result_message=lambda count: t('oilrig_reset_count', count=count),
        )
    def _reset_invader(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_invader'),
            affected=t(
                'repair.affected.invaders',
                default='All invader-event reset state in the loaded world'),
            review=t(
                'repair.review.invaders',
                default='Reset invader-event state using the existing manager action.'),
            operation=lambda: reset_invader(self),
            result_message=lambda count: t('invader_reset_count', count=count),
        )
    def _reset_supply(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_supply'),
            affected=t(
                'repair.affected.supply',
                default='All supply-drop reset state in the loaded world'),
            review=t(
                'repair.review.supply',
                default='Reset supply-drop state using the existing manager action.'),
            operation=lambda: reset_supply(self),
            result_message=lambda count: t('supply_reset_count', count=count),
        )
    def _reset_lock_gimmick(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.reset_lock_gimmick'),
            affected=t(
                'repair.affected.lock_gimmick',
                default='All mini-game tower reset state in the loaded world'),
            review=t(
                'repair.review.lock_gimmick',
                default='Reset mini-game tower state using the existing manager action.'),
            operation=lambda: reset_lock_gimmick(self),
            result_message=lambda count: t(
                'lock_gimmick_reset_count', count=count),
        )
    def _fix_invalid_active_skills(self):
        def result_message(result):
            removed = result.get('removed', 0)
            pals = len(result.get('details', []))
            log_path = result.get('log_path')
            msg = t('deletion.invalid_active_skills_fixed', count=removed, pals=pals) if t else f'Removed {removed} invalid skills from {pals} pals'
            if log_path:
                msg += f'\n\nReport saved to:\n{log_path}'
            return msg
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_invalid_active_skills'),
            affected=t(
                'repair.affected.active_skills',
                default='Invalid active-skill references on every Pal'),
            review=t(
                'repair.review.active_skills',
                default='Remove active skills that the existing legality rules reject.'),
            operation=lambda: fix_invalid_pal_active_skills(self),
            result_message=result_message,
        )
    def _fix_all_timestamps(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_timestamps'),
            affected=t(
                'repair.affected.timestamps',
                default='Every player with a negative last-seen timestamp'),
            review=t(
                'repair.review.timestamps',
                default='Normalize only negative player timestamps using the existing repair action.'),
            operation=lambda: fix_all_negative_timestamps(self),
            result_message=lambda fixed: t(
                'timestamps.fixed_count', count=fixed),
        )
    def _reset_player_timestamp(self, uid):
        return self._run_loaded_save_repair(
            title=t('player.reset_timestamp.menu'),
            affected=t(
                'repair.affected.player_timestamp',
                default='Selected player: {uid}', uid=_short_guid(uid)),
            review=t(
                'repair.review.player_timestamp',
                default='Reset this player timestamp to the current time.'),
            operation=lambda: require_repair_success(
                lambda: reset_selected_player_timestamp(uid, self),
                t('timestamps.reset_failed')),
            result_message=lambda _success: t('timestamps.player_reset'),
        )
    def _open_paldefender(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        dialog = PalDefenderDialog(self)
        dialog.exec()
    def _rebuild_all_guilds(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_all_guilds'),
            affected=t(
                'repair.affected.guilds',
                default='Every guild and its membership links'),
            review=t(
                'repair.review.guilds',
                default='Rebuild guild relationships using the existing guild manager action.'),
            operation=lambda: require_repair_success(
                rebuild_all_guilds, t('guild.rebuild.failed')),
            result_message=lambda _success: t('guild.rebuild.done'),
        )
    def _open_guild_assign_dialog(self, selected_player_uids=()):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        dlg = GuildAssignDialog(
            self, selected_player_uids=selected_player_uids)
        dlg.exec()
        constants.invalidate_container_lookup()
        if 'base_inventory_tab' in self.__dict__:
            self.base_inventory_tab.manager.invalidate_cache()
        QTimer.singleShot(0, self.refresh_all)

    def _show_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        if 'map_tab' not in self.__dict__:
            return
        self._activate_nav('map')
    def _generate_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        def task():
            world_path = generate_world_map(map_type='world')
            tree_path = generate_world_map(map_type='tree')
            return (world_path, tree_path)
        def on_finished(paths):
            world_path, tree_path = paths
            paths_generated = [p for p in (world_path, tree_path) if p]
            if paths_generated:
                from common import open_file_with_default_app
                open_file_with_default_app(paths_generated[0])
                msg_text = '\n'.join(paths_generated)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(t('Done') if t else 'Done')
                msg_box.setText(t('map_saved', path=msg_text) if t else f'Map saved to:\n{msg_text}')
                msg_box.setIcon(QMessageBox.Information)
                msg_box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
                msg_box.exec()
            else:
                self._show_warning(t('Error') if t else 'Error', t('mapgen.failed') if t else 'Map generation failed.')
        run_with_loading(on_finished, task)
    def _save_exclusions(self):
        save_exclusions()
        self._show_info(t('Saved'), t('deletion.saved_exclusions'))
    def _set_loading_screen_mode(self, mode):
        constants.loading_screen_mode = mode
        self.user_settings['loading_screen_mode'] = mode
        self._save_user_settings()
    def _open_pal_name_settings(self):
        from palworld_aio.editor.pal_editor.pal_ops import get_name_mode, set_name_mode, set_sync_nickname
        dialog = BaseDialog(
            t('pal_name_settings.title') if t else 'Pal Name Settings',
            self, min_size=(440, 280),
            kicker=t('ui.settings.appearance', default='Appearance'))
        layout = dialog.content_layout
        mode_label = QLabel(t('pal_name_settings.mode_label') if t else 'Name new pals with:')
        mode_label.setObjectName('bulkActionLabel')
        layout.addWidget(mode_label)
        combo = QComboBox()
        combo.addItem(t('edit_pals.name_mode_new') if t else 'New', 'new')
        combo.addItem(t('edit_pals.name_mode_copy') if t else '© Copy', 'copy')
        combo.addItem(t('edit_pals.name_mode_none') if t else 'No Nickname', 'none')
        cur_mode = get_name_mode()
        combo.setCurrentIndex(list(('new', 'copy', 'none')).index(cur_mode) if cur_mode in ('new', 'copy', 'none') else 0)
        layout.addWidget(combo)
        hint_label = QLabel(t('pal_name_settings.mode_hint') if t else 'Applies when creating pals (Pal Editor, base pals, Global Pal Storage) and to clones. A typed nickname always overrides it.')
        hint_label.setObjectName('bulkHintLabel')
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        nickname_chk = ToggleCheckBtn(t('pal_name_settings.sync_nickname') if t else 'Apply nickname during Bulk Sync')
        nickname_chk.setChecked(bool(constants.bulk_sync_apply_nickname))
        layout.addWidget(nickname_chk)
        dialog.add_confirm_button(t('button.ok') if t else 'OK')
        dialog.cancel_btn.setText(t('button.cancel') if t else 'Cancel')
        if dialog.exec() == QDialog.Accepted:
            set_name_mode(combo.currentData())
            set_sync_nickname(nickname_chk.isChecked())
            self.user_settings['pal_creation_name_mode'] = combo.currentData()
            self.user_settings['bulk_sync_apply_nickname'] = nickname_chk.isChecked()
            self._save_user_settings()
    def _change_language(self, code):
        old_lang = self.user_settings.get('language')
        if old_lang != code:
            self.user_settings['language'] = code
            self._save_user_settings()
            set_language(code)
            load_resources()
            if self.status_stream.detach_window:
                self.status_stream.detach_window.refresh_title()
            self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
            shell = getattr(self, 'workspace_shell', None)
            if shell is not None:
                shell.sidebar.refresh_labels()
                shell.title_bar.window_controls.refresh_labels()
                shell.navigate(shell.router.current_route_id)
            elif getattr(self, 'nav_strip', None) is not None:
                self.nav_strip.refresh_labels()
            self._setup_menus()
            self._refresh_texts()
            self.tools_tab.refresh_labels()
            app_bar = getattr(self, 'app_bar', None)
            if app_bar is not None:
                app_bar.refresh_labels()
            if getattr(self, '_window_controls', None):
                self._window_controls.refresh_labels()
            if getattr(self, '_menu_popup_v2', None):
                self._menu_popup_v2.refresh_labels()
            if 'map_tab' in self.__dict__:
                self.map_tab.refresh_labels()
            if 'inventory_tab' in self.__dict__:
                self.inventory_tab.refresh_labels()
            if 'base_inventory_tab' in self.__dict__:
                self.base_inventory_tab.refresh_labels()
            if 'docs_tab' in self.__dict__:
                self.docs_tab.refresh_labels()
            if 'breeding_tab' in self.__dict__:
                self.breeding_tab.refresh_labels()
            if 'json_editor_tab' in self.__dict__:
                self.json_editor_tab.refresh_labels()
            if 'pal_editor_tab' in self.__dict__:
                self.pal_editor_tab.refresh_labels()
            if hasattr(self, 'players_page'):
                self.players_page.refresh_labels()
            if hasattr(self, '_active_dialogs'):
                for dialog in self._active_dialogs:
                    if hasattr(dialog, 'refresh_labels'):
                        dialog.refresh_labels()
    def _refresh_texts(self):
        tools_version, _ = get_versions()
        self.setWindowTitle(t('app.title', version=tools_version) + ' - ' + t('tool.deletion'))
        if hasattr(self, '_tray_drawer'):
            self._tray_drawer.stats_panel.refresh_labels()
        if hasattr(self, 'players_panel'):
            self.players_panel.refresh_labels()
        if hasattr(self, 'guilds_page'):
            self.guilds_page.refresh_labels()
        elif hasattr(self, 'guilds_panel'):
            self.guilds_panel.refresh_labels()
        if not hasattr(self, 'guilds_page') and hasattr(self, 'guild_members_panel'):
            self.guild_members_panel.refresh_labels()
        if hasattr(self, '_members_empty_state'):
            self._members_empty_state.setText(t('deletion.guild_members.select_hint') if t else 'Select a guild to view its members')
            self._members_empty_state.setHint(t('deletion.guild_members.select_hint_sub') if t else 'Pick a guild in the list above.')
        if hasattr(self, 'bases_page'):
            self.bases_page.refresh_labels()
        elif hasattr(self, 'bases_panel'):
            self.bases_panel.refresh_labels()
        if hasattr(self, 'exclusions_page'):
            self.exclusions_page.refresh_labels()
        elif hasattr(self, 'excl_players_panel'):
            self.excl_players_panel.refresh_labels()
        if not hasattr(self, 'exclusions_page') and hasattr(self, 'excl_guilds_panel'):
            self.excl_guilds_panel.refresh_labels()
        if not hasattr(self, 'exclusions_page') and hasattr(self, 'excl_bases_panel'):
            self.excl_bases_panel.refresh_labels()
        self._apply_excl_empty_states()
        if hasattr(self, 'menu_bar'):
            self._setup_menus()
    def _add_exclusion(self, excl_type, value):
        exclusions = constants.exclusions.setdefault(excl_type, [])
        if value not in exclusions:
            exclusions.append(value)
            save_exclusions()
            self._refresh_exclusions()
        else:
            self._show_info(t('Info'), t('deletion.info.already_in_exclusions', kind=excl_type[:-1].capitalize()))
    def _remove_exclusion(self, excl_type, value):
        exclusions = constants.exclusions.setdefault(excl_type, [])
        if value in exclusions:
            exclusions.remove(value)
            save_exclusions()
            self._refresh_exclusions()
    def _delete_player(self, uid):
        if uid in constants.exclusions.get('players', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_player') if t else f'Player {uid} is in exclusion list and cannot be deleted.')
            return
        delete_player(uid)
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.player_deleted'))
    def _delete_guild(self, gid):
        if gid in constants.exclusions.get('guilds', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_guild') if t else f'Guild {gid} is in exclusion list and cannot be deleted.')
            return
        delete_guild(gid)
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.guild_deleted'))
    def _delete_base(self, bid, gid):
        if bid in constants.exclusions.get('bases', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_base') if t else f'Base {bid} is in exclusion list and cannot be deleted.')
            return
        from ..managers.data_manager import delete_base_camp
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        deleted = False
        for b in base_list:
            if str(b['key']).replace('-', '').lower() == bid.replace('-', '').lower():
                delete_base_camp(b, gid)
                deleted = True
                break
        if deleted:
            constants.invalidate_container_lookup()
            if 'base_inventory_tab' in self.__dict__:
                self.base_inventory_tab.manager.invalidate_cache()
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.base_deleted'))
    def _rename_player(self, uid, old_name):
        new_name = InputDialog.get_text(t('player.rename.title'), t('player.rename.prompt'), self)
        if new_name:
            rename_player(uid, new_name)
            self.refresh_all()
            self._show_info(t('player.rename.done_title'), t('player.rename.done_msg', old=old_name, new=new_name))
    def _unlock_viewing_cage(self, uid):
        if unlock_viewing_cage_for_player(uid, self):
            self._show_info(t('Done'), t('player.viewing_cage.unlocked'))
        else:
            self._show_warning(t('Error'), t('player.viewing_cage.failed'))
    def _rename_guild_action(self, gid, old_name):
        new_name = InputDialog.get_text(t('guild.rename.title'), t('guild.rename.prompt'), self)
        if new_name:
            rename_guild(gid, new_name)
            self.refresh_all()
            self._show_info(t('guild.rename.done_title'), t('guild.rename.done_msg', old=old_name, new=new_name))
    def _set_guild_level(self, gid):
        if not constants.loaded_level_json:
            return
        current_level = 1
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            from palworld_aio.utils import are_equal_uuids
            if are_equal_uuids(g['key'], gid):
                current_level = g['value']['RawData']['value'].get('base_camp_level', 1)
                break
        new_level = LevelInputDialog.get_level(t('guild.menu.set_level') if t else 'Set Guild Level', t('guild.set_level.prompt', current_level=current_level) if t else f'Current level: {current_level}\nEnter new level (1-35):', current_level, self, minimum=1, maximum=35)
        if new_level is not None and new_level != current_level:
            set_guild_level(gid, new_level)
            self.refresh_all()
            self._show_info(t('success.title'), t('guild.level.set', level=new_level))
    def _make_leader(self, gid, uid):
        make_member_leader(gid, uid)
        self.refresh_all()
        self._show_info(t('Done'), t('guild.leader_changed'))
    def _set_guild_member_role(self, gid, uid, role):
        from palworld_aio.managers.guild_manager import set_member_role
        set_member_role(gid, uid, role)
        self.refresh_all()
        page = self.__dict__.get('guilds_page')
        guild = page.selected_guild() if page is not None else None
        if guild is not None:
            self._on_guild_record_selected(guild)
        else:
            gdata = self.guilds_panel.get_selected_data()
            if gdata:
                self._on_guild_selected(gdata)
        self._show_info(t('Done'), t('guild.role_updated'))
    def _import_base_to_guild(self, gid):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select Base Files', '', 'Base Files (*.json *.pstbase)')
        if not file_paths:
            return
        def task():
            successful_imports = 0
            failed_imports = 0
            failed_files = []
            for file_path in file_paths:
                try:
                    exported_data = load_base_file(file_path)
                    if import_base_json(constants.loaded_level_json, exported_data, gid):
                        successful_imports += 1
                    else:
                        failed_imports += 1
                        suffix = ''
                        audit = get_last_import_audit() or {}
                        if audit.get('issues'):
                            suffix = ': ' + '; '.join(audit['issues'])
                        failed_files.append(os.path.basename(file_path) + '(import failed)' + suffix)
                except Exception as e:
                    failed_imports += 1
                    failed_files.append(os.path.basename(file_path) + f'(error: {str(e)})')
            return (successful_imports, failed_imports, failed_files)
        def result_message(result):
            successful_imports, failed_imports, failed_files = result
            msg = f'Successfully imported {successful_imports} base(s).'
            if failed_imports > 0:
                msg += f'\nFailed to import {failed_imports} file(s):\n' + '\n'.join(failed_files)
            return msg
        def on_completed(result):
            successful_imports, _failed_imports, _failed_files = result
            if successful_imports > 0:
                constants.invalidate_container_lookup()
                if 'base_inventory_tab' in self.__dict__:
                    self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
        return self._run_transfer_workflow(
            title=t('base.import_multi', default='Import Bases'),
            source='\n'.join(os.path.basename(path) for path in file_paths),
            target=t(
                'transfer.base.guild_target',
                default='Guild {guild}', guild=_short_guid(gid)),
            review=t(
                'transfer.base.import_review',
                default='Import {count} selected base file(s) into the target guild.',
                count=len(file_paths)),
            backup=t(
                'repair.workflow.loaded_backup',
                default=(
                    'Recovery: a full backup was created when this save was loaded. '
                    'Imports remain in memory until Save Changes.')),
            risk=t(
                'transfer.base.import_risk',
                default='Imported bases add structures, containers, and ownership links to the loaded save.'),
            operation=task,
            result_message=result_message,
            result_success=lambda result: result[0] > 0,
            on_completed=on_completed,
            confirm_text=t('button.import', default='Import'),
        )
    def _export_all_bases(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        bases = get_bases()
        if not bases:
            self._show_info(t('Info') if t else 'Info', 'No bases found in the save.')
            return
        export_dir = QFileDialog.getExistingDirectory(self, 'Select Export Directory')
        if not export_dir:
            return
        export_type = show_question(self, 'Export Format', 'Export as compressed .pstbase files?\n\nYes = .pstbase (smaller)\nNo = .json')
        compressed = export_type if export_type is not None else False
        def task():
            successful_exports = 0
            failed_exports = 0
            failed_bases = []
            for base in bases:
                bid = base['id']
                gname = base['guild_name']
                try:
                    data = export_base_json(constants.loaded_level_json, bid)
                    if not data:
                        failed_exports += 1
                        failed_bases.append(f'Base {bid}(no data)')
                        continue
                    safe_gname = ''.join((c for c in gname if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                    ext = '.pstbase' if compressed else '.json'
                    filename = f'base_{bid}_{safe_gname}{ext}'
                    file_path = os.path.join(export_dir, filename)
                    if compressed:
                        data['_base_id'] = bid
                        data['_version'] = 1
                        with open(file_path, 'wb') as f:
                            f.write(compress_to_pst3(data))
                    else:
                        json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                    successful_exports += 1
                except Exception as e:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(error: {str(e)})')
            return (successful_exports, failed_exports, failed_bases, export_dir)
        def result_message(result):
            successful_exports, failed_exports, failed_bases, export_dir = result
            if successful_exports > 0:
                msg = f'Successfully exported {successful_exports} base(s)to {export_dir}.'
                if failed_exports > 0:
                    msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
                return msg
            return f'Failed to export any bases.\n' + '\n'.join(failed_bases)
        return self._run_transfer_workflow(
            title=t('base.export_all', default='Export All Bases'),
            source=t(
                'transfer.base.loaded_count',
                default='{count} loaded base(s)', count=len(bases)),
            target=export_dir,
            review=t(
                'transfer.base.export_review',
                default='Export each base as {format}.',
                format='.pstbase' if compressed else '.json'),
            backup=t(
                'transfer.export.read_only',
                default='Read-only export: the loaded save is not changed.'),
            operation=task,
            result_message=result_message,
            result_success=lambda result: result[0] > 0,
            confirm_text=t('button.export', default='Export'),
        )
    def _export_bases_for_guild(self, gid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        guild_name = save_manager.get_guild_name_by_id(gid)
        if not guild_name:
            self._show_warning(t('error.title'), f'Guild not found: {gid}')
            return
        bases = get_bases()
        guild_bases = [b for b in bases if str(b['guild_id']) == str(gid)]
        if not guild_bases:
            self._show_info(t('Info') if t else 'Info', f'No bases found for guild "{guild_name}".')
            return
        export_type = show_question(self, 'Export Format', 'Export as compressed .pstbase files?\n\nYes = .pstbase (smaller)\nNo = .json')
        compressed = export_type if export_type is not None else False
        export_dir = QFileDialog.getExistingDirectory(self, f'Select Export Directory for "{guild_name}"')
        if not export_dir:
            return
        def task():
            successful_exports = 0
            failed_exports = 0
            failed_bases = []
            for base in guild_bases:
                bid = base['id']
                gname = base['guild_name']
                try:
                    data = export_base_json(constants.loaded_level_json, bid)
                    if not data:
                        failed_exports += 1
                        failed_bases.append(f'Base {bid}(no data)')
                        continue
                    safe_gname = ''.join((c for c in gname if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                    ext = '.pstbase' if compressed else '.json'
                    filename = f'base_{bid}_{safe_gname}{ext}'
                    file_path = os.path.join(export_dir, filename)
                    if compressed:
                        data['_base_id'] = bid
                        data['_version'] = 1
                        with open(file_path, 'wb') as f:
                            f.write(compress_to_pst3(data))
                    else:
                        json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                    successful_exports += 1
                except Exception as e:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(error: {str(e)})')
            return (successful_exports, failed_exports, failed_bases)
        def result_message(result):
            successful_exports, failed_exports, failed_bases = result
            if successful_exports > 0:
                msg = f'Successfully exported {successful_exports} base(s)for guild "{guild_name}" to {export_dir}.'
                if failed_exports > 0:
                    msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
                return msg
            return f'Failed to export any bases for guild "{guild_name}".\n' + '\n'.join(failed_bases)
        return self._run_transfer_workflow(
            title=t('base.export_guild', default='Export Guild Bases'),
            source=t(
                'transfer.base.guild_source',
                default='{guild}: {count} base(s)',
                guild=guild_name, count=len(guild_bases)),
            target=export_dir,
            review=t(
                'transfer.base.export_review',
                default='Export each base as {format}.',
                format='.pstbase' if compressed else '.json'),
            backup=t(
                'transfer.export.read_only',
                default='Read-only export: the loaded save is not changed.'),
            operation=task,
            result_message=result_message,
            result_success=lambda result: result[0] > 0,
            confirm_text=t('button.export', default='Export'),
        )
    def _export_base(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        default_filename = f'base_{bid}'
        file_path, selected_filter = QFileDialog.getSaveFileName(self, t('base.export.title') if t else 'Export Base', default_filename, 'PSTB Base Files (*.pstbase);;JSON Files (*.json)')
        if not file_path:
            return
        is_pstbase = 'pstbase' in selected_filter if selected_filter else file_path.endswith('.pstbase')
        if is_pstbase and not file_path.endswith('.pstbase'):
            file_path += '.pstbase'
        elif not is_pstbase and not file_path.endswith('.json'):
            file_path += '.json'
        def task():
            data = export_base_json(constants.loaded_level_json, bid)
            if not data:
                return (False, t('base.export.not_found') if t else f'Could not find base data for ID: {bid}')
            if is_pstbase:
                data['_base_id'] = bid
                data['_version'] = 1
                with open(file_path, 'wb') as f:
                    f.write(compress_to_pst3(data))
            else:
                json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
            return (True, None)
        return self._run_transfer_workflow(
            title=t('base.export.title', default='Export Base'),
            source=t(
                'transfer.base.single_source',
                default='Base {base}', base=_short_guid(bid)),
            target=file_path,
            review=t(
                'transfer.base.single_export_review',
                default='Export this base as {format}.',
                format='.pstbase' if is_pstbase else '.json'),
            backup=t(
                'transfer.export.read_only',
                default='Read-only export: the loaded save is not changed.'),
            operation=task,
            result_message=lambda result: (
                t('base.export.success') if result[0]
                else (result[1] or t('base.export.not_found'))),
            result_success=lambda result: bool(result[0]),
            confirm_text=t('button.export', default='Export'),
        )
    def _adjust_base_radius(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        base_camp_data = wsd.get('BaseCampSaveData', {}).get('value', [])
        src_base_entry = next((b for b in base_camp_data if str(b['key']).replace('-', '').lower() == bid.replace('-', '').lower()), None)
        if not src_base_entry:
            self._show_warning(t('error.title') if t else 'Error', t('base.export.not_found') if t else f'Could not find base data for ID: {bid}')
            return
        current_radius = src_base_entry['value']['RawData']['value'].get('area_range', 3500.0)
        new_radius = RadiusInputDialog.get_radius(t('base.radius.title') if t else 'Adjust Base Radius', t('base.radius.prompt') if t else f'Current radius: {int(current_radius)}\nEnter new radius (50% -1000%):', current_radius, self)
        if new_radius is not None and new_radius != current_radius:
            if update_base_area_range(constants.loaded_level_json, bid, new_radius):
                self.refresh_all()
                self._show_info(t('success.title') if t else 'Success', t('base.radius.updated', radius=int(new_radius)) if t else f'Base radius updated to {new_radius}\n\n⚠ Load this save in-game for structures to be reassigned.')
            else:
                self._show_error(t('error.title') if t else 'Error', t('base.radius.failed') if t else 'Failed to update base radius')
    def _import_base(self, gid):
        self._import_base_to_guild(gid)
    def _trim_overfilled_inventories(self):
        return self._run_loaded_save_repair(
            title=t('deletion.menu.fix_overfilled_inventories'),
            affected=t(
                'repair.affected.containers',
                default='Underfilled and overfilled item and Pal containers'),
            review=t(
                'repair.review.containers',
                default='Normalize container sizes using the existing inventory repair action.'),
            operation=lambda: detect_and_trim_overfilled_inventories(self),
            result_message=lambda fixed: t(
                'deletion.trimmed_inventories', fixed=fixed),
        )
    def _nudge_palbox(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        from palworld_aio.editor.dialogs import NudgeInputDialog
        reply = show_question(self, t('confirm.title') if t else 'Confirm', t('base.palbox_nudge.warning') if t else 'This moves ONLY the Palbox structure. All other buildings stay in place. The base center will shift.\n\nContinue?')
        if not reply:
            return
        dialog = NudgeInputDialog(self)
        dialog.setWindowTitle(t('base.palbox_nudge') if t else 'Nudge Palbox')
        if dialog.exec() != QDialog.Accepted:
            return
        dx, dy, dz, _ = dialog.result_value
        if dx == 0 and dy == 0 and dz == 0:
            return
        def task():
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            bid_norm = bid.replace('-', '').lower()
            map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
            found = False
            for obj in map_objs:
                try:
                    if str(obj.get('MapObjectId', {}).get('value', '')) != 'PalBoxV2':
                        continue
                    mr = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                    if str(mr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != bid_norm:
                        continue
                    itc = mr.get('initital_transform_cache', {})
                    if 'translation' in itc:
                        itc['translation']['x'] += dx
                        itc['translation']['y'] += dy
                        itc['translation']['z'] += dz
                    if 'transform' in itc:
                        t2 = itc['transform'].get('translation', {})
                        if t2:
                            t2['x'] += dx
                            t2['y'] += dy
                            t2['z'] += dz
                    found = True
                    break
                except:
                    continue
            constants.invalidate_container_lookup()
            return found
        def on_finished(found):
            if not found:
                self._show_warning(t('error.title') if t else 'Error', t('base.export.not_found') if t else 'Palbox not found for this base.')
                return
            self.refresh_all()
            self._show_info(t('success.title') if t else 'Success', t('base.palbox_nudge.success') if t else 'Palbox nudged successfully.')
        run_with_loading(on_finished, task)
    def _clone_base(self, bid, gid):
        def task():
            return clone_base_complete(constants.loaded_level_json, bid, gid)
        def result_message(success):
            if success:
                return t('clone_base.msg')
            else:
                audit = get_last_import_audit() or {}
                msg = 'Failed to clone base'
                if audit.get('issues'):
                    msg += ': ' + '; '.join(audit['issues'])
                return msg
        return self._run_transfer_workflow(
            title=t('clone.base', default='Clone Base'),
            source=t(
                'transfer.base.single_source',
                default='Base {base}', base=_short_guid(bid)),
            target=t(
                'transfer.base.guild_target',
                default='Guild {guild}', guild=_short_guid(gid)),
            review=t(
                'transfer.base.clone_review',
                default='Create a new base with copied structures, containers, and ownership links.'),
            backup=t(
                'repair.workflow.loaded_backup',
                default=(
                    'Recovery: a full backup was created when this save was loaded. '
                    'The clone remains in memory until Save Changes.')),
            risk=t(
                'transfer.base.clone_risk',
                default='Cloning adds a complete base and remapped identifiers to the loaded save.'),
            operation=task,
            result_message=result_message,
            result_success=bool,
            on_completed=lambda _success: self.refresh_all(),
            confirm_text=t('clone.base', default='Clone Base'),
        )
    def _edit_player_pals(self, uid, name):
        from ..editor.edit_pals import EditPalsDialog
        dialog = EditPalsDialog(uid, name, self)
        if dialog.exec() == QDialog.Accepted:
            QTimer.singleShot(0, self.refresh_all)
    def _edit_player_inventory(self, uid, name):
        from palworld_aio.ui.workspace_context import ContextSelection
        self._activate_contextual_nav(
            'player_inventory', player=ContextSelection(str(uid), str(name)))
        self.stacked_widget.setCurrentIndex(2)
        if 'inventory_tab' in self.__dict__:
            self.inventory_tab.load_player(uid, name)
    def _unlock_all_technologies_for_player(self, uid):
        if unlock_all_technologies_for_player(uid, self):
            self._show_info(t('Done') if t else 'Done', t('player.unlock_technologies.success') if t else 'Unlock All Technologies completed')
        else:
            self._show_warning(t('Error') if t else 'Error', t('player.unlock_technologies.failed') if t else 'Unlock All Technologies failed')
    def _unlock_all_lab_research_for_guild(self, gid):
        if unlock_all_lab_research_for_guild(gid, self):
            self._show_info(t('Done') if t else 'Done', t('guild.unlock_lab_research.success') if t else 'Unlock All Lab Research completed')
        else:
            self._show_warning(t('Error') if t else 'Error', t('guild.unlock_lab_research.failed') if t else 'Unlock All Lab Research failed')
    def _level_up_player(self, uid):
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot level up player - player is at level 1 or unknown')
            return
        if adjust_player_level(uid, current_level + 1):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', 'Player leveled up successfully')
        else:
            self._show_warning(t('Error') if t else 'Error', 'Failed to level up player (already max level?)')
    def _level_down_player(self, uid):
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot level down player - player is at level 1 or unknown')
            return
        if current_level - 1 < 2:
            self._show_warning(t('Error') if t else 'Error', t('player.level.minimum_level') if t else 'Cannot level down player - minimum level is 2')
            return
        if adjust_player_level(uid, current_level - 1):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', 'Player leveled down successfully')
        else:
            self._show_warning(t('Error') if t else 'Error', 'Failed to level down player (already min level?)')
    def _set_player_level(self, uid):
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot set player level - player is at level 1 or unknown')
            return
        new_level = LevelInputDialog.get_level(t('player.set_level.title') if t else 'Set Player Level', t('player.set_level.prompt', current_level=current_level) if t else f'Current level: {current_level}\nEnter new level (2-80):', current_level, self)
        if new_level is not None and new_level != current_level:
            if new_level < 2:
                self._show_warning(t('Error') if t else 'Error', t('player.level.minimum_level') if t else 'Cannot set player level - minimum level is 2')
                return
            if adjust_player_level(uid, new_level):
                self.refresh_all()
                self._show_info(t('Done') if t else 'Done', t('player.level.set_success', level=new_level) if t else f'Player level set to {new_level}')
            else:
                self._show_warning(t('Error') if t else 'Error', t('player.level.set_failed') if t else 'Failed to set player level')
    def _modify_container_slots(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        new_slot_num, ok = QInputDialog.getInt(self, t('modify_container_slots_title') if t else 'Modify Container Slots', t('modify_container_slots_prompt') if t else 'Enter new slot number for all containers:', 50, 1, 1000, 1)
        if ok:
            def task():
                return modify_container_slots(new_slot_num, self)
            def on_finished(modified):
                self.refresh_all()
                self._show_info(t('Done'), t('modify_container_slots_result', modified=modified) if t else f'Modified {modified} containers')
            run_with_loading(on_finished, task)

    def _modify_all_player_slots(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        new_slot_num, ok = QInputDialog.getInt(self, t('modify_all_player_slots_title') if t else 'Modify All Player Slots', t('modify_all_player_slots_prompt') if t else 'Enter new inventory slot count (42-999) for all players:', 42, 42, 999, 1)
        if ok:
            def task():
                return modify_all_player_slots(new_slot_num, self)
            def on_finished(res):
                self.refresh_all()
                if isinstance(res, dict):
                    modified = res.get('modified', 0)
                    total = modified + res.get('skipped', 0)
                else:
                    modified = 0
                    total = 0
                self._show_info(t('Done'), t('modify_all_player_slots_result', modified=modified, total=total, slots=new_slot_num) if t else f'Resized {modified} of {total} player inventories to {new_slot_num} slots')
            run_with_loading(on_finished, task)

    def _modify_all_guild_chest_slots(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        new_slot_num, ok = QInputDialog.getInt(self, t('modify_all_guild_chest_slots_title') if t else 'Modify All Guild Chest Slots', t('modify_all_guild_chest_slots_prompt') if t else 'Enter new slot count for all guild chests:', 50, 1, 1000, 1)
        if ok:
            def task():
                return modify_all_guild_chest_slots(new_slot_num, self)
            def on_finished(modified):
                self.refresh_all()
                self._show_info(t('Done'), t('modify_all_guild_chest_slots_result', modified=modified) if t else f'Modified {modified} guild chest containers')
            run_with_loading(on_finished, task)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            if constants.current_save_path:
                self.refresh_all()
        super().keyPressEvent(event)
    def _get_player_name(self, uid):
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
            for entry in char_map:
                try:
                    save_param_val = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    player_uid_obj = save_param_val.get('OwnerPlayerUId', {})
                    if isinstance(player_uid_obj, dict):
                        player_uid = player_uid_obj.get('value', '')
                        if str(player_uid).replace('-', '').lower() == str(uid).replace('-', '').lower():
                            player_name_obj = save_param_val.get('NickName', {})
                            if isinstance(player_name_obj, dict):
                                return player_name_obj.get('value', {}).get('value', 'Unknown')
                except:
                    continue
        except:
            pass
        return 'Unknown'
