"""Focused tests for the Pal Editor jump-to-box control
(uiux-audit-remediation 7.5 / audit Phase 3.3). The editor is constructed
standalone offscreen; no save is loaded, so the palbox is empty and the
navigation core is exercised directly.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

widget_mod = import_from('palworld_aio.editor.pal_editor.pal_editor_widget')
i18n_mod = import_from('i18n')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture(scope='session')
def app():
    return _app_instance()


@pytest.fixture(scope='session')
def editor(app):
    return widget_mod.PalEditorWidget(None)


# ------------------------------------------- 7.5 control presence

def test_jump_spin_exists_with_tooltip(editor):
    from PyQt6.QtWidgets import QSpinBox
    assert isinstance(editor.box_jump_spin, QSpinBox)
    assert editor.box_jump_spin.objectName() == 'boxJumpSpin'
    assert editor.box_jump_spin.toolTip() == 'Jump to box'
    assert editor.box_jump_spin.accessibleName() == 'Jump to box'


def test_jump_spin_styled_via_qss_not_inline(editor):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    built = qss_mod.build_qss('dark')
    assert 'QSpinBox#boxJumpSpin' in built
    assert editor.box_jump_spin.styleSheet() == ''


def test_jump_i18n_key_present():
    assert i18n_mod.t('pal_editor.jump_to_box') == 'Jump to box'


# ------------------------------------------- _goto_box navigation core

def test_goto_box_navigates_and_clears_state(editor):
    editor.current_box_index = 1
    editor.total_slots = 90  # 3 boxes
    editor._clicked_pal = object()
    editor.selected_pal_slot = ('palbox', 0)
    editor._goto_box(3)
    assert editor.current_box_index == 3
    assert editor._clicked_pal is None
    assert editor.selected_pal_slot is None
    assert 'Box 3' in editor.box_label.text()
    editor._goto_box(2)
    assert editor.current_box_index == 2
    assert 'Box 2' in editor.box_label.text()


def test_goto_box_clamps_out_of_range(editor):
    editor.total_slots = 90
    editor._goto_box(99)
    assert editor.current_box_index == 3
    editor._goto_box(0)
    assert editor.current_box_index == 1


# ------------------------------------------- spin sync

def test_spin_max_tracks_get_max_box(editor):
    editor.total_slots = 120  # 4 boxes
    editor._update_box_label()
    assert editor.box_jump_spin.maximum() == editor._get_max_box() == 4
    editor.total_slots = 60  # 2 boxes
    editor._update_box_label()
    assert editor.box_jump_spin.maximum() == 2
    editor.total_slots = 0
    editor._update_box_label()
    assert editor.box_jump_spin.maximum() == 1


def test_prev_next_keep_spin_in_sync(editor):
    editor.total_slots = 90
    editor.current_box_index = 2
    editor._update_box_label()
    assert editor.box_jump_spin.value() == 2
    editor._next_box()
    assert editor.current_box_index == 3
    assert editor.box_jump_spin.value() == 3
    editor._prev_box()
    assert editor.current_box_index == 2
    assert editor.box_jump_spin.value() == 2
    editor._prev_box()
    editor._prev_box()
    assert editor.current_box_index == 3  # wrapped 1 -> max
    assert editor.box_jump_spin.value() == 3
    editor._next_box()
    assert editor.current_box_index == 1  # wrapped max -> 1
    assert editor.box_jump_spin.value() == 1


def test_prev_next_wrapping_behavior_unchanged(editor):
    editor.total_slots = 90
    editor._goto_box(1)
    editor._next_box()
    editor._next_box()
    editor._next_box()  # at max, wraps to 1
    assert editor.current_box_index == 1
    editor._prev_box()  # at min, wraps to max
    assert editor.current_box_index == 3


def test_no_signal_loop_on_programmatic_sync(editor):
    calls = []
    editor.total_slots = 120
    editor.box_jump_spin.valueChanged.connect(calls.append)
    editor.current_box_index = 4
    editor._update_box_label()
    assert calls == []  # blocked during sync
    editor.box_jump_spin.setValue(2)  # user action -> unblocked signal
    assert calls == [2]
    assert editor.current_box_index == 2
    editor.box_jump_spin.valueChanged.disconnect(calls.append)


def test_jump_value_change_triggers_goto(editor):
    editor.total_slots = 90
    editor.current_box_index = 1
    editor.box_jump_spin.setValue(3)
    assert editor.current_box_index == 3
    assert 'Box 3' in editor.box_label.text()


# ------------------------------------------- dps-mode consistency

def test_dps_mode_uses_same_max_source(editor):
    editor._palbox_mode = 'dps'
    editor.dps_total_slots = 75  # 3 dps pages
    editor.current_box_index = 1
    editor._update_box_label()
    assert editor._get_max_box() == 3
    assert editor.box_jump_spin.maximum() == 3
    assert 'DPS 1/3' in editor.box_label.text()
    editor.box_jump_spin.setValue(3)
    assert editor.current_box_index == 3
    editor._next_box()
    assert editor.current_box_index == 1  # dps pages wrap too
    editor._palbox_mode = 'box'  # restore
    editor.dps_total_slots = 0
    editor._update_box_label()
