from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


entity_mod = import_from('palworld_aio.ui.chrome.entity_browser')
search_mod = import_from('palworld_aio.widgets.search_panel')
components = import_from('palworld_aio.ui.chrome.components')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    i18n_mod = import_from('i18n')
    i18n_mod.load_resources('en_US')


def _panel():
    panel = search_mod.SearchPanel('Players', ['Name', 'UID'])
    panel.set_selection_key(lambda item: item.data(0, Qt.ItemDataRole.UserRole))
    panel.add_item(['Ada', 'AAA…'], data='ada', tooltips={1: 'AAA-111'})
    panel.add_item(['Ben', 'BBB…'], data='ben', tooltips={1: 'BBB-222'})
    panel.add_item(['Cara', 'CCC…'], data='cara', tooltips={1: 'CCC-333'})
    return panel


def test_search_and_named_filters_update_visible_total_count(app):
    panel = _panel()
    panel.set_filter('a_names', lambda item: 'a' in item.text(0).lower())
    assert panel.count_label.text() == '2 of 3 results'
    panel.search_input.setText('CCC-333')
    assert panel.count_label.text() == '1 of 3 results'
    panel.set_filter('a_names', None)
    assert panel.count_label.text() == '1 of 3 results'


def test_filter_widget_has_shared_toolbar_slot(app):
    panel = _panel()
    button = components.make_filter_button('Active')
    panel.add_filter_widget(button)
    assert panel.filter_slot.indexOf(button) >= 0


def test_capture_restore_preserves_search_sort_selection_and_scroll(app):
    panel = _panel()
    panel.search_input.setText('b')
    panel.tree.sortItems(0, Qt.SortOrder.DescendingOrder)
    ben = next(item for item in panel._all_items if item.data(0, Qt.ItemDataRole.UserRole) == 'ben')
    panel.tree.setCurrentItem(ben)
    state = panel.capture_view_state()

    restored = _panel()
    restored.restore_view_state(state)
    assert restored.search_input.text() == 'b'
    assert restored.tree.sortColumn() == 0
    assert restored.tree.header().sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
    assert [item.data(0, Qt.ItemDataRole.UserRole) for item in restored.tree.selectedItems()] == ['ben']


def test_full_technical_value_is_searchable_and_copyable(app):
    from PyQt6.QtGui import QKeyEvent

    panel = _panel()
    panel.set_copyable_columns({1})
    panel.search_input.setText('AAA-111')
    assert panel.count_label.text() == '1 of 3 results'
    ada = next(item for item in panel._all_items if not item.isHidden())
    panel.tree.setCurrentItem(ada)
    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_C,
        Qt.KeyboardModifier.ControlModifier,
    )
    panel.tree.keyPressEvent(event)
    assert ada.data(1, search_mod.GUID_ROLE) == 'AAA-111'
    assert QApplication.clipboard().text() == 'AAA-111'


def test_entity_browser_selection_populates_inspector(app):
    frame = entity_mod.EntityBrowserFrame('Players', ['Name', 'UID'])
    frame.add_inspector_row('UID', monospace=True)
    frame.set_detail_provider(lambda values: (values[0], {0: values[1]}))
    frame.browser.add_item(['Ada', 'AAA-111'])
    frame.browser.tree.setCurrentItem(frame.browser.tree.topLevelItem(0))
    assert frame.inspector._title.text() == 'Ada'
    assert frame.inspector._rows[0][1].value() == 'AAA-111'


def test_compact_inspector_behaves_as_reopenable_drawer(app):
    frame = entity_mod.EntityBrowserFrame('Players', ['Name'])
    frame.set_detail_provider(lambda values: (values[0], {}))
    frame.set_compact(True)
    assert frame.inspector_host.property('layoutMode') == 'drawer'
    assert frame.inspector_host.isHidden()
    frame.browser.add_item(['Ada'])
    frame.browser.tree.setCurrentItem(frame.browser.tree.topLevelItem(0))
    assert not frame.inspector_host.isHidden()
    frame.close_inspector()
    assert frame.inspector_host.isHidden()


def test_collection_lifecycle_states_distinguish_empty_search_loading_and_error(app):
    frame = entity_mod.EntityBrowserFrame('Players', ['Name'])
    frame.configure_collection_states(
        empty_title='No players found',
        empty_message='This save has no players.',
        no_result_title='No matching players',
        no_result_message='Clear the active search.',
        loading_message='Loading players…',
    )
    frame.resize(760, 520)
    frame.show()
    app.processEvents()

    actions = []
    frame.stateActionRequested.connect(actions.append)
    assert frame.collection_state == 'no_save'
    assert not frame.no_save_state.isHidden()
    frame.no_save_state.action_button.click()
    assert actions == ['load_save']
    frame.set_collection_state('loading')
    assert not frame.loading_state.isHidden()
    frame.set_collection_state('error', 'Safe user-facing failure.')
    assert frame.error_state.message_label.text() == 'Safe user-facing failure.'
    frame.error_state.action_button.click()
    assert actions[-1] == 'retry'

    frame.set_collection_state('ready')
    assert not frame.empty_state.isHidden()
    frame.browser.add_item(['Ada'])
    frame.browser.search_input.setText('missing')
    assert not frame.no_result_state.isHidden()
    frame.no_result_state.action_button.click()
    assert frame.browser.search_input.text() == ''
    assert frame.browser.count_label.text() == '1 result'
