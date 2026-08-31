"""Shell lifecycle state model for the PyQt application shell.

Plan 010: introduce standard no-save, loading, loaded, dirty, saving,
and error states so MainWindow coordinates views and commands through
one explicit state without performing raw save mutation itself.

This module is presentation-agnostic and imports no Qt widgets.
"""

from __future__ import annotations

from enum import Enum


class ShellState(Enum):
    NO_SAVE = 'no_save'
    LOADING = 'loading'
    LOADED = 'loaded'
    DIRTY = 'dirty'
    SAVING = 'saving'
    ERROR = 'error'

    @property
    def can_load(self) -> bool:
        return self in (ShellState.NO_SAVE, ShellState.LOADED, ShellState.DIRTY, ShellState.ERROR)

    @property
    def can_save(self) -> bool:
        return self in (ShellState.LOADED, ShellState.DIRTY)

    @property
    def can_edit(self) -> bool:
        return self in (ShellState.LOADED, ShellState.DIRTY)


class ShellStateModel:
    """Tracks the shell lifecycle state and validates transitions.

    UI code reads the state through this model and notifies transitions
    instead of flipping ad-hoc flags.  Mutations to save data still go
    through the save session; this model only mirrors presentation state.
    """

    def __init__(self) -> None:
        self._state: ShellState = ShellState.NO_SAVE

    @property
    def state(self) -> ShellState:
        return self._state

    def reset(self) -> None:
        self._state = ShellState.NO_SAVE

    def _set(self, state: ShellState) -> None:
        self._state = state

    def begin_load(self) -> None:
        self._set(ShellState.LOADING)

    def finish_load(self, success: bool) -> None:
        if success:
            self._set(ShellState.LOADED)
        else:
            self._set(ShellState.ERROR)

    def mark_dirty(self) -> None:
        if self._state in (ShellState.LOADED, ShellState.DIRTY):
            self._set(ShellState.DIRTY)

    def begin_save(self) -> None:
        if self._state.can_save:
            self._set(ShellState.SAVING)

    def finish_save(self, success: bool) -> None:
        if success:
            self._set(ShellState.LOADED)
        else:
            self._set(ShellState.ERROR)

    def fail(self) -> None:
        self._set(ShellState.ERROR)
