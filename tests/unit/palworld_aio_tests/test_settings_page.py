from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication, QFrame

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.settings_page')
_APP = None


@pytest.fixture(scope='module')
def app():
    global _APP
    _APP = QApplication.instance() or QApplication([])
    return _APP


def test_settings_page_has_all_sections_and_restores_preferences(app):
    page = page_mod.SettingsPage({
        'language': 'fr_FR',
        'boot_preference': 'palworld_aio',
        'loading_screen_mode': 'header',
        'reduced_motion': True,
        'automatic_backup_on_load': False,
        'warn_unsaved_exit': False,
        'pal_creation_name_mode': 'none',
        'bulk_sync_apply_nickname': True,
        'console_detached': True,
    })
    roles = {
        section.property('settingsRole')
        for section in page.findChildren(QFrame, 'settingsSection')
    }
    assert roles == {'general', 'appearance', 'saveSafety', 'advanced'}
    restored = page.preferences()
    assert restored.language == 'fr_FR'
    assert restored.boot_preference == 'palworld_aio'
    assert restored.loading_screen_mode == 'header'
    assert restored.reduced_motion
    assert not restored.automatic_backup_on_load
    assert not restored.warn_unsaved_exit
    assert restored.pal_creation_name_mode == 'none'
    assert restored.bulk_sync_apply_nickname
    assert restored.console_detached


def test_corrupt_values_render_defaults_and_edits_emit_valid_mapping(app):
    page = page_mod.SettingsPage({
        'language': 'invalid',
        'loading_screen_mode': [],
        'automatic_backup_on_load': 'no',
    })
    assert page.language_combo.currentData() == 'en_US'
    assert page.loading_combo.currentData() == 'overlay'
    assert page.backup_check.isChecked()
    observed = []
    page.preferencesChanged.connect(observed.append)
    page.reduced_motion_check.click()
    assert observed[-1]['reduced_motion'] is True
    assert observed[-1]['language'] == 'en_US'


def test_settings_page_renders_at_minimum_workspace_width(app):
    page = page_mod.SettingsPage()
    page.resize(700, 570)
    page.show()
    app.processEvents()
    assert not page.grab().isNull()
