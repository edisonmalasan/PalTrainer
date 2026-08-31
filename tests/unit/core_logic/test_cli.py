from __future__ import annotations

import tomllib
from pathlib import Path

from tests.dynamic_importer import import_from

_cli = import_from('cli')
parse_app_options = _cli.parse_app_options
parse_boot_options = _cli.parse_boot_options
BootOptions = _cli.BootOptions
AppOptions = _cli.AppOptions
env_flag = _cli.env_flag

_common = import_from('common')
APP_VERSION = _common.APP_VERSION


def _project_root() -> Path:
    from tests.test_registry import PROJECT_ROOT
    return PROJECT_ROOT


def test_parse_app_options_save_path_only():
    opts = parse_app_options(['C:/world/Level.sav'])
    assert opts.save_path == 'C:/world/Level.sav'
    assert opts.logs is True
    assert opts.fix is True


def test_parse_app_options_flags():
    opts = parse_app_options(['C:/world/Level.sav', '-logs'])
    assert opts.save_path == 'C:/world/Level.sav'
    assert opts.logs is True
    assert opts.fix is False


def test_parse_app_options_fix_implies_logs():
    opts = parse_app_options(['C:/world/Level.sav', '--fix'])
    assert opts.fix is True
    assert opts.logs is True


def test_parse_app_options_no_args():
    opts = parse_app_options([])
    assert opts.save_path is None
    assert opts.logs is False
    assert opts.fix is False


def test_parse_app_options_test_loading_popup():
    opts = parse_app_options(['--test-loading-popup'])
    assert opts.test_loading_popup is True


def test_parse_app_options_preserves_legacy_path_without_extension():
    opts = parse_app_options(['C:/some-legacy-save-path'])
    assert opts.save_path == 'C:/some-legacy-save-path'
    assert opts.logs is True
    assert opts.fix is True


def test_parse_app_options_main_style_argv_is_args_only():
    full_argv = ['main.py', 'C:/world/Level.sav', '-logs']
    opts = parse_app_options(full_argv[1:])
    assert opts.save_path == 'C:/world/Level.sav'
    assert opts.logs is True
    assert opts.fix is False


def test_parse_boot_options_flags():
    opts = parse_boot_options(['--debug', '--no-gui'])
    assert opts.debug is True
    assert opts.no_gui is True
    assert opts.bootup_delay is None


def test_parse_boot_options_delay():
    opts = parse_boot_options(['--bootup-delay', '1500'])
    assert opts.bootup_delay == 1500


def test_parse_boot_options_defaults():
    opts = parse_boot_options([])
    assert opts.debug is False
    assert opts.no_gui is False
    assert opts.bootup_delay is None


def test_app_version_matches_pyproject():
    root = _project_root()
    with (root / 'pyproject.toml').open('rb') as f:
        data = tomllib.load(f)
    assert data['project']['version'] == APP_VERSION
