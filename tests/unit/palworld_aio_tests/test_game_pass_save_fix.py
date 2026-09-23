"""Game Pass/Steam conversion presentation and no-change cancellation."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.game_pass_save_fix')
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


@pytest.fixture
def widget(app, monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'root_dir', str(tmp_path))
    value = module.GamePassSaveFixWidget()
    yield value
    value.deleteLater()


def test_platform_converter_uses_shared_workflow_and_buttons(widget):
    assert isinstance(widget.workflow_review, components.BulkWorkflowReview)
    assert widget.xgp_browse_btn.property('controlRole') == 'secondary'
    assert widget.steam_browse_btn.property('controlRole') == 'secondary'
    assert widget.workflow_review.risk_label.isVisibleTo(
        widget.workflow_review)


def test_cancelled_gamepass_source_reports_no_change(widget, monkeypatch):
    monkeypatch.setattr(
        module.QFileDialog, 'getExistingDirectory',
        lambda *_args, **_kwargs: '',
    )
    widget.get_save_game_pass()
    assert widget.conversion_direction is None
    assert 'No files were changed' in widget.workflow_review.result_label.text()


@pytest.mark.parametrize(('message_type', 'expected'), (
    ('info', 'success'),
    ('critical', 'error'),
))
def test_result_messages_are_durable_in_workflow(
        widget, monkeypatch, message_type, expected):
    monkeypatch.setattr(module, 'show_information', lambda *_args: None)
    monkeypatch.setattr(module, 'show_warning', lambda *_args: None)
    monkeypatch.setattr(module, 'show_critical', lambda *_args: None)
    widget.handle_message(message_type, 'Result', 'Finished fixture operation')
    assert widget.workflow_review.result_label.text() == 'Finished fixture operation'
    assert widget.workflow_review.result_label.property('resultState') == expected
    assert widget.workflow_review.progress.value() == 1
