"""Contextual transfer workflow review and result contracts."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_aio.ui.dialogs.transfer_workflow_dialog')
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
    return module.TransferWorkflowSpec(
        'Import bases', '2 files', 'Fixture Guild', 'Import both bases.',
        'Load-time backup available.', 'Adds new save records.', 'Import')


def test_cancel_before_start_leaves_operation_untouched(app):
    calls = []
    dialog = module.TransferWorkflowDialog(
        _spec(), lambda: calls.append('changed'), str)

    assert isinstance(dialog, components.BaseDialog)
    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    dialog.reject()
    assert calls == []


def test_result_predicate_controls_durable_result(app, monkeypatch):
    monkeypatch.setattr(
        module, 'run_with_loading',
        lambda callback, operation, *args, **kwargs: callback(operation()))
    dialog = module.TransferWorkflowDialog(
        _spec(), lambda: (2, 0),
        lambda result: f'Imported {result[0]} bases.',
        result_success=lambda result: result[0] > 0)

    dialog.start()

    assert dialog.succeeded
    assert dialog.workflow_review.result_label.text() == 'Imported 2 bases.'
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
    assert dialog.run_button.isHidden()
    assert dialog.cancel_btn.text() == 'Close'


def test_failed_result_is_not_emitted_as_completed(app, monkeypatch):
    monkeypatch.setattr(
        module, 'run_with_loading',
        lambda callback, operation, *args, **kwargs: callback(operation()))
    dialog = module.TransferWorkflowDialog(
        _spec(), lambda: False, lambda _result: 'Nothing imported.',
        result_success=bool)
    completed = []
    dialog.completed.connect(completed.append)

    dialog.start()

    assert not dialog.succeeded
    assert completed == []
    assert dialog.workflow_review.result_label.property('resultState') == 'error'
