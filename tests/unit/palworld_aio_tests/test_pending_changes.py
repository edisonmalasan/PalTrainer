from __future__ import annotations

import pytest

from tests.dynamic_importer import import_from


journal_module = import_from('palworld_aio.ui.pending_changes')
context_module = import_from('palworld_aio.ui.workspace_context')
shell_state = import_from('palworld_aio.shell_state')


def _identity(*, read_only: bool = False):
    return context_module.SaveIdentity(
        'world-1', 'Island', 'C:/saves/world-1/Level.sav',
        read_only=read_only,
    )


def test_journal_tracks_distinct_changes_and_only_real_undo():
    journal = journal_module.PendingChangeJournal()
    observed = []
    journal.changed.connect(observed.append)

    first = journal.record('Changed inventory', context='Player A', affected_count=2)
    second = journal.record('Removed Pals', affected_count=3, high_risk=True)

    assert first.can_undo is False
    assert second.can_undo is False
    assert journal.summary.count == 2
    assert journal.summary.latest_label == 'Removed Pals'
    assert journal.summary.has_high_risk is True
    assert observed[-1] == journal.summary

    journal.clear()
    assert journal.summary.count == 0
    assert len(observed) == 3


def test_journal_rejects_unhelpful_entries():
    journal = journal_module.PendingChangeJournal()
    with pytest.raises(ValueError, match='label'):
        journal.record('  ')
    with pytest.raises(ValueError, match='affected count'):
        journal.record('Edit', affected_count=0)
    with pytest.raises(ValueError, match='redo requires'):
        journal.record('Edit', redo=lambda: None)


def test_journal_only_undoes_latest_supported_change_and_redoes_with_callback():
    journal = journal_module.PendingChangeJournal()
    operations = []
    journal.record('Edit A', undo=lambda: operations.append('undo A'),
                   redo=lambda: operations.append('redo A'))
    journal.record('Edit B')
    assert not journal.can_undo
    assert not journal.undo_last()
    assert operations == []

    journal.clear()
    journal.record('Edit A', undo=lambda: operations.append('undo A'),
                   redo=lambda: operations.append('redo A'))
    assert journal.can_undo
    assert journal.undo_last()
    assert operations == ['undo A']
    assert journal.summary.count == 0
    assert journal.can_redo
    assert journal.redo_last()
    assert operations == ['undo A', 'redo A']
    assert journal.summary.count == 1


def test_failed_undo_preserves_pending_change_and_new_edit_clears_redo():
    journal = journal_module.PendingChangeJournal()

    def failed_undo():
        raise RuntimeError('undo failed')

    journal.record('Broken inverse', undo=failed_undo)
    with pytest.raises(RuntimeError, match='undo failed'):
        journal.undo_last()
    assert journal.summary.count == 1

    journal.clear()
    journal.record('Reversible', undo=lambda: None, redo=lambda: None)
    assert journal.undo_last()
    assert journal.can_redo
    journal.record('New edit')
    assert not journal.can_redo


def test_context_distinguishes_backup_recommended_and_read_only():
    context = context_module.WorkspaceContext()
    context.finish_load(
        _identity(),
        backup=context_module.BackupState(recommended=True),
    )
    assert context.snapshot.save_state is shell_state.ShellState.BACKUP_RECOMMENDED
    context.set_pending_changes(journal_module.PendingChangeJournal().summary)
    assert context.snapshot.save_state is shell_state.ShellState.BACKUP_RECOMMENDED
    context.set_pending_changes(context_module.PendingChangesSummary(1, 'Edit'))
    assert context.snapshot.save_state is shell_state.ShellState.DIRTY
    context.begin_save()
    assert context.snapshot.save_state is shell_state.ShellState.SAVING
    context.finish_save(False)
    assert context.snapshot.save_state is shell_state.ShellState.ERROR
    assert context.snapshot.pending_changes.count == 1

    read_only = context_module.WorkspaceContext()
    read_only.finish_load(_identity(read_only=True))
    assert read_only.snapshot.save_state is shell_state.ShellState.READ_ONLY
    read_only.begin_save()
    assert read_only.snapshot.save_state is shell_state.ShellState.READ_ONLY
