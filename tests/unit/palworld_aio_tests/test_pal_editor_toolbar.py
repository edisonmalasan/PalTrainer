"""Focused tests for the Pal Editor toolbar separator, computed-stat
affordance, and skill power tooltip (uiux-audit-remediation 10.1-10.3).
Widgets are constructed standalone offscreen.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

editor_widget_mod = import_from('palworld_aio.editor.pal_editor.pal_editor_widget')
info_widget_mod = import_from('palworld_aio.editor.pal_editor.pal_info_widget')
display_mod = import_from('palworld_aio.editor.pal_editor.pal_info_display')
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
    return editor_widget_mod.PalEditorWidget(None)


@pytest.fixture(scope='session')
def info(app):
    return info_widget_mod.PalInfoWidget()


# --------------------------------------------------- 10.1 toolbar separator

def _header_widgets(editor):
    layout = editor._palbox_layout.itemAt(1).layout()  # header_row FlowLayout
    widgets = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is not None and item.widget() is not None:
            widgets.append(item.widget())
    return widgets


def test_separator_exists_immediately_before_bulk_delete(editor):
    order = _header_widgets(editor)
    sep_index = order.index(editor.bulk_delete_separator)
    delete_index = order.index(editor.bulk_delete_btn)
    assert sep_index == delete_index - 1  # immediately before bulk delete
    # bulk clone sits on the other side of the separator (tier isolation)
    assert order[sep_index - 1] is editor.bulk_clone_btn


def test_separator_styled_via_qss_not_inline(editor):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    built = qss_mod.build_qss('dark')
    assert 'QFrame#toolbarTierSep' in built
    assert editor.bulk_delete_separator.objectName() == 'toolbarTierSep'
    # no inline colour stylesheet on the separator
    assert 'background' not in editor.bulk_delete_separator.styleSheet()
    assert editor.bulk_delete_separator.styleSheet() == ''


def test_button_tiers_and_handlers_unchanged(editor):
    assert editor.restore_all_btn.objectName() == 'warnActionBtn'
    assert editor.max_all_btn.objectName() == 'warnActionBtn'
    assert editor.max_buff_all_btn.objectName() == 'warnActionBtn'
    assert editor.all_skills_all_btn.objectName() == 'warnActionBtn'
    assert editor.sort_btn.objectName() == 'ghostBtn'
    assert editor.select_all_btn.objectName() == 'ghostBtn'
    assert editor.bulk_clone_btn.objectName() == 'warnActionBtn'
    assert editor.bulk_delete_btn.property('class') == 'danger'
    for handler in (editor._restore_all_pals, editor._max_all_pals,
                    editor._max_buff_all_pals, editor._all_skills_all_pals,
                    editor._on_sort_clicked, editor._on_select_all,
                    editor._open_bulk_clone, editor._open_bulk_delete):
        assert callable(handler)


# ---------------------------------------------- 10.2 computed vs editable

def test_computed_stat_labels_carry_read_only_class(info):
    for lbl in (info.atk_lbl, info.def_lbl, info.wspd_lbl):
        assert lbl.property('computedValue') == 'true'


def test_computed_stat_labels_have_hint_tooltip(info):
    for lbl in (info.atk_lbl, info.def_lbl, info.wspd_lbl):
        assert 'Calculated from level, IVs and passives' in lbl.toolTip()
        assert 'read-only' in lbl.toolTip()


def test_computed_class_in_built_qss(app):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    built = qss_mod.build_qss('dark')
    assert 'QLabel[computedValue="true"]' in built


def test_hp_bar_painter_untouched(info):
    assert info.hp_bar.objectName() == 'palStatBar'
    assert info.hp_bar.property('barTier') == 'success'


# -------------------------------------------------- 10.3 skill power hint

def test_skill_power_hint_key_resolves_with_unit_phrase():
    text = i18n_mod.t('pal_editor.skill_power_hint')
    assert 'used to compute damage' in text


def test_power_tooltip_wiring_appends_hint_after_power_line():
    """Regression guard: the display path appends the unit phrase into the
    tooltip parts right after the 'Power:' entry."""
    src = inspect.getsource(display_mod)
    power_pos = src.find("'Power: {skill_power}'")
    if power_pos == -1:
        power_pos = src.find("f'Power: {skill_power}'")
    assert power_pos != -1, 'Power tooltip entry missing'
    hint_pos = src.find("skill_power_hint")
    assert hint_pos != -1, 'unit phrase not wired into the tooltip'
    assert power_pos < hint_pos < power_pos + 600
