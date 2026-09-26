"""Shared review, progress, result, and recovery UI for repair operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PyQt6.QtCore import pyqtSignal

from i18n import t
from loading_manager import run_with_loading
from palworld_aio.ui.chrome.components import BaseDialog, BulkWorkflowReview


@dataclass(frozen=True)
class RepairWorkflowSpec:
    """Presentation contract for one consequential repair operation."""

    title: str
    affected: str
    review: str
    backup: str
    risk: str = ''
    source: str = ''
    target: str = ''
    confirm_text: str = ''


class RepairWorkflowDialog(BaseDialog):
    """Run an existing repair callback while keeping durable local state visible.

    The dialog never owns save mutation logic. It only gates the supplied
    callback behind review, disables cancellation while the callback is active,
    and reports a recovery-oriented result after completion.
    """

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        spec: RepairWorkflowSpec,
        operation: Callable[[], Any],
        result_message: Callable[[Any], str],
        parent=None,
    ) -> None:
        super().__init__(
            spec.title,
            parent,
            min_size=(680, 500),
            danger=bool(spec.risk),
            kicker=t('repair.workflow.kicker', default='Repair and recovery'),
        )
        self.spec = spec
        self.operation = operation
        self.result_message = result_message
        self.result: Any = None
        self.started = False
        self.succeeded = False

        self.workflow_review = BulkWorkflowReview(
            source=spec.source or t(
                'repair.workflow.loaded_source', default='Current loaded save'),
            target=spec.target or spec.affected,
            review=spec.review,
            parent=self,
        )
        self.workflow_review.set_risk(spec.risk, spec.backup)
        self.content_layout.addWidget(self.workflow_review)

        self.run_button = self.add_confirm_button(
            spec.confirm_text or t(
                'repair.workflow.run', default='Run repair'),
            danger=bool(spec.risk),
        )
        self.run_button.clicked.disconnect(self.accept)
        self.run_button.clicked.connect(self.start)
        self.cancel_btn.setText(t('ui.action.cancel', default='Cancel'))

    def start(self) -> bool:
        if self.started:
            return False
        self.started = True
        self.run_button.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.workflow_review.progress.setRange(0, 0)
        self.workflow_review.progress.setFormat(t(
            'repair.workflow.running', default='Repair in progress…'))
        self.workflow_review.progress.show()

        run_with_loading(
            self._on_done,
            self.operation,
            parent=self,
            on_error=self._on_error,
            local_state=True,
        )
        return True

    def _finish_common(self) -> None:
        self.workflow_review.progress.setRange(0, 1)
        self.workflow_review.progress.setValue(1)
        self.run_button.hide()
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText(t('button.close', default='Close'))
        self.close_btn.setEnabled(True)
        self._primary_button = self.cancel_btn
        self.cancel_btn.setFocus()

    def _on_done(self, result: Any) -> None:
        self.result = result
        self.succeeded = True
        self.workflow_review.progress.setFormat(t(
            'repair.workflow.complete', default='Repair complete'))
        self.workflow_review.set_result(self.result_message(result), success=True)
        self._finish_common()
        self.completed.emit(result)

    def _on_error(self, error: Any) -> None:
        detail = str(error).strip()
        self.workflow_review.progress.setFormat(t(
            'repair.workflow.failed_short', default='Repair failed'))
        self.workflow_review.set_result(t(
            'repair.workflow.failed',
            default=(
                'The repair did not complete. Do not save unexpected in-memory '
                'changes; reload the current save or restore its load-time backup. '
                'Details: {detail}'),
            detail=detail,
        ), success=False)
        self._finish_common()
        self.failed.emit(detail)


def loaded_save_repair_spec(
    title: str,
    affected: str,
    review: str,
    *,
    risk: str = '',
    confirm_text: str = '',
    backup: str = '',
) -> RepairWorkflowSpec:
    """Build the standard recovery contract for in-memory save repairs."""

    return RepairWorkflowSpec(
        title=title,
        affected=affected,
        review=review,
        risk=risk,
        confirm_text=confirm_text,
        backup=backup or t(
            'repair.workflow.loaded_backup',
            default=(
                'Level changes stay in memory until Save Changes. A recovery '
                'backup is created before saving high-risk changes.'),
        ),
    )


def require_repair_success(operation: Callable[[], Any], failure_message: str) -> Any:
    """Turn a legacy boolean failure result into the shared error path."""

    result = operation()
    if result is False or result is None:
        raise RuntimeError(failure_message)
    return result
