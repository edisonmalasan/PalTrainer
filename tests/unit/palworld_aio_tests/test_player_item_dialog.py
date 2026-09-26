from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

dialog_mod = import_from('palworld_aio.ui.dialogs.player_item_dialog')
i18n_mod = import_from('i18n')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='module', autouse=True)
def _english():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture
def dialog(monkeypatch):
    _app_instance()
    monkeypatch.setattr(
        dialog_mod.PlayerItemActionDialog, '_load_items', lambda _self: None)
    monkeypatch.setattr(
        dialog_mod.PlayerItemActionDialog, '_load_players', lambda _self: None)
    return dialog_mod.PlayerItemActionDialog()


def test_item_and_ability_bulk_flow_exposes_review_and_backup(dialog):
    assert dialog.workflow_review.objectName() == 'bulkWorkflowReview'
    assert 'backup' in dialog.workflow_review.backup_label.text().lower()
    assert dialog.workflow_review.risk_label.isHidden() is False
    assert dialog.workflow_review.source_value.text()
    assert dialog.workflow_review.target_value.text()
    assert dialog.workflow_review.review_value.text()


def test_add_item_keeps_existing_signal_contract_and_reports_result(
        dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    seen = []
    dialog.item_action_selected.connect(
        lambda item_id, action, players: seen.append(
            (item_id, action, players)))
    dialog.selected_item_id = 'AncientCore'
    dialog.selected_item_name = 'Ancient Core'
    dialog.qty_input.setText('7')
    monkeypatch.setattr(dialog, '_get_selected_players', lambda: ['p1', 'p2'])
    monkeypatch.setattr(dialog, '_load_players', lambda: None)
    monkeypatch.setattr(dialog, '_update_player_list', lambda: None)
    monkeypatch.setattr(dialog, '_find_players_with_item', lambda: None)
    monkeypatch.setattr(
        dialog_mod.ItemData,
        'get_target_container',
        lambda _item_id: 'CommonContainer',
    )
    confirmations = []
    def accept_add(_parent, _title, detail, *_args):
        confirmations.append(detail)
        return QMessageBox.StandardButton.Yes
    monkeypatch.setattr(dialog_mod.QMessageBox, 'question', accept_add)

    dialog._on_add_item()

    assert seen == [(
        'AncientCore', 'add:7:CommonContainer', ['p1', 'p2'])]
    assert confirmations == ['Add 7 × Ancient Core to each of 2 selected players?']
    assert dialog.workflow_review.progress.value() == 1
    assert dialog.workflow_review.result_label.isHidden() is False


def test_cancelled_bulk_add_emits_nothing(dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    seen = []
    dialog.item_action_selected.connect(lambda *_args: seen.append(_args))
    dialog.selected_item_id = 'AncientCore'
    dialog.qty_input.setText('7')
    monkeypatch.setattr(dialog, '_get_selected_players', lambda: ['p1', 'p2'])
    monkeypatch.setattr(
        dialog_mod.ItemData, 'get_target_container',
        lambda _item_id: 'CommonContainer')
    monkeypatch.setattr(
        dialog_mod.QMessageBox, 'question',
        lambda *_args, **_kwargs: QMessageBox.StandardButton.No)

    dialog._on_add_item()

    assert seen == []


def test_cancelled_item_removal_emits_nothing(dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    seen = []
    dialog.item_action_selected.connect(lambda *_args: seen.append(_args))
    dialog.selected_item_id = 'AncientCore'
    dialog.selected_item_name = 'Ancient Core'
    monkeypatch.setattr(dialog, '_get_selected_players', lambda: ['p1', 'p2'])
    monkeypatch.setattr(
        dialog_mod.QMessageBox,
        'question',
        lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
    )

    dialog._on_remove_item()

    assert seen == []
