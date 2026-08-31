from __future__ import annotations
from tests.dynamic_importer import import_from

shell_state = import_from('palworld_aio.shell_state')

ShellState = shell_state.ShellState
ShellStateModel = shell_state.ShellStateModel


def test_initial_state_is_no_save():
    m = ShellStateModel()
    assert m.state == ShellState.NO_SAVE


def test_reset_returns_to_no_save():
    m = ShellStateModel()
    m.begin_load()
    m.finish_load(True)
    m.mark_dirty()
    m.reset()
    assert m.state == ShellState.NO_SAVE


def test_load_transition_success():
    m = ShellStateModel()
    m.begin_load()
    assert m.state == ShellState.LOADING
    m.finish_load(True)
    assert m.state == ShellState.LOADED


def test_load_transition_failure():
    m = ShellStateModel()
    m.begin_load()
    m.finish_load(False)
    assert m.state == ShellState.ERROR


def test_dirty_marks_after_load():
    m = ShellStateModel()
    m.finish_load(True)
    m.mark_dirty()
    assert m.state == ShellState.DIRTY


def test_mark_dirty_ignored_without_loaded_save():
    m = ShellStateModel()
    m.mark_dirty()
    assert m.state == ShellState.NO_SAVE


def test_save_transitions():
    m = ShellStateModel()
    m.finish_load(True)
    m.mark_dirty()
    m.begin_save()
    assert m.state == ShellState.SAVING
    m.finish_save(True)
    assert m.state == ShellState.LOADED


def test_save_failure_sets_error():
    m = ShellStateModel()
    m.finish_load(True)
    m.begin_save()
    m.finish_save(False)
    assert m.state == ShellState.ERROR


def test_fail_sets_error():
    m = ShellStateModel()
    m.fail()
    assert m.state == ShellState.ERROR


def test_can_load_per_state():
    assert ShellState.NO_SAVE.can_load
    assert ShellState.LOADED.can_load
    assert ShellState.DIRTY.can_load
    assert ShellState.ERROR.can_load
    assert not ShellState.LOADING.can_load
    assert not ShellState.SAVING.can_load


def test_can_save_per_state():
    assert ShellState.LOADED.can_save
    assert ShellState.DIRTY.can_save
    assert not ShellState.NO_SAVE.can_save
    assert not ShellState.LOADING.can_save
    assert not ShellState.SAVING.can_save


def test_can_edit_per_state():
    assert ShellState.LOADED.can_edit
    assert ShellState.DIRTY.can_edit
    assert not ShellState.NO_SAVE.can_edit
    assert not ShellState.SAVING.can_edit
