from __future__ import annotations

import pytest

from tests.dynamic_importer import import_from


context = import_from('palworld_aio.ui.workspace_context')
routes = import_from('palworld_aio.ui.routes')
shell_state = import_from('palworld_aio.shell_state')


def _save(save_id: str = 'world-1'):
    return context.SaveIdentity(
        save_id=save_id,
        display_name='Island',
        path=f'C:/saves/{save_id}/Level.sav',
        platform=context.SavePlatform.STEAM,
        modified_at='2026-09-09T10:00:00Z',
    )


def _selection(identifier: str, label: str | None = None):
    return context.ContextSelection(identifier, label or identifier)


def _loaded():
    model = context.WorkspaceContext()
    model.begin_load()
    model.finish_load(_save())
    return model


def test_load_transition_publishes_identifier_only_snapshot():
    model = context.WorkspaceContext(current_route='tools')
    observed = []
    model.subscribe(observed.append)
    model.begin_load()
    loaded = model.finish_load(
        _save(), backup=context.BackupState(2, 'backup-2', 'Today'))

    assert observed[0].save_state is shell_state.ShellState.LOADING
    assert loaded.save_state is shell_state.ShellState.LOADED
    assert loaded.save.save_id == 'world-1'
    assert loaded.save.platform is context.SavePlatform.STEAM
    assert loaded.current_route == 'overview'
    assert loaded.backup.latest_id == 'backup-2'
    assert isinstance(loaded.save.path, str)


def test_loading_a_new_save_invalidates_prior_entity_and_pending_context():
    model = _loaded()
    model.set_player(_selection('player-1'))
    model.set_guild(_selection('guild-1'))
    model.set_base(_selection('base-1'))
    model.set_container(_selection('container-1'))
    model.set_pending_changes(context.PendingChangesSummary(3, 'Edited inventory'))

    loading = model.begin_load()
    assert loading.save is None
    assert loading.player is loading.guild is loading.base is loading.container is None
    assert loading.pending_changes.count == 0


def test_hierarchical_changes_invalidate_only_dependent_context():
    model = _loaded()
    player = _selection('player-1')
    model.set_player(player)
    model.set_guild(_selection('guild-1'))
    model.set_base(_selection('base-1'))
    model.set_container(_selection('container-1'))

    model.set_base(_selection('base-2'))
    assert model.snapshot.player == player
    assert model.snapshot.guild.identifier == 'guild-1'
    assert model.snapshot.base.identifier == 'base-2'
    assert model.snapshot.container is None

    model.set_container(_selection('container-2'))
    model.set_guild(_selection('guild-2'))
    assert model.snapshot.player == player
    assert model.snapshot.base is None
    assert model.snapshot.container is None


def test_invalidate_missing_clears_stale_selection_and_descendants():
    model = _loaded()
    model.set_player(_selection('player-old'))
    model.set_guild(_selection('guild-old'))
    model.set_base(_selection('base-old'))
    model.set_container(_selection('container-old'))

    model.invalidate_missing({
        routes.ContextKind.PLAYER: {'player-new'},
        routes.ContextKind.GUILD: {'guild-new'},
        routes.ContextKind.BASE: {'base-old'},
        routes.ContextKind.CONTAINER: {'container-old'},
    })
    assert model.snapshot.player is None
    assert model.snapshot.guild is None
    assert model.snapshot.base is None
    assert model.snapshot.container is None


def test_smart_defaults_select_only_unambiguous_identifiers():
    model = _loaded()
    model.apply_smart_defaults(
        players=[_selection('player-1')],
        guilds=[_selection('guild-1')],
        bases=[_selection('base-1')],
        containers=[_selection('container-1'), _selection('container-2')],
    )
    assert model.snapshot.player.identifier == 'player-1'
    assert model.snapshot.guild.identifier == 'guild-1'
    assert model.snapshot.base.identifier == 'base-1'
    assert model.snapshot.container is None

    model.apply_smart_defaults(players=[_selection('player-2')])
    assert model.snapshot.player.identifier == 'player-1'


def test_pending_and_save_transitions_preserve_failed_change_summary():
    model = _loaded()
    pending = context.PendingChangesSummary(2, 'Changed two slots', True)
    model.set_pending_changes(pending)
    assert model.snapshot.save_state is shell_state.ShellState.DIRTY
    model.begin_save()
    assert model.snapshot.save_state is shell_state.ShellState.SAVING
    model.finish_save(False)
    assert model.snapshot.save_state is shell_state.ShellState.ERROR
    assert model.snapshot.pending_changes == pending

    model.finish_save(True)
    assert model.snapshot.save_state is shell_state.ShellState.LOADED
    assert model.snapshot.pending_changes.count == 0


def test_route_prerequisites_use_shared_context_identifiers():
    model = _loaded()
    route = routes.resolve_route('player_inventory')
    assert model.missing_prerequisites(route) == frozenset({routes.ContextKind.PLAYER})
    model.set_player(_selection('player-1'))
    assert not model.missing_prerequisites(route)

    model.clear_save()
    assert model.missing_prerequisites(route) == frozenset({
        routes.ContextKind.SAVE,
        routes.ContextKind.PLAYER,
    })


def test_context_rejects_non_identifier_payloads_and_invalid_counts():
    with pytest.raises(ValueError, match='non-empty strings'):
        context.ContextSelection('', 'Player')
    with pytest.raises(ValueError, match='non-empty strings'):
        context.ContextSelection(object(), 'Player')
    with pytest.raises(ValueError, match='cannot be negative'):
        context.BackupState(-1)
    with pytest.raises(ValueError, match='cannot be negative'):
        context.PendingChangesSummary(-1)


def test_unsubscribe_and_noop_updates_do_not_publish_extra_revisions():
    model = context.WorkspaceContext()
    observed = []
    unsubscribe = model.subscribe(observed.append)
    model.set_route('tools')
    first_revision = model.snapshot.revision
    model.set_route('tools')
    assert model.snapshot.revision == first_revision
    assert len(observed) == 1
    unsubscribe()
    model.set_route('overview')
    assert len(observed) == 1
