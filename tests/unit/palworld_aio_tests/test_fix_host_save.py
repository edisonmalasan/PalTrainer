"""Host repair workspace safety presentation."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.fix_host_save')
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


def test_host_workspace_declares_source_target_risk_and_backup(app):
    window = module.FixHostSaveWindow()

    assert isinstance(window.workflow_review, components.BulkWorkflowReview)
    assert window.browse_button.property('controlRole') == 'secondary'
    assert window.xgp_browse_btn.property('controlRole') == 'secondary'
    assert window.migrate_button.property('controlRole') == 'primary'
    assert not window.migrate_button.isEnabled()
    assert 'Backups/Fix Host Save' in window.workflow_review.backup_label.text()
    window.deleteLater()


def test_missing_host_prerequisites_do_not_start_repair(app, monkeypatch):
    window = module.FixHostSaveWindow()
    calls = []
    monkeypatch.setattr(module, 'run_with_loading', lambda *_args, **_kwargs: calls.append('run'))
    monkeypatch.setattr(module, 'show_warning', lambda *_args, **_kwargs: None)

    module.fix_save_wrapper(
        window, window.level_sav_entry, window.old_tree, window.new_tree)

    assert calls == []
    assert not window.migrate_button.isEnabled()
    window.deleteLater()


def test_browsing_host_save_is_backup_and_read_only(monkeypatch, tmp_path):
    level_path = tmp_path / 'Level.sav'
    level_path.write_bytes(b'fixture')
    level_json = {'fixture': True}
    events = []
    monkeypatch.setattr(
        module, 'backup_whole_directory',
        lambda folder, label: events.append(('backup', folder, label)))
    monkeypatch.setattr(module, 'sav_to_json', lambda path: level_json)
    monkeypatch.setattr(
        module, '_build_player_list_from_level',
        lambda data: ([], data))
    monkeypatch.setattr(
        module, 'json_to_sav',
        lambda *_args: events.append(('write',)))

    players, loaded = module.load_save_with_fix(str(level_path))

    assert players == []
    assert loaded is level_json
    assert events == [
        ('backup', str(tmp_path), 'Backups/Fix Host Save'),
    ]
