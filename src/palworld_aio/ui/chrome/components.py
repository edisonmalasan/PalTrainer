"""Shared PyQt6 component library (UI overhaul plan 003).

Factories and small widget classes used by every migrated screen. Components
set objectNames/dynamic properties only — all styling lives in the QSS builder
(chrome/qss_builder.py). Keep public APIs stable: screens across the app
consume these.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence
from PyQt6.QtCore import QPoint, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog as _QtInputDialog,
    QMessageBox as _QtMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome import fonts
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import HEIGHT, SPACING, TYPE

try:
    from i18n import t
except ImportError:  # pragma: no cover - standalone component use
    t = None

_LEVELS = ('neutral', 'success', 'warning', 'danger', 'info', 'special', 'accent')
_BUTTON_TIERS = ('primary', 'secondary', 'tertiary', 'warning', 'destructive')
_BUTTON_ROLE = {
    'default': 'secondary',
    'primary': 'primary',
    'secondary': 'secondary',
    'tertiary': 'tertiary',
    'warning': 'warning',
    'destructive': 'destructive',
    # Compatibility names used by screens awaiting migration.
    'danger': 'destructive',
    'ghost': 'tertiary',
    'tool': 'icon',
}


def _polish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------
def make_panel(parent: Optional[QWidget] = None, padding: int = SPACING['lg']) -> QFrame:
    panel = QFrame(parent)
    panel.setProperty('class', 'panel')
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(SPACING['sm'])
    return panel


def make_card(parent: Optional[QWidget] = None, padding: int = SPACING['md']) -> QFrame:
    card = QFrame(parent)
    card.setProperty('class', 'card')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(SPACING['sm'])
    return card


def make_hdivider() -> QFrame:
    line = QFrame()
    line.setProperty('class', 'divider')
    line.setFrameShape(QFrame.Shape.NoFrame)
    line.setFixedHeight(1)
    return line


def make_vdivider(height: int = 20) -> QFrame:
    line = QFrame()
    line.setProperty('class', 'divider')
    line.setProperty('vertical', True)
    line.setFrameShape(QFrame.Shape.NoFrame)
    line.setFixedWidth(1)
    line.setFixedHeight(height)
    return line


# ---------------------------------------------------------------------------
# Text labels
# ---------------------------------------------------------------------------
def make_label(text: str, kind: str = 'body', parent: Optional[QWidget] = None) -> QLabel:
    label = QLabel(text, parent)
    if kind in ('display', 'title', 'section', 'secondary', 'micro', 'mono'):
        label.setProperty('class', kind)
    label.setFont(fonts.body_font(px=TYPE.get(kind, TYPE['body'])[0]))
    return label


def section_header(text: str, parent: Optional[QWidget] = None) -> QWidget:
    """Section title row with optional trailing content added by the caller."""
    container = QWidget(parent)
    row = QHBoxLayout(container)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(SPACING['sm'])
    label = make_label(text, 'section')
    row.addWidget(label)
    row.addStretch(1)
    container._row = row
    return container


def title_label(text: str, parent: Optional[QWidget] = None) -> QLabel:
    return make_label(text, 'title', parent)


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
def make_button(
    text: str,
    kind: str = 'default',
    icon: Optional[str] = None,
    tooltip: str = '',
    parent: Optional[QWidget] = None,
) -> QPushButton:
    """Create a text action with a semantic hierarchy and accessible name.

    Canonical tiers are primary, secondary, tertiary, warning and destructive.
    ``default``, ``danger``, ``ghost`` and ``tool`` remain compatibility names
    until their owning pages migrate.
    """
    if kind not in _BUTTON_ROLE:
        raise ValueError(f'unknown button kind {kind!r}')
    btn = QPushButton(text, parent)
    if kind != 'default':
        btn.setProperty('class', kind)
    btn.setProperty('controlRole', _BUTTON_ROLE[kind])
    if icon:
        btn.setIcon(app_icons.get_qicon(icon, role='text_secondary'))
        btn.setText(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    btn.setMinimumHeight(HEIGHT['comfortable'])
    btn.setAccessibleName(text or tooltip or tr('ui.action.generic', 'Action'))
    if tooltip:
        btn.setToolTip(tooltip)
        btn.setAccessibleDescription(tooltip)
    return btn


def make_tool_button(icon: str, tooltip: str = '', parent: Optional[QWidget] = None) -> QPushButton:
    """Icon-only button; ``icon`` is an SVG registry name (icon factory)."""
    btn = QPushButton(parent)
    btn.setProperty('class', 'icon')
    btn.setProperty('controlRole', 'icon')
    icon_obj = app_icons.get_qicon(icon, role='text_secondary')
    if icon_obj is not None:
        btn.setIcon(icon_obj)
    btn.setFixedSize(HEIGHT['comfortable'], HEIGHT['comfortable'])
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    accessible_label = tooltip or tr(
        'ui.icon.accessible', '{name} button', name=icon.replace('_', ' ').title())
    btn.setAccessibleName(accessible_label)
    btn.setToolTip(accessible_label)
    return btn


def make_danger_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'danger', parent=parent)


def make_ghost_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'ghost', parent=parent)


def make_warning_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'warning', parent=parent)


def make_destructive_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'destructive', parent=parent)


def make_chip(
    text: str,
    *,
    checked: bool = False,
    checkable: bool = True,
    parent: Optional[QWidget] = None,
) -> QPushButton:
    chip = QPushButton(text, parent)
    chip.setProperty('class', 'chip')
    chip.setProperty('controlRole', 'chip')
    chip.setCheckable(checkable)
    chip.setChecked(checked if checkable else False)
    chip.setCursor(Qt.CursorShape.PointingHandCursor)
    chip.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    chip.setAccessibleName(text)
    return chip


def make_tab_button(
    text: str,
    route_id: str,
    *,
    checked: bool = False,
    parent: Optional[QWidget] = None,
) -> QPushButton:
    tab = make_chip(text, checked=checked, parent=parent)
    tab.setProperty('class', 'tab')
    tab.setProperty('controlRole', 'tab')
    tab.setProperty('routeId', route_id)
    return tab


def make_filter_button(
    text: str,
    *,
    checked: bool = False,
    parent: Optional[QWidget] = None,
) -> QPushButton:
    button = make_chip(text, checked=checked, parent=parent)
    button.setProperty('class', 'filter')
    button.setProperty('controlRole', 'filter')
    return button


class SegmentedControl(QWidget):
    """Exclusive labeled choices presented as one keyboard-reachable control."""

    currentChanged = pyqtSignal(str)

    def __init__(
        self,
        options: Sequence[tuple[str, str]],
        *,
        current: Optional[str] = None,
        accessible_name: str = '',
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        if not options:
            raise ValueError('segmented control requires at least one option')
        ids = [option_id for option_id, _label in options]
        if len(ids) != len(set(ids)):
            raise ValueError('segmented option IDs must be unique')
        if current is not None and current not in ids:
            raise ValueError(f'unknown current option {current!r}')

        self.setProperty('class', 'segmented')
        self.setProperty('controlRole', 'segmented')
        self.setAccessibleName(accessible_name or tr('ui.segmented.options', 'Options'))
        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        selected = current or ids[0]
        last = len(options) - 1
        for index, (option_id, label) in enumerate(options):
            button = QPushButton(label, self)
            button.setProperty('class', 'segmented')
            button.setProperty(
                'segmentPosition',
                'only' if last == 0 else 'start' if index == 0 else 'end' if index == last else 'middle',
            )
            button.setProperty('optionId', option_id)
            button.setCheckable(True)
            button.setChecked(option_id == selected)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName(label)
            button.clicked.connect(
                lambda checked, key=option_id: self.currentChanged.emit(key) if checked else None
            )
            self._group.addButton(button)
            self._buttons[option_id] = button
            row.addWidget(button)

    def current(self) -> str:
        return next(key for key, button in self._buttons.items() if button.isChecked())

    def set_current(self, option_id: str) -> None:
        if option_id not in self._buttons:
            raise KeyError(option_id)
        if self.current() == option_id:
            return
        self._buttons[option_id].setChecked(True)
        self.currentChanged.emit(option_id)


def set_control_tooltip(
    widget: QWidget,
    text: str,
    *,
    accessible_description: str = '',
) -> None:
    """Attach concise help without leaving assistive technology behind."""
    if not text.strip():
        raise ValueError('tooltip text must not be empty')
    widget.setToolTip(text)
    widget.setAccessibleDescription(accessible_description or text)


# ---------------------------------------------------------------------------
# Status indicators
# ---------------------------------------------------------------------------
def make_badge(text: str, level: str = 'neutral', parent: Optional[QWidget] = None) -> QLabel:
    badge = QLabel(text, parent)
    badge.setProperty('badge', level if level in _LEVELS else 'neutral')
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return badge


def set_badge_level(badge: QLabel, level: str) -> None:
    badge.setProperty('badge', level if level in _LEVELS else 'neutral')
    _polish(badge)


def make_status_dot(level: str = 'neutral', size: int = 8, parent: Optional[QWidget] = None) -> QLabel:
    dot = QLabel(parent)
    dot.setProperty('class', 'dot')
    dot.setProperty('level', level if level in _LEVELS else 'neutral')
    dot.setFixedSize(size, size)
    dot.setStyleSheet(f'border-radius: {size // 2}px;')
    return dot


def set_dot_level(dot: QLabel, level: str) -> None:
    dot.setProperty('level', level if level in _LEVELS else 'neutral')
    _polish(dot)


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------
def make_search_field(
    placeholder: str = '',
    on_change: Optional[Callable[[str], None]] = None,
    parent: Optional[QWidget] = None,
) -> tuple[QFrame, QLineEdit]:
    """Bordered search field with a search icon. Returns (container, line_edit)."""
    container = QFrame(parent)
    container.setProperty('class', 'searchField')
    container.setProperty('controlRole', 'search')
    row = QHBoxLayout(container)
    row.setContentsMargins(SPACING['sm'], 2, SPACING['sm'], 2)
    row.setSpacing(SPACING['sm'])
    glyph = QLabel(container)
    glyph.setPixmap(app_icons.get_pixmap('search', role='text_secondary', size=12))
    glyph.setFixedSize(12, 12)
    line = QLineEdit(container)
    line.setFrame(False)
    line.setFont(fonts.body_font())
    line.setClearButtonEnabled(True)
    line.setAccessibleName(placeholder or tr('ui.search.accessible_name', 'Search'))
    line.setMinimumHeight(HEIGHT['default'] - 6)
    if placeholder:
        line.setPlaceholderText(placeholder)
    if on_change is not None:
        line.textChanged.connect(on_change)
    row.addWidget(glyph)
    row.addWidget(line, 1)
    return container, line


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
class ErrorBanner(QFrame):
    """Inline dismissible error surface."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty('class', 'errorBanner')
        self.hide()
        row = QHBoxLayout(self)
        row.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        row.setSpacing(SPACING['sm'])
        self._label = QLabel('')
        self._label.setWordWrap(True)
        self._close = make_tool_button('close')
        self._close.clicked.connect(self.hide)
        row.addWidget(self._label, 1)
        row.addWidget(self._close)

    def show_error(self, message: str) -> None:
        self._label.setText(message)
        self.show()

    def clear(self) -> None:
        self._label.setText('')
        self.hide()


class Toast(QFrame):
    """Ephemeral notification anchored to the parent widget, auto-dismissing."""

    _ICONS = {'success': 'check', 'warning': 'warning', 'danger': 'close', 'info': 'info'}

    def __init__(self, message: str, level: str = 'success',
                 duration_ms: int = 3000, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty('class', 'toast')
        self.setProperty('toast_level', level if level in _LEVELS else 'info')
        self.setWindowFlags(Qt.WindowType.ToolTip)
        row = QHBoxLayout(self)
        row.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        row.setSpacing(SPACING['sm'])
        glyph = QLabel()
        glyph.setPixmap(app_icons.get_pixmap(
            self._ICONS.get(level, self._ICONS['info']),
            role=level if level in app_icons.ROLE_COLORS else 'text_secondary', size=12))
        glyph.setFixedSize(12, 12)
        glyph.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text = QLabel(message)
        text.setWordWrap(True)
        row.addWidget(glyph)
        row.addWidget(text, 1)
        self.adjustSize()
        if parent is not None:
            anchor = parent.rect().bottomRight()
            self.move(parent.mapToGlobal(anchor) -
                      self.rect().bottomRight() -
                      QPoint(SPACING['lg'], SPACING['lg']))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)
        self._timer.start(duration_ms)


def show_toast(message: str, level: str = 'success',
               parent: Optional[QWidget] = None, duration_ms: int = 3000) -> Toast:
    toast = Toast(message, level, duration_ms, parent)
    toast.show()
    return toast


# ---------------------------------------------------------------------------
# Data views
# ---------------------------------------------------------------------------
class DataTable(QWidget):
    """Dense data table: styled headers, hover/selected rows, empty state hook.

    Wraps QTableWidget so per-screen code never hand-styles tables. Columns are
    Interactive-resizable with the last column stretching.
    """

    HEADER_ROW = 28

    def __init__(self, columns: list[str], parent: Optional[QWidget] = None):
        from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QVBoxLayout

        super().__init__(parent)
        self._table = QTableWidget(self)
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(columns)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.setWordWrap(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(28)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)
        self._empty_label: Optional[QLabel] = None

    @property
    def table(self):
        return self._table

    def set_empty_state(self, message: str) -> None:
        if message and self._empty_label is None:
            self._empty_label = QLabel(message, self)
            self._empty_label.setProperty('class', 'secondary')
            self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._table.hide()
            self.layout().addWidget(self._empty_label)
        elif not message and self._empty_label is not None:
            self._empty_label.deleteLater()
            self._empty_label = None
            self._table.show()
        elif self._empty_label is not None:
            self._empty_label.setText(message)


# ---------------------------------------------------------------------------
# Dialog scaffold
# ---------------------------------------------------------------------------
class BulkWorkflowReview(QFrame):
    """Shared source/target/review summary for consequential bulk workflows.

    The widget owns presentation state only. Callers retain their existing
    validation, signals, manager callbacks, and mutation functions.
    """

    def __init__(
        self,
        source: str = '',
        target: str = '',
        review: str = '',
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName('bulkWorkflowReview')
        self.setAccessibleName(tr('ui.bulk.review', 'Bulk action review'))
        root = QVBoxLayout(self)
        root.setContentsMargins(
            SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        root.setSpacing(SPACING['xs'])
        self.source_value = self._add_row(
            root, tr('ui.bulk.source', 'Source'), source)
        self.target_value = self._add_row(
            root, tr('ui.bulk.target', 'Target'), target)
        self.review_value = self._add_row(
            root, tr('ui.bulk.review', 'Review'), review)
        self.risk_label = QLabel('', self)
        self.risk_label.setObjectName('bulkWorkflowRisk')
        self.risk_label.setWordWrap(True)
        self.risk_label.hide()
        root.addWidget(self.risk_label)
        self.backup_label = QLabel('', self)
        self.backup_label.setObjectName('bulkWorkflowBackup')
        self.backup_label.setWordWrap(True)
        self.backup_label.hide()
        root.addWidget(self.backup_label)
        self.progress = QProgressBar(self)
        self.progress.setObjectName('bulkWorkflowProgress')
        self.progress.hide()
        root.addWidget(self.progress)
        self.result_label = QLabel('', self)
        self.result_label.setObjectName('bulkWorkflowResult')
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        root.addWidget(self.result_label)

    def _add_row(self, layout, title: str, value: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(SPACING['sm'])
        label = QLabel(title, self)
        label.setObjectName('bulkWorkflowField')
        row.addWidget(label)
        value_label = QLabel(value, self)
        value_label.setObjectName('bulkWorkflowValue')
        value_label.setWordWrap(True)
        row.addWidget(value_label, 1)
        layout.addLayout(row)
        return value_label

    def set_context(self, *, source: str, target: str, review: str) -> None:
        self.source_value.setText(source)
        self.target_value.setText(target)
        self.review_value.setText(review)
        summary = f'{source}. {target}. {review}'.strip()
        self.setAccessibleDescription(summary)

    def set_risk(self, message: str = '', backup: str = '') -> None:
        self.risk_label.setText(message)
        self.risk_label.setVisible(bool(message))
        self.setProperty('riskVariant', 'destructive' if message else 'standard')
        self.backup_label.setText(backup)
        self.backup_label.setVisible(bool(backup))
        _polish(self)

    def set_progress(self, completed: int, total: int, label: str = '') -> None:
        maximum = max(1, int(total))
        self.progress.setRange(0, maximum)
        self.progress.setValue(max(0, min(int(completed), maximum)))
        self.progress.setFormat(label or f'%v of %m')
        self.progress.show()

    def set_result(self, message: str, success: bool = True) -> None:
        self.result_label.setText(message)
        self.result_label.setProperty('resultState', 'success' if success else 'error')
        self.result_label.setVisible(bool(message))
        _polish(self.result_label)


class BaseDialog(QDialog):
    """Shared dialog scaffold — 022 sheet grammar: kicker + title + rule +
    content zone + footer with isolated danger slot at footer-left.

    Sizing: min sizes only (no fixed frames). Esc rejects; the confirm button
    (if created) accepts. Subclasses populate ``self.content_layout``.
    """

    focusRestored = pyqtSignal(object)

    def __init__(
        self,
        title: str,
        parent: Optional[QWidget] = None,
        min_size: Optional[tuple[int, int]] = None,
        danger: bool = False,
        kicker: str = '',
        escape_enabled: bool = True,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName('baseDialog')
        self.setProperty('riskVariant', 'destructive' if danger else 'standard')
        self.setAccessibleName(title)
        self._escape_enabled = escape_enabled
        self._invoker = QApplication.focusWidget()
        self._focus_restored = False
        self._primary_button: Optional[QPushButton] = None
        if min_size:
            self.setMinimumSize(max(400, min_size[0]), max(0, min_size[1]))
        else:
            self.setMinimumSize(420, 220)
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['xl'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
        root.setSpacing(SPACING['md'])

        head = QHBoxLayout()
        head.setSpacing(SPACING['sm'])
        head_col = QVBoxLayout()
        head_col.setSpacing(0)
        if kicker:
            kicker_lbl = QLabel(kicker.upper(), self)
            kicker_lbl.setObjectName('dialogKicker')
            head_col.addWidget(kicker_lbl)
        self.title_label = make_label(title, 'title')
        self.title_label.setObjectName('dialogTitle')
        head_col.addWidget(self.title_label)
        head.addLayout(head_col)
        head.addStretch(1)
        self.close_btn = make_tool_button('close', tr('ui.action.close', 'Close'))
        self.close_btn.clicked.connect(self.reject)
        head.addWidget(self.close_btn)
        root.addLayout(head)
        root.addWidget(make_hdivider())

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(SPACING['md'])
        root.addLayout(self.content_layout, 1)

        self.footer = QHBoxLayout()
        self.footer.setSpacing(SPACING['sm'])
        # danger actions are isolated at footer-left (022 §3.1)
        self.danger_slot = QHBoxLayout()
        self.danger_slot.setSpacing(SPACING['sm'])
        self.footer.addLayout(self.danger_slot)
        self.footer.addStretch(1)
        root.addLayout(self.footer)
        self.cancel_btn = make_button(tr('ui.action.cancel', 'Cancel'), 'ghost')
        self.cancel_btn.clicked.connect(self.reject)
        self.footer.addWidget(self.cancel_btn)

    def add_confirm_button(self, text: str, danger: bool = False) -> QPushButton:
        btn = make_button(text, 'destructive' if danger else 'primary')
        btn.setProperty('actionRole', 'destructive' if danger else 'primary')
        btn.clicked.connect(self.accept)
        if danger:
            self.danger_slot.addWidget(btn)
        else:
            self.footer.addWidget(btn)
        self._primary_button = btn
        return btn

    def setWindowTitle(self, a0: str | None) -> None:
        """Keep the native title, visible heading, and accessible name aligned."""
        super().setWindowTitle(a0)
        if hasattr(self, 'title_label'):
            title = a0 or ''
            self.title_label.setText(title)
            self.setAccessibleName(title)

    def add_secondary_button(self, text: str, on_clicked) -> QPushButton:
        btn = make_button(text, 'secondary')
        btn.setProperty('actionRole', 'secondary')
        btn.clicked.connect(on_clicked)
        self.footer.insertWidget(self.footer.count() - 1, btn)
        return btn

    def add_danger_button(self, text: str, on_clicked) -> QPushButton:
        """Non-accepting destructive action, isolated footer-left."""
        btn = make_button(text, 'destructive')
        btn.setProperty('actionRole', 'destructive')
        btn.clicked.connect(on_clicked)
        self.danger_slot.addWidget(btn)
        return btn

    def showEvent(self, a0) -> None:
        focused = QApplication.focusWidget()
        if focused is not None and focused.window() is not self:
            self._invoker = focused
        self._focus_restored = False
        super().showEvent(a0)
        QTimer.singleShot(0, self._focus_initial)

    def done(self, a0: int) -> None:
        super().done(a0)
        self._restore_focus()
        QTimer.singleShot(0, self._restore_focus)

    def accept(self) -> None:
        super().accept()
        self._restore_focus()

    def reject(self) -> None:
        super().reject()
        self._restore_focus()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 is not None and a0.key() == Qt.Key.Key_Escape:
            if self._escape_enabled:
                self.reject()
            a0.accept()
            return
        super().keyPressEvent(a0)

    def focusNextPrevChild(self, next: bool) -> bool:
        return _cycle_focus(self, next)

    def _focus_initial(self) -> None:
        target = self._primary_button or self.cancel_btn
        if target.isVisible() and target.isEnabled():
            target.setFocus(Qt.FocusReason.TabFocusReason)

    def _restore_focus(self) -> None:
        if self._focus_restored or self._invoker is None:
            return
        try:
            if not self._invoker.isVisible() or not self._invoker.isEnabled():
                return
            self._focus_restored = True
            self._invoker.setFocus(Qt.FocusReason.OtherFocusReason)
            self.focusRestored.emit(self._invoker)
        except RuntimeError:
            # The invoking widget may have been owned by a preceding modal and
            # deleted before this dialog completed its deferred focus restore.
            self._invoker = None


class MessageDialog(BaseDialog):
    """Shared-scaffold compatibility replacement for simple ``QMessageBox`` use."""

    Icon = _QtMessageBox.Icon
    ButtonRole = _QtMessageBox.ButtonRole
    StandardButton = _QtMessageBox.StandardButton
    Information = _QtMessageBox.Icon.Information
    Warning = _QtMessageBox.Icon.Warning
    Critical = _QtMessageBox.Icon.Critical
    Question = _QtMessageBox.Icon.Question
    NoIcon = _QtMessageBox.Icon.NoIcon
    Ok = _QtMessageBox.StandardButton.Ok
    Yes = _QtMessageBox.StandardButton.Yes
    No = _QtMessageBox.StandardButton.No
    Cancel = _QtMessageBox.StandardButton.Cancel
    AcceptRole = _QtMessageBox.ButtonRole.AcceptRole
    RejectRole = _QtMessageBox.ButtonRole.RejectRole
    DestructiveRole = _QtMessageBox.ButtonRole.DestructiveRole
    ActionRole = _QtMessageBox.ButtonRole.ActionRole

    _STANDARD_TEXT = {
        _QtMessageBox.StandardButton.Ok: 'OK',
        _QtMessageBox.StandardButton.Yes: 'Yes',
        _QtMessageBox.StandardButton.No: 'No',
        _QtMessageBox.StandardButton.Cancel: 'Cancel',
    }
    _STANDARD_ROLE = {
        _QtMessageBox.StandardButton.Ok: _QtMessageBox.ButtonRole.AcceptRole,
        _QtMessageBox.StandardButton.Yes: _QtMessageBox.ButtonRole.AcceptRole,
        _QtMessageBox.StandardButton.No: _QtMessageBox.ButtonRole.RejectRole,
        _QtMessageBox.StandardButton.Cancel: _QtMessageBox.ButtonRole.RejectRole,
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__('', parent, min_size=(440, 220))
        self.setObjectName('messageDialog')
        self.cancel_btn.hide()
        self._clicked_button: Optional[QPushButton] = None
        self._button_roles: dict[QPushButton, object] = {}
        self._standard_buttons: dict[object, QPushButton] = {}
        self.kind_label = make_label('Information', 'secondary', self)
        self.kind_label.setObjectName('messageDialogKind')
        self.content_layout.addWidget(self.kind_label)
        self.message_label = make_label('', 'body', self)
        self.message_label.setObjectName('messageDialogText')
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.content_layout.addWidget(self.message_label)

    def setText(self, message: str) -> None:
        self.message_label.setText(str(message))
        self.setAccessibleDescription(str(message))

    def text(self) -> str:
        return self.message_label.text()

    def setIcon(self, icon) -> None:
        labels = {
            self.Information: ('Information', 'info'),
            self.Warning: ('Warning', 'warning'),
            self.Critical: ('Error', 'danger'),
            self.Question: ('Confirmation', 'accent'),
            self.NoIcon: ('', 'neutral'),
        }
        label, level = labels.get(icon, ('Information', 'info'))
        self.kind_label.setText(label)
        self.kind_label.setProperty('level', level)
        self.kind_label.setVisible(bool(label))
        self.setProperty('riskVariant', 'destructive' if icon == self.Critical
                         else 'warning' if icon == self.Warning else 'standard')
        _polish(self.kind_label)
        _polish(self)

    def _choose(self, button: QPushButton, role) -> None:
        self._clicked_button = button
        if role == self.RejectRole:
            self.reject()
        else:
            self.accept()

    def addButton(self, button_or_text, role=None) -> QPushButton:
        standard = None
        if isinstance(button_or_text, _QtMessageBox.StandardButton):
            standard = button_or_text
            text = self._STANDARD_TEXT.get(standard, str(standard))
            role = self._STANDARD_ROLE.get(standard, self.ActionRole)
        else:
            text = str(button_or_text)
            role = role if role is not None else self.ActionRole
        tier = ('destructive' if role == self.DestructiveRole else
                'primary' if role == self.AcceptRole else 'tertiary')
        button = make_button(text, tier)
        button.setAccessibleName(text)
        button.clicked.connect(lambda _checked=False, b=button, r=role:
                               self._choose(b, r))
        if role == self.DestructiveRole:
            self.danger_slot.addWidget(button)
        else:
            self.footer.addWidget(button)
        self._button_roles[button] = role
        if standard is not None:
            self._standard_buttons[standard] = button
        if role == self.AcceptRole and self._primary_button is None:
            self._primary_button = button
        return button

    def setStandardButtons(self, buttons) -> None:
        for standard in (self.Yes, self.No, self.Ok, self.Cancel):
            if buttons & standard and standard not in self._standard_buttons:
                self.addButton(standard)

    def setDefaultButton(self, button) -> None:
        if isinstance(button, _QtMessageBox.StandardButton):
            button = self._standard_buttons.get(button)
        if button is not None:
            button.setDefault(True)
            self._primary_button = button

    def clickedButton(self) -> Optional[QPushButton]:
        return self._clicked_button

    def buttonRole(self, button: QPushButton):
        return self._button_roles.get(button, self.ActionRole)

    def exec(self) -> int:
        if not self._button_roles:
            self.addButton(self.Ok)
        result = super().exec()
        for standard, button in self._standard_buttons.items():
            if button is self._clicked_button:
                return int(standard.value)
        return result

    @classmethod
    def _show(cls, parent, icon, title, message, buttons=None,
              default_button=None):
        dialog = cls(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.setIcon(icon)
        dialog.setStandardButtons(buttons or cls.Ok)
        if default_button is not None:
            dialog.setDefaultButton(default_button)
        dialog.exec()
        for standard, button in dialog._standard_buttons.items():
            if button is dialog.clickedButton():
                return standard
        return cls.No if buttons and buttons & cls.No else cls.Ok

    @classmethod
    def information(cls, parent, title, message, buttons=None,
                    default_button=None):
        return cls._show(parent, cls.Information, title, message,
                         buttons, default_button)

    @classmethod
    def warning(cls, parent, title, message, buttons=None,
                default_button=None):
        return cls._show(parent, cls.Warning, title, message,
                         buttons, default_button)

    @classmethod
    def critical(cls, parent, title, message, buttons=None,
                 default_button=None):
        return cls._show(parent, cls.Critical, title, message,
                         buttons, default_button)

    @classmethod
    def question(cls, parent, title, message, buttons=None,
                 default_button=None):
        choices = buttons or (cls.Yes | cls.No)
        return cls._show(parent, cls.Question, title, message,
                         choices, default_button or cls.No)


class InputPromptDialog(BaseDialog):
    """Shared-scaffold compatibility replacement for text/integer prompts."""

    InputMode = _QtInputDialog.InputMode
    TextInput = _QtInputDialog.InputMode.TextInput
    IntInput = _QtInputDialog.InputMode.IntInput

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__('', parent, min_size=(420, 220))
        self.setObjectName('inputPromptDialog')
        self.prompt_label = make_label('', 'body', self)
        self.prompt_label.setWordWrap(True)
        self.content_layout.addWidget(self.prompt_label)
        self.text_input = QLineEdit(self)
        self.text_input.setAccessibleName('Value')
        self.content_layout.addWidget(self.text_input)
        self.int_input = QSpinBox(self)
        self.int_input.setRange(-2147483647, 2147483647)
        self.int_input.setAccessibleName('Value')
        self.int_input.hide()
        self.content_layout.addWidget(self.int_input)
        self.confirm_btn = self.add_confirm_button('OK')

    def setLabelText(self, text: str) -> None:
        self.prompt_label.setText(str(text))
        self.setAccessibleDescription(str(text))

    def setInputMode(self, mode) -> None:
        integer = mode == self.IntInput
        self.int_input.setVisible(integer)
        self.text_input.setVisible(not integer)

    def setIntRange(self, minimum: int, maximum: int) -> None:
        self.int_input.setRange(minimum, maximum)

    def setIntValue(self, value: int) -> None:
        self.int_input.setValue(value)

    def setIntStep(self, step: int) -> None:
        self.int_input.setSingleStep(step)

    def intValue(self) -> int:
        return self.int_input.value()

    def setTextValue(self, value: str) -> None:
        self.text_input.setText(value)

    def textValue(self) -> str:
        return self.text_input.text()

    def setOkButtonText(self, text: str) -> None:
        self.confirm_btn.setText(text)

    def setCancelButtonText(self, text: str) -> None:
        self.cancel_btn.setText(text)

    @classmethod
    def getInt(cls, parent, title, label, value=0, min=-2147483647,
               max=2147483647, step=1, flags=None):
        dialog = cls(parent)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setInputMode(cls.IntInput)
        dialog.setIntRange(min, max)
        dialog.int_input.setSingleStep(step)
        dialog.setIntValue(value)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return dialog.intValue(), accepted

    @classmethod
    def getText(cls, parent, title, label, echo=None, text='', flags=None,
                inputMethodHints=None):
        dialog = cls(parent)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setInputMode(cls.TextInput)
        dialog.setTextValue(text)
        if echo is not None:
            dialog.text_input.setEchoMode(echo)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return dialog.textValue(), accepted


def _cycle_focus(container: QWidget, forward: bool) -> bool:
    focusable = [
        widget for widget in container.findChildren(QWidget)
        if widget.isVisibleTo(container)
        and widget.isEnabled()
        and widget.focusPolicy() != Qt.FocusPolicy.NoFocus
    ]
    if not focusable:
        return False
    current = QApplication.focusWidget()
    try:
        index = focusable.index(current)
    except ValueError:
        index = -1 if forward else 0
    target = focusable[(index + (1 if forward else -1)) % len(focusable)]
    target.setFocus(Qt.FocusReason.TabFocusReason if forward else Qt.FocusReason.BacktabFocusReason)
    return True


class Drawer(QFrame):
    """Non-modal contextual editor that contains and restores keyboard focus."""

    closeRequested = pyqtSignal()
    focusRestored = pyqtSignal(object)

    def __init__(self, title: str, parent: Optional[QWidget] = None, *, min_width: int = 320):
        super().__init__(parent)
        self.setObjectName('contextDrawer')
        self.setProperty('riskVariant', 'standard')
        self.setMinimumWidth(min_width)
        self.setAccessibleName(title)
        self._invoker: Optional[QWidget] = None
        self._focus_restored = False
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        root.setSpacing(SPACING['md'])
        header = QHBoxLayout()
        self.title_label = make_label(title, 'title', self)
        header.addWidget(self.title_label, 1)
        self.close_button = make_tool_button(
            'close', tr('ui.drawer.close', 'Close drawer'), self)
        self.close_button.clicked.connect(self.close_drawer)
        header.addWidget(self.close_button)
        root.addLayout(header)
        root.addWidget(make_hdivider())
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(SPACING['md'])
        root.addLayout(self.content_layout, 1)
        self.footer = QHBoxLayout()
        self.footer.setSpacing(SPACING['sm'])
        self.footer.addStretch(1)
        root.addLayout(self.footer)
        self.hide()

    def set_risk_variant(self, variant: str) -> None:
        if variant not in {'standard', 'warning', 'destructive'}:
            raise ValueError(f'unknown drawer risk variant {variant!r}')
        self.setProperty('riskVariant', variant)
        _polish(self)

    def open(self, invoker: Optional[QWidget] = None) -> None:
        self._invoker = invoker or QApplication.focusWidget()
        self._focus_restored = False
        self.show()
        self.raise_()
        QTimer.singleShot(0, self._focus_initial)

    def close_drawer(self) -> None:
        self.hide()
        self.closeRequested.emit()
        self._restore_focus()
        QTimer.singleShot(0, self._restore_focus)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 is not None and a0.key() == Qt.Key.Key_Escape:
            self.close_drawer()
            a0.accept()
            return
        super().keyPressEvent(a0)

    def focusNextPrevChild(self, next: bool) -> bool:
        return _cycle_focus(self, next)

    def _focus_initial(self) -> None:
        _cycle_focus(self, True)

    def _restore_focus(self) -> None:
        if (not self._focus_restored and self._invoker is not None
                and self._invoker.isVisible() and self._invoker.isEnabled()):
            self._focus_restored = True
            self._invoker.setFocus(Qt.FocusReason.OtherFocusReason)
            self.focusRestored.emit(self._invoker)


def confirm(
    parent: Optional[QWidget],
    title: str,
    message: str,
    kind: str = 'info',
    confirm_text: str = 'Confirm',
    cancel_text: str = 'Cancel',
) -> bool:
    """Modal confirmation. kind='danger' styles the confirm button as danger."""
    dialog = BaseDialog(title, parent, min_size=(420, 0))
    dialog.content_layout.addWidget(make_label(message, 'body'))
    btn = dialog.add_confirm_button(confirm_text, danger=(kind == 'danger'))
    dialog.cancel_btn.setText(cancel_text)
    btn.setFocus()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


def create_page_ribbon(title: str, zone: str = '', parent=None) -> QFrame:
    """Page ribbon (plan 020 section 4.4): per-page title header.

    Returns a QFrame with a horizontal layout: display title, zone label,
    stretch, and an action slot the caller can extend. Window controls live
    in the app bar (shell v3), so the ribbon spans the full canvas width.
    """
    ribbon = QFrame(parent)
    ribbon.setObjectName('pageRibbon')
    lay = QHBoxLayout(ribbon)
    lay.setContentsMargins(SPACING['xl'], SPACING['md'], SPACING['lg'], SPACING['md'])
    lay.setSpacing(SPACING['sm'])
    title_lbl = QLabel(title, ribbon)
    title_lbl.setObjectName('ribbonTitle')
    lay.addWidget(title_lbl)
    if zone:
        zone_lbl = QLabel(zone, ribbon)
        zone_lbl.setObjectName('ribbonZone')
        lay.addWidget(zone_lbl)
    lay.addStretch(1)
    ribbon._ribbon_actions_slot = lay
    return ribbon


def ribbon_actions_slot(ribbon: QFrame) -> QHBoxLayout:
    """Public accessor for a page ribbon's trailing action slot.

    Wraps the private ``_ribbon_actions_slot`` so screens never reach into
    ribbon internals directly (ui-modernization Phase 0).
    """
    return ribbon._ribbon_actions_slot


def set_content_margins(target, top: int = 0, bottom: int = 0,
                        left: int = SPACING['lg']) -> None:
    """Apply standard page-row margins.

    Rows span the full canvas width (window controls are in the app bar);
    the left gutter defaults to ``SPACING['lg']``. Accepts any QWidget or
    QLayout.
    """
    target.setContentsMargins(left, top, left, bottom)


def set_picker_selected(button: QPushButton, selected: bool) -> None:
    """modernize-tab-ui 3.5: shared picker selected-state helper.

    Toggles the ``pickerSelected`` dynamic property consumed by the
    qss_builder ``QPushButton#ghostBtn[pickerSelected="true"]`` rule
    (accent border). Used by the Player and Base Inventory picker buttons.
    """
    if button.property('pickerSelected') == ('true' if selected else None):
        return
    button.setProperty('pickerSelected', 'true' if selected else None)
    button.style().unpolish(button)
    button.style().polish(button)


class PageFooter(QFrame):
    """Shared page footer (top-nav-shell 4.1): status text left, actions right.

    Page-grammar reference implementation for table pages: Players/Guilds/
    Bases/Exclusions bulk bars and the JSON editor footer consolidate onto
    this frame. Exposes ``status_label`` and the trailing ``actions`` layout;
    callers keep full ownership of their buttons and wiring.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('tableFooter')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(SPACING['lg'], 4, SPACING['lg'], 4)
        lay.setSpacing(SPACING['sm'])
        self.status_label = QLabel('')
        self.status_label.setObjectName('bulkHintLabel')
        lay.addWidget(self.status_label)
        lay.addSpacing(SPACING['sm'])
        lay.addStretch(1)
        self.actions = lay


def create_page_footer(status_text: str = '', parent=None) -> PageFooter:
    """Convenience constructor for the shared page footer."""
    footer = PageFooter(parent)
    if status_text:
        footer.status_label.setText(status_text)
    return footer


# ---------------------------------------------------------------------------
# Inspector panel (uiux-audit-remediation 4.1 / design D7)
# ---------------------------------------------------------------------------
class CopyValueRow(QWidget):
    """Monospace identifier value with tooltip + click-to-copy and the
    transient copy.svg -> check.svg feedback (task 2 pattern)."""

    _COPY_FEEDBACK_MS = 2000

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('copyValueRow')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._row_label = ''
        self._value = QPushButton('')
        self._value.setObjectName('inspectorCopyValue')
        self._value.setFlat(True)
        self._value.setCursor(Qt.CursorShape.PointingHandCursor)
        self._value.setIcon(app_icons.get_qicon('copy', role='text_secondary'))
        lay.addWidget(self._value, 1)
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_feedback)
        self._value.clicked.connect(self._on_copy)

    def set_label(self, label: str) -> None:
        self._row_label = str(label or '')

    def set_value(self, value: str) -> None:
        value = str(value or '')
        self._value.setText(value)
        self._value.setToolTip(value)
        self._value.setAccessibleName(f'{self._row_label}: {value}'.strip(': '))
        self._value.setVisible(bool(value))

    def value(self) -> str:
        return self._value.text()

    def _on_copy(self) -> None:
        if not self._value.text():
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self._value.text())
        self._value.setIcon(app_icons.get_qicon('check', role='success'))
        self._reset_timer.start(self._COPY_FEEDBACK_MS)

    def _reset_feedback(self) -> None:
        self._value.setIcon(app_icons.get_qicon('copy', role='text_secondary'))


class InspectorPanel(QFrame):
    """Right-hand detail panel following the Docs list-plus-detail pattern
    (design D7): title row, stat-grid rows (label/value pairs, values may be
    monospace), an optional action slot, and the shared empty-state
    presentation when nothing is selected."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('inspectorPanel')
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        self._root.setSpacing(SPACING['xs'])

        self._title = QLabel('')
        self._title.setObjectName('inspectorTitle')
        self._root.addWidget(self._title)

        self._grid_host = QWidget(self)
        self._grid = QVBoxLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(SPACING['xs'])
        self._rows: list[tuple[QLabel, QWidget]] = []
        self._root.addWidget(self._grid_host)

        self._content_widgets: list[QWidget] = []

        self._actions_host = QWidget(self)
        self._actions = QHBoxLayout(self._actions_host)
        self._actions.setContentsMargins(0, SPACING['xs'], 0, 0)
        self._actions.setSpacing(SPACING['sm'])
        self._actions.addStretch(1)
        self._root.addWidget(self._actions_host)

        self._empty = QLabel(t('inspector.no_selection') if t else 'Nothing selected')
        self._empty.setObjectName('inspectorEmpty')
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        self._empty.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._root.addWidget(self._empty, 1)

        self.show_empty()

    def add_row(self, label: str, monospace: bool = False) -> QWidget:
        """Append a stat-grid row; returns the value widget (QLabel, or
        CopyValueRow when monospace). Call ``show_details`` to set values."""
        label_lbl = make_label(label, 'micro')
        label_lbl.setObjectName('inspectorRowLabel')
        if monospace:
            value: QWidget = CopyValueRow()
            value.set_label(label)
            value.setFont(fonts.mono_font())
        else:
            value = QLabel('')
            value.setObjectName('inspectorRowValue')
            value.setWordWrap(True)
        self._grid.addWidget(label_lbl)
        self._grid.addWidget(value)
        self._rows.append((label_lbl, value))
        return value

    def add_action(self, button: QPushButton) -> None:
        self._actions.insertWidget(self._actions.count() - 1, button)

    def add_content_widget(self, widget: QWidget, *, stretch: int = 0) -> None:
        """Place structured inspector content between summary rows and actions."""
        widget.setParent(self)
        self._content_widgets.append(widget)
        self._root.insertWidget(
            self._root.indexOf(self._actions_host), widget, stretch)
        widget.hide()

    def show_details(self, title: str, values: dict[int, str] | None = None) -> None:
        """Populate the title and, by row index, the row values. Rows whose
        value is empty/None hide their label row."""
        self._title.setText(title)
        self._title.show()
        values = values or {}
        for index, (label_lbl, value) in enumerate(self._rows):
            text = str(values.get(index, '') or '')
            if isinstance(value, CopyValueRow):
                value.set_value(text)
                label_lbl.setVisible(bool(text))
            else:
                value.setText(text)
                value.setVisible(bool(text))
                label_lbl.setVisible(bool(text))
        self._grid_host.show()
        for widget in self._content_widgets:
            widget.show()
        self._actions_host.show()
        self._empty.hide()

    def show_empty(self, message: str | None = None) -> None:
        self._title.hide()
        self._grid_host.hide()
        for widget in self._content_widgets:
            widget.hide()
        self._actions_host.hide()
        self._empty.setText(message if message else
                            (t('inspector.no_selection') if t else 'Nothing selected'))
        self._empty.show()

    def clear(self) -> None:
        self.show_empty()

    def refresh_labels(self) -> None:
        if self._empty.isVisible():
            self.show_empty()


class InspectorSideColumn(QFrame):
    """Bases/Players/Guilds right-side inspector column (design D7):
    fixed-width surface hosting an InspectorPanel at full canvas height."""

    def __init__(self, width: int = 340, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('inspectorSideColumn')
        self.setFixedWidth(width)
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.panel = InspectorPanel(self)
        col.addWidget(self.panel, 1)
