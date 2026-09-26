"""Presentation record of edits still held in the loaded save session.

Entries describe observed in-memory changes. They do not imply that an edit can
be rolled back; a callback must be supplied before Undo can be offered.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

from PyQt6.QtCore import QObject, pyqtSignal

from palworld_aio.ui.workspace_context import PendingChangesSummary


@dataclass(frozen=True, slots=True)
class PendingChange:
    change_id: str
    label: str
    context: str = ''
    affected_count: int | None = None
    high_risk: bool = False
    undo: Callable[[], None] | None = None
    redo: Callable[[], None] | None = None

    @property
    def can_undo(self) -> bool:
        return self.undo is not None


class PendingChangeJournal(QObject):
    """Tracks edits for one loaded save until a confirmed save or reload."""

    changed = pyqtSignal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._changes: list[PendingChange] = []
        self._undone: list[PendingChange] = []
        self._applying_inverse = False

    @property
    def changes(self) -> tuple[PendingChange, ...]:
        return tuple(self._changes)

    @property
    def can_undo(self) -> bool:
        return bool(self._changes and self._changes[-1].can_undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._undone and self._undone[-1].redo is not None)

    @property
    def summary(self) -> PendingChangesSummary:
        return PendingChangesSummary(
            count=len(self._changes),
            latest_label=self._changes[-1].label if self._changes else None,
            has_high_risk=any(change.high_risk for change in self._changes),
        )

    def record(
        self,
        label: str,
        *,
        context: str = '',
        affected_count: int | None = None,
        high_risk: bool = False,
        undo: Callable[[], None] | None = None,
        redo: Callable[[], None] | None = None,
    ) -> PendingChange:
        if self._applying_inverse:
            raise RuntimeError('undo/redo callbacks cannot record changes')
        if not label.strip():
            raise ValueError('change label must not be empty')
        if affected_count is not None and affected_count < 1:
            raise ValueError('affected count must be positive')
        if redo is not None and undo is None:
            raise ValueError('redo requires an undo callback')
        change = PendingChange(
            change_id=uuid4().hex,
            label=label.strip(),
            context=context.strip(),
            affected_count=affected_count,
            high_risk=high_risk,
            undo=undo,
            redo=redo,
        )
        self._changes.append(change)
        self._undone.clear()
        self.changed.emit(self.summary)
        return change

    def undo_last(self) -> bool:
        if self._applying_inverse:
            raise RuntimeError('undo/redo callbacks cannot be nested')
        if not self.can_undo:
            return False
        change = self._changes[-1]
        assert change.undo is not None
        self._applying_inverse = True
        try:
            change.undo()
        finally:
            self._applying_inverse = False
        self._changes.pop()
        if change.redo is not None:
            self._undone.append(change)
        self.changed.emit(self.summary)
        return True

    def redo_last(self) -> bool:
        if self._applying_inverse:
            raise RuntimeError('undo/redo callbacks cannot be nested')
        if not self.can_redo:
            return False
        change = self._undone[-1]
        assert change.redo is not None
        self._applying_inverse = True
        try:
            change.redo()
        finally:
            self._applying_inverse = False
        self._undone.pop()
        self._changes.append(change)
        self.changed.emit(self.summary)
        return True

    def clear(self) -> None:
        if self._applying_inverse:
            raise RuntimeError('undo/redo callbacks cannot clear changes')
        if self._changes or self._undone:
            self._changes.clear()
            self._undone.clear()
            self.changed.emit(self.summary)


__all__ = ['PendingChange', 'PendingChangeJournal']
