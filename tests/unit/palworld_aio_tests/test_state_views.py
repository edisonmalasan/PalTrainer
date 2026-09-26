from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


states = import_from('palworld_aio.ui.chrome.state_views')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ('factory', 'kind', 'title', 'action'),
    [
        (lambda: states.PrerequisiteState('Choose a player', 'Player context is required.', 'Choose Player'), 'prerequisite', 'Choose a player', 'Choose Player'),
        (lambda: states.ConfiguredEmptyState('No exclusions', 'This save has no exclusions.', 'Add Exclusion'), 'configured_empty', 'No exclusions', 'Add Exclusion'),
        (lambda: states.NoResultState('No matches', 'No players match the active filters.'), 'no_result', 'No matches', 'Clear filters'),
        (lambda: states.ErrorState('Could not load players', 'Check the save and try again.'), 'error', 'Could not load players', 'Retry'),
    ],
)
def test_state_types_have_distinct_copy_and_actions(app, factory, kind, title, action):
    view = factory()
    assert view.property('stateKind') == kind
    assert view.title_label.text() == title
    assert view.message_label.text()
    assert view.action_button.text() == action
    assert view.action_button.accessibleName() == action
    assert view.accessibleName() == title


def test_state_primary_action_emits(app):
    view = states.ErrorState('Failed', 'Try again')
    seen = []
    view.actionTriggered.connect(lambda: seen.append(True))
    view.action_button.click()
    assert seen == [True]


def test_skeleton_is_non_blank_and_validates_rows(app):
    skeleton = states.SkeletonView('Loading base containers…', rows=3)
    assert skeleton.property('stateKind') == 'loading'
    assert skeleton.status_label.text() == 'Loading base containers…'
    assert len(skeleton.rows) == 3
    with pytest.raises(ValueError):
        states.SkeletonView(rows=0)


def test_blocking_progress_supports_indeterminate_determinate_and_cancel(app):
    progress = states.BlockingProgress('Saving', 'Preparing backup…', cancelable=True)
    assert progress.progress.minimum() == 0 and progress.progress.maximum() == 0
    progress.set_progress(2, 5, 'Writing entities…')
    assert progress.progress.maximum() == 5
    assert progress.progress.value() == 2
    assert progress.message_label.text() == 'Writing entities…'
    seen = []
    progress.cancelRequested.connect(lambda: seen.append(True))
    progress.cancel_button.click()
    assert seen == [True]
    with pytest.raises(ValueError):
        progress.set_progress(-1, 5)


def test_operation_results_are_semantically_distinct(app):
    success = states.OperationResultState(True, 'Save complete', 'Backup and save succeeded.')
    failure = states.OperationResultState(False, 'Save failed', 'The original save was preserved.', 'View recovery')
    assert success.success is True
    assert success.property('stateKind') == 'operation_success'
    assert failure.success is False
    assert failure.property('stateKind') == 'operation_error'
    assert failure.action_button.text() == 'View recovery'


@pytest.mark.parametrize('level', ['success', 'warning', 'danger', 'info'])
def test_notification_levels_are_accessible_and_dismissible(app, level):
    banner = states.NotificationBanner('Operation finished', level, 'Details')
    assert banner.property('level') == level
    assert banner.accessibleName().startswith(level.title())
    assert banner.action_button.text() == 'Details'
    seen = []
    banner.dismissed.connect(lambda: seen.append(True))
    banner.close_button.click()
    assert banner.isHidden()
    assert seen == [True]


def test_notification_rejects_unknown_semantic_level(app):
    with pytest.raises(ValueError):
        states.NotificationBanner('Nope', 'purple')
