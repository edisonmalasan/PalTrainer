from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


catalog = import_from('palworld_aio.application.backup_catalog')
page_mod = import_from('palworld_aio.ui.pages.backups_page')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _record(path='C:/Backups/fixture'):
    return catalog.BackupRecord(
        'fixture', Path(path),
        datetime(2026, 9, 9, 13, 45),
        'Before Player Inventory Edit', 'Local World', 8_808_038,
    )


def test_empty_state_explains_backup_discovery_and_can_refresh(app):
    page = page_mod.BackupsPage()
    observed = []
    page.refreshRequested.connect(lambda: observed.append(True))
    assert not page.empty_state.isHidden()
    assert page.scroll.isHidden()
    assert page.count_label.text() == '0 backups'
    page.empty_state.action_button.click()
    assert observed == [True]


def test_rows_render_timestamp_reason_source_size_and_actions(app):
    record = _record()
    page = page_mod.BackupsPage()
    page.set_backups((record,))
    restored = []
    revealed = []
    page.restoreRequested.connect(restored.append)
    page.revealRequested.connect(revealed.append)
    row = page.rows[0]

    assert row.timestamp_label.text() == 'Sep 09, 2026  01:45 PM'
    assert row.reason_label.text() == 'Before Player Inventory Edit'
    assert row.source_badge.text() == 'Local World'
    assert row.size_label.text() == '8.4 MB'
    row.reveal_button.click()
    row.restore_button.click()
    assert revealed == [str(record.path)]
    assert restored == [record]


def test_progress_blocks_restore_then_result_reenables_actions(app):
    page = page_mod.BackupsPage()
    page.set_backups((_record(),))
    page.set_loading('Creating safety backup')
    assert not page.progress.isHidden()
    assert page.progress.message_label.text() == 'Creating safety backup'
    assert not page.rows[0].restore_button.isEnabled()
    assert not page.refresh_button.isEnabled()

    page.set_result(True, 'Backup restored safely')
    assert page.progress.isHidden()
    assert page.result_banner is not None
    assert page.result_banner.message_label.text() == 'Backup restored safely'
    assert page.rows[0].restore_button.isEnabled()
    assert page.refresh_button.isEnabled()


def test_rows_remain_readable_at_compact_width(app):
    page = page_mod.BackupsPage()
    page.set_backups((_record(), _record('C:/Backups/second')))
    page.resize(620, 650)
    page.show()
    app.processEvents()
    assert len(page.rows) == 2
    assert not page.grab().isNull()
