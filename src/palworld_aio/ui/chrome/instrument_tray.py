"""InstrumentTray — save state, selection, and statistics altitudes of the
NexusBand (plan 020).

The tray occupies the middle of the band. It shows:

- save altitude: one compact state row; click triggers save; spinner while
  loading/saving; dirty pulses
- selection altitude: PLAYER / GUILD / BASE micro rows (legacy
  set_player/set_guild/set_base call sites feed these)
- metrics altitude: players/guilds/bases/pals mini counts with an Expand
  affordance that opens the TrayDrawer (canvas-local overlay owned by
  MainWindow; see plan 020 §4.2)

The TrayDrawer hosts the existing StatsPanel unchanged (before/after/result
deltas, copy button) — behavior preserved, geometry replaced.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect,
)

from i18n import t
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.widgets.stats_panel import StatsPanel

_SPIN_FRAMES = '\u25D0\u25D3\u25D1\u25D2'


def _txt(key: str, fallback: str) -> str:
    return t(key) if t else fallback


class _StateRow(QPushButton):
    """Save-state altitude: icon + micro text; whole row is the save action."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('trayStateRow')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedHeight(30)
        self._icon_label = QLabel(self)
        self._icon_label.setObjectName('trayStateIcon')
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setGeometry(4, 3, 22, 24)
        self._text_label = QLabel(self)
        self._text_label.setObjectName('trayStateText')
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._text_label.setGeometry(28, 3, 44, 24)

    def set_state(self, icon: str, text: str, state_key: str) -> None:
        self._icon_label.setText(icon)
        self._text_label.setText(text)
        self._icon_label.setProperty('state', state_key)
        self.setProperty('state', state_key)
        for w in (self._icon_label, self._text_label, self):
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()

    def set_spin(self, frame: str) -> None:
        self._icon_label.setText(frame)


class _SelectionRow(QWidget):
    def __init__(self, label_key: str, fallback: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 1, 6, 1)
        lay.setSpacing(2)
        self.name_label = QLabel(_txt(label_key, fallback))
        self.name_label.setObjectName('trayLabel')
        self.value_label = QLabel('—')
        self.value_label.setObjectName('trayValue')
        self.value_label.setProperty('placeholder', 'true')
        self.value_label.setWordWrap(True)
        lay.addWidget(self.name_label)
        lay.addStretch(1)
        lay.addWidget(self.value_label)

    def set_value(self, name) -> None:
        if name:
            self.value_label.setText(str(name))
            self.value_label.setProperty('placeholder', 'false')
            self.value_label.setToolTip(str(name))
        else:
            self.value_label.setText('—')
            self.value_label.setProperty('placeholder', 'true')
            self.value_label.setToolTip('')
        self.value_label.style().unpolish(self.value_label)
        self.value_label.style().polish(self.value_label)

    def refresh_label(self, label_key: str, fallback: str) -> None:
        self.name_label.setText(_txt(label_key, fallback))


class _MetricRow(QWidget):
    """Field report: four mono counts in a 2x2 micro grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('trayMetrics')
        grid = QVBoxLayout(self)
        grid.setContentsMargins(4, 2, 4, 2)
        grid.setSpacing(0)
        self._metrics = {}
        pairs = [
            ('players', 'deletion.stats.players', 'Players'),
            ('guilds', 'deletion.stats.guilds', 'Guilds'),
            ('bases', 'deletion.stats.bases', 'Bases'),
            ('pals', 'deletion.stats.pals', 'Pals'),
        ]
        for idx, (key, label_key, fallback) in enumerate(pairs):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(2, 0, 2, 0)
            rl.setSpacing(2)
            name = QLabel(_txt(label_key, fallback))
            name.setObjectName('trayLabel')
            value = QLabel('—')
            value.setObjectName('trayMetricValue')
            value.setProperty('placeholder', 'true')
            rl.addWidget(name)
            rl.addStretch(1)
            rl.addWidget(value)
            grid.addWidget(row)
            self._metrics[key] = value

    def set_metrics(self, stats: dict) -> None:
        for key, label in self._metrics.items():
            raw = stats.get(key.title(), stats.get(key, 0)) if stats else 0
            try:
                value = int(str(raw))
            except (TypeError, ValueError):
                value = 0
            label.setText(str(value) if value else '—')
            label.setProperty('placeholder', 'false' if value else 'true')
            label.style().unpolish(label)
            label.style().polish(label)

    def refresh_labels(self) -> None:
        # labels are rebuilt on language switch via refresh_all; keep simple
        pass


class _SectionHeader(QLabel):
    def __init__(self, key: str, fallback: str, parent=None):
        super().__init__(_txt(key, fallback), parent)
        self.setObjectName('traySection')
        self._key = key
        self._fallback = fallback

    def refresh(self) -> None:
        self.setText(_txt(self._key, self._fallback))


class InstrumentTray(QWidget):
    """Middle altitude block of the NexusBand."""

    save_clicked = pyqtSignal()
    expand_requested = pyqtSignal()

    _STATE_ICONS = {
        'no_save': ('', 'no_save'),
        'loading': (_SPIN_FRAMES[0], 'loading'),
        'loaded': ('\uf00c', 'loaded'),
        'dirty': ('\uf071', 'dirty'),
        'saving': (_SPIN_FRAMES[0], 'saving'),
        'error': ('\uf00d', 'error'),
    }
    _STATE_TEXT = {
        'no_save': 'No save',
        'loading': 'Loading',
        'loaded': 'Loaded',
        'dirty': 'Unsaved',
        'saving': 'Saving',
        'error': 'Error',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('instrumentTray')
        self._shell_state = 'no_save'
        self._spin_frame = 0
        self._spin_timer: QTimer | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(1)

        self.state_row = _StateRow()
        self.state_row.clicked.connect(self.save_clicked.emit)
        self.state_row.setToolTip(_txt('menu.file.save_changes', 'Save Changes'))
        self.state_row.setAccessibleName(_txt('menu.file.save_changes', 'Save Changes'))
        lay.addWidget(self.state_row)

        rule = QFrame()
        rule.setObjectName('bandZoneRule')
        rule.setFixedHeight(1)
        lay.addWidget(rule)

        self.sel_header = _SectionHeader('deletion.results_panel', 'Selection')
        lay.addWidget(self.sel_header)
        self.player_row = _SelectionRow('deletion.selected_player_label', 'Player')
        self.guild_row = _SelectionRow('deletion.selected_guild_label', 'Guild')
        self.base_row = _SelectionRow('deletion.selected_base_label', 'Base')
        lay.addWidget(self.player_row)
        lay.addWidget(self.guild_row)
        lay.addWidget(self.base_row)

        rule2 = QFrame()
        rule2.setObjectName('bandZoneRule')
        rule2.setFixedHeight(1)
        lay.addWidget(rule2)

        self.stats_header = _SectionHeader('deletion.stats_panel', 'Statistics')
        lay.addWidget(self.stats_header)
        self.metric_row = _MetricRow()
        lay.addWidget(self.metric_row)
        self.expand_btn = QPushButton(f'{app_icons.get_icon("chevron_up")}  {_txt("sidebar.open", "Expand")}')
        self.expand_btn.setObjectName('trayExpandBtn')
        self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_btn.setFixedHeight(22)
        self.expand_btn.clicked.connect(self.expand_requested.emit)
        lay.addWidget(self.expand_btn)

        self._apply_state('no_save')

    # ------------------------------------------------------------ state
    def _apply_state(self, key: str) -> None:
        icon, state_key = self._STATE_ICONS.get(key, ('', 'no_save'))
        self.state_row.set_state(icon, self._STATE_TEXT.get(key, key), state_key)

    def set_shell_state(self, state) -> None:
        """Reflect ShellStateModel lifecycle (same enum values as old header)."""
        try:
            from palworld_aio.shell_state import ShellState
            key = state.value if isinstance(state, ShellState) else str(state)
        except (ImportError, AttributeError):
            key = str(state)
        self._shell_state = key
        self._stop_spin()
        self._apply_state(key)
        if key in ('loading', 'saving'):
            self._spin_timer = QTimer(self)
            self._spin_timer.timeout.connect(self._tick_spin)
            self._spin_timer.start(200)

    def set_loading_state(self, state: str) -> None:
        """loading_manager 'header' mode contract (constants.header_loading_widget)."""
        if state == 'loading':
            self.set_shell_state('loading')
        elif state == 'idle':
            # real shell signals restore the true state; only clear a spinner
            # that was started by this path without a matching lifecycle event
            if self._shell_state in ('loading', 'saving') and self._spin_timer is not None:
                self._stop_spin()
                self._apply_state('no_save')

    def _tick_spin(self) -> None:
        self._spin_frame = (self._spin_frame + 1) % 4
        try:
            self.state_row.set_spin(_SPIN_FRAMES[self._spin_frame])
        except RuntimeError:
            self._stop_spin()

    def _stop_spin(self) -> None:
        if self._spin_timer is not None:
            self._spin_timer.stop()
            self._spin_timer = None
        self._spin_frame = 0

    def set_dirty(self, dirty: bool) -> None:
        if dirty and self._shell_state == 'loaded':
            self._apply_state('dirty')
        elif not dirty and self._shell_state == 'dirty':
            self._apply_state('loaded')

    # -------------------------------------------------------- selection
    def set_player(self, name) -> None:
        self.player_row.set_value(name)

    def set_guild(self, name) -> None:
        self.guild_row.set_value(name)

    def set_base(self, base_id) -> None:
        self.base_row.set_value(base_id)

    def clear_selection(self) -> None:
        self.set_player(None)
        self.set_guild(None)
        self.set_base(None)

    # ---------------------------------------------------------- metrics
    def update_metrics(self, stats: dict) -> None:
        self.metric_row.set_metrics(stats)

    # ----------------------------------------------------------- drawer
    def is_expanded(self) -> bool:
        try:
            return self._expanded  # type: ignore[attr-defined]
        except AttributeError:
            return False

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)  # type: ignore[attr-defined]
        icon = app_icons.get_icon('chevron_up' if expanded else 'chevron_down')
        label = _txt('sidebar.close', 'Collapse') if expanded else _txt('sidebar.open', 'Expand')
        self.expand_btn.setText(f'{icon}  {label}')

    # ----------------------------------------------------------- labels
    def refresh_labels(self) -> None:
        self.state_row.setToolTip(_txt('menu.file.save_changes', 'Save Changes'))
        self.state_row.setAccessibleName(_txt('menu.file.save_changes', 'Save Changes'))
        self.sel_header.refresh()
        self.stats_header.refresh()
        self.player_row.refresh_label('deletion.selected_player_label', 'Player')
        self.guild_row.refresh_label('deletion.selected_guild_label', 'Guild')
        self.base_row.refresh_label('deletion.selected_base_label', 'Base')


class TrayDrawer(QFrame):
    """Canvas-local overlay (child of the central widget, not a window) with
    the full statistics grid. Esc / scrim click close it (MainWindow wires)."""

    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('trayDrawer')
        self.setFixedWidth(360)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        head = QHBoxLayout()
        title = QLabel(_txt('deletion.stats_panel', 'Statistics'))
        title.setObjectName('drawerTitle')
        head.addWidget(title)
        head.addStretch(1)
        close_btn = QPushButton(app_icons.get_icon('close'))
        close_btn.setObjectName('drawerCloseBtn')
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setToolTip(_txt('button.close', 'Close'))
        close_btn.clicked.connect(self.close_requested.emit)
        head.addWidget(close_btn)
        lay.addLayout(head)
        self.stats_panel = StatsPanel()
        self.stats_panel.setObjectName('statsGrid')
        lay.addWidget(self.stats_panel, stretch=1)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 130))
        self.setGraphicsEffect(shadow)

    def refresh_labels(self) -> None:
        self.stats_panel.refresh_labels()
