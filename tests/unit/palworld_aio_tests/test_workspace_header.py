from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


header_mod = import_from('palworld_aio.ui.chrome.workspace_header')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_save_context_states_and_accessibility(app):
    control = header_mod.SaveContextControl()
    for state in ('no_save', 'loading', 'loaded', 'dirty', 'saving', 'error'):
        control.set_context(state, 'Local World', 'Steam')
        assert control.state == state
        assert control.property('saveState') == state
        assert control.accessibleName() == 'Save context: Local World'
        assert control.accessibleDescription() == 'Steam'
        assert not control.icon().isNull()
    with pytest.raises(ValueError):
        control.set_context('unknown', 'World')


def test_breadcrumb_context_emits_stable_identifier(app):
    bar = header_mod.BreadcrumbBar()
    seen = []
    bar.activated.connect(seen.append)
    bar.set_items([
        header_mod.ContextItem('world', 'World'),
        header_mod.ContextItem('player:1', 'Hathaway', 'player'),
    ])
    bar._buttons['player:1'].click()
    assert seen == ['player:1']
    assert bar._buttons['player:1'].accessibleName() == 'Player: Hathaway'


def test_pending_changes_never_hides_state(app):
    pending = header_mod.PendingChangesButton()
    assert pending.count == 0
    assert pending.text() == 'No pending changes'
    pending.set_count(2)
    assert pending.count == 2
    assert pending.property('hasChanges') is True
    assert pending.accessibleName() == '2 pending changes'
    with pytest.raises(ValueError):
        pending.set_count(-1)


def test_notification_host_owns_and_clears_widgets(app):
    host = header_mod.NotificationHost()
    notice = QLabel('Saved')
    host.add_notification(notice)
    assert notice.parent() is host
    assert host.layout().count() == 1
    host.clear_notifications()
    assert host.layout().count() == 0


def test_default_and_minimum_width_keep_priority_actions_reachable(app):
    host = QWidget()
    host_layout = QVBoxLayout(host)
    header = header_mod.WorkspaceHeader('Players', 'Browse and manage players')
    host_layout.addWidget(header)
    header.set_context_items([
        header_mod.ContextItem('save', 'Local World', 'save'),
        header_mod.ContextItem('player', 'Hathaway', 'player'),
    ])
    primary = header.add_action('save', 'Save Changes', primary=True, icon='save')
    optional = header.add_action('export', 'Export', icon='export')

    host.resize(1450, 160)
    host.show()
    app.processEvents()
    assert not header.compact
    assert primary.isVisibleTo(header)
    assert optional.isVisibleTo(header)
    assert not header.overflow_button.isVisibleTo(header)

    host.resize(1024, 160)
    app.processEvents()
    assert header.compact
    assert primary.isVisibleTo(header)
    assert not optional.isVisibleTo(header)
    assert header.overflow_button.isVisibleTo(header)
    assert header._overflow_actions['export'].text() == 'Export'
    assert header.title_label.text() == 'Players'
    assert header.save_context.isVisibleTo(header)
    assert header.pending_changes.isVisibleTo(header)


def test_workspace_action_ids_are_unique(app):
    header = header_mod.WorkspaceHeader('Tools')
    header.add_action('run', 'Run')
    with pytest.raises(ValueError):
        header.add_action('run', 'Run again')
