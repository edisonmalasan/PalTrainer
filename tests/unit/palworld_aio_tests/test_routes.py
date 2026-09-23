from __future__ import annotations

import re

import pytest

from tests.dynamic_importer import import_from
from tests.test_registry import PROJECT_ROOT


routes = import_from('palworld_aio.ui.routes')
icons = import_from('palworld_aio.ui.chrome.icons')


def _inventoried_route_ids() -> list[str]:
    inventory = (
        PROJECT_ROOT
        / 'openspec'
        / 'changes'
        / 'implement-audit-uiux-rehaul'
        / 'migration-inventory.md'
    ).read_text(encoding='utf-8')
    table = inventory.split('## Registered Routes and Pages', 1)[1].split(
        '## Dialog and Dialog-Like Inventory', 1)[0]
    found: list[str] = []
    for line in table.splitlines():
        if not line.startswith('|'):
            continue
        first_cell = line.split('|', 2)[1]
        found.extend(re.findall(r'`([a-z][a-z0-9_]*)`', first_cell))
    return found


def _descriptor(route_id: str, *, shortcut: str | None = None):
    return routes.RouteDescriptor(
        route_id=route_id,
        group=routes.RouteGroup.WORKSPACE,
        label_key=f'ui.route.{route_id}.label',
        label=route_id.title(),
        icon='grid',
        help_key=f'ui.route.{route_id}.help',
        help_text='Help',
        shortcut=shortcut,
    )


def test_every_inventoried_destination_resolves_exactly_once():
    inventoried = _inventoried_route_ids()
    assert len(inventoried) == len(set(inventoried))
    assert set(inventoried) == set(routes.ROUTES.ids)
    assert len(routes.ROUTES) == len(inventoried)
    assert all(routes.resolve_route(route_id).route_id == route_id
               for route_id in inventoried)


def test_all_six_workflow_groups_are_ordered_and_non_empty():
    assert tuple(routes.RouteGroup) == (
        routes.RouteGroup.WORKSPACE,
        routes.RouteGroup.WORLD,
        routes.RouteGroup.EDITORS,
        routes.RouteGroup.TOOLS,
        routes.RouteGroup.REFERENCE,
        routes.RouteGroup.SYSTEM,
    )
    assert all(routes.ROUTES.for_group(group) for group in routes.RouteGroup)


def test_every_reference_route_is_registered_and_reachable():
    reference_routes = routes.ROUTES.for_group(routes.RouteGroup.REFERENCE)
    assert tuple(route.route_id for route in reference_routes) == ('breeding', 'docs')
    assert all(route.legacy_index is not None for route in reference_routes)
    assert all(route.shortcut for route in reference_routes)


def test_routes_have_local_vector_icons_and_complete_presentation_metadata():
    for route in routes.ROUTES:
        assert route.label_key.startswith('ui.route.')
        assert route.label.strip()
        assert route.help_key.startswith('ui.route.')
        assert route.help_text.strip()
        assert icons.has_vector_icon(route.icon), route.route_id


def test_legacy_route_indices_and_shortcuts_are_preserved():
    expected = {
        'tools': (0, 'Ctrl+1'),
        'base_inventory': (1, 'Ctrl+2'),
        'player_inventory': (2, 'Ctrl+3'),
        'pal_editor': (3, 'Ctrl+4'),
        'players': (4, 'Ctrl+5'),
        'guilds': (5, 'Ctrl+6'),
        'bases': (6, 'Ctrl+7'),
        'map': (7, 'Ctrl+8'),
        'exclusions': (8, 'Ctrl+9'),
        'json_editor': (9, 'Ctrl+0'),
        'docs': (10, 'Ctrl+='),
        'breeding': (11, 'Ctrl+-'),
    }
    assert {
        route_id: (routes.ROUTES.resolve(route_id).legacy_index,
                   routes.ROUTES.resolve(route_id).shortcut)
        for route_id in expected
    } == expected


def test_entity_prerequisites_are_explicit_and_accepted():
    inventory = routes.ROUTES.resolve('player_inventory')
    assert inventory.requires_save
    assert inventory.required_context == frozenset({routes.ContextKind.PLAYER})
    assert inventory.required_context <= inventory.accepted_context
    assert not routes.ROUTES.resolve('overview').requires_save


def test_registry_rejects_duplicate_ids_and_shortcuts():
    with pytest.raises(ValueError, match='duplicate route id'):
        routes.RouteRegistry((_descriptor('one'), _descriptor('one')))
    with pytest.raises(ValueError, match='duplicate shortcut'):
        routes.RouteRegistry((
            _descriptor('one', shortcut='Ctrl+K'),
            _descriptor('two', shortcut='ctrl + k'),
        ))


def test_unknown_route_has_diagnostic_error():
    with pytest.raises(KeyError, match='unknown workspace route: missing'):
        routes.resolve_route('missing')
