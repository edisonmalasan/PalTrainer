"""Illegal-player repair selection and durable operation state."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_aio.ui.dialogs.fix_illegal_player_dialog')
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


def test_selected_illegal_players_emit_repair_without_closing(app):
    data = {
        'a' * 32: {
            'player_name': 'Fixture', 'guild_name': 'Guild', 'level': 12,
            'stat_count': 2, 'illegal_stats': {'level': 99, 'stamina': 999},
        },
    }
    dialog = module.FixIllegalPlayerDialog(data)
    requests = []
    dialog.fix_requested.connect(requests.append)

    dialog._on_fix()

    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    assert requests == [['a' * 32]]
    assert dialog.repair_running
    assert dialog.result() == 0
    dialog.finish_repair('Fixed 1 player.')
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
    assert dialog.cancel_btn.isEnabled()


def test_deselect_all_prevents_repair_request(app):
    data = {
        'b' * 32: {
            'player_name': 'Fixture', 'guild_name': 'Guild', 'level': 1,
            'stat_count': 1, 'illegal_stats': {'level': 99},
        },
    }
    dialog = module.FixIllegalPlayerDialog(data)
    requests = []
    dialog.fix_requested.connect(requests.append)
    dialog._deselect_all()

    dialog._on_fix()

    assert requests == []
    assert not dialog.repair_running
