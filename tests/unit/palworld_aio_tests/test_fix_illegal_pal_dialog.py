"""Illegal-Pal repair selection and durable operation state."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_aio.ui.dialogs.fix_illegal_pal_dialog')
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


def test_selected_illegal_pals_emit_repair_without_closing(app):
    data = {
        'a' * 32: {
            'player_name': 'Fixture', 'guild_name': 'Guild', 'level': 12,
            'pal_count': 1,
            'illegals': [{
                'cid': '', 'name': 'Lamball', 'level': 99, 'rank': 1,
                'illegal_markers': ['level'],
            }],
        },
    }
    dialog = module.FixIllegalPalDialog(data)
    requests = []
    dialog.repair_requested.connect(requests.append)

    dialog._on_fix()

    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    assert requests == [['a' * 32]]
    assert dialog.repair_running
    assert dialog.result() == 0
    dialog.finish_repair('Fixed 1 illegal Pal.')
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
    assert dialog.cancel_btn.isEnabled()


def test_cancel_with_selection_does_not_emit_repair(app):
    data = {
        'b' * 32: {
            'player_name': 'Fixture', 'guild_name': 'Guild', 'level': 1,
            'pal_count': 1, 'illegals': [],
        },
    }
    dialog = module.FixIllegalPalDialog(data)
    requests = []
    dialog.repair_requested.connect(requests.append)

    dialog.reject()

    assert requests == []
