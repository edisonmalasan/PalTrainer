from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

dialog_mod = import_from('palworld_aio.ui.dialogs.player_pal_dialog')
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
        dialog_mod.PlayerPalActionDialog, '_load_data', lambda _self: None)
    return dialog_mod.PlayerPalActionDialog()


def test_pal_bulk_flow_exposes_review_risk_and_backup(dialog):
    assert dialog.workflow_review.objectName() == 'bulkWorkflowReview'
    assert dialog.workflow_review.property('riskVariant') == 'destructive'
    assert 'cannot be undone' in dialog.workflow_review.risk_label.text()
    assert 'backup' in dialog.workflow_review.backup_label.text().lower()


def test_double_click_delete_uses_confirmation_and_preserves_signal_contract(
        dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    confirmations = []
    seen = []
    dialog.pal_action_selected.connect(
        lambda source, action, targets: seen.append(
            (source, action, targets)))
    dialog.selected_pal_id = 'SheepBall'
    dialog.selected_pal_name = 'Lamball'
    global_ops = import_from(
        'palworld_aio.editor.pal_editor.pal_editor_global_ops')
    monkeypatch.setattr(global_ops, 'count_pals_for_deletion',
                        lambda _pal_id: 12)
    monkeypatch.setattr(
        dialog_mod.QMessageBox,
        'question',
        lambda _parent, _title, detail, *_args, **_kwargs: (
            confirmations.append(detail) or QMessageBox.StandardButton.Yes),
    )

    dialog._on_delete_pal_direct()

    assert len(confirmations) == 1
    assert 'Delete 12 Lamball Pals' in confirmations[0]
    assert 'Back up' in confirmations[0]
    assert seen == [('all', 'delete_pal:SheepBall', [])]
    assert dialog.workflow_review.result_label.isHidden() is False


def test_skill_removal_keeps_scope_encoding(dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    seen = []
    dialog.pal_action_selected.connect(
        lambda source, action, targets: seen.append(
            (source, action, targets)))
    dialog.selected_active_skill_id = 'FireBall'
    dialog.selected_active_skill_name = 'Fire Ball'
    dialog.selected_passive_skill_id = 'Runner'
    dialog.selected_passive_skill_name = 'Runner'
    dialog.skills_player_pals_checkbox.setChecked(True)
    dialog.skills_base_pals_checkbox.setChecked(False)
    dialog.skills_dps_pals_checkbox.setChecked(True)
    monkeypatch.setattr(
        dialog_mod.QMessageBox,
        'question',
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )

    dialog._on_remove_skills()

    assert seen == [(
        'all', 'remove_all:FireBall:Runner:player,dps', [])]


def test_cancelled_pal_delete_emits_nothing(dialog, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    seen = []
    dialog.pal_action_selected.connect(lambda *_args: seen.append(_args))
    dialog.selected_pal_id = 'SheepBall'
    dialog.selected_pal_name = 'Lamball'
    monkeypatch.setattr(
        dialog_mod.QMessageBox,
        'question',
        lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
    )

    dialog._on_delete_pal()

    assert seen == []
