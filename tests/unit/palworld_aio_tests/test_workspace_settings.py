from __future__ import annotations

from tests.dynamic_importer import import_from


settings_mod = import_from('palworld_aio.ui.workspace_settings')
context_mod = import_from('palworld_aio.ui.workspace_context')
router_mod = import_from('palworld_aio.ui.router')
routes = import_from('palworld_aio.ui.routes')


def _loaded(save_id='world-1'):
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(save_id, 'Island', 'C:/Level.sav'))
    return context


def test_versioned_settings_round_trip_all_workspace_state():
    raw = {
        'version': settings_mod.WORKSPACE_SETTINGS_VERSION,
        'sidebar_collapsed': True,
        'sidebar_width': 276,
        'splitter_sizes': [800, 340],
        'current_route': 'players',
        'last_routes': {'world': 'players', 'editors': 'pal_editor'},
        'recent_save_id': 'world-1',
        'recent_saves': [{
            'save_id': 'world-1', 'display_name': 'Island',
            'path': 'C:/Saves/Island', 'platform': 'steam',
        }],
        'recent_context': {
            'player': {'identifier': 'p1', 'label': 'Ada', 'detail': 'Level 50'},
        },
        'page_view_state': {
            'players': {'search': 'ada', 'selected': ['p1'], 'scroll': 42},
        },
    }
    settings = settings_mod.WorkspaceSettings.from_mapping(raw)
    assert settings.to_mapping() == raw


def test_malformed_and_stale_versions_fall_back_without_exception():
    assert settings_mod.WorkspaceSettings.from_mapping(None) == settings_mod.WorkspaceSettings()
    assert settings_mod.WorkspaceSettings.from_mapping(
        {'version': 999, 'current_route': 'missing'}) == settings_mod.WorkspaceSettings()
    settings = settings_mod.WorkspaceSettings.from_mapping({
        'version': settings_mod.WORKSPACE_SETTINGS_VERSION,
        'sidebar_collapsed': 'yes',
        'sidebar_width': 'wide',
        'splitter_sizes': ['bad'],
        'current_route': 'missing',
        'last_routes': {'world': 'docs', 'bad': 'players'},
        'recent_context': {'player': object(), 'unknown': {'identifier': 'x'}},
        'page_view_state': {
            'missing': {'x': 1},
            'players': 'bad',
            'guilds': {'widget': object()},
        },
    })
    assert settings.sidebar_collapsed is False
    assert settings.sidebar_width == 240
    assert settings.splitter_sizes == ()
    assert settings.current_route == 'overview'
    assert not settings.last_routes
    assert not settings.recent_context
    assert not settings.page_view_state


def test_recent_saves_are_bounded_deduplicated_relocatable_and_removable():
    settings = settings_mod.WorkspaceSettings()
    for index in range(7):
        save = context_mod.SaveIdentity(
            f'world-{index}', f'Island {index}', f'C:/world-{index}')
        settings.remember_save(save)
    assert len(settings.recent_saves) == settings_mod.MAX_RECENT_SAVES
    assert settings.recent_saves[0].save_id == 'world-6'

    settings.remember_save(context_mod.SaveIdentity(
        'world-4', 'Island 4', 'C:/world-4'))
    assert settings.recent_saves[0].save_id == 'world-4'
    assert len(settings.recent_saves) == settings_mod.MAX_RECENT_SAVES

    assert settings.relocate_recent_save('world-4', 'D:/located-world')
    assert settings.recent_saves[0].path == 'D:/located-world'
    assert settings.remove_recent_save('D:/located-world')
    assert all(item.path != 'D:/located-world' for item in settings.recent_saves)


def test_recent_context_only_restores_for_same_save_identity():
    source = _loaded()
    source.set_player(context_mod.ContextSelection('p1', 'Ada'))
    source.set_guild(context_mod.ContextSelection('g1', 'Builders'))
    settings = settings_mod.WorkspaceSettings()
    settings.capture_context(source)

    matching = _loaded()
    assert settings.restore_context(matching)
    assert matching.snapshot.player.identifier == 'p1'
    assert matching.snapshot.guild.identifier == 'g1'

    different = _loaded('world-2')
    assert not settings.restore_context(different)
    assert different.snapshot.player is None


def test_router_persistent_state_restores_route_memory_and_page_tokens():
    class Page:
        def __init__(self):
            self.state = {'search': 'ada', 'selected': ['p1']}
        def capture_view_state(self):
            return self.state
        def restore_view_state(self, state):
            self.state = dict(state)

    first = router_mod.WorkspaceRouter(_loaded())
    page = Page()
    first.register_page('players', page)
    first.navigate('players')
    state = first.export_persistent_state()

    second = router_mod.WorkspaceRouter(_loaded())
    restored = Page()
    restored.state = {}
    second.register_page('players', restored)
    result = second.restore_persistent_state(**state)
    assert result.route.route_id == 'players'
    assert restored.state == {'search': 'ada', 'selected': ['p1']}
    assert second.last_route(routes.RouteGroup.WORLD) == 'players'


def test_route_validation_drops_wrong_group_last_routes_and_unknown_pages():
    settings = settings_mod.WorkspaceSettings.from_mapping({
        'version': settings_mod.WORKSPACE_SETTINGS_VERSION,
        'current_route': 'players',
        'last_routes': {'world': 'docs', 'reference': 'docs'},
        'page_view_state': {'players': {'search': ''}, 'unknown': {'x': 1}},
    })
    assert settings.last_routes == {'reference': 'docs'}
    assert settings.page_view_state == {'players': {'search': ''}}
