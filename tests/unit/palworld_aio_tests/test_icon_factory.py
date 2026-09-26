"""Unit tests for the bundled, local-only vector icon factory."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

icons = import_from('palworld_aio.ui.chrome.icons')

EXPECTED_CORE = [
    'tools', 'map', 'base_inventory', 'player_inventory', 'pal_editor',
    'players', 'guilds', 'bases', 'exclusions', 'json_editor', 'breeding',
    'docs', 'save', 'console', 'toolbox', 'warning', 'info', 'menu',
    'minimize', 'maximize', 'restore', 'close', 'search', 'chevron_down',
    'chevron_up', 'chevron_right', 'chevron_left', 'edit', 'player_select',
    'external_link', 'copy', 'check', 'trash', 'download', 'upload',
    'refresh', 'import', 'export', 'steam', 'gamepass', 'cloud',
    'check_circle', 'save_state', 'spinner', 'crosshair', 'container', 'grid',
]

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


def test_svg_assets_exist_for_all_core_names():
    for name in EXPECTED_CORE:
        assert icons.has_vector_icon(name), f'missing svg asset: {name}'


def test_get_pixmap_renders_every_core_icon():
    _app_instance()
    for name in EXPECTED_CORE:
        pix = icons.get_pixmap(name, '#F59E0B', 16)
        assert pix is not None, f'render failed: {name}'
        assert not pix.isNull()
        assert pix.width() == 16


def test_get_qicon_returns_icon():
    _app_instance()
    icon = icons.get_qicon('save', role='accent')
    assert icon is not None
    assert not icon.isNull()


def test_pixmap_cache_hits():
    _app_instance()
    first = icons.get_pixmap('tools', '#ECE7E0', 16)
    second = icons.get_pixmap('tools', '#ECE7E0', 16)
    assert first is second


def test_role_color_resolves_from_palette():
    assert icons.role_color('accent').lower() == '#f59e0b'
    assert icons.role_color('text').startswith('#')


def test_unknown_icon_returns_none():
    _app_instance()
    assert icons.get_pixmap('definitely_not_an_icon') is None
    assert icons.get_qicon('definitely_not_an_icon') is None


def test_public_registry_contains_only_bundled_vectors():
    names = icons.available_vector_icons()
    assert set(EXPECTED_CORE) <= names
    assert not hasattr(icons, 'get_icon')


def test_svg_assets_are_token_tintable_and_local_only():
    for name in icons.available_vector_icons():
        source = icons._svg_source(name)
        assert source is not None
        assert '__COLOR__' in source
        lowered = source.lower()
        assert 'href="http://' not in lowered
        assert 'href="https://' not in lowered
        assert "href='http://" not in lowered
        assert "href='https://" not in lowered
