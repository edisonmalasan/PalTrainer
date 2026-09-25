"""Identifier-only presentation context shared by workspace pages.

The context never retains decoded save records or widgets.  Managers remain the
source of truth and resolve these stable identifiers whenever a page needs its
authoritative data.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Callable, Iterable, Mapping

from palworld_aio.shell_state import ShellState
from palworld_aio.ui.routes import ContextKind, RouteDescriptor


class SavePlatform(StrEnum):
    UNKNOWN = 'unknown'
    STEAM = 'steam'
    XBOX = 'xbox'


@dataclass(frozen=True, slots=True)
class SaveIdentity:
    save_id: str
    display_name: str
    path: str
    platform: SavePlatform = SavePlatform.UNKNOWN
    modified_at: str | None = None
    read_only: bool = False

    def __post_init__(self) -> None:
        if not self.save_id.strip():
            raise ValueError('save_id must not be empty')
        if not self.display_name.strip():
            raise ValueError('display_name must not be empty')


@dataclass(frozen=True, slots=True)
class ContextSelection:
    identifier: str
    label: str
    detail: str = ''

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError('context identifiers must be non-empty strings')
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError('context labels must be non-empty strings')


@dataclass(frozen=True, slots=True)
class BackupState:
    count: int = 0
    latest_id: str | None = None
    latest_label: str | None = None
    recommended: bool = False

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError('backup count cannot be negative')
        if self.latest_id is not None and not isinstance(self.latest_id, str):
            raise TypeError('backup identifiers must be strings')


@dataclass(frozen=True, slots=True)
class PendingChangesSummary:
    count: int = 0
    latest_label: str | None = None
    has_high_risk: bool = False

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError('pending change count cannot be negative')


@dataclass(frozen=True, slots=True)
class WorkspaceContextSnapshot:
    revision: int
    save_state: ShellState
    save: SaveIdentity | None
    player: ContextSelection | None
    guild: ContextSelection | None
    base: ContextSelection | None
    container: ContextSelection | None
    backup: BackupState
    pending_changes: PendingChangesSummary
    current_route: str


ContextListener = Callable[[WorkspaceContextSnapshot], None]


class WorkspaceContext:
    """Mutable coordinator with immutable snapshots and explicit invalidation."""

    def __init__(self, *, current_route: str = 'overview') -> None:
        self._snapshot = WorkspaceContextSnapshot(
            revision=0,
            save_state=ShellState.NO_SAVE,
            save=None,
            player=None,
            guild=None,
            base=None,
            container=None,
            backup=BackupState(),
            pending_changes=PendingChangesSummary(),
            current_route=current_route,
        )
        self._listeners: list[ContextListener] = []

    @property
    def snapshot(self) -> WorkspaceContextSnapshot:
        return self._snapshot

    def subscribe(self, listener: ContextListener) -> Callable[[], None]:
        if listener not in self._listeners:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def _update(self, **changes: object) -> WorkspaceContextSnapshot:
        candidate = replace(self._snapshot, **changes)
        if candidate == self._snapshot:
            return self._snapshot
        self._snapshot = replace(candidate, revision=self._snapshot.revision + 1)
        for listener in tuple(self._listeners):
            listener(self._snapshot)
        return self._snapshot

    def begin_load(self) -> WorkspaceContextSnapshot:
        """Enter loading and invalidate every value tied to the prior save."""
        return self._update(
            save_state=ShellState.LOADING,
            save=None,
            player=None,
            guild=None,
            base=None,
            container=None,
            backup=BackupState(),
            pending_changes=PendingChangesSummary(),
        )

    def finish_load(
        self,
        save: SaveIdentity | None,
        *,
        success: bool = True,
        backup: BackupState | None = None,
    ) -> WorkspaceContextSnapshot:
        if success and save is None:
            raise ValueError('a successful load requires a save identity')
        resting_state = (
            ShellState.READ_ONLY if save is not None and save.read_only
            else ShellState.BACKUP_RECOMMENDED
            if backup is not None and backup.recommended
            else ShellState.LOADED
        )
        return self._update(
            save_state=resting_state if success else ShellState.ERROR,
            save=save if success else None,
            backup=backup or BackupState(),
            player=None,
            guild=None,
            base=None,
            container=None,
            pending_changes=PendingChangesSummary(),
            current_route='overview' if success else self._snapshot.current_route,
        )

    def clear_save(self) -> WorkspaceContextSnapshot:
        return self._update(
            save_state=ShellState.NO_SAVE,
            save=None,
            player=None,
            guild=None,
            base=None,
            container=None,
            backup=BackupState(),
            pending_changes=PendingChangesSummary(),
            current_route='overview',
        )

    def set_route(self, route_id: str) -> WorkspaceContextSnapshot:
        if not route_id.strip():
            raise ValueError('route_id must not be empty')
        return self._update(current_route=route_id)

    def set_player(self, selection: ContextSelection | None) -> WorkspaceContextSnapshot:
        return self._update(player=selection)

    def set_guild(self, selection: ContextSelection | None) -> WorkspaceContextSnapshot:
        if selection == self._snapshot.guild:
            return self._snapshot
        return self._update(guild=selection, base=None, container=None)

    def set_base(self, selection: ContextSelection | None) -> WorkspaceContextSnapshot:
        if selection == self._snapshot.base:
            return self._snapshot
        return self._update(base=selection, container=None)

    def set_container(
        self, selection: ContextSelection | None,
    ) -> WorkspaceContextSnapshot:
        return self._update(container=selection)

    def set_backup_state(self, state: BackupState) -> WorkspaceContextSnapshot:
        current = self._snapshot.save_state
        if current in (ShellState.LOADED, ShellState.BACKUP_RECOMMENDED):
            current = (ShellState.BACKUP_RECOMMENDED if state.recommended
                       else ShellState.LOADED)
        return self._update(backup=state, save_state=current)

    def set_pending_changes(
        self, summary: PendingChangesSummary,
    ) -> WorkspaceContextSnapshot:
        state = self._snapshot.save_state
        if summary.count and state in (ShellState.LOADED, ShellState.DIRTY,
                                       ShellState.BACKUP_RECOMMENDED):
            state = ShellState.DIRTY
        elif not summary.count and state is ShellState.DIRTY:
            state = (ShellState.BACKUP_RECOMMENDED
                     if self._snapshot.backup.recommended else ShellState.LOADED)
        return self._update(pending_changes=summary, save_state=state)

    def begin_save(self) -> WorkspaceContextSnapshot:
        if not self._snapshot.save_state.can_save:
            return self._snapshot
        return self._update(save_state=ShellState.SAVING)

    def finish_save(self, success: bool) -> WorkspaceContextSnapshot:
        return self._update(
            save_state=(ShellState.BACKUP_RECOMMENDED
                        if success and self._snapshot.backup.recommended
                        else ShellState.LOADED if success else ShellState.ERROR),
            pending_changes=(
                PendingChangesSummary()
                if success else self._snapshot.pending_changes
            ),
        )

    def apply_smart_defaults(
        self,
        *,
        players: Iterable[ContextSelection] = (),
        guilds: Iterable[ContextSelection] = (),
        bases: Iterable[ContextSelection] = (),
        containers: Iterable[ContextSelection] = (),
    ) -> WorkspaceContextSnapshot:
        """Select an option only when it is the sole valid choice.

        Base and container candidates are expected to already be scoped to the
        selected parent.  Ambiguous lists never overwrite an existing choice.
        """
        if self._snapshot.save is None:
            return self._snapshot
        changes: dict[str, ContextSelection] = {}
        for field, candidates in (
            ('player', players),
            ('guild', guilds),
            ('base', bases),
            ('container', containers),
        ):
            values = tuple(candidates)
            if getattr(self._snapshot, field) is None and len(values) == 1:
                changes[field] = values[0]
        return self._update(**changes) if changes else self._snapshot

    def invalidate_missing(
        self,
        valid_ids: Mapping[ContextKind, Iterable[str]],
    ) -> WorkspaceContextSnapshot:
        """Clear stale selections and their dependent descendants."""
        valid = {kind: {str(value) for value in values}
                 for kind, values in valid_ids.items()}
        changes: dict[str, ContextSelection | None] = {}
        player = self._snapshot.player
        if (player is not None and ContextKind.PLAYER in valid
                and player.identifier not in valid[ContextKind.PLAYER]):
            changes['player'] = None

        guild = self._snapshot.guild
        guild_invalid = (guild is not None and ContextKind.GUILD in valid
                         and guild.identifier not in valid[ContextKind.GUILD])
        if guild_invalid:
            changes.update(guild=None, base=None, container=None)
        else:
            base = self._snapshot.base
            base_invalid = (base is not None and ContextKind.BASE in valid
                            and base.identifier not in valid[ContextKind.BASE])
            if base_invalid:
                changes.update(base=None, container=None)
            else:
                container = self._snapshot.container
                if (container is not None and ContextKind.CONTAINER in valid
                        and container.identifier not in valid[ContextKind.CONTAINER]):
                    changes['container'] = None
        return self._update(**changes) if changes else self._snapshot

    def missing_prerequisites(self, route: RouteDescriptor) -> frozenset[ContextKind]:
        missing: set[ContextKind] = set()
        if route.requires_save and self._snapshot.save is None:
            missing.add(ContextKind.SAVE)
        for kind in route.required_context:
            if getattr(self._snapshot, kind.value, None) is None:
                missing.add(kind)
        return frozenset(missing)


__all__ = [
    'BackupState',
    'ContextSelection',
    'PendingChangesSummary',
    'SaveIdentity',
    'SavePlatform',
    'WorkspaceContext',
    'WorkspaceContextSnapshot',
]
