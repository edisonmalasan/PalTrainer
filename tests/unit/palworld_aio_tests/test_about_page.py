from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.about_page')
system_info = import_from('palworld_aio.application.system_info')
_APP = None


@pytest.fixture(scope='module')
def app():
    global _APP
    _APP = QApplication.instance() or QApplication([])
    return _APP


def _page():
    return page_mod.AboutPage(system_info.ProductInfo(
        '2.4.0', '1.0.3', project_url='https://example.test/project'))


def test_about_presents_versions_links_updates_and_diagnostics(app):
    page = _page()
    projects = []
    updates = []
    diagnostics = []
    page.projectRequested.connect(projects.append)
    page.updateCheckRequested.connect(lambda: updates.append(True))
    page.diagnosticsRequested.connect(lambda: diagnostics.append(True))

    assert page.app_badge.text() == 'PalTrainer 2.4.0'
    assert page.game_badge.text() == 'Palworld 1.0.3'
    page.project_button.click()
    page.update_button.click()
    page.diagnostics_button.click()
    assert projects == ['https://example.test/project']
    assert updates == [True]
    assert diagnostics == [True]
    assert not page.update_button.isEnabled()


def test_update_state_explains_available_current_and_failure(app):
    page = _page()
    page.set_update_state('available', current='2.4.0', latest='2.5.0')
    assert page.update_banner.property('status') == 'available'
    assert '2.4.0' in page.update_label.text()
    assert '2.5.0' in page.update_label.text()
    page.set_update_state('current', current='2.4.0')
    assert page.update_banner.property('status') == 'current'
    page.set_update_state('error', detail='Network unavailable')
    assert page.update_label.text() == 'Network unavailable'


def test_about_renders_responsively_at_compact_width(app):
    page = _page()
    page.resize(700, 570)
    page.show()
    app.processEvents()
    assert page._detail_columns == 1
    assert not page.grab().isNull()
