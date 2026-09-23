"""Shared source/target workflow dialog for contextual transfer operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PyQt6.QtCore import pyqtSignal

from i18n import t
from loading_manager import run_with_loading
from palworld_aio.ui.chrome.components import BaseDialog, BulkWorkflowReview


@dataclass(frozen=True)
class TransferWorkflowSpec:
    title: str
    source: str
    target: str
    review: str
    backup: str = ''
    risk: str = ''
    confirm_text: str = ''


class TransferWorkflowDialog(BaseDialog):
    """Review and run a caller-owned import, export, clone, or transfer."""

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        spec: TransferWorkflowSpec,
        operation: Callable[[], Any],
        result_message: Callable[[Any], str],
        parent=None,
        *,
        result_success: Callable[[Any], bool] | None = None,
    ) -> None:
        super().__init__(
            spec.title,
            parent,
            min_size=(700, 540),
            danger=bool(spec.risk),
            kicker=t('transfer.workflow.kicker', default='Transfer workflow'),
        )
        self.operation = operation
        self.result_message = result_message
        self.result_success = result_success or (lambda _result: True)
        self.started = False
        self.succeeded = False
        self.result: Any = None
        self.workflow_review = BulkWorkflowReview(
            spec.source, spec.target, spec.review, self)
        self.workflow_review.set_risk(spec.risk, spec.backup)
        self.content_layout.addWidget(self.workflow_review)
        self.run_button = self.add_confirm_button(
            spec.confirm_text or t(
                'transfer.workflow.run', default='Run operation'),
            danger=bool(spec.risk),
        )
        self.run_button.clicked.disconnect(self.accept)
        self.run_button.clicked.connect(self.start)

    def start(self) -> bool:
        if self.started:
            return False
        self.started = True
        self.run_button.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.workflow_review.progress.setRange(0, 0)
        self.workflow_review.progress.setFormat(t(
            'transfer.workflow.running', default='Operation in progress…'))
        self.workflow_review.progress.show()
        run_with_loading(
            self._on_done,
            self.operation,
            parent=self,
            on_error=self._on_error,
            local_state=True,
        )
        return True

    def _finish(self) -> None:
        self.run_button.hide()
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText(t('button.close', default='Close'))
        self.close_btn.setEnabled(True)
        self._primary_button = self.cancel_btn
        self.cancel_btn.setFocus()

    def _on_done(self, result: Any) -> None:
        self.result = result
        self.succeeded = self.result_success(result)
        self.workflow_review.set_progress(
            1, 1,
            t('transfer.workflow.complete', default='Operation complete')
            if self.succeeded else
            t('transfer.workflow.failed_short', default='Operation failed'))
        self.workflow_review.set_result(
            self.result_message(result), success=self.succeeded)
        self._finish()
        if self.succeeded:
            self.completed.emit(result)
        else:
            self.failed.emit(self.workflow_review.result_label.text())

    def _on_error(self, error: Any) -> None:
        detail = str(error).strip()
        self.workflow_review.set_progress(
            1, 1, t('transfer.workflow.failed_short', default='Operation failed'))
        self.workflow_review.set_result(t(
            'transfer.workflow.failed',
            default='The operation did not complete. No further changes were applied. {detail}',
            detail=detail), success=False)
        self._finish()
        self.failed.emit(detail)
