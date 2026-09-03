"""Shared PyQt6 component library (UI overhaul plan 003).

Factories and small widget classes used by every migrated screen. Components
set objectNames/dynamic properties only — all styling lives in the QSS builder
(chrome/qss_builder.py). Keep public APIs stable: screens across the app
consume these.
"""
from __future__ import annotations

from typing import Callable, Optional
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome import fonts
from palworld_aio.ui.chrome.tokens import HEIGHT, SPACING, TYPE

_LEVELS = ('neutral', 'success', 'warning', 'danger', 'info', 'special', 'accent')


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
    """kind: default | primary | danger | ghost | tool"""
    btn = QPushButton(text, parent)
    if kind in ('primary', 'danger', 'ghost', 'tool'):
        btn.setProperty('class', kind)
    if icon:
        btn.setText(f'{icon}  {text}')
        btn.setFont(fonts.icon_font(13))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    btn.setMinimumHeight(HEIGHT['comfortable'])
    if tooltip:
        btn.setToolTip(tooltip)
        btn.setAccessibleName(text)
    return btn


def make_tool_button(icon: str, tooltip: str = '', parent: Optional[QWidget] = None) -> QPushButton:
    btn = QPushButton(icon, parent)
    btn.setProperty('class', 'tool')
    btn.setFont(fonts.icon_font(13))
    btn.setFixedSize(HEIGHT['comfortable'], HEIGHT['comfortable'])
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def make_danger_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'danger', parent=parent)


def make_ghost_button(text: str, parent: Optional[QWidget] = None) -> QPushButton:
    return make_button(text, 'ghost', parent=parent)


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
    """Bordered search field with a search glyph. Returns (container, line_edit)."""
    container = QFrame(parent)
    container.setProperty('class', 'searchField')
    row = QHBoxLayout(container)
    row.setContentsMargins(SPACING['sm'], 2, SPACING['sm'], 2)
    row.setSpacing(SPACING['sm'])
    glyph = QLabel('\uf002', container)
    glyph.setFont(fonts.icon_font(11))
    line = QLineEdit(container)
    line.setFrame(False)
    line.setFont(fonts.body_font())
    line.setClearButtonEnabled(True)
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
        self._close = make_tool_button('\uf00d')
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

    _ICONS = {'success': '\uf00c', 'warning': '\uf071', 'danger': '\uf00d', 'info': '\uf05a'}

    def __init__(self, message: str, level: str = 'success',
                 duration_ms: int = 3000, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty('class', 'toast')
        self.setProperty('toast_level', level if level in _LEVELS else 'info')
        self.setWindowFlags(Qt.WindowType.ToolTip)
        row = QHBoxLayout(self)
        row.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        row.setSpacing(SPACING['sm'])
        glyph = QLabel(self._ICONS.get(level, self._ICONS['info']))
        glyph.setFont(fonts.icon_font(12))
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
class BaseDialog(QDialog):
    """Shared dialog scaffold: title bar, content area, footer buttons.

    Sizing: min sizes only (no fixed frames). Esc rejects; the confirm button
    (if created) accepts. Subclasses populate ``self.content_layout``.
    """

    def __init__(
        self,
        title: str,
        parent: Optional[QWidget] = None,
        min_size: Optional[tuple[int, int]] = None,
        danger: bool = False,
    ):
        super().__init__(parent)
        self.setModal(True)
        if min_size:
            self.setMinimumSize(*min_size)
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['xl'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
        root.setSpacing(SPACING['md'])

        head = QHBoxLayout()
        head.setSpacing(SPACING['sm'])
        self.title_label = make_label(title, 'title')
        head.addWidget(self.title_label)
        head.addStretch(1)
        self.close_btn = make_tool_button('\uf00d')
        self.close_btn.clicked.connect(self.reject)
        head.addWidget(self.close_btn)
        root.addLayout(head)
        root.addWidget(make_hdivider())

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(SPACING['md'])
        root.addLayout(self.content_layout, 1)

        self.footer = QHBoxLayout()
        self.footer.setSpacing(SPACING['sm'])
        self.footer.addStretch(1)
        root.addLayout(self.footer)
        self.cancel_btn = make_button('Cancel', 'ghost')
        self.cancel_btn.clicked.connect(self.reject)
        self.footer.addWidget(self.cancel_btn)

    def add_confirm_button(self, text: str, danger: bool = False) -> QPushButton:
        btn = make_button(text, 'danger' if danger else 'primary')
        btn.clicked.connect(self.accept)
        self.footer.addWidget(btn)
        return btn


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
