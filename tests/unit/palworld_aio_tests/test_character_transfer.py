"""Character Transfer workspace prerequisite and staged-result UI."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.character_transfer')
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


@pytest.fixture(autouse=True)
def reset_state():
    module.level_sav_path = None
    module.t_level_sav_path = None
    module.level_json = None
    module.targ_lvl = None
    module.selected_source_player = None
    module.selected_target_player = None
    module.modified_target_players.clear()
    yield
    module.modified_target_players.clear()


def test_workspace_uses_shared_review_and_gates_actions(app):
    window = module.CharacterTransferWindow()

    assert isinstance(window.workflow_review, components.BulkWorkflowReview)
    assert window.src_btn.property('controlRole') == 'secondary'
    assert window.tgt_btn.property('controlRole') == 'secondary'
    assert window.transfer_btn.property('controlRole') == 'primary'
    assert not window.transfer_btn.isEnabled()
    assert not window.transfer_all_btn.isEnabled()
    assert not window.save_btn.isEnabled()
    window.deleteLater()


def test_source_target_selection_enables_staging_then_save(app):
    window = module.CharacterTransferWindow()
    module.level_sav_path = 'C:/source/Level.sav'
    module.t_level_sav_path = 'C:/target/Level.sav'
    module.level_json = {'loaded': True}
    module.targ_lvl = {'loaded': True}
    module.selected_source_player = 'A' * 32
    module.selected_target_player = 'B' * 32
    window.source_level_path_label.setText(module.level_sav_path)
    window.target_level_path_label.setText(module.t_level_sav_path)

    window._sync_transfer_review()

    assert window.transfer_btn.isEnabled()
    assert window.transfer_all_btn.isEnabled()
    assert not window.save_btn.isEnabled()
    module.modified_target_players.add(module.selected_target_player)
    window._set_transfer_result('Transfer staged in memory.')
    assert window.save_btn.isEnabled()
    assert window.workflow_review.result_label.property('resultState') == 'success'
    window.deleteLater()
