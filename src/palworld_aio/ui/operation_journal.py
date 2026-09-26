"""Bounded, presentation-safe history of meaningful application operations."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Callable, Iterable, Iterator
from uuid import uuid4

from PyQt6.QtCore import QObject, pyqtSignal


class ActivityKind(StrEnum):
    LOAD = 'load'
    BACKUP = 'backup'
    MUTATION = 'mutation'
    SAVE = 'save'
    TOOL = 'tool'
    FAILURE = 'failure'


class ActivityStatus(StrEnum):
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    FAILED = 'failed'
    UNDONE = 'undone'


UndoCallback = Callable[[], None]


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    event_id: str
    occurred_at: datetime
    kind: ActivityKind
    title: str
    context: str
    status: ActivityStatus
    detail: str = ''
    undo: UndoCallback | None = None

    @property
    def can_undo(self) -> bool:
        return self.undo is not None and self.status is not ActivityStatus.UNDONE


class OperationJournal(QObject):
    """Oldest-to-newest event collection with an explicit retention limit."""

    changed = pyqtSignal(object)

    def __init__(
        self,
        *,
        max_events: int = 200,
        clock: Callable[[], datetime] = datetime.now,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if max_events < 1:
            raise ValueError('max_events must be positive')
        self.max_events = max_events
        self._clock = clock
        self._events: list[ActivityEvent] = []

    @property
    def events(self) -> tuple[ActivityEvent, ...]:
        return tuple(self._events)

    def __iter__(self) -> Iterator[ActivityEvent]:
        return iter(self._events)

    def record(
        self,
        kind: ActivityKind,
        title: str,
        *,
        context: str = '',
        status: ActivityStatus = ActivityStatus.SUCCESS,
        detail: str = '',
        undo: UndoCallback | None = None,
    ) -> ActivityEvent:
        if not title.strip():
            raise ValueError('activity title must not be empty')
        event = ActivityEvent(
            event_id=uuid4().hex,
            occurred_at=self._clock(),
            kind=kind,
            title=title,
            context=context,
            status=status,
            detail=detail,
            undo=undo,
        )
        self._events.append(event)
        if len(self._events) > self.max_events:
            del self._events[:-self.max_events]
        self.changed.emit(self.events)
        return event

    def replace(self, events: Iterable[ActivityEvent]) -> None:
        self._events = list(events)[-self.max_events:]
        self.changed.emit(self.events)

    def clear(self) -> None:
        if not self._events:
            return
        self._events.clear()
        self.changed.emit(self.events)

    def undo_event(self, event_id: str) -> bool:
        for index, event in enumerate(self._events):
            if event.event_id != event_id or not event.can_undo:
                continue
            callback = event.undo
            if callback is None:
                return False
            callback()
            self._events[index] = replace(
                event, status=ActivityStatus.UNDONE, undo=None)
            self.changed.emit(self.events)
            return True
        return False


__all__ = [
    'ActivityEvent', 'ActivityKind', 'ActivityStatus', 'OperationJournal',
    'UndoCallback',
]
