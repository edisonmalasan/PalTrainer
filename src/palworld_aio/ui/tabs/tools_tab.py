import os
import sys
import traceback
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGridLayout, QApplication, QDialog, QStylePainter, QStyleOptionButton, QStyle
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QRectF, QObject, QEvent, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QCursor, QDragEnterEvent, QDropEvent, QDragLeaveEvent, QPainter, QColor, QPen, QPainterPath, QFontMetrics, QFontDatabase, QGuiApplication
from i18n import t
from loading_manager import show_critical
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.ui.chrome.styles import ThemeManager
CONVERTING_TOOL_KEYS = ['tool.convert.saves', 'tool.convert.gamepass.steam', 'tool.convert.steamid', 'tool.restore_map']
MANAGEMENT_TOOL_KEYS = ['tool.slot_injector', 'tool.character_transfer', 'tool.fix_host_save']
TOOL_DESCRIPTIONS = {'tool.convert.saves': 'tool.convert.saves.desc', 'tool.convert.gamepass.steam': 'tool.convert.gamepass.steam.desc', 'tool.convert.steamid': 'tool.convert.steamid.desc', 'tool.restore_map': 'tool.restore_map.desc', 'tool.slot_injector': 'tool.slot_injector.desc', 'tool.character_transfer': 'tool.character_transfer.desc', 'tool.fix_host_save': 'tool.fix_host_save.desc'}


class _RestoreOnCloseFilter(QObject):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self._callback = callback

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Close, QEvent.Hide):
            self._callback()
        return super().eventFilter(watched, event)


def center_window(win):
    win_center = win.frameGeometry().center()
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def center_on_parent(dialog):
    parent = dialog.parent()
    dialog.adjustSize()
    size = dialog.size()
    if not size.isValid() or size.width() < 100 or size.height() < 50:
        min_size = dialog.minimumSize()
        if min_size.isValid() and min_size.width() > 0 and (min_size.height() > 0):
            size = min_size
        else:
            size = QSize(400, 300)
    if parent and hasattr(parent, 'geometry'):
        parent_rect = parent.geometry()
        parent_center = parent_rect.center()
        screen = QApplication.screenAt(parent_center)
        if screen is None:
            screen = QApplication.primaryScreen()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        dialog.move(dialog_x, dialog_y)
    else:
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = screen_geometry.x() + (screen_geometry.width() - size.width()) // 2
        dialog_y = screen_geometry.y() + (screen_geometry.height() - size.height()) // 2
        dialog.move(dialog_x, dialog_y)
class ConversionOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_option = None
        self.setWindowTitle(t('tool.convert.saves') if t else 'Convert Save Files')
        self.setModal(True)
        self.setFixedWidth(380)
        self._setup_ui()
        self._load_theme()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        sheet = QFrame()
        sheet.setObjectName('dialogSheet')
        sheet_layout = QVBoxLayout(sheet)
        sheet_layout.setContentsMargins(0, 0, 0, 0)
        sheet_layout.setSpacing(12)
        kicker = QLabel((t('tools.section.converting') if t else 'Converting').upper())
        kicker.setObjectName('dialogKicker')
        sheet_layout.addWidget(kicker)
        title_label = QLabel(t('tool.convert.saves') if t else 'Convert Save Files')
        title_label.setObjectName('dialogTitle')
        sheet_layout.addWidget(title_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName('dialogSeparator')
        sheet_layout.addWidget(separator)
        sheet_layout.addSpacing(4)
        options = [('tool.convert.any.to_json', 0), ('tool.convert.any.to_sav', 1)]
        for key, index in options:
            btn = QPushButton(t(key) if t else key)
            btn.setObjectName('dialogOption')
            btn.setFixedHeight(36)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, idx=index: self._on_option_selected(idx))
            sheet_layout.addWidget(btn)
        sheet_layout.addStretch(1)
        cancel_btn = QPushButton(t('Cancel') if t else 'Cancel')
        cancel_btn.setObjectName('dialogCancel')
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        sheet_layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(sheet)
    def _on_option_selected(self, index):
        self.selected_option = index
        self.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    def _load_theme(self):
        ThemeManager.apply_to_widget(self)
class ToolCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, label_text, tooltip_text, description_text=None, icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName('toolCard')
        self.setProperty('class', 'toolCard')
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setObjectName('toolCardIcon')
        dpr = QGuiApplication.primaryScreen().devicePixelRatio() if QGuiApplication.primaryScreen() else 1.0
        target = int(40 * dpr)
        if icon_path and os.path.exists(icon_path):
            pix = QIcon(icon_path).pixmap(QSize(256, 256))
            if not pix.isNull():
                pix = pix.scaled(target, target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pix.setDevicePixelRatio(dpr)
                self.icon_label.setPixmap(pix)
        else:
            default_icon = resource_path(constants.get_base_path(), 'icon.ico')
            if os.path.exists(default_icon):
                pix = QIcon(default_icon).pixmap(QSize(256, 256))
                if not pix.isNull():
                    pix = pix.scaled(target, target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pix.setDevicePixelRatio(dpr)
                    self.icon_label.setPixmap(pix)
        layout.addWidget(self.icon_label)
        text_column = QVBoxLayout()
        text_column.setSpacing(4)
        text_column.addStretch()
        self.title_label = QLabel(label_text)
        self.title_label.setToolTip(tooltip_text)
        self.title_label.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.title_label.setObjectName('toolCardTitle')
        text_column.addWidget(self.title_label)
        if description_text:
            self.desc_label = QLabel(description_text)
            self.desc_label.setFont(QFont(constants.FONT_FAMILY, 9))
            self.desc_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.desc_label.setObjectName('toolCardDesc')
            self.desc_label.setWordWrap(True)
            text_column.addWidget(self.desc_label)
        else:
            self.desc_label = None
        text_column.addStretch()
        layout.addLayout(text_column, 1)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
class DropOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(False)
        self._drop_text = t('tools.drop_title') if t else 'Drop Level.sav to Load Save'
        self._drop_hint = t('tools.drop_hint_overlay') if t else "Or click the 'Load Save' button above"
    def paintEvent(self, event):
        from palworld_aio.ui.chrome import tokens as _tokens
        pal = _tokens.resolve()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(5, 7, 10, 220))
        inner = self.rect().adjusted(30, 30, -30, -30)
        path = QPainterPath()
        path.addRoundedRect(QRectF(inner), 16, 16)
        accent = QColor(pal['accent'])
        painter.fillPath(path, QColor(accent.red(), accent.green(), accent.blue(), 20))
        pen = QPen(accent)
        pen.setWidth(4)
        pen.setDashPattern([12, 6])
        painter.setPen(pen)
        painter.drawPath(path)
        box_h = inner.height()
        center_y = inner.y() + box_h / 2
        icon_font = QFont(constants.FONT_FAMILY_NERD, 46, QFont.Bold)
        painter.setFont(icon_font)
        painter.setPen(accent)
        icon_rect = QRectF(inner.x(), center_y - 80, inner.width(), 60)
        painter.drawText(icon_rect, Qt.AlignHCenter | Qt.AlignBottom, '\uf07b')
        font = QFont(constants.FONT_FAMILY, 22, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 255))
        text_rect = QRectF(inner.x(), center_y - 10, inner.width(), 40)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignCenter, self._drop_text)
        font_small = QFont(constants.FONT_FAMILY, 13)
        painter.setFont(font_small)
        painter.setPen(QColor(pal['text_secondary']))
        hint_rect = QRectF(inner.x(), center_y + 40, inner.width(), 30)
        painter.drawText(hint_rect, Qt.AlignHCenter | Qt.AlignTop, self._drop_hint)
class StatIconBtn(QPushButton):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        font_family = self._resolve_nerdfont()
        self.setFont(QFont(font_family, 11))
        self.setFixedSize(44, 28)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFocusPolicy(Qt.NoFocus)
        self.setObjectName('statIconBtn')

    @staticmethod
    def _resolve_nerdfont():
        candidates = [constants.FONT_FAMILY_NERD, 'NerdFontsSymbolsOnly', 'Segoe Fluent Icons', 'Segoe UI Symbol', constants.FONT_FAMILY]
        for name in candidates:
            if name in QFontDatabase.families():
                return name
        return constants.FONT_FAMILY

    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()
class ToolsTab(QWidget):
    """Start page v2 (plan 021): operations masthead + field report + campaign
    strip + mission columns. All 7 tool entry points and deep-links preserved;
    the old centered save card and glass tool-card grids are retired."""

    # (translation key, handler attribute, handler index) per mission zone
    MISSION_ZONES = (
        ('tools.section.converting', (
            ('tool.convert.saves', '_run_converting_tool', 0),
            ('tool.convert.gamepass.steam', '_run_converting_tool', 1),
            ('tool.convert.steamid', '_run_converting_tool', 2),
        )),
        ('tools.section.management', (
            ('tool.slot_injector', '_run_management_tool', 0),
            ('tool.character_transfer', '_run_management_tool', 1),
            ('tool.fix_host_save', '_run_management_tool', 2),
        )),
        ('tools.section.world', (
            ('tool.restore_map', '_run_converting_tool', 3),
        )),
    )
    CAMPAIGN_STEPS = (
        ('tool.convert.saves', '_run_converting_tool', 0),
        ('tool.convert.gamepass.steam', '_run_converting_tool', 1),
        ('tool.character_transfer', '_run_management_tool', 1),
        ('tool.fix_host_save', '_run_management_tool', 2),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._mission_rows = []
        self._campaign_btns = []
        self._setup_ui()

    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import create_page_ribbon
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(create_page_ribbon(t('tools_tab') if t else 'Start', (t('sidebar.section.inspect') if t else 'Load & Inspect').upper(), self))
        canvas = QWidget()
        canvas.setObjectName('startCanvas')
        body = QVBoxLayout(canvas)
        body.setContentsMargins(24, 18, 24, 20)
        body.setSpacing(18)
        body.addWidget(self._create_ops_masthead())
        body.addWidget(self._create_field_report())
        body.addWidget(self._create_campaign_strip())
        columns_row = QHBoxLayout()
        columns_row.setSpacing(24)
        for zone_key, rows in self.MISSION_ZONES:
            columns_row.addWidget(self._create_mission_column(zone_key, rows), stretch=1)
        columns_row.addStretch(0)
        body.addLayout(columns_row)
        body.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName('startScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(canvas)
        root.addWidget(scroll, stretch=1)
        self._setup_save_manager_connection()

    # ------------------------------------------------------------- masthead
    def _create_ops_masthead(self):
        mast = QFrame()
        mast.setObjectName('opsMasthead')
        lay = QVBoxLayout(mast)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        kicker = QLabel((t('ops.save_ledger') if t else 'WORLD SAVE LEDGER').upper())
        kicker.setObjectName('opsKicker')
        lay.addWidget(kicker)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        self._save_status_label = QLabel(t('dashboard.no_save') if t else 'No Save Loaded')
        self._save_status_label.setObjectName('opsWorldName')
        top_row.addWidget(self._save_status_label)
        self._save_state_dot = QLabel()
        self._save_state_dot.setObjectName('opsStateDot')
        self._save_state_dot.setFixedSize(10, 10)
        top_row.addWidget(self._save_state_dot)
        top_row.addStretch(1)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        import nerdfont as nf
        _nf_font = QFont(constants.FONT_FAMILY_NERD, 11)
        self._load_steam_btn = QPushButton()
        self._load_steam_btn.setObjectName('opsLoadBtn')
        self._load_steam_btn.setFont(_nf_font)
        self._load_steam_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._load_steam_btn.setMinimumHeight(36)
        self._load_steam_btn.clicked.connect(self._on_load_save_clicked)
        btn_row.addWidget(self._load_steam_btn)
        self._load_xgp_btn = QPushButton()
        self._load_xgp_btn.setObjectName('opsLoadBtn')
        self._load_xgp_btn.setProperty('loadKind', 'secondary')
        self._load_xgp_btn.setFont(_nf_font)
        self._load_xgp_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._load_xgp_btn.setMinimumHeight(36)
        self._load_xgp_btn.clicked.connect(self._on_load_xgp_clicked)
        btn_row.addWidget(self._load_xgp_btn)
        self._refresh_save_btns()
        top_row.addLayout(btn_row)
        lay.addLayout(top_row)
        self._save_path_label = QPushButton(t('tools.no_save_loaded') if t else 'No save loaded')
        self._save_path_label.setObjectName('opsSavePath')
        self._save_path_label.setFlat(True)
        self._save_path_label.setCursor(QCursor(Qt.PointingHandCursor))
        self._save_path_label.clicked.connect(lambda: self._on_save_path_label_clicked())
        lay.addWidget(self._save_path_label)
        self._drag_hint_label = QLabel(t('tools.drag_hint') if t else 'or drag & drop a Level.sav file here')
        self._drag_hint_label.setObjectName('opsDropHint')
        lay.addWidget(self._drag_hint_label)
        return mast

    def _create_field_report(self):
        frame = QFrame()
        frame.setObjectName('fieldReport')
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(24)
        kicker = QLabel((t('ops.field_report') if t else 'FIELD REPORT').upper())
        kicker.setObjectName('opsKicker')
        lay.addWidget(kicker)
        self._stat_cards = {}
        self._stat_label_refs = {}
        stats = [('players', 'dashboard.stat_players'), ('guilds', 'dashboard.stat_guilds'), ('bases', 'dashboard.stat_bases'), ('pals', 'dashboard.stat_pals')]
        for key, label_key in stats:
            chip = QWidget()
            chip.setObjectName('fieldMetric')
            chip.setCursor(QCursor(Qt.PointingHandCursor))
            cl = QVBoxLayout(chip)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(0)
            val = QLabel('—')
            val.setObjectName('fieldMetricValue')
            cl.addWidget(val)
            lbl = QLabel(t(label_key) if t else key)
            lbl.setObjectName('trayLabel')
            cl.addWidget(lbl)
            nav_key = {'players': 'players', 'guilds': 'guilds', 'bases': 'bases', 'pals': 'pal_editor'}.get(key)
            if nav_key and hasattr(self, 'parent_window') and self.parent_window:
                chip.mouseReleaseEvent = self._make_nav_release(nav_key)
            lay.addWidget(chip)
            self._stat_cards[key] = val
            self._stat_label_refs[key] = lbl
        lay.addStretch(1)
        return frame

    def _make_nav_release(self, nav_key):
        def _handler(event):
            if event.button() == Qt.LeftButton and hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.nexus_band.set_active(nav_key)
                self.parent_window._on_nav_changed(nav_key)
        return _handler

    def _create_campaign_strip(self):
        strip = QFrame()
        strip.setObjectName('campaignStrip')
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(16)
        kicker = QLabel((t('ops.campaign') if t else 'CAMPAIGN').upper())
        kicker.setObjectName('opsKicker')
        lay.addWidget(kicker)
        for idx, (tool_key, handler, hidx) in enumerate(self.CAMPAIGN_STEPS, start=1):
            btn = QPushButton(f'{idx:02d}  {t(tool_key) if t else tool_key}')
            btn.setObjectName('campaignStep')
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked=False, h=handler, i=hidx: getattr(self, h)(i))
            lay.addWidget(btn)
            self._campaign_btns.append((btn, tool_key))
        lay.addStretch(1)
        return strip

    def _create_mission_column(self, zone_key, rows):
        col = QWidget()
        col.setObjectName('missionColumn')
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        head = QLabel((t(zone_key) if t else zone_key).upper())
        head.setObjectName('missionZone')
        v.addWidget(head)
        v.addWidget(self._make_hairline())
        for tool_key, handler, hidx in rows:
            row = QPushButton()
            row.setObjectName('missionRow')
            row.setCursor(QCursor(Qt.PointingHandCursor))
            row.setMinimumHeight(44)
            name = t(tool_key) if t else tool_key
            desc_key = TOOL_DESCRIPTIONS.get(tool_key)
            desc = t(desc_key) if desc_key and t else ''
            row.setText(name)
            row.setToolTip(desc or name)
            row.clicked.connect(lambda checked=False, h=handler, i=hidx: getattr(self, h)(i))
            v.addWidget(row)
            self._mission_rows.append((row, tool_key))
        v.addStretch(1)
        return col

    @staticmethod
    def _make_hairline():
        line = QFrame()
        line.setObjectName('bandZoneRule')
        line.setFixedHeight(1)
        return line

    def _create_header_bar(self):
        return QWidget()
    def _on_save_path_label_clicked(self):
        if constants.current_save_path:
            import subprocess
            subprocess.Popen(['explorer', '/select,', os.path.join(constants.current_save_path, 'Level.sav')])
    def _setup_save_manager_connection(self):
        from palworld_aio.managers.save_manager import save_manager
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                save_manager.load_finished.disconnect(self._on_save_load_finished)
            except (TypeError, RuntimeError):
                pass
        save_manager.load_finished.connect(self._on_save_load_finished)
    def _on_load_save_clicked(self):
        if hasattr(self, 'parent_window') and self.parent_window:
            self.parent_window._load_save()
    def _on_load_xgp_clicked(self):
        if hasattr(self, 'parent_window') and self.parent_window:
            self.parent_window._load_xgp_save()
    def _on_save_load_finished(self, success):
        if success:
            if hasattr(self, '_save_path_label') and hasattr(constants, 'current_save_path') and constants.current_save_path:
                self._save_path_label.setText(constants.current_save_path)
                self._set_save_status('loaded')
            self.refresh()

    def _set_save_status(self, state):
        """state: 'no_save' | 'loaded' — styling via opsWorldName[state] QSS."""
        if hasattr(self, '_save_status_label'):
            text_key = 'tools.save_loaded' if state == 'loaded' else 'dashboard.no_save'
            self._save_status_label.setText(t(text_key) if t else text_key)
            self._save_status_label.setProperty('state', state)
            self._save_status_label.style().unpolish(self._save_status_label)
            self._save_status_label.style().polish(self._save_status_label)
        if hasattr(self, '_save_state_dot'):
            self._save_state_dot.setProperty('state', state)
            self._save_state_dot.style().unpolish(self._save_state_dot)
            self._save_state_dot.style().polish(self._save_state_dot)
    @staticmethod
    def _safe_list(data: dict, key: str) -> list:
        return data.get(key, {}).get('value', [])

    def _update_stats(self):
        from palworld_aio.managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        try:
            for key, label in self._stat_cards.items():
                raw = stats.get(key.title(), 0)
                try:
                    value = int(str(raw))
                except (TypeError, ValueError):
                    value = 0
                label.setText(str(value) if value else '—')
                label.setProperty('placeholder', 'false' if value else 'true')
                label.style().unpolish(label)
                label.style().polish(label)
        except (KeyError, AttributeError):
            pass
        if hasattr(self, 'parent_window') and self.parent_window and hasattr(self.parent_window, 'results_widget'):
            self.parent_window.results_widget.refresh_stats_after()
    def _import_and_call(self, module_name, function_name, *args):
        try:
            src_path = constants.get_src_path()
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            import importlib
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(*args) if args else func()
        except Exception as e:
            print(f'Error importing/calling {module_name}.{function_name}: {e}')
            traceback.print_exc()
            show_critical(self, t('Error') if t else 'Error', f'Failed to run tool: {e}')
            raise
    def _reset_save_session(self):
        if constants.loaded_level_json is None:
            return
        from palworld_aio.managers.save_manager import save_manager
        save_manager._reset_state()
        constants.invalidate_container_lookup()
        self._set_save_status('no_save')
        self._save_path_label.setText(t('tools.no_save_loaded') if t else 'No save loaded')
        for key in self._stat_cards:
            self._stat_cards[key].setText('—')
    def _run_converting_tool(self, index):
        self._reset_save_session()
        try:
            dialog = None
            if index == 0:
                options_dialog = ConversionOptionsDialog(self)
                self._animate_dialog_slide_in(options_dialog)
                result = options_dialog.exec()
                if result == QDialog.Accepted and options_dialog.selected_option is not None:
                    if options_dialog.selected_option == 0:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'json')
                    elif options_dialog.selected_option == 1:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'sav')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.game_pass_save_fix', 'game_pass_save_fix')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.convertids', 'convert_steam_id')
            elif index == 3:
                dialog = self._import_and_call('palworld_toolsets.restore_map', 'restore_map')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running converting tool {index}: {e}')
    def _run_management_tool(self, index):
        self._reset_save_session()
        try:
            dialog = None
            if index == 0:
                dialog = self._import_and_call('palworld_toolsets.slot_injector', 'slot_injector')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.character_transfer', 'character_transfer')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.fix_host_save', 'fix_host_save')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running management tool {index}: {e}')
    def _animate_dialog_slide_in(self, dialog):
        if dialog is None:
            return
        dialog.setWindowFlags(dialog.windowFlags() | Qt.Dialog)
        parent_window = self.window()
        if parent_window:
            dialog.setParent(parent_window)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.Window)
        dialog.adjustSize()
        center_window(dialog)
        dialog.setWindowOpacity(0.0)
        _main = self.parent_window
        if _main and _main.isVisible():
            QApplication.setQuitOnLastWindowClosed(False)
            _main.hide()
            restored = False

            def _show():
                nonlocal restored
                if restored:
                    return
                restored = True
                if _main:
                    _main.show()
                    _main.activateWindow()
                    _main.raise_()
                QApplication.setQuitOnLastWindowClosed(True)

            if isinstance(dialog, QDialog):
                dialog.finished.connect(lambda r: _show())
            dialog._restore_filter = _RestoreOnCloseFilter(_show, dialog)
            dialog.installEventFilter(dialog._restore_filter)
        dialog.show()
        self.fade_animation = QPropertyAnimation(dialog, b'windowOpacity')
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
    def _refresh_save_btns(self):
        import nerdfont as nf
        if hasattr(self, '_load_steam_btn') and self._load_steam_btn:
            self._load_steam_btn.setText(f"{nf.icons['nf-fa-steam']}  {t('tools.btn_steam')}")
        if hasattr(self, '_load_xgp_btn') and self._load_xgp_btn:
            self._load_xgp_btn.setText(f"{nf.icons['nf-fa-xbox']}  {t('tools.btn_gamepass')}")
    def refresh_labels(self):
        self._refresh_save_btns()
        if hasattr(self, '_load_btn') and self._load_btn:
            self._load_btn.setText(t('menu.file.load_save') if t else 'Load Save')
        if hasattr(self, '_save_path_label') and self._save_path_label:
            if not (hasattr(constants, 'current_save_path') and constants.current_save_path):
                self._save_path_label.setText(t('tools.no_save_loaded') if t else 'No save loaded')
                self._set_save_status('no_save')
            else:
                self._set_save_status('loaded')
        if hasattr(self, '_drag_hint_label') and self._drag_hint_label:
            self._drag_hint_label.setText(t('tools.drag_hint') if t else 'or drag & drop a Level.sav file here')
        for row, tool_key in self._mission_rows:
            label = t(tool_key) if t else tool_key
            row.setText(label)
            desc_key = TOOL_DESCRIPTIONS.get(tool_key)
            row.setToolTip((t(desc_key) if t else desc_key) if desc_key else label)
        for btn, tool_key in self._campaign_btns:
            idx = self._campaign_btns.index((btn, tool_key)) + 1
            btn.setText(f'{idx:02d}  {t(tool_key) if t else tool_key}')
        if hasattr(self.parent_window, '_drop_overlay'):
            self.parent_window._drop_overlay._drop_text = t('tools.drop_title') if t else 'Drop Level.sav to Load Save'
            self.parent_window._drop_overlay._drop_hint = t('tools.drop_hint_overlay') if t else "Or click the 'Load Save' button above"
            self.parent_window._drop_overlay.update()
        if hasattr(self, '_stat_label_refs'):
            for key, lbl in self._stat_label_refs.items():
                lbl.setText(t('dashboard.stat_' + key) if t else key)
    def refresh(self):
        self._update_stats()
