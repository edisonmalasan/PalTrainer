from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.exclusions_page')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    import_from('i18n').load_resources('en_US')


def _records():
    return {
        'players': ['PLAYER-1', 'PLAYER-2'],
        'guilds': ['GUILD-1'],
        'bases': [],
    }


def test_one_browser_switches_segment_data_and_preserves_search(app):
    page = page_mod.ExclusionsPage()
    page.set_loaded(True)
    page.set_exclusions(_records())
    assert page.browser.count_label.text() == '2 results'
    page.browser.search_input.setText('PLAYER-2')
    page.switch_view('guilds')
    assert page.browser.search_input.text() == ''
    assert page.browser.count_label.text() == '1 result'
    page.switch_view('players')
    assert page.browser.search_input.text() == 'PLAYER-2'
    assert page.browser.count_label.text() == '1 of 2 results'


def test_add_and_remove_use_the_active_segment(app):
    page = page_mod.ExclusionsPage()
    page.set_loaded(True)
    page.set_exclusions(_records())
    adds = []
    removes = []
    page.addRequested.connect(adds.append)
    page.removeRequested.connect(lambda kind, value: removes.append((kind, value)))
    page.switch_view('guilds')
    assert not page.remove_button.isEnabled()
    page.add_button.click()
    selected = page.browser.tree.topLevelItem(0)
    page.browser.tree.setCurrentItem(selected)
    page.remove_button.click()
    assert adds == ['guilds']
    assert removes == [('guilds', 'GUILD-1')]


def test_loaded_empty_guidance_and_no_save_state_are_distinct(app):
    page = page_mod.ExclusionsPage()
    page.set_exclusions(_records())
    page.switch_view('bases')
    page.set_loaded(False)
    assert page.entity_browser.collection_state == 'no_save'
    assert 'load a save' in page.entity_browser.no_save_state.title_label.text().lower()
    assert not page.add_button.isEnabled()
    page.set_loaded(True)
    assert page.entity_browser.collection_state == 'ready'
    assert 'No bases exclusions configured' in (
        page.entity_browser.empty_state.message_label.text())
    assert 'Add Exclusion' in page.entity_browser.empty_state.message_label.text()
    assert page.add_button.isEnabled()


def test_selected_identifier_opens_compact_inspector(app):
    page = page_mod.ExclusionsPage()
    page.set_loaded(True)
    page.set_exclusions(_records())
    selected = page.browser.tree.topLevelItem(0)
    page.browser.tree.setCurrentItem(selected)
    page.resize(760, 650)
    page.show()
    app.processEvents()
    assert page.entity_browser._compact
    assert not page.entity_browser.inspector_host.isHidden()
    assert page.inspector._rows[1][1].value() == selected.text(0)
