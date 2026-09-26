"""Durable Activity workspace backed by :mod:`operation_journal`."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from palworld_aio.ui.chrome.components import make_badge, make_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.state_views import ConfiguredEmptyState
from palworld_aio.ui.chrome.tokens import SPACING
from palworld_aio.ui.operation_journal import (
    ActivityEvent, ActivityStatus, OperationJournal,
)


_BADGE_LEVEL = {
    ActivityStatus.INFO: 'info',
    ActivityStatus.SUCCESS: 'success',
    ActivityStatus.WARNING: 'warning',
    ActivityStatus.FAILED: 'danger',
    ActivityStatus.UNDONE: 'neutral',
}


class ActivityRow(QFrame):
    def __init__(
        self,
        event: ActivityEvent,
        journal: OperationJournal,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.event = event
        self.setObjectName('activityRow')
        self.setProperty('status', event.status.value)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        layout.setSpacing(SPACING['xs'])
        heading = QHBoxLayout()
        self.time_label = QLabel(event.occurred_at.strftime('%H:%M'), self)
        self.time_label.setObjectName('activityTime')
        self.time_label.setAccessibleName(
            event.occurred_at.strftime('%b %d, %Y %I:%M %p'))
        heading.addWidget(self.time_label)
        title = QLabel(event.title, self)
        title.setObjectName('activityTitle')
        heading.addWidget(title, 1)
        heading.addWidget(make_badge(
            tr(f'ui.activity.status.{event.status.value}',
               event.status.value.replace('_', ' ').title()),
            _BADGE_LEVEL[event.status], self))
        layout.addLayout(heading)
        if event.context:
            context = QLabel(event.context, self)
            context.setObjectName('activityContext')
            context.setWordWrap(True)
            layout.addWidget(context)
        self.detail_label = QLabel(event.detail, self)
        self.detail_label.setObjectName('activityDetail')
        self.detail_label.setWordWrap(True)
        self.detail_label.setVisible(False)
        layout.addWidget(self.detail_label)
        actions = QHBoxLayout()
        actions.addStretch(1)
        if event.detail:
            self.detail_button = make_button(
                tr('ui.activity.details', 'Details'), 'tertiary', parent=self)
            self.detail_button.setCheckable(True)
            self.detail_button.clicked.connect(self._toggle_detail)
            actions.addWidget(self.detail_button)
        else:
            self.detail_button = None
        if event.can_undo:
            self.undo_button = make_button(
                tr('ui.activity.undo', 'Undo'), 'secondary', parent=self)
            self.undo_button.clicked.connect(
                lambda _checked=False: journal.undo_event(event.event_id))
            actions.addWidget(self.undo_button)
        else:
            self.undo_button = None
        layout.addLayout(actions)
        self.setAccessibleName(event.title)
        self.setAccessibleDescription(' • '.join(
            value for value in (event.context, event.detail) if value))

    def _toggle_detail(self, checked: bool) -> None:
        self.detail_label.setVisible(checked)
        if self.detail_button is not None:
            self.detail_button.setText(
                tr('ui.activity.hide_details', 'Hide details') if checked
                else tr('ui.activity.details', 'Details'))


class ActivityPage(QWidget):
    def __init__(
        self,
        journal: OperationJournal,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('activityPage')
        self.journal = journal
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['md'])
        toolbar = QHBoxLayout()
        self.count_label = QLabel('', self)
        self.count_label.setObjectName('activityCount')
        toolbar.addWidget(self.count_label)
        toolbar.addStretch(1)
        self.clear_button = make_button(
            tr('ui.activity.clear', 'Clear activity'), 'tertiary', parent=self)
        self.clear_button.clicked.connect(journal.clear)
        toolbar.addWidget(self.clear_button)
        root.addLayout(toolbar)
        self.empty_state = ConfiguredEmptyState(
            tr('ui.activity.empty_title', 'No activity yet'),
            tr('ui.activity.empty_message',
               'Loads, backups, changes, saves, and utility operations will appear here.'),
            parent=self,
        )
        root.addWidget(self.empty_state, 1)
        self.scroll = QScrollArea(self)
        self.scroll.setObjectName('activityScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.body = QWidget(self.scroll)
        self.body.setObjectName('activityBody')
        self.rows_layout = QVBoxLayout(self.body)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(SPACING['sm'])
        self.scroll.setWidget(self.body)
        root.addWidget(self.scroll, 1)
        journal.changed.connect(self._rebuild)
        self._rebuild(journal.events)

    def _rebuild(self, events: tuple[ActivityEvent, ...]) -> None:
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.rows = []
        for event in events:
            row = ActivityRow(event, self.journal, self.body)
            self.rows_layout.addWidget(row)
            self.rows.append(row)
        self.rows_layout.addStretch(1)
        count = len(events)
        self.count_label.setText(tr(
            'ui.activity.count', '{count} events', count=count))
        self.clear_button.setEnabled(bool(events))
        self.empty_state.setVisible(not events)
        self.scroll.setVisible(bool(events))


__all__ = ['ActivityPage', 'ActivityRow']
