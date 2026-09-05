"""AppBar — shell v3 top bar (top-nav-shell tasks 2.1-2.3).

Replaces the floating WindowControls cluster and the NexusBand masthead/tray
with one 46px top bar, in reading order:

- brand: circular logo mark + "PalTrainer" wordmark (click = app menu popup)
- save chip: ShellState icon + label; click = save; spinner while
  loading/saving; dirty dot; update-available pulse
- context indicator: current PLAYER/GUILD/BASE selection (elided), click opens
  the statistics popover
- utilities: console, tab guide, warnings (badge), about
- window controls: minimize / maximize / close (right-aligned)

The whole bar is the frameless window drag strip; interactive children are
exempt (MainWindow routes presses through AppBar.hit_drag_zone).
"""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSize
from PyQt6.QtGui import QCursor, QPainter, QColor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QMenu,
)

from i18n import t
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.window_controls import WindowControls


def _txt(key: str, fallback: str) -> str:
    return t(key, default=fallback) if t else fallback


class _CompositeButton(QPushButton):
    """QPushButton hosting a child layout: sizeHint must reflect the layout,
    or the bar clips the chip/brand text to the bare button size."""

    def sizeHint(self) -> QSize:
        if self.layout() is not None:
            hint = self.layout().sizeHint()
            margins = self.layout().contentsMargins()
            return QSize(hint.width() + margins.left() + margins.right(),
                         hint.height() + margins.top() + margins.bottom())
        return super().sizeHint()


def _logo_path() -> str | None:
    try:
        from resource_resolver import resource_path
        path = resource_path(constants.get_base_path(), 'assets', 'branding', 'logo.png')
        return path if os.path.isfile(path) else None
    except Exception:
        return None


class BrandMark(_CompositeButton):
    """Logo mark + wordmark; click opens the app menu popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('brandMark')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(_txt('deletion.title', 'PalTrainer'))
        self.setAccessibleName(_txt('deletion.title', 'PalTrainer'))
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 2, 10, 2)
        row.setSpacing(8)
        self.mark = QLabel()
        self.mark.setObjectName('brandMarkIcon')
        self.mark.setFixedSize(22, 22)
        self.mark.setScaledContents(True)
        pix = self._load_round_logo()
        if pix is not None:
            self.mark.setPixmap(pix)
        row.addWidget(self.mark)
        # Product name is a brand constant, not translated.
        self.wordmark = QLabel('PalTrainer')
        self.wordmark.setObjectName('brandWordmark')
        row.addWidget(self.wordmark)

    @staticmethod
    def _load_round_logo():
        from PyQt6.QtGui import QPixmap
        path = _logo_path()
        if not path:
            return None
        source = QPixmap(path)
        if source.isNull():
            return None
        size = 44
        scaled = source.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        from PyQt6.QtCore import QRectF
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        from PyQt6.QtGui import QPainterPath
        clip = QPainterPath()
        clip.addEllipse(QRectF(0, 0, size, size))
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        dpr = _screen_dpr()
        out.setDevicePixelRatio(dpr)
        return out

    # pulse support (update available) — tint border via property
    def set_pulse(self, on: bool) -> None:
        self.setProperty('pulse', 'true' if on else 'false')
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class SaveStateChip(_CompositeButton):
    """Shell state chip: icon + state label, click = save, dirty dot."""

    _STATE_ICONS = {
        'no_save': None,
        'loading': 'spinner',
        'loaded': 'check_circle',
        'dirty': 'save_state',
        'saving': 'spinner',
        'error': 'close',
    }
    _STATE_TEXT_KEYS = {
        'no_save': ('tray.state.no_save', 'No save'),
        'loading': ('tray.state.loading', 'Loading'),
        'loaded': ('tray.state.loaded', 'Loaded'),
        'dirty': ('tray.state.dirty', 'Unsaved'),
        'saving': ('tray.state.saving', 'Saving'),
        'error': ('tray.state.error', 'Error'),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('saveStateChip')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(_txt('menu.file.save_changes', 'Save Changes'))
        self.setAccessibleName(_txt('menu.file.save_changes', 'Save Changes'))
        self._state_key = 'no_save'
        self._spin_angle = 0
        self._spin_timer: QTimer | None = None
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 2, 10, 2)
        row.setSpacing(6)
        self._icon_label = QLabel()
        self._icon_label.setObjectName('saveChipIcon')
        self._icon_label.setFixedSize(14, 14)
        row.addWidget(self._icon_label)
        self._text_label = QLabel(_txt(*SaveStateChip._STATE_TEXT_KEYS['no_save']))
        self._text_label.setObjectName('saveChipText')
        row.addWidget(self._text_label)
        # dirty dot paints over the chip (top-right corner)
        self._dirty_dot = QLabel(self)
        self._dirty_dot.setObjectName('saveChipDirtyDot')
        self._dirty_dot.setFixedSize(7, 7)
        self._dirty_dot.setVisible(False)
        self.apply_state('no_save')

    # ------------------------------------------------------------- state
    def apply_state(self, key: str) -> None:
        if key not in self._STATE_ICONS:
            key = 'no_save'
        self._state_key = key
        self._stop_spin()
        self._render_icon()
        self._text_label.setText(_txt(*self._STATE_TEXT_KEYS[key]))
        self.setProperty('state', key)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        if key in ('loading', 'saving'):
            self._spin_timer = QTimer(self)
            self._spin_timer.timeout.connect(self._tick_spin)
            self._spin_timer.start(120)

    def _render_icon(self) -> None:
        name = self._STATE_ICONS.get(self._state_key)
        if not name:
            self._icon_label.clear()
            return
        role_by_state = {
            'loaded': 'success',
            'dirty': 'warning',
            'error': 'danger',
        }
        role = role_by_state.get(self._state_key, 'text_secondary')
        pix = app_icons.get_pixmap(name, None, 14, dpr=self.devicePixelRatioF(),
                                   role=role)
        if self._state_key in ('loading', 'saving'):
            from PyQt6.QtGui import QTransform
            pix = pix.transformed(QTransform().rotate(self._spin_angle))
        self._icon_label.setPixmap(pix)

    def _tick_spin(self) -> None:
        self._spin_angle = (self._spin_angle + 30) % 360
        self._render_icon()

    def _stop_spin(self) -> None:
        if self._spin_timer is not None:
            self._spin_timer.stop()
            self._spin_timer = None
        self._spin_angle = 0

    def set_dirty(self, dirty: bool) -> None:
        self._dirty_dot.setVisible(bool(dirty))

    def set_shell_state(self, state) -> None:
        try:
            from palworld_aio.shell_state import ShellState
            key = state.value if isinstance(state, ShellState) else str(state)
        except (ImportError, AttributeError):
            key = str(state)
        self.apply_state(key)

    def set_loading_state(self, state: str) -> None:
        """loading_manager 'header' mode contract (constants.header_loading_widget)."""
        if state == 'loading':
            self.apply_state('loading')
        elif state == 'idle':
            if self._state_key in ('loading', 'saving'):
                self.apply_state('no_save')

    def pulse_update(self, on: bool) -> None:
        self.setProperty('pulse', 'true' if on else 'false')
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class ContextIndicator(_CompositeButton):
    """Current selection context (PLAYER/GUILD/BASE); click opens stats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('contextIndicator')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(_txt('deletion.results_panel', 'Selection'))
        self.setAccessibleName(_txt('deletion.results_panel', 'Selection'))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 8, 2)
        lay.setSpacing(8)
        self._col = QVBoxLayout()
        self._col.setContentsMargins(0, 1, 0, 1)
        self._col.setSpacing(0)
        self.player_label = self._make_row()
        self.guild_label = self._make_row()
        self.base_label = self._make_row()
        self._col.addWidget(self.player_label)
        self._col.addWidget(self.guild_label)
        self._col.addWidget(self.base_label)
        lay.addLayout(self._col)

    def _make_row(self) -> QLabel:
        label = QLabel('—')
        label.setObjectName('contextRow')
        label.setFixedWidth(120)
        return label

    @staticmethod
    def _set_row(label: QLabel, prefix: str, value) -> None:
        text = f'{prefix} {value}' if value else prefix
        fm = label.fontMetrics()
        label.setText(fm.elidedText(text, Qt.TextElideMode.ElideRight,
                                    label.width() - 4))
        label.setToolTip(str(value) if value else '')

    def set_player(self, name) -> None:
        self._set_row(self.player_label, _txt('deletion.selected_player_label', 'Player'), name)

    def set_guild(self, name) -> None:
        self._set_row(self.guild_label, _txt('deletion.selected_guild_label', 'Guild'), name)

    def set_base(self, base_id) -> None:
        self._set_row(self.base_label, _txt('deletion.selected_base_label', 'Base'), base_id)

    def clear_selection(self) -> None:
        self.set_player(None)
        self.set_guild(None)
        self.set_base(None)


class UtilityButton(QPushButton):
    """Icon-only app bar utility button."""

    def __init__(self, icon_name: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setObjectName('appBarUtility')
        self.setIcon(app_icons.get_qicon(icon_name, role='text_secondary'))
        self.setFixedSize(30, 26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self._icon_name = icon_name

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self.setIcon(app_icons.get_qicon(name, role='text_secondary'))


class AppBar(QFrame):
    """Shell v3 top bar. Owns brand, save chip, context, utilities, controls."""

    save_clicked = pyqtSignal()
    console_toggled = pyqtSignal()
    guide_clicked = pyqtSignal()
    about_clicked = pyqtSignal()
    masthead_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('appBar')
        self.setFixedHeight(46)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        self.brand = BrandMark()
        self.brand.clicked.connect(self.masthead_clicked.emit)
        lay.addWidget(self.brand)

        self.save_chip = SaveStateChip()
        self.save_chip.clicked.connect(self.save_clicked.emit)
        lay.addWidget(self.save_chip)

        self.context = ContextIndicator()
        lay.addWidget(self.context)

        lay.addStretch(1)

        self.console_btn = UtilityButton('console', _txt('console.detach', 'Console'))
        self.console_btn.clicked.connect(self.console_toggled.emit)
        lay.addWidget(self.console_btn)
        self.guide_btn = UtilityButton('toolbox', _txt('tab_guide.tooltip', 'Tab Usage Guide'))
        self.guide_btn.clicked.connect(self.guide_clicked.emit)
        lay.addWidget(self.guide_btn)
        self.warn_btn = UtilityButton('warning', _txt('warning.title', 'Warnings'))
        self.warn_btn.setObjectName('appBarWarnBtn')
        self.warn_btn.setVisible(False)
        lay.addWidget(self.warn_btn)
        self.about_btn = UtilityButton('info', _txt('about.title', 'About PalTrainer'))
        self.about_btn.clicked.connect(self.about_clicked.emit)
        lay.addWidget(self.about_btn)

        self.window_controls = WindowControls(self)
        lay.addSpacing(6)
        lay.addWidget(self.window_controls)

        self._warn_slot = None

    # ------------------------------------------------------------ wiring
    def set_warning_slot(self, slot) -> None:
        self._warn_slot = slot

    def show_warning(self, show: bool = True) -> None:
        self.warn_btn.setVisible(show)

    def _noop_warn(self) -> None:
        if self._warn_slot is not None:
            self._warn_slot()

    def connect_warn(self) -> None:
        try:
            self.warn_btn.clicked.disconnect(self._noop_warn)
        except TypeError:
            pass
        self.warn_btn.clicked.connect(self._noop_warn)

    # --------------------------------------------------- drag zone check
    def hit_drag_zone(self, pos_on_bar) -> bool:
        """True when pos_on_bar (AppBar-local) is over non-interactive space."""
        child = self.childAt(pos_on_bar)
        while child is not None:
            if isinstance(child, (QPushButton, QMenu)):
                return False
            if child is self:
                break
            child = child.parentWidget()
        return True

    # ---------------------------------------------------------- i18n
    def refresh_labels(self) -> None:
        self.save_chip.setToolTip(_txt('menu.file.save_changes', 'Save Changes'))
        self.console_btn.setToolTip(_txt('console.detach', 'Console'))
        self.guide_btn.setToolTip(_txt('tab_guide.tooltip', 'Tab Usage Guide'))
        self.warn_btn.setToolTip(_txt('warning.title', 'Warnings'))
        self.about_btn.setToolTip(_txt('about.title', 'About PalTrainer'))


def _screen_dpr() -> float:
    from PyQt6.QtGui import QGuiApplication
    screen = QGuiApplication.primaryScreen()
    return screen.devicePixelRatio() if screen else 1.0
