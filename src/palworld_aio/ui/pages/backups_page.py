"""First-class browser and operation surface for full-save backups."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from palworld_aio.application.backup_catalog import BackupRecord, format_size
from palworld_aio.ui.chrome.components import make_badge, make_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.state_views import (
    BlockingProgress, ConfiguredEmptyState, NotificationBanner,
)
from palworld_aio.ui.chrome.tokens import SPACING


class BackupRow(QFrame):
    restoreRequested = pyqtSignal(object)
    revealRequested = pyqtSignal(str)

    def __init__(
        self,
        backup: BackupRecord,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.backup = backup
        self.setObjectName('backupRow')
        self.setAccessibleName(tr(
            'ui.backups.row_accessible',
            'Backup from {timestamp}',
            timestamp=backup.created_at.strftime('%b %d, %Y %I:%M %p'),
        ))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        layout.setSpacing(SPACING['xs'])

        heading = QHBoxLayout()
        self.timestamp_label = QLabel(
            backup.created_at.strftime('%b %d, %Y  %I:%M %p'), self)
        self.timestamp_label.setObjectName('backupTimestamp')
        heading.addWidget(self.timestamp_label, 1)
        self.source_badge = make_badge(
            backup.source or tr('ui.backups.unknown_source', 'Unknown source'),
            'neutral', self)
        heading.addWidget(self.source_badge)
        layout.addLayout(heading)

        self.reason_label = QLabel(backup.reason, self)
        self.reason_label.setObjectName('backupReason')
        self.reason_label.setWordWrap(True)
        layout.addWidget(self.reason_label)
        self.size_label = QLabel(format_size(backup.size_bytes), self)
        self.size_label.setObjectName('backupSize')
        layout.addWidget(self.size_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.reveal_button = make_button(
            tr('ui.backups.open_folder', 'Open Folder'),
            'tertiary', parent=self)
        self.reveal_button.clicked.connect(
            lambda _checked=False: self.revealRequested.emit(str(backup.path)))
        actions.addWidget(self.reveal_button)
        self.restore_button = make_button(
            tr('ui.backups.restore', 'Restore'), 'secondary', parent=self)
        self.restore_button.clicked.connect(
            lambda _checked=False: self.restoreRequested.emit(backup))
        actions.addWidget(self.restore_button)
        layout.addLayout(actions)


class BackupsPage(QWidget):
    refreshRequested = pyqtSignal()
    revealRequested = pyqtSignal(str)
    restoreRequested = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('backupsPage')
        self.rows: list[BackupRow] = []
        self.result_banner: NotificationBanner | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['md'])

        toolbar = QHBoxLayout()
        self.count_label = QLabel('', self)
        self.count_label.setObjectName('backupCount')
        toolbar.addWidget(self.count_label)
        toolbar.addStretch(1)
        self.refresh_button = make_button(
            tr('ui.backups.refresh', 'Refresh'), 'tertiary', parent=self)
        self.refresh_button.clicked.connect(self.refreshRequested.emit)
        toolbar.addWidget(self.refresh_button)
        root.addLayout(toolbar)

        self.progress = BlockingProgress(
            tr('ui.backups.progress_title', 'Restoring backup'),
            tr('ui.backups.progress_message',
               'Creating a safety backup before replacing save files.'),
            parent=self,
        )
        self.progress.setObjectName('backupProgress')
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.result_host = QVBoxLayout()
        root.addLayout(self.result_host)

        self.empty_state = ConfiguredEmptyState(
            tr('ui.backups.empty_title', 'No backups found'),
            tr('ui.backups.empty_message',
               'Automatic and manual full-save backups will appear here.'),
            tr('ui.backups.refresh', 'Refresh'),
            self,
        )
        self.empty_state.actionTriggered.connect(self.refreshRequested.emit)
        root.addWidget(self.empty_state, 1)

        self.scroll = QScrollArea(self)
        self.scroll.setObjectName('backupsScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.body = QWidget(self.scroll)
        self.body.setObjectName('backupsBody')
        self.rows_layout = QVBoxLayout(self.body)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(SPACING['sm'])
        self.scroll.setWidget(self.body)
        root.addWidget(self.scroll, 1)
        self.set_backups(())

    def set_backups(self, backups: tuple[BackupRecord, ...]) -> None:
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.rows = []
        for backup in backups:
            row = BackupRow(backup, self.body)
            row.restoreRequested.connect(self.restoreRequested.emit)
            row.revealRequested.connect(self.revealRequested.emit)
            self.rows_layout.addWidget(row)
            self.rows.append(row)
        self.rows_layout.addStretch(1)
        count = len(backups)
        self.count_label.setText(tr(
            'ui.backups.count', '{count} backups', count=count))
        self.empty_state.setVisible(not backups)
        self.scroll.setVisible(bool(backups))

    def set_loading(self, message: str = '') -> None:
        self._clear_result()
        if message:
            self.progress.message_label.setText(message)
            self.progress.setAccessibleDescription(message)
        self.progress.setVisible(True)
        self.refresh_button.setEnabled(False)
        for row in self.rows:
            row.restore_button.setEnabled(False)

    def set_result(self, success: bool, message: str) -> None:
        self.progress.setVisible(False)
        self.refresh_button.setEnabled(True)
        for row in self.rows:
            row.restore_button.setEnabled(True)
        self._clear_result()
        self.result_banner = NotificationBanner(
            message, 'success' if success else 'danger', parent=self)
        self.result_banner.dismissed.connect(self._clear_result)
        self.result_host.addWidget(self.result_banner)

    def clear_operation(self) -> None:
        self.progress.setVisible(False)
        self.refresh_button.setEnabled(True)
        for row in self.rows:
            row.restore_button.setEnabled(True)
        self._clear_result()

    def _clear_result(self) -> None:
        if self.result_banner is None:
            return
        banner = self.result_banner
        self.result_banner = None
        banner.hide()
        banner.setParent(None)
        banner.deleteLater()


__all__ = ['BackupRow', 'BackupsPage']
