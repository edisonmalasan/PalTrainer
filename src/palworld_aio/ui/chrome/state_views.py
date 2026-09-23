"""Standard local, blocking, result, and notification presentation states."""
from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_button, make_tool_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING


class StateView(QFrame):
    """Icon, headline, explanation, and optional recovery action."""

    actionTriggered = pyqtSignal()
    secondaryActionTriggered = pyqtSignal()

    def __init__(
        self,
        kind: str,
        title: str,
        message: str,
        *,
        icon: str,
        action_text: str = '',
        secondary_action_text: str = '',
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setProperty('class', 'stateView')
        self.setProperty('stateKind', kind)
        self.setAccessibleName(title)
        self.setAccessibleDescription(message)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['xl'], SPACING['xxl'], SPACING['xl'], SPACING['xxl'])
        layout.setSpacing(SPACING['sm'])
        layout.addStretch(1)
        self.icon_label = QLabel(self)
        self.icon_label.setProperty('class', 'stateIcon')
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = app_icons.get_pixmap(icon, role={
            'error': 'danger', 'prerequisite': 'warning', 'operation_error': 'danger',
            'operation_success': 'success',
        }.get(kind, 'text_secondary'), size=32)
        if pixmap is not None:
            self.icon_label.setPixmap(pixmap)
        self.icon_label.setAccessibleName('')
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel(title, self)
        self.title_label.setProperty('class', 'stateTitle')
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.message_label = QLabel(message, self)
        self.message_label.setProperty('class', 'stateMessage')
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.action_button = None
        self.secondary_action_button = None
        if action_text:
            self.action_button = make_button(action_text, 'primary', parent=self)
            self.action_button.clicked.connect(self.actionTriggered.emit)
            actions.addWidget(self.action_button)
        if secondary_action_text:
            self.secondary_action_button = make_button(secondary_action_text, 'tertiary', parent=self)
            self.secondary_action_button.clicked.connect(self.secondaryActionTriggered.emit)
            actions.addWidget(self.secondary_action_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)


class PrerequisiteState(StateView):
    def __init__(self, title: str, message: str, action_text: str, parent=None):
        super().__init__('prerequisite', title, message, icon='warning', action_text=action_text, parent=parent)


class ConfiguredEmptyState(StateView):
    def __init__(self, title: str, message: str, action_text: str = '', parent=None):
        super().__init__('configured_empty', title, message, icon='info', action_text=action_text, parent=parent)


class NoResultState(StateView):
    def __init__(self, title: str, message: str, action_text: Optional[str] = None, parent=None):
        action_text = action_text or tr('ui.state.clear_filters', 'Clear filters')
        super().__init__('no_result', title, message, icon='search', action_text=action_text, parent=parent)


class ErrorState(StateView):
    def __init__(self, title: str, message: str, action_text: Optional[str] = None, parent=None):
        action_text = action_text or tr('ui.state.retry', 'Retry')
        super().__init__('error', title, message, icon='warning', action_text=action_text, parent=parent)


class SkeletonView(QFrame):
    """Non-blank local loading placeholder with an accessible status label."""

    def __init__(self, message: Optional[str] = None, rows: int = 4, parent=None):
        super().__init__(parent)
        message = message or tr('ui.state.loading', 'Loading…')
        if rows < 1:
            raise ValueError('skeleton rows must be positive')
        self.setProperty('class', 'skeletonView')
        self.setProperty('stateKind', 'loading')
        self.setAccessibleName(message)
        self.setAccessibleDescription(message)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        layout.setSpacing(SPACING['sm'])
        self.status_label = QLabel(message, self)
        self.status_label.setProperty('class', 'stateMessage')
        layout.addWidget(self.status_label)
        self.rows: list[QFrame] = []
        for index in range(rows):
            row = QFrame(self)
            row.setProperty('class', 'skeletonLine')
            row.setProperty('lineLength', 'short' if index == rows - 1 else 'full')
            row.setFixedHeight(12)
            self.rows.append(row)
            layout.addWidget(row)
        layout.addStretch(1)


class BlockingProgress(QFrame):
    """Blocking operation status for a page region with optional safe cancel."""

    cancelRequested = pyqtSignal()

    def __init__(self, title: str, message: str = '', *, cancelable: bool = False, parent=None):
        super().__init__(parent)
        self.setProperty('class', 'blockingProgress')
        self.setProperty('stateKind', 'blocking_progress')
        self.setAccessibleName(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        layout.setSpacing(SPACING['md'])
        self.title_label = QLabel(title, self)
        self.title_label.setProperty('class', 'stateTitle')
        self.message_label = QLabel(message, self)
        self.message_label.setProperty('class', 'stateMessage')
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        layout.addWidget(self.progress)
        self.cancel_button = make_button(tr('ui.action.cancel', 'Cancel'), 'tertiary', parent=self)
        self.cancel_button.setVisible(cancelable)
        self.cancel_button.clicked.connect(self.cancelRequested.emit)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignRight)

    def set_progress(self, current: int, total: int, message: str = '') -> None:
        if total < 0 or current < 0:
            raise ValueError('progress values cannot be negative')
        if total == 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, total)
            self.progress.setValue(min(current, total))
        if message:
            self.message_label.setText(message)
            self.setAccessibleDescription(message)


class OperationResultState(StateView):
    def __init__(self, success: bool, title: str, message: str, action_text: str = '', parent=None):
        super().__init__(
            'operation_success' if success else 'operation_error',
            title,
            message,
            icon='check_circle' if success else 'warning',
            action_text=action_text,
            parent=parent,
        )
        self.success = success


class NotificationBanner(QFrame):
    """Concise dismissible feedback; durable detail belongs in Activity."""

    dismissed = pyqtSignal()
    actionTriggered = pyqtSignal()

    def __init__(self, message: str, level: str = 'info', action_text: str = '', parent=None):
        super().__init__(parent)
        if level not in {'success', 'warning', 'danger', 'info'}:
            raise ValueError(f'unknown notification level {level!r}')
        self.setProperty('class', 'notificationBanner')
        self.setProperty('level', level)
        self.setAccessibleName(tr(
            'ui.notification.accessible', '{level}: {message}',
            level=level.title(), message=message))
        row = QHBoxLayout(self)
        row.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        row.setSpacing(SPACING['sm'])
        icon = QLabel(self)
        icon.setPixmap(app_icons.get_pixmap(
            {'success': 'check_circle', 'warning': 'warning', 'danger': 'warning', 'info': 'info'}[level],
            role=level,
            size=16,
        ))
        row.addWidget(icon)
        self.message_label = QLabel(message, self)
        self.message_label.setWordWrap(True)
        row.addWidget(self.message_label, 1)
        self.action_button = None
        if action_text:
            self.action_button = make_button(action_text, 'tertiary', parent=self)
            self.action_button.clicked.connect(self.actionTriggered.emit)
            row.addWidget(self.action_button)
        self.close_button = make_tool_button(
            'close', tr('ui.notification.dismiss', 'Dismiss notification'), self)
        self.close_button.clicked.connect(self._dismiss)
        row.addWidget(self.close_button)

    def _dismiss(self) -> None:
        self.hide()
        self.dismissed.emit()
