"""Slot Injector source, target, risk, and staged-result contracts."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.slot_injector')
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


def test_workspace_uses_shared_review_and_gates_unloaded_actions(app):
    dialog = module.SlotNumUpdaterApp()

    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    assert dialog.browse_button.property('controlRole') == 'secondary'
    assert dialog.apply_selected_btn.property('controlRole') == 'primary'
    assert not dialog.apply_selected_btn.isEnabled()
    assert not dialog.apply_all_btn.isEnabled()
    assert not dialog.save_changes_btn.isEnabled()
    dialog.deleteLater()


def test_selected_reduction_declares_destructive_pal_risk(app, monkeypatch):
    dialog = module.SlotNumUpdaterApp()
    container = {'slot_num': 100, 'used_slots': 90}
    dialog.gvas_file = object()
    dialog.player_containers = [container]
    dialog.new_slots_entry.setValue(80)
    monkeypatch.setattr(dialog, 'get_selected_containers', lambda: [container])

    dialog._sync_workflow_review()

    assert dialog.apply_selected_btn.isEnabled()
    assert dialog.workflow_review.property('riskVariant') == 'destructive'
    assert 'Pals' in dialog.workflow_review.risk_label.text()
    dialog.deleteLater()


def test_cancelled_apply_does_not_mutate_container(app, monkeypatch):
    dialog = module.SlotNumUpdaterApp()
    container = {
        'slot_num': 100, 'used_slots': 10, 'container_id': 'fixture',
        'entry': {'value': {'SlotNum': {'value': 100}, 'Slots': {'value': {'values': []}}}},
    }
    dialog.gvas_file = object()
    dialog.new_slots_entry.setValue(120)
    monkeypatch.setattr(
        module.QMessageBox, 'question',
        lambda *_args, **_kwargs: module.QMessageBox.No)

    dialog._apply_to_containers([container])

    assert container['slot_num'] == 100
    assert container['entry']['value']['SlotNum']['value'] == 100
    assert 'No container slot values were changed' in (
        dialog.workflow_review.result_label.text())
    dialog.deleteLater()
