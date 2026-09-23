from __future__ import annotations

from tests.dynamic_importer import import_from


preferences_mod = import_from('palworld_aio.ui.user_preferences')


def test_supported_preferences_round_trip_like_an_application_restart():
    raw = {
        'language': 'ja_JP',
        'boot_preference': 'palworld_aio',
        'loading_screen_mode': 'header',
        'reduced_motion': True,
        'automatic_backup_on_load': False,
        'warn_unsaved_exit': False,
        'pal_creation_name_mode': 'copy',
        'bulk_sync_apply_nickname': True,
        'console_detached': True,
        'show_icons': False,
        'tray_expanded': True,
        'console_window_geometry': 'encoded-geometry',
    }
    first_run = preferences_mod.UserPreferences.from_mapping(raw)
    restarted = preferences_mod.UserPreferences.from_mapping(
        first_run.to_mapping())
    assert restarted == first_run


def test_corrupt_supported_values_fall_back_without_dropping_extensions():
    normalized = preferences_mod.normalize_user_settings({
        'language': 'xx_XX',
        'boot_preference': 42,
        'loading_screen_mode': 'sparkles',
        'reduced_motion': 'yes',
        'automatic_backup_on_load': 1,
        'warn_unsaved_exit': None,
        'pal_creation_name_mode': 'random',
        'console_detached': [],
        'console_window_geometry': {'not': 'geometry'},
        'workspace_ui': 'broken',
        'extension_setting': {'kept': True},
    })
    defaults = preferences_mod.UserPreferences().to_mapping()
    for key, value in defaults.items():
        assert normalized[key] == value
    assert normalized['extension_setting'] == {'kept': True}
    assert 'workspace_ui' not in normalized


def test_non_mapping_config_recovers_all_defaults():
    assert preferences_mod.normalize_user_settings(['broken']) == (
        preferences_mod.UserPreferences().to_mapping())
