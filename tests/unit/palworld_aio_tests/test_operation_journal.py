from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from tests.dynamic_importer import import_from


journal_mod = import_from('palworld_aio.ui.operation_journal')


def test_journal_is_chronological_bounded_and_clearable():
    now = datetime(2026, 9, 9, 20, 0)
    ticks = iter(now + timedelta(minutes=value) for value in range(4))
    journal = journal_mod.OperationJournal(max_events=3, clock=lambda: next(ticks))
    observed = []
    journal.changed.connect(observed.append)
    for title in ('Load', 'Backup', 'Mutation', 'Save'):
        journal.record(journal_mod.ActivityKind.SAVE, title)
    assert [event.title for event in journal.events] == [
        'Backup', 'Mutation', 'Save']
    assert [event.occurred_at for event in journal.events] == sorted(
        event.occurred_at for event in journal.events)
    assert observed[-1] == journal.events
    journal.clear()
    assert journal.events == ()


def test_undo_exists_only_with_real_callback_and_runs_once():
    journal = journal_mod.OperationJournal()
    calls = []
    plain = journal.record(journal_mod.ActivityKind.LOAD, 'Loaded')
    reversible = journal.record(
        journal_mod.ActivityKind.MUTATION, 'Renamed player',
        undo=lambda: calls.append('undo'))
    assert not plain.can_undo
    assert reversible.can_undo
    assert not journal.undo_event(plain.event_id)
    assert journal.undo_event(reversible.event_id)
    assert calls == ['undo']
    assert journal.events[-1].status is journal_mod.ActivityStatus.UNDONE
    assert not journal.events[-1].can_undo
    assert not journal.undo_event(reversible.event_id)


def test_journal_validates_capacity_and_titles():
    with pytest.raises(ValueError, match='positive'):
        journal_mod.OperationJournal(max_events=0)
    with pytest.raises(ValueError, match='title'):
        journal_mod.OperationJournal().record(
            journal_mod.ActivityKind.FAILURE, '  ')
