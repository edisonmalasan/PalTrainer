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

    @property
    def can_undo(self) -> bool:
        return self.undo is not None


class PendingChangeJournal(QObject):
    """Tracks edits for one loaded save until a confirmed save or reload."""

    changed = pyqtSignal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._changes: list[PendingChange] = []

    @property
    def changes(self) -> tuple[PendingChange, ...]:
        return tuple(self._changes)

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
    ) -> PendingChange:
        if not label.strip():
            raise ValueError('change label must not be empty')
        if affected_count is not None and affected_count < 1:
            raise ValueError('affected count must be positive')
        change = PendingChange(
            change_id=uuid4().hex,
            label=label.strip(),
            context=context.strip(),
            affected_count=affected_count,
            high_risk=high_risk,
            undo=undo,
        )
        self._changes.append(change)
        self.changed.emit(self.summary)
        return change

    def clear(self) -> None:
        if self._changes:
            self._changes.clear()
            self.changed.emit(self.summary)


__all__ = ['PendingChange', 'PendingChangeJournal']
