"""Responsive workspace-header and context primitives for the audit shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_chip, make_tool_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import HEIGHT, SPACING


_SAVE_STATES = {'no_save', 'loading', 'loaded', 'dirty', 'saving', 'error'}
_SAVE_ICONS = {
    'no_save': 'save_state',
    'loading': 'spinner',
    'loaded': 'check_circle',
    'dirty': 'warning',
    'saving': 'spinner',
    'error': 'warning',
}


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    label: str
    kind: str = 'context'
    clickable: bool = True


class SaveContextControl(QPushButton):
    """Always-reachable summary and entry point for the current save."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('workspaceSaveContext')
        self.setProperty('controlRole', 'saveContext')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(HEIGHT['comfortable'])
        self._state = 'no_save'
        self._title = tr('ui.save.no_save_title', 'No save loaded')
        self._detail = tr('ui.save.no_save_detail', 'Open or drop a save to begin')
        self.set_context('no_save', self._title, self._detail)

    @property
    def state(self) -> str:
        return self._state

    def set_context(self, state: str, title: str, detail: str = '') -> None:
        if state not in _SAVE_STATES:
            raise ValueError(f'unknown save state {state!r}')
        self._state = state
        self._title = title.strip() or tr('ui.save.no_save_title', 'No save loaded')
        self._detail = detail.strip()
        self.setProperty('saveState', state)
        self.setText(self._title if not self._detail else f'{self._title}\n{self._detail}')
        self.setAccessibleName(tr(
            'ui.save.context_accessible', 'Save context: {title}', title=self._title))
        self.setAccessibleDescription(self._detail)
        self.setToolTip(self._detail or self._title)
        icon = app_icons.get_qicon(_SAVE_ICONS[state], role={
            'loaded': 'success', 'dirty': 'warning', 'error': 'danger',
            'loading': 'info', 'saving': 'info',
        }.get(state, 'text_secondary'))
        if icon is not None:
            self.setIcon(icon)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_compact(self, compact: bool) -> None:
        self.setProperty('compact', compact)
        self.setText(self._title if compact or not self._detail else f'{self._title}\n{self._detail}')

    def set_loading_state(self, state: str) -> None:
        """Compatibility contract used by the existing loading manager."""
        if state == 'loading':
            self.set_context('loading', self._title, self._detail)
        elif state == 'idle' and self._state in {'loading', 'saving'}:
            target = 'loaded' if self._title != tr(
                'ui.save.no_save_title', 'No save loaded') else 'no_save'
            self.set_context(target, self._title, self._detail)


class BreadcrumbBar(QFrame):
    """Readable, optionally clickable route/entity context."""

    activated = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('workspaceContextBar')
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING['xs'])
        self._items: list[ContextItem] = []
        self._buttons: dict[str, QPushButton] = {}
        self._layout.addStretch(1)

    @property
    def items(self) -> tuple[ContextItem, ...]:
        return tuple(self._items)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def set_items(self, items: Sequence[ContextItem]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._items = list(items)
        self._buttons.clear()
        for index, context in enumerate(self._items):
            if index:
                separator = QLabel('/', self)
                separator.setProperty('class', 'contextSeparator')
                separator.setAccessibleName(tr('ui.context.separator', 'Context separator'))
                self._layout.addWidget(separator)
            chip = make_chip(context.label, checkable=False, parent=self)
            chip.setProperty('contextKind', context.kind)
            chip.setProperty('contextId', context.item_id)
            chip.setEnabled(context.clickable)
            chip.setAccessibleName(tr(
                'ui.context.item_accessible', '{kind}: {label}',
                kind=context.kind.title(), label=context.label))
            if context.clickable:
                chip.clicked.connect(
                    lambda _checked=False, key=context.item_id: self.activated.emit(key)
                )
            self._buttons[context.item_id] = chip
            self._layout.addWidget(chip)
        self._layout.addStretch(1)


class PendingChangesButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('pendingChangesButton')
        self.setProperty('controlRole', 'pendingChanges')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.set_count(0)

    @property
    def count(self) -> int:
        return int(self.property('changeCount') or 0)

    def set_count(self, count: int) -> None:
        if count < 0:
            raise ValueError('pending change count cannot be negative')
        self.setProperty('changeCount', count)
        self.setProperty('hasChanges', count > 0)
        if count == 0:
            text = tr('ui.pending.none', 'No pending changes')
        elif count == 1:
            text = tr('ui.pending.one', '1 pending change')
        else:
            text = tr('ui.pending.many', '{count} pending changes', count=count)
        self.setText(text)
        self.setAccessibleName(self.text())
        self.setToolTip(tr('ui.pending.review', 'Review pending changes'))
        self.style().unpolish(self)
        self.style().polish(self)


class NotificationHost(QFrame):
    """Stable shell slot for page banners and notification components."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('notificationHost')
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING['xs'])

    def add_notification(self, widget: QWidget) -> None:
        widget.setParent(self)
        self._layout.addWidget(widget)

    def clear_notifications(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class WorkspaceHeader(QFrame):
    """Page identity, save/entity context, and priority-aware action host."""

    COMPACT_WIDTH = 1100

    def __init__(self, title: str, description: str = '', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('workspaceHeader')
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._compact = False
        self._optional_buttons: dict[str, QPushButton] = {}
        self._overflow_actions: dict[str, QAction] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['sm'])
        top = QHBoxLayout()
        top.setSpacing(SPACING['md'])

        identity = QVBoxLayout()
        identity.setSpacing(0)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName('workspaceTitle')
        self.title_label.setAccessibleName(tr(
            'ui.page.accessible', 'Page: {title}', title=title))
        self.description_label = QLabel(description, self)
        self.description_label.setObjectName('workspaceDescription')
        self.description_label.setVisible(bool(description))
        identity.addWidget(self.title_label)
        identity.addWidget(self.description_label)
        top.addLayout(identity, 1)

        self.save_context = SaveContextControl(self)
        top.addWidget(self.save_context)
        self.pending_changes = PendingChangesButton(self)
        top.addWidget(self.pending_changes)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(SPACING['xs'])
        top.addLayout(self._actions)

        self.overflow_button = make_tool_button(
            'menu', tr('ui.action.more', 'More actions'), self)
        self.overflow_menu = QMenu(self.overflow_button)
        self.overflow_menu.setObjectName('appContextMenu')
        self.overflow_menu.setAccessibleName(tr(
            'ui.menu.context_actions', 'Context actions'))
        self.overflow_button.setMenu(self.overflow_menu)
        self.overflow_button.hide()
        top.addWidget(self.overflow_button)
        root.addLayout(top)

        self.context_bar = BreadcrumbBar(self)
        root.addWidget(self.context_bar)
        self.notifications = NotificationHost(self)
        root.addWidget(self.notifications)

    @property
    def compact(self) -> bool:
        return self._compact

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def set_context_items(self, items: Sequence[ContextItem]) -> None:
        self.context_bar.set_items(items)
        self.context_bar.setVisible(bool(items))

    def add_action(
        self,
        action_id: str,
        label: str,
        callback: Optional[Callable[[], None]] = None,
        *,
        primary: bool = False,
        icon: Optional[str] = None,
    ) -> QPushButton:
        if action_id in self._optional_buttons or action_id in self._overflow_actions:
            raise ValueError(f'duplicate workspace action {action_id!r}')
        button = QPushButton(label, self)
        button.setProperty('class', 'primary' if primary else 'secondary')
        button.setProperty('actionPriority', 'primary' if primary else 'optional')
        button.setAccessibleName(label)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if icon:
            icon_obj = app_icons.get_qicon(icon, role='text_on_accent' if primary else 'text_secondary')
            if icon_obj is not None:
                button.setIcon(icon_obj)
        if callback is not None:
            button.clicked.connect(callback)
        self._actions.addWidget(button)
        if not primary:
            overflow_action = QAction(label, self.overflow_menu)
            overflow_action.setObjectName(action_id)
            if callback is not None:
                overflow_action.triggered.connect(callback)
            self.overflow_menu.addAction(overflow_action)
            self._optional_buttons[action_id] = button
            self._overflow_actions[action_id] = overflow_action
        self._apply_compact()
        return button

    def set_compact(self, compact: bool) -> None:
        if self._compact == compact:
            return
        self._compact = compact
        self.setProperty('compact', compact)
        self._apply_compact()

    def _apply_compact(self) -> None:
        self.description_label.setVisible(bool(self.description_label.text()) and not self._compact)
        self.save_context.set_compact(self._compact)
        for button in self._optional_buttons.values():
            button.setVisible(not self._compact)
        self.overflow_button.setVisible(self._compact and bool(self._optional_buttons))

    def resizeEvent(self, a0) -> None:
        self.set_compact(a0.size().width() <= self.COMPACT_WIDTH)
        super().resizeEvent(a0)
