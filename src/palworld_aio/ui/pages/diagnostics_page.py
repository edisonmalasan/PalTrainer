"""Safe diagnostics summary and technical console workspace."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from palworld_aio.application.system_info import (
    DiagnosticsInfo, build_diagnostics_info,
)
from palworld_aio.ui.chrome.components import make_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING


class DiagnosticsPage(QWidget):
    copyRequested = pyqtSignal(str)
    exportRequested = pyqtSignal(str)
    revealPathRequested = pyqtSignal(str)
    detachConsoleRequested = pyqtSignal()
    updateCheckRequested = pyqtSignal()

    MAX_CONSOLE_CHARS = 100_000

    def __init__(
        self,
        info: DiagnosticsInfo | None = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.info = info or build_diagnostics_info()
        self.setObjectName('diagnosticsPage')
        self.setAccessibleName(tr('ui.diagnostics.title', 'Diagnostics'))
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['md'])

        scroll = QScrollArea(self)
        scroll.setObjectName('diagnosticsScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget(scroll)
        body.setObjectName('diagnosticsBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['lg'])

        summary = QFrame(body)
        summary.setObjectName('diagnosticsSummary')
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        summary_layout.setHorizontalSpacing(SPACING['xl'])
        summary_layout.setVerticalSpacing(SPACING['sm'])
        rows = (
            (tr('ui.diagnostics.app', 'Application'), self.info.app_version),
            (tr('ui.diagnostics.game', 'Supported game'), self.info.game_version),
            ('Python', self.info.python_version),
            ('Qt / PyQt', f'{self.info.qt_version} / {self.info.pyqt_version}'),
            (tr('ui.diagnostics.os', 'Operating system'), self.info.operating_system),
            (tr('ui.diagnostics.architecture', 'Architecture'), self.info.architecture),
            (tr('ui.diagnostics.mode', 'Launch mode'),
             tr('ui.diagnostics.packaged', 'Packaged application')
             if self.info.packaged else
             tr('ui.diagnostics.development', 'Development checkout')),
        )
        for index, (label, value) in enumerate(rows):
            label_widget = QLabel(label, summary)
            label_widget.setProperty('class', 'secondary')
            value_widget = QLabel(value, summary)
            value_widget.setObjectName('diagnosticsValue')
            value_widget.setWordWrap(True)
            value_widget.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            value_widget.setTextInteractionFlags(
                value_widget.textInteractionFlags()
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse)
            summary_layout.addWidget(label_widget, index, 0)
            summary_layout.addWidget(value_widget, index, 1)
        summary_layout.setColumnStretch(1, 1)
        layout.addWidget(summary)

        paths = QFrame(body)
        paths.setObjectName('diagnosticsPaths')
        paths_layout = QVBoxLayout(paths)
        paths_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        paths_layout.setSpacing(SPACING['sm'])
        paths_title = QLabel(tr('ui.diagnostics.paths', 'Application paths'), paths)
        paths_title.setObjectName('diagnosticsSectionTitle')
        paths_layout.addWidget(paths_title)
        for label, path in self.info.paths.items():
            row = QFrame(paths)
            row.setObjectName('diagnosticsPathRow')
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, SPACING['xs'], 0, SPACING['xs'])
            name = QLabel(tr(
                f'ui.diagnostics.path.{label}',
                label.replace('_', ' ').title()), row)
            name.setMinimumWidth(105)
            name.setProperty('class', 'secondary')
            row_layout.addWidget(name)
            value = QLabel(path, row)
            value.setObjectName('diagnosticsPath')
            value.setWordWrap(True)
            value.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            value.setToolTip(path)
            value.setAccessibleName(f'{name.text()}: {path}')
            value.setTextInteractionFlags(
                value.textInteractionFlags()
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse)
            row_layout.addWidget(value, 1)
            reveal = make_button(
                tr('ui.diagnostics.open', 'Open'), 'tertiary',
                icon='external_link', parent=row)
            reveal.clicked.connect(
                lambda _checked=False, selected=path:
                self.revealPathRequested.emit(selected))
            row_layout.addWidget(reveal)
            paths_layout.addWidget(row)
        layout.addWidget(paths)

        report = QFrame(body)
        report.setObjectName('diagnosticsReport')
        report_layout = QVBoxLayout(report)
        report_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        report_layout.setSpacing(SPACING['sm'])
        report_title = QLabel(
            tr('ui.diagnostics.report', 'Support report'), report)
        report_title.setObjectName('diagnosticsSectionTitle')
        report_layout.addWidget(report_title)
        privacy = QLabel(tr(
            'ui.diagnostics.privacy',
            'Save paths, save data, player identifiers, and console output are '
            'excluded by default.'), report)
        privacy.setObjectName('diagnosticsPrivacy')
        privacy.setWordWrap(True)
        report_layout.addWidget(privacy)
        self.include_console_check = QCheckBox(tr(
            'ui.diagnostics.include_console',
            'Include technical console output (may contain local paths)'), report)
        self.include_console_check.setAccessibleDescription(tr(
            'ui.diagnostics.include_console_help',
            'Off by default. Review the report before sharing it.'))
        report_layout.addWidget(self.include_console_check)
        report_actions = QHBoxLayout()
        self.copy_button = make_button(
            tr('ui.diagnostics.copy', 'Copy Report'), 'secondary',
            icon='copy', parent=report)
        self.copy_button.clicked.connect(
            lambda _checked=False: self.copyRequested.emit(self.report_text()))
        report_actions.addWidget(self.copy_button)
        self.export_button = make_button(
            tr('ui.diagnostics.export', 'Export Report'), 'secondary',
            icon='export', parent=report)
        self.export_button.clicked.connect(
            lambda _checked=False: self.exportRequested.emit(self.report_text()))
        report_actions.addWidget(self.export_button)
        self.update_button = make_button(
            tr('base_inventory.check_updates', 'Check for Updates'), 'tertiary',
            icon='refresh', parent=report)
        self.update_button.clicked.connect(self.updateCheckRequested.emit)
        report_actions.addWidget(self.update_button)
        report_actions.addStretch(1)
        report_layout.addLayout(report_actions)
        self.result_label = QLabel('', report)
        self.result_label.setObjectName('diagnosticsResult')
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        report_layout.addWidget(self.result_label)
        layout.addWidget(report)

        console = QFrame(body)
        console.setObjectName('diagnosticsConsole')
        console_layout = QVBoxLayout(console)
        console_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        console_layout.setSpacing(SPACING['sm'])
        console_head = QHBoxLayout()
        console_title = QLabel(
            tr('ui.diagnostics.console', 'Technical console'), console)
        console_title.setObjectName('diagnosticsSectionTitle')
        console_head.addWidget(console_title)
        console_head.addStretch(1)
        self.detach_button = make_button(
            tr('console.detach', 'Detach'), 'tertiary',
            icon='console', parent=console)
        self.detach_button.clicked.connect(self.detachConsoleRequested.emit)
        console_head.addWidget(self.detach_button)
        console_layout.addLayout(console_head)
        self.console_output = QPlainTextEdit(console)
        self.console_output.setObjectName('diagnosticsConsoleOutput')
        self.console_output.setReadOnly(True)
        self.console_output.setMinimumHeight(190)
        self.console_output.setAccessibleName(
            tr('ui.diagnostics.console', 'Technical console'))
        console_layout.addWidget(self.console_output)
        layout.addWidget(console)
        layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

    def report_text(self) -> str:
        report = self.info.report()
        if not self.include_console_check.isChecked():
            return report
        output = self.console_output.toPlainText().strip()
        return f'{report}\n\nTechnical console (user included)\n{output or "No output."}'

    def set_console_text(self, text: str) -> None:
        self.console_output.setPlainText(text[-self.MAX_CONSOLE_CHARS:])
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_output.setTextCursor(cursor)

    def append_console_message(self, text: str) -> None:
        current = self.console_output.toPlainText()
        self.set_console_text(f'{current}\n{text}'.strip())

    def set_console_detached(self, detached: bool) -> None:
        self.detach_button.setText(
            tr('console.reattach', 'Reattach') if detached
            else tr('console.detach', 'Detach'))
        self.detach_button.setAccessibleName(self.detach_button.text())

    def set_result(self, message: str, status: str = 'success') -> None:
        self.result_label.setText(message)
        self.result_label.setProperty('status', status)
        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)
        self.result_label.show()

    def set_update_warning(self, message: str) -> None:
        if message:
            self.set_result(message, 'warning')


__all__ = ['DiagnosticsPage']
