from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.players_page')
context_mod = import_from('palworld_aio.ui.workspace_context')
shell_mod = import_from('palworld_aio.ui.chrome.workspace_shell')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    import_from('i18n').load_resources('en_US')


def _players():
    return (
        page_mod.PlayerRow(
            'AAA-111', 'Ada', 'Just now', 70, 220,
            'Unnamed Guild', 'GUILD-1', 25, True, 0),
        page_mod.PlayerRow(
            'BBB-222', 'Ben', '2 days ago', 32, 18,
            'Builders', 'GUILD-2', 12, False, 172800),
        page_mod.PlayerRow(
            'CCC-333', 'Cara', '5 days ago', 8, 4,
            '', '', 0, False, 432000),
    )


def _item(page, uid):
    return next(
        item for item in page.browser._all_items
        if item.data(0, Qt.ItemDataRole.UserRole) == uid)


def test_players_use_name_first_columns_and_hide_full_identifiers(app):
    page = page_mod.PlayersPage()
    page.set_players(_players())
    assert page.browser.tree.headerItem().text(0) == 'Player Name'
    assert page.browser.tree.headerItem().text(1) == 'Level'
    assert page.browser.tree.headerItem().text(5) == 'Role'
    assert all(page.browser.tree.isColumnHidden(column) for column in (6, 7, 8))
    assert page.browser.count_label.text() == '3 results'
    assert _item(page, 'AAA-111').text(0) == 'Ada'
    page.browser.search_input.setText('AAA-111')
    assert page.browser.count_label.text() == '1 of 3 results'


def test_selection_populates_structured_inspector_and_direct_links(app):
    page = page_mod.PlayersPage()
    page.set_players(_players())
    selected = []
    inventory = []
    pals = []
    guilds = []
    page.playerSelected.connect(selected.append)
    page.openInventoryRequested.connect(
        lambda uid, name: inventory.append((uid, name)))
    page.openPalEditorRequested.connect(
        lambda uid, name: pals.append((uid, name)))
    page.openGuildRequested.connect(guilds.append)
    assert not page.inventory_button.isEnabled()
    assert not page.pal_editor_button.isEnabled()
    assert not page.guild_button.isEnabled()
    page.browser.tree.setCurrentItem(_item(page, 'AAA-111'))

    assert selected[-1].uid == 'AAA-111'
    assert page.inspector._title.text() == 'Ada'
    assert page.inspector._rows[0][1].text() == '70'
    assert page.inspector._rows[4][1].text() == 'Guild Master'
    assert page.inspector._rows[5][1].value() == 'AAA-111'
    page.inventory_button.click()
    page.pal_editor_button.click()
    page.guild_button.click()
    assert inventory == [('AAA-111', 'Ada')]
    assert pals == [('AAA-111', 'Ada')]
    assert guilds == ['GUILD-1']


def test_contextual_bulk_footer_tracks_extended_selection(app):
    page = page_mod.PlayersPage()
    page.set_players(_players())
    assert not page.bulk_item_button.isEnabled()
    observed = []
    page.bulkItemsRequested.connect(observed.append)
    first = _item(page, 'AAA-111')
    second = _item(page, 'BBB-222')
    first.setSelected(True)
    second.setSelected(True)
    assert page.bulk_footer.status_label.text() == '2 players selected'
    assert page.bulk_item_button.isEnabled()
    page.bulk_item_button.click()
    assert set(observed[0]) == {'AAA-111', 'BBB-222'}


def test_filter_sort_selection_and_compact_inspector_restore(app):
    page = page_mod.PlayersPage()
    page.set_players(_players())
    page.browser.search_input.setText('ben')
    page.browser.tree.sortItems(1, Qt.SortOrder.DescendingOrder)
    ben = _item(page, 'BBB-222')
    page.browser.tree.setCurrentItem(ben)
    state = page.capture_view_state()

    restored = page_mod.PlayersPage()
    restored.set_players(_players())
    restored.restore_view_state(state)
    assert restored.browser.search_input.text() == 'ben'
    assert restored.selected_uids() == ('BBB-222',)
    restored.resize(760, 650)
    restored.show()
    app.processEvents()
    assert restored.entity_browser._compact
    assert not restored.entity_browser.inspector_host.isHidden()


def test_router_history_restores_player_filter_sort_and_selection(app):
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'world', 'Fixture World', 'C:/Fixture',
        context_mod.SavePlatform.STEAM))
    shell = shell_mod.WorkspaceShell(context)
    page = page_mod.PlayersPage()
    page.set_players(_players())
    shell.register_page('players', page)
    shell.register_page('activity', page_mod.QWidget())
    shell.navigate('players')
    page.browser.search_input.setText('ben')
    page.browser.tree.sortItems(1, Qt.SortOrder.DescendingOrder)
    page.browser.tree.setCurrentItem(_item(page, 'BBB-222'))
    shell.navigate('activity')
    page.browser.search_input.clear()
    page.browser.tree.clearSelection()

    shell.go_back()

    assert shell.router.current_route_id == 'players'
    assert page.browser.search_input.text() == 'ben'
    assert page.selected_uids() == ('BBB-222',)
