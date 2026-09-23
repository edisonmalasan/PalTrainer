from __future__ import annotations

import pytest

from tests.dynamic_importer import import_from


router_mod = import_from('palworld_aio.ui.router')
context_mod = import_from('palworld_aio.ui.workspace_context')
routes = import_from('palworld_aio.ui.routes')


class FakePage:
    def __init__(self, state=None):
        self.state = dict(state or {})
        self.restored = []

    def capture_view_state(self):
        return dict(self.state)

    def restore_view_state(self, state):
        self.state = dict(state)
        self.restored.append(dict(state))


def _selection(identifier: str):
    return context_mod.ContextSelection(identifier, identifier.title())


def _loaded_context():
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity('world', 'Island', 'C:/Level.sav'))
    return context


def test_navigation_captures_and_restores_page_filter_selection_and_scroll():
    context = _loaded_context()
    router = router_mod.WorkspaceRouter(context)
    overview = FakePage({'section': 'summary'})
    players = FakePage({'search': 'ada', 'selected': ['player-1'], 'scroll': 84})
    router.register_page('overview', overview)
    router.register_page('players', players)

    router.navigate('players')
    router.navigate('guilds')
    players.state = {}
    result = router.back(valid_ids={routes.ContextKind.PLAYER: {'player-1'}})

    assert result.route.route_id == 'players'
    assert result.restored_view_state == {
        'search': 'ada', 'selected': ['player-1'], 'scroll': 84,
    }
    assert players.restored[-1] == result.restored_view_state
    assert router.can_go_forward


def test_back_forward_restore_contextual_entity_identifiers():
    context = _loaded_context()
    router = router_mod.WorkspaceRouter(context)
    router.open_contextual('players', player=_selection('player-1'))
    router.open_contextual('guilds', guild=_selection('guild-1'))
    assert context.snapshot.player.identifier == 'player-1'
    assert context.snapshot.guild.identifier == 'guild-1'

    router.back(valid_ids={
        routes.ContextKind.PLAYER: {'player-1'},
        routes.ContextKind.GUILD: {'guild-1'},
    })
    assert router.current_route_id == 'players'
    assert context.snapshot.player.identifier == 'player-1'
    assert context.snapshot.guild is None

    router.forward(valid_ids={
        routes.ContextKind.PLAYER: {'player-1'},
        routes.ContextKind.GUILD: {'guild-1'},
    })
    assert router.current_route_id == 'guilds'
    assert context.snapshot.guild.identifier == 'guild-1'


def test_invalid_restored_context_becomes_explicit_prerequisite_state():
    context = _loaded_context()
    router = router_mod.WorkspaceRouter(context)
    router.open_contextual('player_inventory', player=_selection('player-deleted'))
    router.navigate('docs')

    result = router.back(valid_ids={routes.ContextKind.PLAYER: {'player-live'}})
    assert result.route.route_id == 'player_inventory'
    assert not result.ready
    assert result.missing_prerequisites == frozenset({routes.ContextKind.PLAYER})
    assert context.snapshot.player is None


def test_last_route_per_group_uses_remembered_route_then_group_default():
    router = router_mod.WorkspaceRouter(_loaded_context())
    assert router.last_route(routes.RouteGroup.WORLD) == 'map'
    router.navigate('guilds')
    router.navigate('docs')
    assert router.last_route(routes.RouteGroup.WORLD) == 'guilds'
    assert router.last_route(routes.RouteGroup.REFERENCE) == 'docs'


def test_new_navigation_clears_forward_history():
    router = router_mod.WorkspaceRouter(_loaded_context())
    router.navigate('players')
    router.navigate('guilds')
    router.back()
    assert router.can_go_forward
    router.navigate('bases')
    assert not router.can_go_forward


def test_contextual_links_reject_context_the_route_does_not_accept():
    router = router_mod.WorkspaceRouter(_loaded_context())
    with pytest.raises(ValueError, match='does not accept context: base'):
        router.open_contextual('settings', base=_selection('base-1'))
    with pytest.raises(ValueError, match='unknown context link'):
        router.open_contextual('players', item=_selection('item-1'))


def test_view_state_must_be_serializable_and_is_defensively_copied():
    router = router_mod.WorkspaceRouter(_loaded_context())
    page = FakePage({'filters': ['online']})
    router.register_page('overview', page)
    router.navigate('players')
    page.state['filters'].append('changed-later')
    assert router.back_entries[-1].view_state == {'filters': ['online']}

    bad = FakePage({'widget': object()})
    router = router_mod.WorkspaceRouter(_loaded_context())
    router.register_page('overview', bad)
    with pytest.raises(ValueError, match='JSON-serializable'):
        router.navigate('players')


def test_reset_for_new_save_drops_entity_history_and_page_tokens():
    context = _loaded_context()
    router = router_mod.WorkspaceRouter(context)
    players = FakePage({'selected': ['player-old']})
    router.register_page('players', players)
    router.open_contextual('players', player=_selection('player-old'))
    router.navigate('docs')

    result = router.reset_for_save()
    assert result.route.route_id == 'overview'
    assert not router.can_go_back
    assert not router.can_go_forward


def test_navigation_listener_receives_ready_and_prerequisite_results():
    router = router_mod.WorkspaceRouter(_loaded_context())
    observed = []
    unsubscribe = router.subscribe(observed.append)
    router.navigate('players')
    router.navigate('player_inventory')
    unsubscribe()
    router.navigate('docs')
    assert observed[0].ready
    assert not observed[1].ready
    assert len(observed) == 2
