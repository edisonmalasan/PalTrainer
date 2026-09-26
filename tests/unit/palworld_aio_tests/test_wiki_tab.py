"""Reference workspace search, states, routes, and editor deep links."""
from __future__ import annotations

import json
import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

wiki_mod = import_from('palworld_aio.ui.tabs.docs.wiki_tab')
i18n_mod = import_from('i18n')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture(scope='session')
def app():
    return _app_instance()


def test_reference_categories_cover_audit_domains():
    category_ids = {category[0] for category in wiki_mod._CATEGORIES}
    assert {
        'pals', 'items', 'active_skills', 'passive_skills',
        'technologies', 'world_data', 'internal_ids',
    } <= category_ids


def test_dictionary_data_is_normalized_for_browser(monkeypatch, tmp_path):
    game_data = tmp_path / 'game_data'
    game_data.mkdir()
    (game_data / 'fixture.json').write_text(json.dumps({
        'records': {
            'Alpha': {'display_name': 'Alpha Record', 'rank': 2},
            'IconId': '/icons/ui/icon.webp',
        },
    }), encoding='utf-8')
    monkeypatch.setattr(wiki_mod.constants, 'get_base_path', lambda: str(tmp_path))
    monkeypatch.setattr(
        wiki_mod, 'resource_path',
        lambda base, *parts: os.path.join(base, *parts),
    )

    records = wiki_mod._load_json('fixture.json', 'records')

    assert records[0] == {
        'display_name': 'Alpha Record', 'rank': 2,
        'id': 'Alpha', 'name': 'Alpha Record',
    }
    assert records[1]['id'] == 'IconId'
    assert records[1]['icon'] == '/icons/ui/icon.webp'


def test_reference_page_has_count_and_no_result_state(app):
    page = wiki_mod.WikiCategoryPage('items')
    page._all_data = [
        {'asset': 'Item_A', 'name': 'Alpha'},
        {'asset': 'Item_B', 'name': 'Beta'},
    ]
    page._loaded = True
    page._apply_sort_filter()
    assert page._result_count.text() == '2 of 2'

    page._search.setText('missing')
    assert page._result_count.text() == '0 of 2'
    assert page._list_stack.currentWidget() is page._no_result_state

    page._no_result_state.actionTriggered.emit()
    assert page._search.text() == ''
    assert page._list_stack.currentWidget() is page._list


def test_open_reference_selects_identifier_and_category(app, monkeypatch):
    def load_fixture(page):
        page._all_data = ([{'asset': 'Item_A', 'name': 'Alpha'}]
                          if page._cat == 'items' else [])
        page._loaded = True
        page._apply_sort_filter()

    monkeypatch.setattr(wiki_mod.WikiCategoryPage, 'load', load_fixture)
    workspace = wiki_mod.WikiTab()

    assert workspace.open_reference('item', 'item_a')
    assert workspace._cat_stack.currentWidget() is workspace._pages['items']
    selected = workspace._pages['items']._list.currentItem()
    assert selected is not None
    assert selected.text() == 'Alpha'
    assert not workspace.open_reference('unknown-category', 'Item_A')
