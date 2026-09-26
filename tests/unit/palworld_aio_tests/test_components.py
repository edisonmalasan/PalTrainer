from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

components = import_from('palworld_aio.ui.chrome.components')
qss_builder = import_from('palworld_aio.ui.chrome.qss_builder')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture
def app():
    return _app_instance()


def test_button_kinds(app):
    for kind in ('default', 'primary', 'danger', 'ghost', 'tool'):
        btn = components.make_button('Go', kind)
        assert btn.property('class') == (kind if kind != 'default' else None)
        assert btn.accessibleName() == 'Go'
    assert components.make_button('Save').property('class') is None


@pytest.mark.parametrize(
    ('kind', 'role'),
    [
        ('primary', 'primary'),
        ('secondary', 'secondary'),
        ('tertiary', 'tertiary'),
        ('warning', 'warning'),
        ('destructive', 'destructive'),
    ],
)
def test_canonical_button_tiers_are_accessible(app, kind, role):
    from PyQt6.QtCore import Qt

    button = components.make_button('Apply', kind, tooltip='Apply the change')
    assert button.property('class') == kind
    assert button.property('controlRole') == role
    assert button.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert button.accessibleName() == 'Apply'
    assert button.accessibleDescription() == 'Apply the change'
    assert button.toolTip() == 'Apply the change'


def test_unknown_button_tier_is_rejected(app):
    with pytest.raises(ValueError):
        components.make_button('Nope', 'mystery')


def test_icon_button_uses_vector_icon_and_accessible_help(app):
    from PyQt6.QtCore import Qt

    button = components.make_tool_button('close', 'Close panel')
    assert button.property('class') == 'icon'
    assert button.property('controlRole') == 'icon'
    assert button.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert button.accessibleName() == 'Close panel'
    assert button.toolTip() == 'Close panel'
    assert not button.icon().isNull()


def test_segmented_control_is_exclusive_and_emits_ids(app):
    control = components.SegmentedControl(
        [('all', 'All'), ('safe', 'Safe'), ('risky', 'Risky')],
        current='safe',
        accessible_name='Risk filter',
    )
    seen = []
    control.currentChanged.connect(seen.append)

    assert control.current() == 'safe'
    assert control.accessibleName() == 'Risk filter'
    assert all(button.isCheckable() for button in control._buttons.values())
    control._buttons['risky'].click()
    assert control.current() == 'risky'
    assert seen == ['risky']
    control.set_current('all')
    assert control.current() == 'all'
    assert seen == ['risky', 'all']
    with pytest.raises(KeyError):
        control.set_current('missing')


def test_segmented_control_rejects_invalid_options(app):
    with pytest.raises(ValueError):
        components.SegmentedControl([])
    with pytest.raises(ValueError):
        components.SegmentedControl([('same', 'A'), ('same', 'B')])
    with pytest.raises(ValueError):
        components.SegmentedControl([('one', 'One')], current='two')


@pytest.mark.parametrize(
    ('factory', 'role'),
    [
        (lambda: components.make_chip('Loaded', checked=True), 'chip'),
        (lambda: components.make_filter_button('Warnings', checked=True), 'filter'),
        (lambda: components.make_tab_button('Players', 'players', checked=True), 'tab'),
    ],
)
def test_checkable_control_primitives(factory, role, app):
    from PyQt6.QtCore import Qt

    button = factory()
    assert button.property('class') == role
    assert button.property('controlRole') == role
    assert button.isCheckable() and button.isChecked()
    assert button.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert button.accessibleName()


def test_control_tooltip_has_accessible_description(app):
    from PyQt6.QtWidgets import QPushButton

    button = QPushButton('Details')
    components.set_control_tooltip(button, 'Shows the full identifier')
    assert button.toolTip() == 'Shows the full identifier'
    assert button.accessibleDescription() == 'Shows the full identifier'
    with pytest.raises(ValueError):
        components.set_control_tooltip(button, ' ')


def test_shared_control_qss_defines_all_applicable_states():
    qss = qss_builder.build_qss('dark')
    for tier in ('primary', 'secondary', 'tertiary', 'warning', 'destructive', 'icon'):
        for state in ('hover', 'pressed', 'checked', 'focus', 'disabled'):
            assert f'QPushButton[class="{tier}"]:{state}' in qss
    for tier in ('segmented', 'chip', 'filter', 'tab'):
        for state in ('hover', 'pressed', 'checked', 'focus', 'disabled'):
            assert f'[class="{tier}"]:{state}' in qss


def test_badge_levels(app):
    badge = components.make_badge('3', 'danger')
    assert badge.property('badge') == 'danger'
    components.set_badge_level(badge, 'bogus')
    assert badge.property('badge') == 'neutral'


def test_status_dot_levels(app):
    dot = components.make_status_dot('success')
    assert dot.property('level') == 'success'
    components.set_dot_level(dot, 'info')
    assert dot.property('level') == 'info'


def test_search_field_emits(app):
    seen = []
    _, line = components.make_search_field('Find', on_change=seen.append)
    line.setText('abc')
    assert seen == ['abc']
    assert line.accessibleName() == 'Find'


def test_error_banner_toggle(app):
    banner = components.ErrorBanner()
    assert banner.isHidden()
    banner.show_error('bad thing')
    assert not banner.isHidden()
    banner.clear()
    assert banner.isHidden()


def test_bulk_workflow_review_tracks_context_risk_progress_and_result(app):
    review = components.BulkWorkflowReview(
        source='Ancient Core',
        target='3 selected players',
        review='Add 10 items to each inventory.',
    )
    review.set_risk('Existing values may be replaced.', 'Backup available.')
    review.set_progress(2, 3, 'Applying 2 of 3')
    review.set_result('Updated 3 players.')

    assert review.source_value.text() == 'Ancient Core'
    assert review.target_value.text() == '3 selected players'
    assert review.review_value.text() == 'Add 10 items to each inventory.'
    assert review.property('riskVariant') == 'destructive'
    assert review.risk_label.isHidden() is False
    assert review.backup_label.isHidden() is False
    assert review.progress.maximum() == 3
    assert review.progress.value() == 2
    assert review.result_label.property('resultState') == 'success'


def test_base_dialog_scaffold(app):
    dialog = components.BaseDialog('Title', min_size=(400, 200))
    assert dialog.title_label.text() == 'Title'
    dialog.add_confirm_button('Apply')
    assert dialog.cancel_btn.text() == 'Cancel'
    dialog.cancel_btn.click()
    assert dialog.result() == 0  # Rejected


def test_message_dialog_preserves_standard_button_results(app):
    from PyQt6.QtCore import QTimer

    dialog = components.MessageDialog()
    dialog.setWindowTitle('Confirm')
    dialog.setText('Apply this change?')
    dialog.setIcon(dialog.Question)
    dialog.setStandardButtons(dialog.Yes | dialog.No)
    dialog.setDefaultButton(dialog.No)
    QTimer.singleShot(0, dialog._standard_buttons[dialog.Yes].click)

    assert dialog.exec() == dialog.Yes
    assert dialog.clickedButton() is dialog._standard_buttons[dialog.Yes]
    assert dialog.title_label.text() == 'Confirm'
    assert dialog.accessibleDescription() == 'Apply this change?'


def test_input_prompt_dialog_preserves_integer_contract(app):
    from PyQt6.QtCore import QTimer

    dialog = components.InputPromptDialog()
    dialog.setWindowTitle('Slots')
    dialog.setLabelText('New slot count')
    dialog.setInputMode(dialog.IntInput)
    dialog.setIntRange(1, 100)
    dialog.setIntStep(5)
    dialog.setIntValue(40)
    QTimer.singleShot(0, dialog.confirm_btn.click)

    assert dialog.exec() == dialog.DialogCode.Accepted
    assert dialog.intValue() == 40
    assert dialog.int_input.singleStep() == 5


def test_dialog_minimum_size_footer_roles_and_risk_variant(app):
    dialog = components.BaseDialog('Delete Pals', min_size=(200, 100), danger=True)
    secondary = dialog.add_secondary_button('Preview', lambda: None)
    destructive = dialog.add_confirm_button('Delete 12 Pals', danger=True)
    assert dialog.minimumWidth() >= 400
    assert dialog.property('riskVariant') == 'destructive'
    assert secondary.property('actionRole') == 'secondary'
    assert destructive.property('actionRole') == 'destructive'
    assert dialog.danger_slot.indexOf(destructive) >= 0
    assert destructive.property('class') == 'destructive'


def test_dialog_escape_can_close_or_be_safely_disabled(app):
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import Qt

    closable = components.BaseDialog('Closable')
    closable.show()
    closable.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert closable.result() == 0

    blocked = components.BaseDialog('Saving', escape_enabled=False)
    blocked.show()
    blocked.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert blocked.isVisible()
    blocked.reject()


def test_dialog_focus_is_contained_and_restored(app):
    from PyQt6.QtWidgets import QPushButton, QWidget

    host = QWidget()
    invoker = QPushButton('Open', host)
    host.show()
    invoker.show()
    invoker.setFocus()
    app.processEvents()
    dialog = components.BaseDialog('Edit', parent=host)
    confirm = dialog.add_confirm_button('Apply')
    restored = []
    dialog.focusRestored.connect(restored.append)
    dialog.show()
    app.processEvents()
    assert confirm.hasFocus()
    dialog.focusNextPrevChild(True)
    assert app.focusWidget() is not None
    assert app.focusWidget().window() is dialog
    dialog.reject()
    app.processEvents()
    assert restored == [invoker]


def test_drawer_focus_escape_and_risk_contract(app):
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QPushButton, QWidget

    host = QWidget()
    invoker = QPushButton('Inspect', host)
    drawer = components.Drawer('Player details', host)
    field = QPushButton('Edit name', drawer)
    drawer.content_layout.addWidget(field)
    host.show()
    invoker.show()
    invoker.setFocus()
    restored = []
    drawer.focusRestored.connect(restored.append)
    drawer.set_risk_variant('warning')
    drawer.open(invoker)
    app.processEvents()
    assert drawer.property('riskVariant') == 'warning'
    assert app.focusWidget().window() is host
    drawer.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    app.processEvents()
    assert drawer.isHidden()
    assert restored == [invoker]
    with pytest.raises(ValueError):
        drawer.set_risk_variant('unknown')


def test_data_table_empty_state(app):
    table = components.DataTable(['Name', 'Count'])
    table.set_empty_state('Nothing here')
    assert not table.table.isVisible()
    table.set_empty_state('')
    table.set_empty_state('Still nothing')
