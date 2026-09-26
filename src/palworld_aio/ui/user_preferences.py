"""Validated, version-independent application preferences.

Workspace navigation state has its own versioned contract.  This module owns
the small set of user-facing application preferences and deliberately keeps
unknown keys so older utilities can continue sharing ``user.cfg``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


LANGUAGES: tuple[str, ...] = (
    'en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP',
    'ko_KR', 'pt_BR', 'pt_PT',
)
BOOT_PREFERENCES: tuple[str, ...] = ('menu', 'palworld_aio')
LOADING_SCREEN_MODES: tuple[str, ...] = ('overlay', 'header')
PAL_NAME_MODES: tuple[str, ...] = ('new', 'copy', 'none')


@dataclass(frozen=True, slots=True)
class UserPreferences:
    language: str = 'en_US'
    boot_preference: str = 'menu'
    loading_screen_mode: str = 'overlay'
    reduced_motion: bool = False
    automatic_backup_on_load: bool = True
    warn_unsaved_exit: bool = True
    pal_creation_name_mode: str = 'new'
    bulk_sync_apply_nickname: bool = False
    console_detached: bool = False
    show_icons: bool = True
    tray_expanded: bool = False
    console_window_geometry: str | None = None

    @classmethod
    def from_mapping(cls, raw: object) -> 'UserPreferences':
        source = raw if isinstance(raw, Mapping) else {}
        defaults = cls()

        def choice(key: str, allowed: tuple[str, ...]) -> str:
            value = source.get(key)
            return value if isinstance(value, str) and value in allowed else getattr(defaults, key)

        def flag(key: str) -> bool:
            value = source.get(key)
            return value if isinstance(value, bool) else getattr(defaults, key)

        geometry = source.get('console_window_geometry')
        if not isinstance(geometry, str) or not geometry:
            geometry = None
        return cls(
            language=choice('language', LANGUAGES),
            boot_preference=choice('boot_preference', BOOT_PREFERENCES),
            loading_screen_mode=choice(
                'loading_screen_mode', LOADING_SCREEN_MODES),
            reduced_motion=flag('reduced_motion'),
            automatic_backup_on_load=flag('automatic_backup_on_load'),
            warn_unsaved_exit=flag('warn_unsaved_exit'),
            pal_creation_name_mode=choice(
                'pal_creation_name_mode', PAL_NAME_MODES),
            bulk_sync_apply_nickname=flag('bulk_sync_apply_nickname'),
            console_detached=flag('console_detached'),
            show_icons=flag('show_icons'),
            tray_expanded=flag('tray_expanded'),
            console_window_geometry=geometry,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            'language': self.language,
            'boot_preference': self.boot_preference,
            'loading_screen_mode': self.loading_screen_mode,
            'reduced_motion': self.reduced_motion,
            'automatic_backup_on_load': self.automatic_backup_on_load,
            'warn_unsaved_exit': self.warn_unsaved_exit,
            'pal_creation_name_mode': self.pal_creation_name_mode,
            'bulk_sync_apply_nickname': self.bulk_sync_apply_nickname,
            'console_detached': self.console_detached,
            'show_icons': self.show_icons,
            'tray_expanded': self.tray_expanded,
            'console_window_geometry': self.console_window_geometry,
        }


def normalize_user_settings(raw: object) -> dict[str, object]:
    """Return a safe config mapping while preserving unrelated extension data."""
    normalized = dict(raw) if isinstance(raw, Mapping) else {}
    normalized.update(UserPreferences.from_mapping(raw).to_mapping())
    workspace = normalized.get('workspace_ui')
    if workspace is not None and not isinstance(workspace, Mapping):
        normalized.pop('workspace_ui', None)
    return normalized


__all__ = [
    'BOOT_PREFERENCES', 'LANGUAGES', 'LOADING_SCREEN_MODES', 'PAL_NAME_MODES',
    'UserPreferences', 'normalize_user_settings',
]
