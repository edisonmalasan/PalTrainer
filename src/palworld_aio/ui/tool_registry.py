"""Declarative inventory for every utility exposed by Tool Center."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Iterator

from palworld_aio.ui.routes import ContextKind


class ToolCategory(StrEnum):
    SAVE_FORMAT = 'save_format'
    REPAIR_RECOVERY = 'repair_recovery'
    TRANSFER_INJECTION = 'transfer_injection'
    ADDITIONAL = 'additional'


class ToolRisk(StrEnum):
    SAFE = 'safe'
    CAUTION = 'caution'
    HIGH = 'high'


class DataRequirement(StrEnum):
    NONE = 'none'
    IDENTIFIER = 'identifier'
    SAVE_FILE = 'save_file'
    SAVE_FOLDER = 'save_folder'
    PLAYER_SAVE = 'player_save'
    WORLD_SAVE = 'world_save'
    OUTPUT_FILE = 'output_file'


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    tool_id: str
    category: ToolCategory
    title_key: str
    description_key: str
    icon: str
    requires_save: bool
    required_context: frozenset[ContextKind]
    risk: ToolRisk
    source_requirement: DataRequirement
    target_requirement: DataRequirement
    handler_name: str
    handler_index: int
    search_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tool_id or not self.title_key or not self.description_key:
            raise ValueError('tool identity and localization keys are required')
        if not self.handler_name or self.handler_index < 0:
            raise ValueError('a valid launch handler is required')

    def launch(self, target: object) -> None:
        """Invoke this tool through its existing, behavior-preserving handler."""
        callback = getattr(target, self.handler_name)
        callback(self.handler_index)


class ToolRegistry:
    def __init__(self, tools: Iterable[ToolDescriptor]) -> None:
        values = tuple(tools)
        by_id = {tool.tool_id: tool for tool in values}
        if len(by_id) != len(values):
            raise ValueError('tool IDs must be unique')
        self._tools = values
        self._by_id = by_id

    def __iter__(self) -> Iterator[ToolDescriptor]:
        return iter(self._tools)

    def __len__(self) -> int:
        return len(self._tools)

    def resolve(self, tool_id: str) -> ToolDescriptor:
        try:
            return self._by_id[tool_id]
        except KeyError as exc:
            raise KeyError(f'unknown tool: {tool_id}') from exc

    def in_category(self, category: ToolCategory) -> tuple[ToolDescriptor, ...]:
        return tuple(tool for tool in self._tools if tool.category is category)

    def search(self, query: str) -> tuple[ToolDescriptor, ...]:
        terms = tuple(part.casefold() for part in query.split() if part)
        if not terms:
            return self._tools
        return tuple(
            tool for tool in self._tools
            if all(term in self._search_text(tool) for term in terms)
        )

    @staticmethod
    def _search_text(tool: ToolDescriptor) -> str:
        return ' '.join((
            tool.tool_id.replace('_', ' '),
            tool.title_key.replace('.', ' '),
            tool.description_key.replace('.', ' '),
            *tool.search_terms,
        )).casefold()


TOOLS = ToolRegistry((
    ToolDescriptor(
        'convert_saves', ToolCategory.SAVE_FORMAT,
        'tool.convert.saves', 'tool.convert.saves.desc', 'export',
        False, frozenset(), ToolRisk.SAFE,
        DataRequirement.SAVE_FILE, DataRequirement.OUTPUT_FILE,
        '_run_converting_tool', 0,
        ('json', 'sav', 'format', 'serialize', 'deserialize'),
    ),
    ToolDescriptor(
        'convert_gamepass_steam', ToolCategory.SAVE_FORMAT,
        'tool.convert.gamepass.steam', 'tool.convert.gamepass.steam.desc',
        'gamepass', False, frozenset(), ToolRisk.CAUTION,
        DataRequirement.SAVE_FOLDER, DataRequirement.SAVE_FOLDER,
        '_run_converting_tool', 1,
        ('xbox', 'xgp', 'game pass', 'steam', 'platform'),
    ),
    ToolDescriptor(
        'convert_steam_id', ToolCategory.SAVE_FORMAT,
        'tool.convert.steamid', 'tool.convert.steamid.desc', 'copy',
        False, frozenset(), ToolRisk.SAFE,
        DataRequirement.IDENTIFIER, DataRequirement.NONE,
        '_run_converting_tool', 2,
        ('steam id', 'nosteam', 'uid', 'account'),
    ),
    ToolDescriptor(
        'restore_map', ToolCategory.REPAIR_RECOVERY,
        'tool.restore_map', 'tool.restore_map.desc', 'map',
        False, frozenset(), ToolRisk.CAUTION,
        DataRequirement.SAVE_FILE, DataRequirement.SAVE_FILE,
        '_run_converting_tool', 3,
        ('map progress', 'reveal', 'recovery'),
    ),
    ToolDescriptor(
        'fix_host_save', ToolCategory.REPAIR_RECOVERY,
        'tool.fix_host_save', 'tool.fix_host_save.desc', 'check_circle',
        False, frozenset(), ToolRisk.HIGH,
        DataRequirement.PLAYER_SAVE, DataRequirement.PLAYER_SAVE,
        '_run_management_tool', 2,
        ('host', 'repair', 'swap uid', 'co-op'),
    ),
    ToolDescriptor(
        'character_transfer', ToolCategory.TRANSFER_INJECTION,
        'tool.character_transfer', 'tool.character_transfer.desc',
        'player_select', False, frozenset(), ToolRisk.HIGH,
        DataRequirement.SAVE_FOLDER, DataRequirement.SAVE_FOLDER,
        '_run_management_tool', 1,
        ('character', 'player', 'server', 'move'),
    ),
    ToolDescriptor(
        'slot_injector', ToolCategory.TRANSFER_INJECTION,
        'tool.slot_injector', 'tool.slot_injector.desc', 'container',
        False, frozenset(), ToolRisk.HIGH,
        DataRequirement.PLAYER_SAVE, DataRequirement.WORLD_SAVE,
        '_run_management_tool', 0,
        ('slot', 'inject', 'player', 'world'),
    ),
))


__all__ = [
    'DataRequirement', 'TOOLS', 'ToolCategory', 'ToolDescriptor',
    'ToolRegistry', 'ToolRisk',
]
