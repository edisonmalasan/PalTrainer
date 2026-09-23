from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


overview_mod = import_from('palworld_aio.ui.pages.overview_page')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _model():
    return overview_mod.LoadedOverviewModel(
        save_name='Local World',
        platform='Steam',
        modified_at='4 minutes ago',
        backup_label='Backup available',
        pending_changes=2,
        counts={'players': 1, 'guilds': 2, 'bases': 3, 'pals': 220},
        activity=(
            overview_mod.OverviewActivityItem('Save loaded', 'Today', 'success'),
            overview_mod.OverviewActivityItem('Backup created', '8.4 MB', 'success'),
        ),
    )


def test_loaded_fixture_renders_identity_safety_counts_and_activity(app):
    page = overview_mod.OverviewPage()
    page.set_loaded(_model())
    page.resize(1000, 650)
    page.show()
    app.processEvents()
    assert page.save_name_label.text() == 'Local World'
    assert page.save_detail_label.text() == 'Steam • Modified 4 minutes ago'
    assert page.backup_label.text() == 'Backup available'
    assert page.pending_label.text() == '2 pending changes'
    assert page.metric_cards['pals'].text().startswith('220')
    assert page.activity_layout.count() == 2
    assert not page.grab().isNull()


def test_metrics_and_quick_actions_emit_routes(app):
    page = overview_mod.OverviewPage()
    page.set_loaded(_model())
    observed = []
    page.navigateRequested.connect(observed.append)
    page.metric_cards['players'].click()
    page.quick_buttons['base_inventory'].click()
    assert observed == ['players', 'base_inventory']


def test_metric_layout_is_responsive(app):
    page = overview_mod.OverviewPage()
    page.set_loaded(_model())
    page.resize(700, 650)
    page.show()
    app.processEvents()
    assert page._metric_columns == 2
    page.resize(1000, 650)
    app.processEvents()
    assert page._metric_columns == 4


def test_negative_pending_changes_are_rejected(app):
    model = _model()
    with pytest.raises(ValueError, match='cannot be negative'):
        overview_mod.OverviewPage().set_loaded(
            overview_mod.LoadedOverviewModel(
                model.save_name, model.platform, model.modified_at,
                model.backup_label, -1, model.counts,
            ))


def test_context_summary_updates_safety_state_without_losing_metrics(app):
    page = overview_mod.OverviewPage()
    page.set_loaded(_model())
    page.update_context_summary(
        pending_changes=4,
        backup_label='Backup recommended',
    )
    assert page.pending_label.text() == '4 pending changes'
    assert page.backup_label.text() == 'Backup recommended'
    assert page.metric_cards['pals'].text().startswith('220')


def test_no_save_state_exposes_open_drop_recent_and_standalone_actions(app):
    page = overview_mod.OverviewPage()
    page.set_no_save((
        overview_mod.RecentSaveEntry(
            'world-1', 'Island', 'C:/Saves/Island', available=True),
        overview_mod.RecentSaveEntry(
            'world-2', 'Old Server', 'D:/Missing', available=False),
    ))
    observed = []
    page.openSaveRequested.connect(lambda: observed.append(('file', '')))
    page.openFolderRequested.connect(lambda: observed.append(('folder', '')))
    page.recentSaveRequested.connect(lambda value: observed.append(('recent', value)))
    page.locateRecentRequested.connect(lambda value: observed.append(('locate', value)))
    page.removeRecentRequested.connect(lambda value: observed.append(('remove', value)))
    page.utilityRequested.connect(lambda value: observed.append(('utility', value)))

    page.open_save_button.click()
    page.open_folder_button.click()
    page.recent_rows['world-1'].findChildren(overview_mod.QPushButton)[0].click()
    invalid_buttons = page.recent_rows['world-2'].findChildren(
        overview_mod.QPushButton)
    invalid_buttons[0].click()
    invalid_buttons[1].click()
    page.utility_buttons['convert_saves'].click()

    assert observed == [
        ('file', ''), ('folder', ''), ('recent', 'C:/Saves/Island'),
        ('locate', 'world-2'), ('remove', 'world-2'),
        ('utility', 'convert_saves'),
    ]
    assert 'Drop a Level.sav' in page.findChild(
        overview_mod.QLabel, 'overviewDropHint').text()


def test_no_save_recent_empty_and_compact_utility_layout(app):
    page = overview_mod.OverviewPage()
    page.set_no_save(())
    assert page.stack.currentWidget() is page.no_save_view
    assert page.findChild(overview_mod.QLabel, 'overviewRecentEmpty') is not None
    page.resize(700, 650)
    page.show()
    app.processEvents()
    assert page._utility_columns == 1
