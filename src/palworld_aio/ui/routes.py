"""Metadata-driven route definitions for the PalTrainer workspace.

The registry deliberately contains presentation metadata only.  Pages and save
objects are resolved by the shell and managers so route state remains stable and
serializable across lazy widget creation and save reloads.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping


class RouteGroup(StrEnum):
    WORKSPACE = 'workspace'
    WORLD = 'world'
    EDITORS = 'editors'
    TOOLS = 'tools'
    REFERENCE = 'reference'
    SYSTEM = 'system'


class ContextKind(StrEnum):
    SAVE = 'save'
    PLAYER = 'player'
    GUILD = 'guild'
    BASE = 'base'
    CONTAINER = 'container'
    BACKUP = 'backup'


class RouteRisk(StrEnum):
    SAFE = 'safe'
    CAUTION = 'caution'
    HIGH = 'high'


@dataclass(frozen=True, slots=True)
class RouteDescriptor:
    """Serializable navigation metadata for one stable destination."""

    route_id: str
    group: RouteGroup
    label_key: str
    label: str
    icon: str
    help_key: str
    help_text: str
    shortcut: str | None = None
    requires_save: bool = False
    required_context: frozenset[ContextKind] = frozenset()
    accepted_context: frozenset[ContextKind] = frozenset()
    risk: RouteRisk = RouteRisk.SAFE
    legacy_index: int | None = None

    def __post_init__(self) -> None:
        if not self.route_id or self.route_id != self.route_id.strip():
            raise ValueError('route_id must be a non-empty, trimmed string')
        if self.required_context - self.accepted_context:
            raise ValueError(
                f'{self.route_id}: required context must also be accepted context')
        if self.required_context and not self.requires_save:
            raise ValueError(
                f'{self.route_id}: entity context requires a loaded save')


class RouteRegistry:
    """Validated, ordered lookup for route descriptors."""

    def __init__(self, routes: Iterable[RouteDescriptor]) -> None:
        ordered = tuple(routes)
        by_id: dict[str, RouteDescriptor] = {}
        shortcuts: dict[str, str] = {}
        for route in ordered:
            if route.route_id in by_id:
                raise ValueError(f'duplicate route id: {route.route_id}')
            by_id[route.route_id] = route
            if route.shortcut:
                shortcut_key = route.shortcut.casefold().replace(' ', '')
                if shortcut_key in shortcuts:
                    owner = shortcuts[shortcut_key]
                    raise ValueError(
                        f'duplicate shortcut {route.shortcut}: {owner}, {route.route_id}')
                shortcuts[shortcut_key] = route.route_id
        self._ordered = ordered
        self._by_id: Mapping[str, RouteDescriptor] = MappingProxyType(by_id)

    def __iter__(self) -> Iterator[RouteDescriptor]:
        return iter(self._ordered)

    def __len__(self) -> int:
        return len(self._ordered)

    def __contains__(self, route_id: object) -> bool:
        return route_id in self._by_id

    def resolve(self, route_id: str) -> RouteDescriptor:
        """Return a route or raise a diagnostic lookup error."""
        try:
            return self._by_id[route_id]
        except KeyError:
            raise KeyError(f'unknown workspace route: {route_id}') from None

    def get(self, route_id: str) -> RouteDescriptor | None:
        return self._by_id.get(route_id)

    def for_group(self, group: RouteGroup | str) -> tuple[RouteDescriptor, ...]:
        resolved_group = RouteGroup(group)
        return tuple(route for route in self._ordered if route.group is resolved_group)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(route.route_id for route in self._ordered)


def _route(
    route_id: str,
    group: RouteGroup,
    label: str,
    icon: str,
    help_text: str,
    *,
    shortcut: str | None = None,
    requires_save: bool = False,
    required_context: Iterable[ContextKind] = (),
    accepted_context: Iterable[ContextKind] = (),
    risk: RouteRisk = RouteRisk.SAFE,
    legacy_index: int | None = None,
) -> RouteDescriptor:
    return RouteDescriptor(
        route_id=route_id,
        group=group,
        label_key=f'ui.route.{route_id}.label',
        label=label,
        icon=icon,
        help_key=f'ui.route.{route_id}.help',
        help_text=help_text,
        shortcut=shortcut,
        requires_save=requires_save,
        required_context=frozenset(required_context),
        accepted_context=frozenset(accepted_context),
        risk=risk,
        legacy_index=legacy_index,
    )


_SAVE = (ContextKind.SAVE,)
_WORLD = (
    ContextKind.SAVE,
    ContextKind.PLAYER,
    ContextKind.GUILD,
    ContextKind.BASE,
)
_ALL_CONTEXT = (*_WORLD, ContextKind.CONTAINER, ContextKind.BACKUP)


ROUTES = RouteRegistry((
    _route('overview', RouteGroup.WORKSPACE, 'Overview', 'grid',
           'Save summary, status, and quick actions.', shortcut='Ctrl+Shift+O',
           accepted_context=_ALL_CONTEXT),
    _route('activity', RouteGroup.WORKSPACE, 'Activity', 'console',
           'Recent load, save, backup, and tool operations.', shortcut='Ctrl+Shift+A',
           accepted_context=_SAVE),
    _route('backups', RouteGroup.WORKSPACE, 'Backups', 'restore',
           'Browse and restore save backups.', shortcut='Ctrl+Shift+B',
           accepted_context=(ContextKind.SAVE, ContextKind.BACKUP),
           risk=RouteRisk.CAUTION),

    _route('map', RouteGroup.WORLD, 'Map', 'map',
           'Inspect the world map, bases, and entity locations.', shortcut='Ctrl+8',
           requires_save=True, accepted_context=_WORLD, legacy_index=7),
    _route('bases', RouteGroup.WORLD, 'Bases', 'bases',
           'Browse and manage world bases.', shortcut='Ctrl+7', requires_save=True,
           accepted_context=(ContextKind.SAVE, ContextKind.BASE, ContextKind.GUILD),
           risk=RouteRisk.CAUTION, legacy_index=6),
    _route('players', RouteGroup.WORLD, 'Players', 'players',
           'Browse players and their world relationships.', shortcut='Ctrl+5',
           requires_save=True,
           accepted_context=(ContextKind.SAVE, ContextKind.PLAYER, ContextKind.GUILD),
           risk=RouteRisk.CAUTION, legacy_index=4),
    _route('guilds', RouteGroup.WORLD, 'Guilds', 'guilds',
           'Browse guilds, members, and owned bases.', shortcut='Ctrl+6',
           requires_save=True,
           accepted_context=(ContextKind.SAVE, ContextKind.GUILD, ContextKind.PLAYER,
                             ContextKind.BASE),
           risk=RouteRisk.CAUTION, legacy_index=5),
    _route('exclusions', RouteGroup.WORLD, 'Exclusions', 'exclusions',
           'Review entities protected from cleanup workflows.', shortcut='Ctrl+9',
           requires_save=True, accepted_context=_WORLD, legacy_index=8),

    _route('player_inventory', RouteGroup.EDITORS, 'Player Inventory',
           'player_inventory', 'Edit a selected player inventory.', shortcut='Ctrl+3',
           requires_save=True, required_context=(ContextKind.PLAYER,),
           accepted_context=(ContextKind.SAVE, ContextKind.PLAYER),
           risk=RouteRisk.CAUTION, legacy_index=2),
    _route('base_inventory', RouteGroup.EDITORS, 'Base Inventory', 'base_inventory',
           'Edit containers belonging to a selected base or guild.', shortcut='Ctrl+2',
           requires_save=True,
           accepted_context=(ContextKind.SAVE, ContextKind.GUILD, ContextKind.BASE,
                             ContextKind.CONTAINER),
           risk=RouteRisk.CAUTION, legacy_index=1),
    _route('pal_editor', RouteGroup.EDITORS, 'Pal Editor', 'pal_editor',
           'Browse and edit player and base Pals.', shortcut='Ctrl+4',
           requires_save=True,
           accepted_context=(ContextKind.SAVE, ContextKind.PLAYER, ContextKind.GUILD,
                             ContextKind.BASE, ContextKind.CONTAINER),
           risk=RouteRisk.CAUTION, legacy_index=3),
    _route('json_editor', RouteGroup.EDITORS, 'JSON Editor', 'json_editor',
           'Inspect and edit the raw save representation.', shortcut='Ctrl+0',
           requires_save=True, accepted_context=_SAVE, risk=RouteRisk.HIGH,
           legacy_index=9),

    _route('tools', RouteGroup.TOOLS, 'Tool Center', 'tools',
           'Find conversion, repair, import, and export utilities.', shortcut='Ctrl+1',
           accepted_context=_ALL_CONTEXT, risk=RouteRisk.CAUTION, legacy_index=0),

    _route('breeding', RouteGroup.REFERENCE, 'Breeding', 'breeding',
           'Explore Pal breeding combinations.', shortcut='Ctrl+-',
           accepted_context=(ContextKind.SAVE, ContextKind.PLAYER), legacy_index=11),
    _route('docs', RouteGroup.REFERENCE, 'Reference', 'docs',
           'Browse Palworld items, Pals, skills, and internal reference data.',
           shortcut='Ctrl+=', accepted_context=_ALL_CONTEXT, legacy_index=10),

    _route('settings', RouteGroup.SYSTEM, 'Settings', 'cog',
           'Configure appearance, naming, backups, and application behavior.',
           shortcut='Ctrl+,', accepted_context=_SAVE),
    _route('about', RouteGroup.SYSTEM, 'About', 'info',
           'View PalTrainer version, credits, and project information.'),
    _route('diagnostics', RouteGroup.SYSTEM, 'Diagnostics', 'console',
           'Inspect logs and technical information for troubleshooting.',
           accepted_context=_SAVE),
))


GROUP_LABEL_KEYS: Mapping[RouteGroup, str] = MappingProxyType({
    group: f'ui.route_group.{group.value}' for group in RouteGroup
})


def resolve_route(route_id: str) -> RouteDescriptor:
    return ROUTES.resolve(route_id)


__all__ = [
    'ContextKind',
    'GROUP_LABEL_KEYS',
    'ROUTES',
    'RouteDescriptor',
    'RouteGroup',
    'RouteRegistry',
    'RouteRisk',
    'resolve_route',
]
