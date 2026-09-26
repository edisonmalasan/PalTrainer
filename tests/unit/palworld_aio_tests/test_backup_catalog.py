from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

import pytest

from tests.dynamic_importer import import_from


catalog = import_from('palworld_aio.application.backup_catalog')


def _save_folder(path: Path, marker: bytes) -> Path:
    path.mkdir(parents=True)
    (path / 'Level.sav').write_bytes(marker + b'-level')
    (path / 'LevelMeta.sav').write_bytes(marker + b'-meta')
    players = path / 'Players'
    players.mkdir()
    (players / f'{marker.decode()}.sav').write_bytes(marker + b'-player')
    return path


def test_discover_backups_reads_metadata_and_sorts_newest_first(tmp_path):
    older = _save_folder(
        tmp_path / 'Before_Player_Edit' / 'PalworldSave_backup_20260908_120000',
        b'older',
    )
    newer = _save_folder(
        tmp_path / 'AllinOneTools' / 'PalworldSave_backup_20260909_134500',
        b'newer',
    )
    invalid = tmp_path / 'Other' / 'PalworldSave_backup_20260910_120000'
    invalid.mkdir(parents=True)
    (invalid / 'Level.sav').write_bytes(b'incomplete')

    records = catalog.discover_backups(
        tmp_path, source_reader=lambda path: f'World {path.name[-6:]}')

    assert [record.path for record in records] == [newer, older]
    assert records[0].created_at == datetime(2026, 9, 9, 13, 45)
    assert records[0].reason == 'AllinOneTools'
    assert records[0].source == 'World 134500'
    assert records[0].size_bytes > 0


def test_restore_creates_safety_snapshot_then_replaces_the_save(tmp_path):
    current = _save_folder(tmp_path / 'current', b'current')
    backup_path = _save_folder(tmp_path / 'backup', b'backup')
    record = catalog.BackupRecord(
        'backup', backup_path, datetime(2026, 9, 9),
        'Before Player Edit', 'Local World', 42,
    )
    progress = []

    result = catalog.restore_backup(
        record, current, tmp_path / 'safety', progress=progress.append)

    assert progress == [
        'Creating safety backup', 'Preparing restore',
        'Restoring files', 'Restore complete',
    ]
    assert (current / 'Level.sav').read_bytes() == b'backup-level'
    assert sorted(path.name for path in (current / 'Players').iterdir()) == [
        'backup.sav']
    assert (result.safety_backup_path / 'Level.sav').read_bytes() == (
        b'current-level')
    assert (result.safety_backup_path / 'Players' / 'current.sav').is_file()


def test_failed_restore_rolls_back_and_reports_safety_path(tmp_path, monkeypatch):
    current = _save_folder(tmp_path / 'current', b'current')
    backup_path = _save_folder(tmp_path / 'backup', b'backup')
    record = catalog.BackupRecord(
        'backup', backup_path, datetime(2026, 9, 9), 'Manual', 'World', 42)
    original_install = catalog._install_staged_snapshot
    calls = 0

    def fail_first_install(stage, target):
        nonlocal calls
        calls += 1
        if calls == 1:
            shutil.copy2(stage / 'Level.sav', target / 'Level.sav')
            raise OSError('simulated interrupted restore')
        original_install(stage, target)

    monkeypatch.setattr(catalog, '_install_staged_snapshot', fail_first_install)

    with pytest.raises(catalog.BackupRestoreError) as caught:
        catalog.restore_backup(record, current, tmp_path / 'safety')

    assert calls == 2
    assert caught.value.safety_backup_path.is_dir()
    assert caught.value.original_changed is False
    assert (current / 'Level.sav').read_bytes() == b'current-level'
    assert (current / 'Players' / 'current.sav').is_file()


def test_restore_stage_failure_keeps_original_and_safety_copy(
        tmp_path, monkeypatch):
    current = _save_folder(tmp_path / 'current', b'current')
    backup_path = _save_folder(tmp_path / 'backup', b'backup')
    record = catalog.BackupRecord(
        'backup', backup_path, datetime(2026, 9, 9), 'Manual', 'World', 42)
    monkeypatch.setattr(catalog, '_stage_snapshot',
                        lambda *_args: (_ for _ in ()).throw(OSError('stage failed')))

    with pytest.raises(catalog.BackupRestoreError) as caught:
        catalog.restore_backup(record, current, tmp_path / 'safety')

    assert caught.value.original_changed is False
    assert caught.value.safety_backup_path.is_dir()
    assert (current / 'Level.sav').read_bytes() == b'current-level'


def test_restore_and_rollback_failure_reports_uncertain_original(
        tmp_path, monkeypatch):
    current = _save_folder(tmp_path / 'current', b'current')
    backup_path = _save_folder(tmp_path / 'backup', b'backup')
    record = catalog.BackupRecord(
        'backup', backup_path, datetime(2026, 9, 9), 'Manual', 'World', 42)

    def fail_install(stage, target):
        shutil.copy2(stage / 'Level.sav', target / 'Level.sav')
        raise OSError('install failed')

    monkeypatch.setattr(catalog, '_install_staged_snapshot', fail_install)

    with pytest.raises(catalog.BackupRestoreError) as caught:
        catalog.restore_backup(record, current, tmp_path / 'safety')

    assert caught.value.original_changed is None
    assert caught.value.safety_backup_path.is_dir()


def test_invalid_restore_inputs_and_size_formatting(tmp_path):
    current = _save_folder(tmp_path / 'current', b'current')
    record = catalog.BackupRecord(
        'same', current, datetime(2026, 9, 9), 'Manual', 'World', 0)
    with pytest.raises(ValueError, match='different folders'):
        catalog.restore_backup(record, current, tmp_path / 'safety')
    assert catalog.format_size(0) == '0 B'
    assert catalog.format_size(1536) == '1.5 KB'
    with pytest.raises(ValueError, match='negative'):
        catalog.format_size(-1)
