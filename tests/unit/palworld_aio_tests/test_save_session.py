from __future__ import annotations
import os
import time

import pytest
from tests.dynamic_importer import import_from

session_mod = import_from('palworld_aio.managers.save_session')
constants = import_from('palworld_aio.constants')

SaveSession = session_mod.SaveSession
SaveSessionError = session_mod.SaveSessionError
SaveNoPathError = session_mod.SaveNoPathError
SaveNotLevelError = session_mod.SaveNotLevelError
SaveMissingPlayersError = session_mod.SaveMissingPlayersError
SaveWriteError = session_mod.SaveWriteError


_LIFECYCLE_FIELDS = (
    'loaded_level_json', 'loaded_level_mtime', 'current_save_path',
    'backup_save_path', 'srcGuildMapping', 'base_guild_lookup',
    'files_to_delete', 'PLAYER_PAL_COUNTS', 'player_levels',
    'player_character_cache', 'player_duplicate_bodies', 'PLAYER_DETAILS_CACHE',
    'PLAYER_REMAPS', 'selected_source_player', 'original_loaded_level_json',
    'xgp_container_path', 'xgp_save_id', 'xgp_container_index', 'xgp_loaded',
    'gps_path', 'gps_gvas', 'gps_xgp_container_path', 'dirty',
)


@pytest.fixture
def session():
    return SaveSession()


@pytest.fixture
def save_dir(tmp_path):
    players = tmp_path / 'Players'
    players.mkdir()
    level = tmp_path / 'Level.sav'
    level.write_bytes(b'save-data')
    return tmp_path


@pytest.fixture(autouse=True)
def _reset_constants():
    yield
    session_mod.save_session.reset()


def _snapshot_state():
    return {name: getattr(constants, name) for name in _LIFECYCLE_FIELDS}


def _restore_state(state):
    for name, value in state.items():
        setattr(constants, name, value)


@pytest.fixture
def preserved_state():
    return _snapshot_state()


# ---------------------------------------------------------------------------
# Path approval
# ---------------------------------------------------------------------------

def test_approve_save_path_accepts_valid(session, save_dir):
    path = str(save_dir / 'Level.sav')
    assert session.approve_save_path(path) == path


def test_approve_save_path_rejects_empty(session):
    with pytest.raises(SaveNoPathError):
        session.approve_save_path('')


def test_approve_save_path_rejects_non_level(session, save_dir):
    other = save_dir / 'LocalData.sav'
    other.write_bytes(b'x')
    with pytest.raises(SaveNotLevelError):
        session.approve_save_path(str(other))


def test_approve_save_path_rejects_missing_players(session, tmp_path):
    level = tmp_path / 'Level.sav'
    level.write_bytes(b'x')
    with pytest.raises(SaveMissingPlayersError):
        session.approve_save_path(str(level))


# ---------------------------------------------------------------------------
# Snapshot / stale
# ---------------------------------------------------------------------------

def test_snapshot_none_without_save(session):
    constants.current_save_path = None
    assert session.snapshot() is None


def test_snapshot_records_mtime(session, save_dir):
    constants.current_save_path = str(save_dir)
    snap = session.snapshot()
    assert snap is not None
    assert snap.path == str(save_dir / 'Level.sav')
    assert snap.mtime == os.path.getmtime(save_dir / 'Level.sav')


def test_is_stale_false_when_not_loaded(session):
    constants.current_save_path = None
    constants.loaded_level_mtime = None
    assert session.is_stale() is False


def test_is_stale_detects_modified_file(session, save_dir):
    level = save_dir / 'Level.sav'
    constants.current_save_path = str(save_dir)
    constants.loaded_level_mtime = os.path.getmtime(level)
    old = time.time() - 3600
    os.utime(level, (old, old))
    assert session.is_stale() is True


def test_is_stale_false_when_unchanged(session, save_dir):
    level = save_dir / 'Level.sav'
    constants.current_save_path = str(save_dir)
    constants.loaded_level_mtime = os.path.getmtime(level)
    assert session.is_stale() is False


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------

def test_atomic_write_creates_and_replaces(session, tmp_path):
    target = tmp_path / 'nested' / 'out.sav'
    session.atomic_write(str(target), b'first')
    assert target.read_bytes() == b'first'
    session.atomic_write(str(target), b'second')
    assert target.read_bytes() == b'second'


def test_atomic_write_leaves_no_temp_files(session, tmp_path):
    target = tmp_path / 'out.sav'
    session.atomic_write(str(target), b'data')
    leftovers = [p for p in tmp_path.iterdir() if p.name.endswith('.pt')]
    assert leftovers == []


def test_save_raises_when_nothing_loaded(session):
    session.reset()
    with pytest.raises(SaveSessionError):
        session.save()


# ---------------------------------------------------------------------------
# Save core: atomic replacement, pending deletions, dirty refresh
# ---------------------------------------------------------------------------

def test_save_replaces_level_atomically(session, save_dir, monkeypatch):
    level = save_dir / 'Level.sav'
    constants.current_save_path = str(save_dir)
    constants.backup_save_path = str(save_dir)
    constants.loaded_level_json = {'fake': True}
    constants.loaded_level_mtime = os.path.getmtime(level)
    constants.dirty = True
    constants.xgp_loaded = False

    def fake_wrapper_to_sav(wrapper, path):
        with open(path, 'wb') as f:
            f.write(b'new-data')

    monkeypatch.setattr('palworld_aio.utils.wrapper_to_sav', fake_wrapper_to_sav)
    session.save()
    assert level.read_bytes() == b'new-data'
    assert constants.dirty is False
    assert constants.loaded_level_mtime == os.path.getmtime(level)


def test_save_applies_pending_deletions(session, save_dir, monkeypatch):
    players = save_dir / 'Players'
    (players / 'DEADBEEF.sav').write_bytes(b'x')
    (players / 'DEADBEEF_dps.sav').write_bytes(b'x')
    constants.current_save_path = str(save_dir)
    constants.backup_save_path = str(save_dir)
    constants.loaded_level_json = {'fake': True}
    constants.loaded_level_mtime = os.path.getmtime(save_dir / 'Level.sav')
    constants.files_to_delete = {'deadbeef'}
    constants.xgp_loaded = False

    def fake_wrapper_to_sav(wrapper, path):
        with open(path, 'wb') as f:
            f.write(b'new-data')

    monkeypatch.setattr('palworld_aio.utils.wrapper_to_sav', fake_wrapper_to_sav)
    session.save()
    assert not (players / 'DEADBEEF.sav').exists()
    assert not (players / 'DEADBEEF_dps.sav').exists()
    assert constants.files_to_delete == set()


def test_save_raises_write_error_and_cleans_tmp(session, save_dir, monkeypatch):
    constants.current_save_path = str(save_dir)
    constants.backup_save_path = str(save_dir)
    constants.loaded_level_json = {'fake': True}
    constants.loaded_level_mtime = os.path.getmtime(save_dir / 'Level.sav')

    def failing_wrapper_to_sav(wrapper, path):
        raise RuntimeError('boom')

    monkeypatch.setattr('palworld_aio.utils.wrapper_to_sav', failing_wrapper_to_sav)
    with pytest.raises(SaveWriteError):
        session.save()
    leftovers = [p for p in save_dir.iterdir() if p.name.endswith('.sav.pt')]
    assert leftovers == []


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_lifecycle_state(session, preserved_state):
    try:
        constants.loaded_level_json = {'x': 1}
        constants.loaded_level_mtime = 123.0
        constants.current_save_path = 'C:/fake'
        constants.backup_save_path = 'C:/fake'
        constants.srcGuildMapping = object()
        constants.base_guild_lookup = {'a': 1}
        constants.files_to_delete = {'uid'}
        constants.xgp_loaded = True
        constants.dirty = True
        session.reset()
        assert constants.loaded_level_json is None
        assert constants.loaded_level_mtime is None
        assert constants.current_save_path is None
        assert constants.backup_save_path is None
        assert constants.srcGuildMapping is None
        assert constants.base_guild_lookup == {}
        assert constants.files_to_delete == set()
        assert constants.xgp_loaded is False
        assert constants.dirty is False
    finally:
        _restore_state(preserved_state)
