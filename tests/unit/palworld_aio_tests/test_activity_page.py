from __future__ import annotations

import os
from datetime import datetime

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.activity_page')
journal_mod = import_from('palworld_aio.ui.operation_journal')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _journal():
    return journal_mod.OperationJournal(
        clock=lambda: datetime(2026, 9, 9, 23, 41))


def test_empty_activity_explains_future_events_and_clear_is_disabled(app):
    page = page_mod.ActivityPage(_journal())
    assert not page.empty_state.isHidden()
    assert page.scroll.isHidden()
    assert page.empty_state.title_label.text() == 'No activity yet'
    assert 'Loads, backups, changes' in page.empty_state.message_label.text()
    assert not page.clear_button.isEnabled()


def test_page_renders_load_backup_mutation_save_and_failure_in_order(app):
    journal = _journal()
    page = page_mod.ActivityPage(journal)
    fixtures = (
        (journal_mod.ActivityKind.LOAD, 'Save loaded', journal_mod.ActivityStatus.SUCCESS),
        (journal_mod.ActivityKind.BACKUP, 'Backup created', journal_mod.ActivityStatus.SUCCESS),
        (journal_mod.ActivityKind.MUTATION, 'Inventory changed', journal_mod.ActivityStatus.WARNING),
        (journal_mod.ActivityKind.SAVE, 'Changes saved', journal_mod.ActivityStatus.SUCCESS),
        (journal_mod.ActivityKind.FAILURE, 'Save failed', journal_mod.ActivityStatus.FAILED),
    )
    for kind, title, status in fixtures:
        journal.record(kind, title, context='Island', status=status, detail='Fixture detail')
    assert [row.event.title for row in page.rows] == [item[1] for item in fixtures]
    assert page.count_label.text() == '5 events'
    assert page.clear_button.isEnabled()
    page.rows[0].detail_button.click()
    assert not page.rows[0].detail_label.isHidden()


def test_undo_button_only_appears_for_supported_event_and_clear_empties(app):
    journal = _journal()
    page = page_mod.ActivityPage(journal)
    calls = []
    journal.record(journal_mod.ActivityKind.LOAD, 'Loaded')
    journal.record(
        journal_mod.ActivityKind.MUTATION, 'Changed', undo=lambda: calls.append(True))
    assert page.rows[0].undo_button is None
    assert page.rows[1].undo_button is not None
    page.rows[1].undo_button.click()
    assert calls == [True]
    assert page.rows[1].undo_button is None
    page.clear_button.click()
    assert journal.events == ()
    assert page.rows == []
