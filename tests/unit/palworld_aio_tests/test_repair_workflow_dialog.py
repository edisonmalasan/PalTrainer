"""Shared repair review, cancellation, success, and failure contracts."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_aio.ui.dialogs.repair_workflow_dialog')
components = import_from('palworld_aio.ui.chrome.components')
i18n = import_from('i18n')

_app = None


@pytest.fixture(scope='session', autouse=True)
def _locale():
    i18n.load_resources('en_US')


@pytest.fixture(scope='session')
def app():
    global _app
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    return _app


def _spec():
    return module.loaded_save_repair_spec(
        'Repair fixtures',
        '3 fixture records',
        'Normalize fixture records.',
        risk='Fixture values will change.',
    )


def test_repair_dialog_uses_shared_review_and_recovery_copy(app):
    dialog = module.RepairWorkflowDialog(_spec(), lambda: 3, str)

    assert isinstance(dialog, components.BaseDialog)
    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    assert 'backup' in dialog.workflow_review.backup_label.text().lower()
    assert dialog.run_button.property('controlRole') == 'destructive'


def test_cancel_before_start_does_not_call_operation(app):
    calls = []
    dialog = module.RepairWorkflowDialog(
        _spec(), lambda: calls.append('mutated'), str)

    dialog.reject()

    assert calls == []
    assert not dialog.started


def test_success_keeps_result_in_dialog(app, monkeypatch):
    def immediate(callback, operation, *args, **kwargs):
        callback(operation())

    monkeypatch.setattr(module, 'run_with_loading', immediate)
    dialog = module.RepairWorkflowDialog(
        _spec(), lambda: 4, lambda count: f'Repaired {count} records.')
    completed = []
    dialog.completed.connect(completed.append)

    assert dialog.start()

    assert completed == [4]
    assert dialog.succeeded
    assert dialog.workflow_review.result_label.text() == 'Repaired 4 records.'
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
    assert dialog.run_button.isHidden()
    assert dialog.cancel_btn.text() == 'Close'


def test_failure_exposes_reload_or_backup_recovery(app, monkeypatch):
    def immediate(_callback, _operation, *args, **kwargs):
        kwargs['on_error']('fixture failure')

    monkeypatch.setattr(module, 'run_with_loading', immediate)
    dialog = module.RepairWorkflowDialog(_spec(), lambda: None, str)

    dialog.start()

    result = dialog.workflow_review.result_label.text().lower()
    assert 'fixture failure' in result
    assert 'reload' in result
    assert 'backup' in result
    assert dialog.workflow_review.result_label.property('resultState') == 'error'


def test_legacy_false_result_enters_failure_path():
    with pytest.raises(RuntimeError, match='did not succeed'):
        module.require_repair_success(lambda: False, 'did not succeed')
