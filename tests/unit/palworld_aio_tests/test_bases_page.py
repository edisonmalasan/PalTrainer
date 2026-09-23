from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.bases_page')
context_mod = import_from('palworld_aio.ui.workspace_context')
shell_mod = import_from('palworld_aio.ui.chrome.workspace_shell')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    import_from('i18n').load_resources('en_US')


def _bases():
    return (
        page_mod.BaseRow(
            'BASE-AAA-111111', 'Base 1', 'GUILD-1', 'Unnamed Guild',
            25, 'X -1681, Y 1032'),
        page_mod.BaseRow(
            'BASE-BBB-222222', 'Base 2', 'GUILD-1', 'Unnamed Guild',
            25, 'X 425, Y -97'),
        page_mod.BaseRow(
            'BASE-CCC-333333', 'Base 1', 'GUILD-2', 'Builders',
            12, ''),
    )


def _item(page, base_id):
    return next(
        item for item in page.browser._all_items
        if item.data(0, Qt.ItemDataRole.UserRole) == base_id)


def test_bases_are_human_first_with_secondary_identifiers(app):
    page = page_mod.BasesPage()
    page.set_bases(_bases())
    assert page.browser.tree.headerItem().text(0) == 'Base'
    assert page.browser.tree.headerItem().text(1) == 'Guild Name'
    assert page.browser.tree.headerItem().text(5) == 'Base ID'
    assert _item(page, 'BASE-AAA-111111').text(0) == 'Base 1'
    assert _item(page, 'BASE-AAA-111111').text(5) == 'BASE-AAA…'
    assert page.browser.tree.isColumnHidden(6)
    assert page.browser.tree.isColumnHidden(7)
    page.browser.search_input.setText('BASE-CCC-333333')
    assert page.browser.count_label.text() == '1 of 3 results'


def test_selection_populates_details_and_related_workspace_links(app):
    page = page_mod.BasesPage()
    page.set_bases(_bases())
    selected = []
    inventory = []
    maps = []
    guilds = []
    page.baseSelected.connect(selected.append)
    page.openInventoryRequested.connect(inventory.append)
    page.openMapRequested.connect(maps.append)
    page.openGuildRequested.connect(guilds.append)
    assert not page.inventory_button.isEnabled()
    assert not page.map_button.isEnabled()
    assert not page.guild_button.isEnabled()
    page.browser.tree.setCurrentItem(_item(page, 'BASE-AAA-111111'))

    assert selected[-1].base_id == 'BASE-AAA-111111'
    assert page.inspector._title.text() == 'Base 1'
    assert page.inspector._rows[1][1].text() == 'Unnamed Guild'
    assert page.inspector._rows[3][1].text() == 'X -1681, Y 1032'
    assert page.inspector._rows[4][1].value() == 'BASE-AAA-111111'
    page.inventory_button.click()
    page.map_button.click()
    page.guild_button.click()
    assert inventory[0].base_id == 'BASE-AAA-111111'
    assert maps[0].base_id == 'BASE-AAA-111111'
    assert guilds[0].guild_id == 'GUILD-1'


def test_router_history_and_compact_drawer_restore_selection(app):
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'world', 'Fixture World', 'C:/Fixture',
        context_mod.SavePlatform.STEAM))
    shell = shell_mod.WorkspaceShell(context)
    page = page_mod.BasesPage()
    page.set_bases(_bases())
    shell.register_page('bases', page)
    shell.register_page('activity', QWidget())
    shell.navigate('bases')
    page.browser.search_input.setText('builders')
    page.browser.tree.setCurrentItem(_item(page, 'BASE-CCC-333333'))
    shell.navigate('activity')
    page.browser.search_input.clear()
    page.browser.tree.clearSelection()

    shell.go_back()
    assert page.browser.search_input.text() == 'builders'
    assert page.selected_base().base_id == 'BASE-CCC-333333'

    compact = page_mod.BasesPage()
    compact.set_bases(_bases())
    compact.browser.tree.setCurrentItem(_item(compact, 'BASE-CCC-333333'))
    compact.resize(760, 650)
    compact.show()
    app.processEvents()
    assert compact.entity_browser._compact
    assert not compact.entity_browser.inspector_host.isHidden()
