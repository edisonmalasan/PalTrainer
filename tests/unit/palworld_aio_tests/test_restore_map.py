"""Map restore discovery, backup ordering, and workflow presentation."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.restore_map')
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


def test_discovery_finds_nested_local_data(monkeypatch, tmp_path):
    world = tmp_path / 'owner' / 'world'
    world.mkdir(parents=True)
    (world / 'LocalData.sav').write_bytes(b'fixture')
    monkeypatch.setattr(module, 'savegames_path', str(tmp_path))
    monkeypatch.setattr(module.constants, 'loaded_level_json', None)
    monkeypatch.setattr(module.constants, 'current_save_path', None)

    assert module.discover_local_data_folders() == [str(world)]


def test_clear_local_fog_backs_up_before_mutation(monkeypatch):
    events = []
    monkeypatch.setattr(
        module, 'discover_local_data_folders', lambda: ['fixture-world'])
    monkeypatch.setattr(
        module, 'backup_local_data', lambda folder: events.append(('backup', folder)))
    monkeypatch.setattr(
        module, 'clear_fog_in_local_data',
        lambda path: events.append(('clear', path)))

    assert module.clear_fog_in_all_subfolders() == 1
    assert events == [
        ('backup', 'fixture-world'),
        ('clear', os.path.join('fixture-world', 'LocalData.sav')),
    ]


def test_dialog_declares_risk_backup_and_no_change_cancel(app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        module, 'discover_local_data_folders', lambda: ['fixture-world'])
    monkeypatch.setattr(
        module, 'clear_fog_in_all_subfolders', lambda: calls.append('changed'))
    dialog = module.RestoreMapDialog()

    assert isinstance(dialog, components.BaseDialog)
    assert isinstance(dialog.workflow_review, components.BulkWorkflowReview)
    assert 'Backups/Restore Map' in dialog.workflow_review.backup_label.text()
    dialog.reject()

    assert calls == []


def test_local_restore_reports_affected_count(app, monkeypatch):
    monkeypatch.setattr(
        module, 'discover_local_data_folders', lambda: ['fixture-world'])
    monkeypatch.setattr(module, 'clear_fog_in_all_subfolders', lambda: 2)

    def immediate(callback, operation, *args, **kwargs):
        callback(operation())

    monkeypatch.setattr(module, 'run_with_loading', immediate)
    dialog = module.RestoreMapDialog()
    dialog.on_local_clear_fog()

    assert '2' in dialog.workflow_review.result_label.text()
    assert dialog.workflow_review.result_label.property('resultState') == 'success'
