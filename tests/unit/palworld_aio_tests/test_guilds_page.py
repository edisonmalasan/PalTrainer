from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.guilds_page')
context_mod = import_from('palworld_aio.ui.workspace_context')
shell_mod = import_from('palworld_aio.ui.chrome.workspace_shell')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope='module', autouse=True)
def _i18n_en_us():
    import_from('i18n').load_resources('en_US')


def _guilds():
    return (
        page_mod.GuildRow('GUILD-AAA-111111', 'Rayne Syndicate', 25, 2, 2),
        page_mod.GuildRow('GUILD-BBB-222222', 'Free Pal Alliance', 12, 1, 1),
    )


def _members():
    return (
        page_mod.GuildMemberRow(
            'PLAYER-AAA-111111', 'Ada', 'Guild Master', 55, 40,
            '2h ago', True, 1, 7200.0),
        page_mod.GuildMemberRow(
            'PLAYER-BBB-222222', 'Ben', 'Member', 32, 18,
            '1d ago', False, 3, 86400.0),
    )


def _guild_item(page, guild_id):
    return next(
        item for item in page.browser._all_items
        if item.data(0, Qt.ItemDataRole.UserRole) == guild_id)


def _member_item(page, uid):
    return next(
        item for item in page.members_browser._all_items
        if item.data(0, Qt.ItemDataRole.UserRole) == uid)


def test_guilds_are_name_first_with_row_prerequisite_copy(app):
    page = page_mod.GuildsPage()
    page.set_guilds(_guilds())
    assert page.browser.tree.headerItem().text(0) == 'Guild Name'
    assert page.browser.tree.headerItem().text(4) == 'Guild ID'
    assert _guild_item(page, 'GUILD-AAA-111111').text(0) == 'Rayne Syndicate'
    assert _guild_item(page, 'GUILD-AAA-111111').text(4) == 'GUILD-AA…'
    assert page.browser.tree.isColumnHidden(5)
    assert 'Click a guild row' in page.inspector._empty.text()
    assert page.members_browser.isHidden()
    page.browser.search_input.setText('GUILD-BBB-222222')
    assert page.browser.count_label.text() == '1 of 2 results'


def test_guild_selection_shows_members_details_and_related_links(app):
    page = page_mod.GuildsPage()
    page.set_guilds(_guilds())
    guilds = []
    members = []
    players_links = []
    bases_links = []
    page.guildSelected.connect(guilds.append)
    page.memberSelected.connect(members.append)
    page.openPlayersRequested.connect(players_links.append)
    page.openBasesRequested.connect(bases_links.append)
    assert not page.players_button.isEnabled()
    assert not page.bases_button.isEnabled()

    page.browser.tree.setCurrentItem(_guild_item(page, 'GUILD-AAA-111111'))
    assert guilds[-1].guild_id == 'GUILD-AAA-111111'
    assert page.inspector._title.text() == 'Rayne Syndicate'
    assert page.inspector._rows[0][1].text() == '25'
    assert page.inspector._rows[2][1].text() == '2'
    assert page.inspector._rows[3][1].value() == 'GUILD-AAA-111111'

    page.set_members('GUILD-AAA-111111', _members())
    page.members_browser.tree.setCurrentItem(
        _member_item(page, 'PLAYER-AAA-111111'))
    assert members[-1].uid == 'PLAYER-AAA-111111'
    assert _member_item(page, 'PLAYER-AAA-111111').text(0) == 'Leader · Ada'
    assert _member_item(page, 'PLAYER-AAA-111111').text(1) == 'Guild Master'
    assert page.members_browser.tree.isColumnHidden(4)
    assert page.members_browser.tree.isColumnHidden(5)

    page.players_button.click()
    page.bases_button.click()
    assert players_links[0].guild_id == 'GUILD-AAA-111111'
    assert bases_links[0].guild_id == 'GUILD-AAA-111111'


def test_router_and_compact_drawer_restore_guild_state(app):
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'world', 'Fixture World', 'C:/Fixture',
        context_mod.SavePlatform.STEAM))
    shell = shell_mod.WorkspaceShell(context)
    page = page_mod.GuildsPage()
    page.set_guilds(_guilds())
    shell.register_page('guilds', page)
    shell.register_page('activity', QWidget())
    shell.navigate('guilds')
    page.browser.search_input.setText('Rayne')
    page.browser.tree.setCurrentItem(_guild_item(page, 'GUILD-AAA-111111'))
    shell.navigate('activity')
    page.browser.search_input.clear()
    page.browser.tree.clearSelection()

    shell.go_back()
    assert page.browser.search_input.text() == 'Rayne'
    assert page.selected_guild().guild_id == 'GUILD-AAA-111111'

    compact = page_mod.GuildsPage()
    compact.set_guilds(_guilds())
    compact.browser.tree.setCurrentItem(
        _guild_item(compact, 'GUILD-AAA-111111'))
    compact.resize(760, 650)
    compact.show()
    app.processEvents()
    assert compact.entity_browser._compact
    assert compact.entity_browser.inspector_host.maximumHeight() == 390
    assert not compact.entity_browser.inspector_host.isHidden()
