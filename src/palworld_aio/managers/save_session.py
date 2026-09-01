"""Compatibility facade for the former save-session manager module."""

from palworld_aio.application.save_session import (
    SaveBackupError,
    SaveMissingPlayersError,
    SaveNoPathError,
    SaveNotLevelError,
    SavePathError,
    SaveSession,
    SaveSessionError,
    SaveSnapshot,
    SaveStaleError,
    SaveWriteError,
    save_session,
)

__all__ = [
    'SaveBackupError',
    'SaveMissingPlayersError',
    'SaveNoPathError',
    'SaveNotLevelError',
    'SavePathError',
    'SaveSession',
    'SaveSessionError',
    'SaveSnapshot',
    'SaveStaleError',
    'SaveWriteError',
    'save_session',
]
