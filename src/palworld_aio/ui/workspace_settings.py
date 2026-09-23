"""Versioned persistence contract for workspace-only UI state."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Mapping

from palworld_aio.ui.routes import ContextKind, ROUTES, RouteGroup, RouteRegistry
from palworld_aio.ui.workspace_context import (
    ContextSelection, SaveIdentity, WorkspaceContext,
)


WORKSPACE_SETTINGS_VERSION = 1
MAX_RECENT_SAVES = 5


@dataclass(frozen=True, slots=True)
class RecentSaveSetting:
    save_id: str
    display_name: str
    path: str
    platform: str = 'unknown'


@dataclass(slots=True)
class WorkspaceSettings:
    version: int = WORKSPACE_SETTINGS_VERSION
    sidebar_collapsed: bool = False
    sidebar_width: int = 240
    splitter_sizes: tuple[int, ...] = ()
    current_route: str = 'overview'
    last_routes: dict[str, str] = field(default_factory=dict)
    recent_save_id: str | None = None
    recent_saves: tuple[RecentSaveSetting, ...] = ()
    recent_context: dict[str, dict[str, str]] = field(default_factory=dict)
    page_view_state: dict[str, dict[str, object]] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        raw: object,
        registry: RouteRegistry = ROUTES,
    ) -> 'WorkspaceSettings':
        default = cls()
        if not isinstance(raw, Mapping) or raw.get('version') != WORKSPACE_SETTINGS_VERSION:
            return default
        collapsed = raw.get('sidebar_collapsed', False)
        width = raw.get('sidebar_width', 240)
        if not isinstance(collapsed, bool):
            collapsed = False
        if not isinstance(width, int) or isinstance(width, bool):
            width = 240
        width = max(208, min(320, width))
        splitter = raw.get('splitter_sizes', ())
        if not isinstance(splitter, (list, tuple)) or not all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in splitter
        ):
            splitter = ()
        current = raw.get('current_route', 'overview')
        if not isinstance(current, str) or current not in registry:
            current = 'overview'
        last_routes = {}
        source_last = raw.get('last_routes', {})
        if isinstance(source_last, Mapping):
            for group, route_id in source_last.items():
                try:
                    resolved_group = RouteGroup(str(group))
                    route = registry.resolve(str(route_id))
                except (ValueError, KeyError):
                    continue
                if route.group is resolved_group:
                    last_routes[resolved_group.value] = route.route_id
        recent_context = {}
        source_context = raw.get('recent_context', {})
        if isinstance(source_context, Mapping):
            for kind, value in source_context.items():
                if kind not in {item.value for item in ContextKind if item is not ContextKind.SAVE}:
                    continue
                if not isinstance(value, Mapping):
                    continue
                identifier, label = value.get('identifier'), value.get('label')
                if isinstance(identifier, str) and identifier and isinstance(label, str) and label:
                    recent_context[str(kind)] = {
                        'identifier': identifier,
                        'label': label,
                        'detail': str(value.get('detail', '')),
                    }
        page_state = {}
        source_pages = raw.get('page_view_state', {})
        if isinstance(source_pages, Mapping):
            for route_id, state in source_pages.items():
                if route_id in registry and isinstance(state, Mapping):
                    candidate = dict(state)
                    try:
                        json.dumps(candidate)
                    except (TypeError, ValueError):
                        continue
                    page_state[str(route_id)] = candidate
        save_id = raw.get('recent_save_id')
        if not isinstance(save_id, str) or not save_id:
            save_id = None
        recent_saves = []
        source_saves = raw.get('recent_saves', ())
        if isinstance(source_saves, (list, tuple)):
            for value in source_saves[:MAX_RECENT_SAVES]:
                if not isinstance(value, Mapping):
                    continue
                candidate = (
                    value.get('save_id'), value.get('display_name'),
                    value.get('path'), value.get('platform', 'unknown'),
                )
                if not all(isinstance(item, str) and item for item in candidate):
                    continue
                recent_saves.append(RecentSaveSetting(*candidate))
        return cls(
            sidebar_collapsed=collapsed,
            sidebar_width=width,
            splitter_sizes=tuple(splitter),
            current_route=current,
            last_routes=last_routes,
            recent_save_id=save_id,
            recent_saves=tuple(recent_saves),
            recent_context=recent_context,
            page_view_state=page_state,
        )

    def capture_context(self, context: WorkspaceContext) -> None:
        snapshot = context.snapshot
        self.recent_save_id = snapshot.save.save_id if snapshot.save else None
        if snapshot.save is not None:
            self.remember_save(snapshot.save)
        self.recent_context = {}
        for kind in (ContextKind.PLAYER, ContextKind.GUILD, ContextKind.BASE,
                     ContextKind.CONTAINER):
            selection = getattr(snapshot, kind.value)
            if selection is not None:
                self.recent_context[kind.value] = {
                    'identifier': selection.identifier,
                    'label': selection.label,
                    'detail': selection.detail,
                }

    def remember_save(self, save: SaveIdentity) -> None:
        """Put a reusable local save at the front of the bounded recent list."""
        if not save.path or 'paltrainer_xgp_' in save.path.lower():
            return
        entry = RecentSaveSetting(
            save_id=save.save_id,
            display_name=save.display_name,
            path=save.path,
            platform=save.platform.value,
        )
        others = tuple(
            item for item in self.recent_saves
            if item.save_id != entry.save_id and item.path != entry.path
        )
        self.recent_saves = (entry, *others)[:MAX_RECENT_SAVES]

    def remove_recent_save(self, save_id: str) -> bool:
        updated = tuple(item for item in self.recent_saves if item.save_id != save_id)
        changed = updated != self.recent_saves
        self.recent_saves = updated
        if self.recent_save_id == save_id:
            self.recent_save_id = None
            self.recent_context = {}
        return changed

    def relocate_recent_save(self, save_id: str, path: str) -> bool:
        for index, item in enumerate(self.recent_saves):
            if item.save_id != save_id:
                continue
            replacement = RecentSaveSetting(
                save_id=path,
                display_name=item.display_name,
                path=path,
                platform=item.platform,
            )
            values = list(self.recent_saves)
            values[index] = replacement
            self.recent_saves = tuple(values)
            if self.recent_save_id == save_id:
                self.recent_save_id = path
            return True
        return False

    def restore_context(self, context: WorkspaceContext) -> bool:
        snapshot = context.snapshot
        if snapshot.save is None or snapshot.save.save_id != self.recent_save_id:
            return False
        selections = {
            kind: ContextSelection(**self.recent_context[kind.value])
            for kind in (ContextKind.PLAYER, ContextKind.GUILD, ContextKind.BASE,
                         ContextKind.CONTAINER)
            if kind.value in self.recent_context
        }
        if ContextKind.PLAYER in selections:
            context.set_player(selections[ContextKind.PLAYER])
        if ContextKind.GUILD in selections:
            context.set_guild(selections[ContextKind.GUILD])
        if ContextKind.BASE in selections:
            context.set_base(selections[ContextKind.BASE])
        if ContextKind.CONTAINER in selections:
            context.set_container(selections[ContextKind.CONTAINER])
        return bool(selections)

    def to_mapping(self) -> dict[str, object]:
        return {
            'version': WORKSPACE_SETTINGS_VERSION,
            'sidebar_collapsed': self.sidebar_collapsed,
            'sidebar_width': self.sidebar_width,
            'splitter_sizes': list(self.splitter_sizes),
            'current_route': self.current_route,
            'last_routes': dict(self.last_routes),
            'recent_save_id': self.recent_save_id,
            'recent_saves': [
                {
                    'save_id': item.save_id,
                    'display_name': item.display_name,
                    'path': item.path,
                    'platform': item.platform,
                }
                for item in self.recent_saves
            ],
            'recent_context': {
                kind: dict(value) for kind, value in self.recent_context.items()
            },
            'page_view_state': {
                route: dict(state) for route, state in self.page_view_state.items()
            },
        }


__all__ = [
    'MAX_RECENT_SAVES', 'RecentSaveSetting', 'WORKSPACE_SETTINGS_VERSION',
    'WorkspaceSettings',
]
