from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.tool_center_page')
context_mod = import_from('palworld_aio.ui.workspace_context')
registry_mod = import_from('palworld_aio.ui.tool_registry')
routes_mod = import_from('palworld_aio.ui.routes')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_tool_center_renders_every_registered_tool_and_launches(app):
    page = page_mod.ToolCenterPage(context_mod.WorkspaceContext())
    assert set(page.cards) == {tool.tool_id for tool in registry_mod.TOOLS}
    observed = []
    page.launchRequested.connect(observed.append)
    page.cards['character_transfer'].action_button.click()
    assert observed == ['character_transfer']
    assert page.cards['character_transfer'].requirement_label.text() == 'Ready'


def test_search_and_category_filters_are_composable(app):
    page = page_mod.ToolCenterPage(context_mod.WorkspaceContext())
    page.search_input.setText('host')
    assert page.visible_tool_ids() == ('fix_host_save',)
    page.search_input.clear()
    page.set_category(registry_mod.ToolCategory.SAVE_FORMAT)
    assert page.visible_tool_ids() == (
        'convert_saves', 'convert_gamepass_steam', 'convert_steam_id')
    page.search_input.setText('steam id')
    assert page.visible_tool_ids() == ('convert_steam_id',)
    page.category_buttons[registry_mod.ToolCategory.SAVE_FORMAT].click()
    assert page.category_buttons[registry_mod.ToolCategory.SAVE_FORMAT].isChecked()


def test_unmet_prerequisite_explains_and_routes_to_required_action(app):
    gated = registry_mod.ToolDescriptor(
        'gated', registry_mod.ToolCategory.ADDITIONAL,
        'tool.gated', 'tool.gated.desc', 'toolbox', True,
        frozenset({routes_mod.ContextKind.PLAYER}),
        registry_mod.ToolRisk.CAUTION,
        registry_mod.DataRequirement.NONE,
        registry_mod.DataRequirement.NONE,
        '_run_management_tool', 0, ('gated',),
    )
    context = context_mod.WorkspaceContext()
    page = page_mod.ToolCenterPage(
        context, registry_mod.ToolRegistry((gated,)))
    observed = []
    page.prerequisiteRequested.connect(observed.append)
    card = page.cards['gated']
    assert 'Save' in card.requirement_label.text()
    card.action_button.click()
    assert observed == ['save']

    context.finish_load(context_mod.SaveIdentity(
        'world', 'Island', 'C:/Island', context_mod.SavePlatform.STEAM))
    assert 'Player' in card.requirement_label.text()
    card.action_button.click()
    assert observed == ['save', 'player']

    context.set_player(context_mod.ContextSelection('p1', 'Ada'))
    launched = []
    page.launchRequested.connect(launched.append)
    card.action_button.click()
    assert launched == ['gated']


def test_tool_cards_reflow_to_one_column_at_compact_width(app):
    page = page_mod.ToolCenterPage(context_mod.WorkspaceContext())
    page.resize(700, 650)
    page.show()
    app.processEvents()
    assert page._columns == 1
    page.resize(900, 650)
    app.processEvents()
    assert page._columns == 2
