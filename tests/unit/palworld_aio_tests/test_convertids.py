"""Steam-ID conversion workflow contracts."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.convertids')
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


@pytest.mark.parametrize('raw', (
    '76561198000000000',
    'steam_76561198000000000',
    'https://steamcommunity.com/profiles/76561198000000000/',
))
def test_normalize_steam_id_accepts_supported_inputs(raw):
    assert module.normalize_steam_id(raw) == 76561198000000000


def test_normalize_steam_id_rejects_invalid_input():
    with pytest.raises(ValueError, match='invalid Steam ID'):
        module.normalize_steam_id('not-an-id')


def test_dialog_uses_shared_review_and_reports_success(app):
    dialog = module.SteamIdConversionDialog()
    assert isinstance(dialog, components.BaseDialog)
    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    dialog.steam_entry.setText('76561198000000000')

    assert dialog.convert_input()
    assert dialog.copy_button.isEnabled()
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
    assert '76561198000000000' in dialog.workflow_review.source_value.text()


def test_invalid_dialog_input_has_failure_result(app):
    dialog = module.SteamIdConversionDialog()
    dialog.steam_entry.setText('bad')
    assert not dialog.convert_input()
    assert not dialog.copy_button.isEnabled()
    assert dialog.workflow_review.result_label.property('resultState') == 'error'
