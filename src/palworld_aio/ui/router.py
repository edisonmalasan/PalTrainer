"""Workspace navigation, history, contextual links, and view-state hooks."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
from typing import Callable, Mapping, Protocol

from palworld_aio.ui.routes import (
    ContextKind,
    ROUTES,
    RouteDescriptor,
    RouteGroup,
    RouteRegistry,
)
from palworld_aio.ui.workspace_context import ContextSelection, WorkspaceContext


class PageStateAdapter(Protocol):
    def capture_view_state(self) -> Mapping[str, object]: ...

    def restore_view_state(self, state: Mapping[str, object]) -> None: ...


@dataclass(frozen=True, slots=True)
class ContextToken:
    player: ContextSelection | None = None
    guild: ContextSelection | None = None
    base: ContextSelection | None = None
    container: ContextSelection | None = None


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    route_id: str
    context: ContextToken = field(default_factory=ContextToken)
    view_state: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NavigationResult:
    route: RouteDescriptor
    missing_prerequisites: frozenset[ContextKind]
    restored_view_state: Mapping[str, object]

    @property
    def ready(self) -> bool:
        return not self.missing_prerequisites


NavigationListener = Callable[[NavigationResult], None]


def _copy_state(state: Mapping[str, object]) -> dict[str, object]:
    copied = deepcopy(dict(state))
    try:
        json.dumps(copied)
    except (TypeError, ValueError) as exc:
        raise ValueError('page view state must contain JSON-serializable values') from exc
    return copied


class WorkspaceRouter:
    """Separates serializable navigation state from page widget lifetime."""

    def __init__(
        self,
        context: WorkspaceContext,
        registry: RouteRegistry = ROUTES,
        *,
        initial_route: str = 'overview',
        history_limit: int = 100,
    ) -> None:
        if history_limit < 1:
            raise ValueError('history_limit must be positive')
        registry.resolve(initial_route)
        self._context = context
        self._registry = registry
        self._history_limit = history_limit
        self._current = HistoryEntry(initial_route)
        self._back: list[HistoryEntry] = []
        self._forward: list[HistoryEntry] = []
        self._last_by_group: dict[RouteGroup, str] = {
            registry.resolve(initial_route).group: initial_route,
        }
        self._page_state: dict[str, dict[str, object]] = {}
        self._adapters: dict[str, PageStateAdapter] = {}
        self._listeners: list[NavigationListener] = []
        context.set_route(initial_route)

    @property
    def current_route_id(self) -> str:
        return self._current.route_id

    @property
    def can_go_back(self) -> bool:
        return bool(self._back)

    @property
    def can_go_forward(self) -> bool:
        return bool(self._forward)

    @property
    def back_entries(self) -> tuple[HistoryEntry, ...]:
        return tuple(self._back)

    @property
    def forward_entries(self) -> tuple[HistoryEntry, ...]:
        return tuple(self._forward)

    def subscribe(self, listener: NavigationListener) -> Callable[[], None]:
        if listener not in self._listeners:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def register_page(self, route_id: str, adapter: PageStateAdapter) -> None:
        self._registry.resolve(route_id)
        self._adapters[route_id] = adapter

    def unregister_page(self, route_id: str) -> None:
        self._adapters.pop(route_id, None)

    def last_route(self, group: RouteGroup | str) -> str:
        resolved_group = RouteGroup(group)
        remembered = self._last_by_group.get(resolved_group)
        if remembered is not None:
            return remembered
        return self._registry.for_group(resolved_group)[0].route_id

    def _context_token(self) -> ContextToken:
        snapshot = self._context.snapshot
        return ContextToken(
            player=snapshot.player,
            guild=snapshot.guild,
            base=snapshot.base,
            container=snapshot.container,
        )

    def _capture_current(self) -> HistoryEntry:
        adapter = self._adapters.get(self._current.route_id)
        state = dict(self._current.view_state)
        if adapter is not None:
            state = _copy_state(adapter.capture_view_state())
            self._page_state[self._current.route_id] = state
        return HistoryEntry(
            route_id=self._current.route_id,
            context=self._context_token(),
            view_state=state,
        )

    def _push(self, stack: list[HistoryEntry], entry: HistoryEntry) -> None:
        stack.append(entry)
        if len(stack) > self._history_limit:
            del stack[:-self._history_limit]

    def _apply_context_token(self, token: ContextToken) -> None:
        self._context.set_player(token.player)
        self._context.set_guild(token.guild)
        self._context.set_base(token.base)
        self._context.set_container(token.container)

    def _apply_context_link(
        self,
        route: RouteDescriptor,
        linked: Mapping[ContextKind, ContextSelection],
    ) -> None:
        unsupported = set(linked) - set(route.accepted_context)
        if unsupported:
            names = ', '.join(sorted(kind.value for kind in unsupported))
            raise ValueError(f'{route.route_id} does not accept context: {names}')
        # Parent-before-child keeps the context hierarchy coherent.
        for kind in (
            ContextKind.PLAYER,
            ContextKind.GUILD,
            ContextKind.BASE,
            ContextKind.CONTAINER,
        ):
            if kind not in linked:
                continue
            selection = linked[kind]
            if kind is ContextKind.PLAYER:
                self._context.set_player(selection)
            elif kind is ContextKind.GUILD:
                self._context.set_guild(selection)
            elif kind is ContextKind.BASE:
                self._context.set_base(selection)
            elif kind is ContextKind.CONTAINER:
                self._context.set_container(selection)

    def _activate(
        self,
        entry: HistoryEntry,
        *,
        valid_ids: Mapping[ContextKind, set[str]] | None = None,
        restore_context: bool = False,
    ) -> NavigationResult:
        route = self._registry.resolve(entry.route_id)
        if restore_context:
            self._apply_context_token(entry.context)
        if valid_ids is not None:
            self._context.invalidate_missing(valid_ids)
        self._context.set_route(route.route_id)
        state = _copy_state(entry.view_state)
        self._current = HistoryEntry(route.route_id, self._context_token(), state)
        self._last_by_group[route.group] = route.route_id
        adapter = self._adapters.get(route.route_id)
        if adapter is not None and state:
            adapter.restore_view_state(_copy_state(state))
        result = NavigationResult(
            route=route,
            missing_prerequisites=self._context.missing_prerequisites(route),
            restored_view_state=state,
        )
        for listener in tuple(self._listeners):
            listener(result)
        return result

    def navigate(
        self,
        route_id: str,
        *,
        context: Mapping[ContextKind, ContextSelection] | None = None,
        view_state: Mapping[str, object] | None = None,
    ) -> NavigationResult:
        route = self._registry.resolve(route_id)
        linked = context or {}
        if route_id == self._current.route_id and not linked:
            return self._activate(self._capture_current())
        self._push(self._back, self._capture_current())
        self._forward.clear()
        if linked:
            self._apply_context_link(route, linked)
        entry = HistoryEntry(
            route_id=route_id,
            context=self._context_token(),
            view_state=_copy_state(
                view_state if view_state is not None
                else self._page_state.get(route_id, {})),
        )
        return self._activate(entry)

    def open_contextual(
        self,
        route_id: str,
        **context: ContextSelection,
    ) -> NavigationResult:
        try:
            linked = {ContextKind(name): selection for name, selection in context.items()}
        except ValueError as exc:
            raise ValueError(f'unknown context link: {exc}') from None
        return self.navigate(route_id, context=linked)

    def back(
        self,
        *,
        valid_ids: Mapping[ContextKind, set[str]] | None = None,
    ) -> NavigationResult | None:
        if not self._back:
            return None
        self._push(self._forward, self._capture_current())
        return self._activate(
            self._back.pop(), valid_ids=valid_ids, restore_context=True)

    def forward(
        self,
        *,
        valid_ids: Mapping[ContextKind, set[str]] | None = None,
    ) -> NavigationResult | None:
        if not self._forward:
            return None
        self._push(self._back, self._capture_current())
        return self._activate(
            self._forward.pop(), valid_ids=valid_ids, restore_context=True)

    def reset_for_save(self, *, route_id: str = 'overview') -> NavigationResult:
        """Drop history/view tokens that may identify records in another save."""
        self._back.clear()
        self._forward.clear()
        self._page_state.clear()
        self._last_by_group.clear()
        self._context.set_player(None)
        self._context.set_guild(None)
        return self._activate(HistoryEntry(route_id))

    def export_persistent_state(self) -> dict[str, object]:
        current = self._capture_current()
        if current.view_state:
            self._page_state[current.route_id] = _copy_state(current.view_state)
        return {
            'current_route': current.route_id,
            'last_routes': {
                group.value: route_id
                for group, route_id in self._last_by_group.items()
            },
            'page_view_state': deepcopy(self._page_state),
        }

    def restore_persistent_state(
        self,
        *,
        current_route: str,
        last_routes: Mapping[str, str],
        page_view_state: Mapping[str, Mapping[str, object]],
    ) -> NavigationResult:
        self._registry.resolve(current_route)
        self._back.clear()
        self._forward.clear()
        self._last_by_group = {}
        for group_value, route_id in last_routes.items():
            group = RouteGroup(group_value)
            route = self._registry.resolve(route_id)
            if route.group is group:
                self._last_by_group[group] = route_id
        self._page_state = {
            route_id: _copy_state(state)
            for route_id, state in page_view_state.items()
            if route_id in self._registry
        }
        return self._activate(HistoryEntry(
            current_route,
            self._context_token(),
            _copy_state(self._page_state.get(current_route, {})),
        ))


__all__ = [
    'ContextToken',
    'HistoryEntry',
    'NavigationResult',
    'PageStateAdapter',
    'WorkspaceRouter',
]
