"""Discovery and guarded restoration for PalTrainer full-save backups."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import shutil
import tempfile
from typing import Callable


_BACKUP_PREFIX = 'PalworldSave_backup_'
_SAVE_FILES = ('Level.sav', 'LevelMeta.sav', 'WorldOption.sav', 'LocalData.sav')
ProgressCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class BackupRecord:
    backup_id: str
    path: Path
    created_at: datetime
    reason: str
    source: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class RestoreResult:
    restored_backup: BackupRecord
    safety_backup_path: Path
    target_path: Path


class BackupRestoreError(RuntimeError):
    """Restore failure that preserves the path to the safety snapshot."""

    def __init__(self, message: str, safety_backup_path: Path) -> None:
        super().__init__(message)
        self.safety_backup_path = safety_backup_path


def default_backups_root() -> Path:
    from resource_resolver import get_data_base
    return Path(get_data_base()) / 'Backups'


def _created_at(path: Path) -> datetime:
    raw = path.name.removeprefix(_BACKUP_PREFIX)
    try:
        return datetime.strptime(raw, '%Y%m%d_%H%M%S')
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime)


def _human_reason(path: Path) -> str:
    value = path.parent.name.replace('_', ' ').replace('-', ' ').strip()
    return value or 'Automatic backup'


def _folder_size(path: Path) -> int:
    total = 0
    for candidate in path.rglob('*'):
        try:
            if candidate.is_file():
                total += candidate.stat().st_size
        except OSError:
            continue
    return total


def read_backup_source(path: Path) -> str:
    meta = path / 'LevelMeta.sav'
    if meta.is_file():
        try:
            from palworld_aio.utils import sav_to_gvasfile
            value = sav_to_gvasfile(str(meta)).properties
            return str(value.get('SaveData', {}).get('value', {}).get(
                'WorldName', {}).get('value', 'Unknown world'))
        except Exception:
            pass
    return 'Unknown world'


def discover_backups(
    root: Path | None = None,
    *,
    source_reader: Callable[[Path], str] = read_backup_source,
) -> tuple[BackupRecord, ...]:
    catalog_root = (root or default_backups_root()).resolve()
    if not catalog_root.is_dir():
        return ()
    records = []
    for path in catalog_root.rglob(f'{_BACKUP_PREFIX}*'):
        if not path.is_dir():
            continue
        if not (path / 'Level.sav').is_file() or not (path / 'Players').is_dir():
            continue
        records.append(BackupRecord(
            backup_id=str(path.resolve()),
            path=path.resolve(),
            created_at=_created_at(path),
            reason=_human_reason(path),
            source=source_reader(path),
            size_bytes=_folder_size(path),
        ))
    return tuple(sorted(records, key=lambda item: item.created_at, reverse=True))


def _validate_save_folder(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f'{label} folder does not exist: {resolved}')
    if not (resolved / 'Level.sav').is_file():
        raise ValueError(f'{label} is missing Level.sav')
    if not (resolved / 'Players').is_dir():
        raise ValueError(f'{label} is missing the Players folder')
    return resolved


def _copy_snapshot(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for name in _SAVE_FILES:
        candidate = source / name
        if candidate.is_file():
            shutil.copy2(candidate, destination / name)
    shutil.copytree(source / 'Players', destination / 'Players')


def create_backup_snapshot(
    source: Path,
    destination_root: Path,
    *,
    now: datetime | None = None,
) -> Path:
    source = _validate_save_folder(source, 'Current save')
    destination_root = destination_root.resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now()).strftime('%Y%m%d_%H%M%S_%f')
    destination = destination_root / f'{_BACKUP_PREFIX}{timestamp}'
    _copy_snapshot(source, destination)
    return destination


def _stage_snapshot(source: Path, target_parent: Path) -> Path:
    stage = Path(tempfile.mkdtemp(prefix='.paltrainer_restore_', dir=target_parent))
    try:
        for name in _SAVE_FILES:
            candidate = source / name
            if candidate.is_file():
                shutil.copy2(candidate, stage / name)
        shutil.copytree(source / 'Players', stage / 'Players')
        return stage
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _install_staged_snapshot(stage: Path, target: Path) -> None:
    for name in _SAVE_FILES:
        staged = stage / name
        if staged.is_file():
            os.replace(staged, target / name)
    retired_players = stage.parent / f'.paltrainer_players_{stage.name}'
    target_players = target / 'Players'
    os.replace(target_players, retired_players)
    try:
        os.replace(stage / 'Players', target_players)
    except Exception:
        os.replace(retired_players, target_players)
        raise
    shutil.rmtree(retired_players, ignore_errors=True)


def restore_backup(
    backup: BackupRecord,
    current_save: Path,
    safety_root: Path,
    *,
    progress: ProgressCallback | None = None,
) -> RestoreResult:
    source = _validate_save_folder(backup.path, 'Backup')
    target = _validate_save_folder(current_save, 'Current save')
    if source == target:
        raise ValueError('backup and current save must be different folders')
    report = progress or (lambda _message: None)
    report('Creating safety backup')
    safety = create_backup_snapshot(target, safety_root)
    report('Preparing restore')
    stage = _stage_snapshot(source, target.parent)
    try:
        report('Restoring files')
        _install_staged_snapshot(stage, target)
    except Exception as restore_error:
        rollback_stage = _stage_snapshot(safety, target.parent)
        try:
            _install_staged_snapshot(rollback_stage, target)
        except Exception as rollback_error:
            raise BackupRestoreError(
                'The restore and automatic rollback both failed. '
                f'Your safety backup is available at {safety}. '
                f'Rollback error: {rollback_error}',
                safety,
            ) from restore_error
        finally:
            shutil.rmtree(rollback_stage, ignore_errors=True)
        raise BackupRestoreError(
            'The backup could not be restored. The original save was '
            f'recovered from the safety backup at {safety}.',
            safety,
        ) from restore_error
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    report('Restore complete')
    return RestoreResult(backup, safety, target)


def format_size(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ValueError('size cannot be negative')
    size = float(size_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} GB'


__all__ = [
    'BackupRecord', 'BackupRestoreError', 'RestoreResult',
    'create_backup_snapshot',
    'default_backups_root', 'discover_backups', 'format_size',
    'read_backup_source', 'restore_backup',
]
