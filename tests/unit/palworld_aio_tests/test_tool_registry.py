from __future__ import annotations

import pytest

from tests.dynamic_importer import import_from


registry_mod = import_from('palworld_aio.ui.tool_registry')
tools_tab_mod = import_from('palworld_aio.ui.tabs.tools_tab')


def test_registry_is_complete_against_existing_tool_launch_handlers():
    legacy = {
        (title_key, handler_name, handler_index)
        for _zone, rows in tools_tab_mod.ToolsTab.MISSION_ZONES
        for title_key, handler_name, handler_index in rows
    }
    registered = {
        (tool.title_key, tool.handler_name, tool.handler_index)
        for tool in registry_mod.TOOLS
    }
    assert registered == legacy
    assert len(registry_mod.TOOLS) == 7


def test_every_tool_declares_complete_metadata():
    for tool in registry_mod.TOOLS:
        assert tool.description_key.endswith('.desc')
        assert tool.icon
        assert isinstance(tool.requires_save, bool)
        assert isinstance(tool.required_context, frozenset)
        assert isinstance(tool.risk, registry_mod.ToolRisk)
        assert isinstance(tool.source_requirement, registry_mod.DataRequirement)
        assert isinstance(tool.target_requirement, registry_mod.DataRequirement)
        assert tool.search_terms


def test_registry_groups_resolves_and_searches_synonyms():
    repair = registry_mod.TOOLS.in_category(
        registry_mod.ToolCategory.REPAIR_RECOVERY)
    assert {tool.tool_id for tool in repair} == {'restore_map', 'fix_host_save'}
    assert registry_mod.TOOLS.resolve('slot_injector').handler_index == 0
    assert [tool.tool_id for tool in registry_mod.TOOLS.search('xbox platform')] == [
        'convert_gamepass_steam']
    assert {tool.tool_id for tool in registry_mod.TOOLS.search('player')} == {
        'character_transfer', 'slot_injector',
    }
    with pytest.raises(KeyError, match='unknown tool'):
        registry_mod.TOOLS.resolve('missing')


def test_launch_delegates_to_preserved_handler_and_index():
    calls = []

    class Target:
        def _run_converting_tool(self, index):
            calls.append(('convert', index))

        def _run_management_tool(self, index):
            calls.append(('manage', index))

    registry_mod.TOOLS.resolve('restore_map').launch(Target())
    registry_mod.TOOLS.resolve('character_transfer').launch(Target())
    assert calls == [('convert', 3), ('manage', 1)]
