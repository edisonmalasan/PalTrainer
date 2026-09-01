from __future__ import annotations

import os
import shutil
import tempfile
import time

from palworld_aio import constants
from palworld_aio.application.derived_state import (
    build_player_levels,
    refresh_death_bag_protection,
)


class SaveSessionError(Exception):
    """Base error for save session operations."""


class SavePathError(SaveSessionError):
    """The provided save path is invalid or unusable."""


class SaveNoPathError(SavePathError):
    """No save path was provided."""


class SaveNotLevelError(SavePathError):
    """The path does not point to a ``Level.sav`` file."""


class SaveMissingPlayersError(SavePathError):
    """The save folder is missing its ``Players`` directory."""


class SaveStaleError(SaveSessionError):
    """Save file on disk has changed since it was loaded."""


class SaveBackupError(SaveSessionError):
    """Backup creation failed."""


class SaveWriteError(SaveSessionError):
    """Writing the save file failed."""


class SaveSnapshot:
    """Immutable record of file state at a point in time."""

    __slots__ = ('path', 'mtime', 'taken_at')

    def __init__(self, path: str, mtime: float) -> None:
        self.path = path
        self.mtime = mtime
        self.taken_at = time.time()


class SaveSession:
    """Owns save lifecycle state, operations, and mutation of the shared
    ``constants`` read-model.

    This is the single writer of lifecycle fields in
    :mod:`palworld_aio.constants` (``loaded_level_json``,
    ``current_save_path``, ``loaded_level_mtime``, ``backup_save_path``,
    ``srcGuildMapping``, ``files_to_delete``, etc.).  The rest of the
    application reads those fields without change.

    The session is UI-free: callers own dialogs, signal emission, and the
    worker/task boundary.  Long-running operations are exposed as plain
    methods so they can run behind ``run_with_loading`` or any owned task
    runner.
    """

    def __init__(self) -> None:
        self.dps_executor: object = None
        self.dps_futures: list = []
        self.dps_tasks: list = []
        self.player_sav_cache: dict = {}
        self._xgp_temp_dir: str | None = None
        self._disabled_adapters: list[str] = []
        self.last_guild_mapping_error: str | None = None
        self._last_snapshot: SaveSnapshot | None = None

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return constants.loaded_level_json is not None

    @property
    def is_dirty(self) -> bool:
        return constants.dirty

    @is_dirty.setter
    def is_dirty(self, value: bool) -> None:
        constants.dirty = value

    @property
    def current_save_path(self) -> str | None:
        return constants.current_save_path

    @current_save_path.setter
    def current_save_path(self, value: str | None) -> None:
        constants.current_save_path = value

    @property
    def backup_save_path(self) -> str | None:
        return constants.backup_save_path

    @backup_save_path.setter
    def backup_save_path(self, value: str | None) -> None:
        constants.backup_save_path = value

    @property
    def loaded_level_json(self):
        return constants.loaded_level_json

    @property
    def loaded_mtime(self) -> float | None:
        return constants.loaded_level_mtime

    @property
    def pending_deletions(self) -> set:
        return constants.files_to_delete

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        constants.loaded_level_json = None
        constants.loaded_level_mtime = None
        constants.current_save_path = None
        constants.backup_save_path = None
        constants.srcGuildMapping = None
        constants.base_guild_lookup = {}
        constants.files_to_delete = set()
        constants.PLAYER_PAL_COUNTS = {}
        constants.player_levels = {}
        constants.player_character_cache = {}
        constants.player_duplicate_bodies = {}
        constants.PLAYER_DETAILS_CACHE = {}
        constants.PLAYER_REMAPS = {}
        constants.death_bag_protected_instance_ids.clear()
        constants.death_bag_protected_container_ids.clear()
        constants.selected_source_player = None
        constants.original_loaded_level_json = None
        constants.xgp_container_path = None
        constants.xgp_save_id = None
        constants.xgp_container_index = None
        constants.xgp_loaded = False
        constants.gps_path = None
        constants.gps_gvas = None
        constants.gps_xgp_container_path = None
        constants.dirty = False
        from palobject import MappingCacheObject
        if hasattr(MappingCacheObject, '_MappingCacheInstances'):
            MappingCacheObject._MappingCacheInstances.clear()
        self.dps_tasks.clear()
        self.player_sav_cache.clear()
        if self._xgp_temp_dir:
            shutil.rmtree(self._xgp_temp_dir, ignore_errors=True)
            self._xgp_temp_dir = None

    # ------------------------------------------------------------------
    # Path approval
    # ------------------------------------------------------------------

    def approve_save_path(self, path: str) -> str:
        if not path:
            raise SaveNoPathError('No path provided')
        if not path.endswith('Level.sav'):
            raise SaveNotLevelError('File must be Level.sav')
        d = os.path.dirname(path)
        players_dir = os.path.join(d, 'Players')
        if not os.path.isdir(players_dir):
            raise SaveMissingPlayersError('Players folder not found')
        return path

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def make_backup(self, tool_name: str) -> str | None:
        if not constants.backup_save_path:
            return None
        from import_libs import backup_whole_directory
        try:
            backup_whole_directory(constants.backup_save_path, f'Backups/{tool_name}')
            return constants.backup_save_path
        except Exception as e:
            raise SaveBackupError(f'Backup failed: {e}') from e

    # ------------------------------------------------------------------
    # Snapshot / stale
    # ------------------------------------------------------------------

    def snapshot(self) -> SaveSnapshot | None:
        if not constants.current_save_path:
            return None
        level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
        try:
            mtime = os.path.getmtime(level_sav_path)
            return SaveSnapshot(level_sav_path, mtime)
        except OSError:
            return None

    def is_stale(self) -> bool:
        if not constants.current_save_path:
            return False
        baseline = self._last_snapshot.mtime if self._last_snapshot else constants.loaded_level_mtime
        if baseline is None:
            return False
        level_path = os.path.join(constants.current_save_path, 'Level.sav')
        try:
            return os.path.getmtime(level_path) != baseline
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Atomic write
    # ------------------------------------------------------------------

    def atomic_write(self, path: str, data: bytes) -> None:
        target_dir = os.path.dirname(path)
        os.makedirs(target_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix='.pt', dir=target_dir)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            os.replace(tmp_path, path)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise SaveWriteError(f'Atomic write failed: {e}') from e

    # ------------------------------------------------------------------
    # Load core (no reset, no backup — callers own those)
    # ------------------------------------------------------------------

    def load(self, path: str) -> bool:
        if not os.path.isfile(path):
            return False
        constants.current_save_path = os.path.dirname(path)
        constants.backup_save_path = constants.current_save_path
        from palworld_aio.utils import sav_to_gvas_wrapper
        from palobject import MappingCacheObject
        try:
            constants.loaded_level_json = sav_to_gvas_wrapper(path)
            constants.loaded_level_mtime = os.path.getmtime(path)
        except Exception:
            return False
        constants.invalidate_container_lookup()
        refresh_death_bag_protection()
        from palworld_aio.inventory.dynamic_item_manager import get_dynamic_item_manager
        get_dynamic_item_manager().sync_with_save_data(constants.loaded_level_json)
        build_player_levels()
        if not constants.loaded_level_json:
            return False
        data_source = constants.loaded_level_json['properties']['worldSaveData']['value']
        try:
            if hasattr(MappingCacheObject, 'clear_cache'):
                MappingCacheObject.clear_cache()
            constants.srcGuildMapping = MappingCacheObject.get(data_source, use_mp=True)
            if constants.srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
                constants.srcGuildMapping.GroupSaveDataMap = {}
            self.last_guild_mapping_error = None
        except Exception as e:
            constants.srcGuildMapping = None
            self.last_guild_mapping_error = str(e)
        constants.base_guild_lookup = {}
        if constants.srcGuildMapping:
            for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                gid = str(gid_uuid)
                guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                for base_id_uuid in gdata['value']['RawData']['value'].get('base_ids', []):
                    constants.base_guild_lookup[str(base_id_uuid)] = {'GuildName': guild_name, 'GuildID': gid}
        self._last_snapshot = self.snapshot()
        return True

    # ------------------------------------------------------------------
    # Reload core
    # ------------------------------------------------------------------

    def reload(self) -> bool:
        if not constants.current_save_path:
            raise SaveSessionError('No save is currently loaded')
        level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
        if not os.path.exists(level_sav_path):
            raise SaveSessionError(f'Level.sav not found at {level_sav_path}')
        return self.load(level_sav_path)

    # ------------------------------------------------------------------
    # Save core (write, pending deletions, mtime refresh, clear dirty)
    # ------------------------------------------------------------------

    def save(self) -> None:
        if not constants.current_save_path or not constants.loaded_level_json:
            raise SaveSessionError('No save is currently loaded')
        level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
        from palworld_aio.utils import wrapper_to_sav
        fd, tmp_path = tempfile.mkstemp(suffix='.sav.pt', dir=constants.current_save_path)
        os.close(fd)
        try:
            wrapper_to_sav(constants.loaded_level_json, tmp_path)
            os.replace(tmp_path, level_sav_path)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise SaveWriteError(f'Write failed: {e}') from e
        players_folder = os.path.join(constants.current_save_path, 'Players')
        for uid in constants.files_to_delete:
            f = os.path.join(players_folder, uid.upper() + '.sav')
            f_dps = os.path.join(players_folder, f'{uid.upper()}_dps.sav')
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
            try:
                os.remove(f_dps)
            except FileNotFoundError:
                pass
        constants.files_to_delete.clear()
        if not constants.xgp_loaded:
            constants.loaded_level_mtime = os.path.getmtime(level_sav_path)
        self._last_snapshot = self.snapshot()
        constants.dirty = False


# module-level singleton for shared use
save_session = SaveSession()
