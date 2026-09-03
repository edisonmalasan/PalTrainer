from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

components = import_from('palworld_aio.ui.chrome.components')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture
def app():
    return _app_instance()


def test_button_kinds(app):
    for kind in ('default', 'primary', 'danger', 'ghost', 'tool'):
        btn = components.make_button('Go', kind)
        assert btn.property('class') == (kind if kind != 'default' else None)
    assert components.make_button('Save').property('class') is None


def test_badge_levels(app):
    badge = components.make_badge('3', 'danger')
    assert badge.property('badge') == 'danger'
    components.set_badge_level(badge, 'bogus')
    assert badge.property('badge') == 'neutral'


def test_status_dot_levels(app):
    dot = components.make_status_dot('success')
    assert dot.property('level') == 'success'
    components.set_dot_level(dot, 'info')
    assert dot.property('level') == 'info'


def test_search_field_emits(app):
    seen = []
    _, line = components.make_search_field('Find', on_change=seen.append)
    line.setText('abc')
    assert seen == ['abc']


def test_error_banner_toggle(app):
    banner = components.ErrorBanner()
    assert banner.isHidden()
    banner.show_error('bad thing')
    assert not banner.isHidden()
    banner.clear()
    assert banner.isHidden()


def test_base_dialog_scaffold(app):
    dialog = components.BaseDialog('Title', min_size=(400, 200))
    assert dialog.title_label.text() == 'Title'
    dialog.add_confirm_button('Apply')
    assert dialog.cancel_btn.text() == 'Cancel'
    dialog.cancel_btn.click()
    assert dialog.result() == 0  # Rejected


def test_data_table_empty_state(app):
    table = components.DataTable(['Name', 'Count'])
    table.set_empty_state('Nothing here')
    assert not table.table.isVisible()
    table.set_empty_state('')
    table.set_empty_state('Still nothing')
