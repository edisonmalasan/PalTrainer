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


def test_multi_selection_shows_counted_single_row_with_overflow(editor):
    from PyQt6.QtWidgets import QHBoxLayout

    editor.selected_pal_slot = ('palbox', 0)
    editor._multi_selected = {('palbox', 1)}
    editor._update_multi_toolbar()

    assert editor.multi_toolbar.isHidden() is False
    assert isinstance(editor.multi_toolbar.layout(), QHBoxLayout)
    assert editor.multi_count_label.text() == '2 pals selected'
    assert editor.multi_toolbar.accessibleName() == 'Actions for 2 selected Pals'
    assert editor.multi_heal_btn.property('actionTier') == 'safe'
    assert editor.multi_delete_btn.property('actionTier') == 'destructive'
    assert editor.multi_delete_separator.isHidden() is False
    assert editor.multi_more_btn.isHidden() is False
    for name in (
        'multi_max_btn', 'multi_buff_btn', 'multi_skills_btn',
        'multi_rename_btn',
    ):
        button = editor._multi_action_buttons[name]
        assert button.isHidden() is True
        assert button.property('actionTier') == 'bulk'
        assert button.accessibleDescription() == '2 selected Pals are affected.'
        assert callable(editor._multi_overflow_handlers[name])
    for action in (
        editor.restore_all_btn, editor.max_all_btn, editor.max_buff_all_btn,
        editor.all_skills_all_btn, editor.sort_btn, editor.select_all_btn,
        editor.bulk_clone_btn, editor.bulk_delete_separator,
        editor.bulk_delete_btn,
    ):
        assert action.isHidden() is True

    editor._multi_selected.clear()
    editor.selected_pal_slot = None
    editor._update_multi_toolbar()


def test_all_multi_action_buttons_keep_their_handlers(editor):
    for button in editor._multi_action_buttons.values():
        assert button.receivers(button.clicked) >= 1
    assert editor.multi_deselect_btn.receivers(
        editor.multi_deselect_btn.clicked) >= 1
    assert editor.multi_more_btn.receivers(editor.multi_more_btn.clicked) >= 1
    for button in (
        editor.restore_all_btn, editor.max_all_btn, editor.max_buff_all_btn,
        editor.all_skills_all_btn, editor.sort_btn, editor.select_all_btn,
        editor.bulk_clone_btn, editor.bulk_delete_btn,
    ):
        assert button.receivers(button.clicked) >= 1


def test_overflow_selection_dispatches_the_existing_handler(editor, monkeypatch):
    menu_mod = import_from('palworld_aio.widgets.scrollable_context_menu')
    seen = []

    class _Menu:
        def __init__(self, _parent):
            self.items = []

        def add_item(self, key, text):
            self.items.append((key, text))

        def exec(self, _position):
            assert [key for key, _text in self.items] == [
                'multi_max_btn', 'multi_buff_btn', 'multi_skills_btn',
                'multi_rename_btn',
            ]
            return 'multi_max_btn'

    original = editor._multi_overflow_handlers['multi_max_btn']
    editor._multi_overflow_handlers['multi_max_btn'] = lambda: seen.append('max')
    monkeypatch.setattr(menu_mod, 'ScrollableContextMenu', _Menu)

    editor._open_multi_overflow()

    assert seen == ['max']
    editor._multi_overflow_handlers['multi_max_btn'] = original


def test_cancelled_destructive_bulk_action_preserves_selection(
        editor, monkeypatch):
    first = {'key': {'InstanceId': {'value': 'pal-one'}}, 'data': {}}
    second = {'key': {'InstanceId': {'value': 'pal-two'}}, 'data': {}}
    editor.palbox_pal_dict = {0: first, 1: second}
    editor.selected_pal_slot = ('palbox', 0)
    editor._multi_selected = {('palbox', 1)}
    monkeypatch.setattr(editor_widget_mod, 'show_question', lambda *_args: False)

    editor._on_bulk_delete_selected()

    assert editor.palbox_pal_dict == {0: first, 1: second}
    assert editor.selected_pal_slot == ('palbox', 0)
    assert editor._multi_selected == {('palbox', 1)}
    editor.palbox_pal_dict = {}
    editor.selected_pal_slot = None
    editor._multi_selected.clear()
    editor._update_multi_toolbar()


def test_editor_has_source_collection_and_responsive_inspector_regions(editor):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QSplitter

    assert isinstance(editor.workspace_splitter, QSplitter)
    assert isinstance(editor.collection_splitter, QSplitter)
    assert editor.party_panel.parent() is editor.collection_splitter
    assert editor.palbox_panel.parent() is editor.collection_splitter
    assert editor.collection_splitter.parent() is editor.workspace_splitter
    assert editor.inspector_host.parent() is editor.workspace_splitter
    assert editor.pal_info.parent() is editor.inspector_host
    assert editor.inspector_host.accessibleName() == 'Selected Pal inspector'

    editor.resize(900, 700)
    editor._apply_responsive_layout()
    assert editor.workspace_splitter.orientation() == Qt.Orientation.Vertical
    assert editor.inspector_host.property('responsiveMode') == 'stacked'
    editor.resize(1200, 700)
    editor._apply_responsive_layout()
    assert editor.workspace_splitter.orientation() == Qt.Orientation.Horizontal
    assert editor.inspector_host.property('responsiveMode') == 'side-by-side'


def test_editor_source_modes_use_shared_chips_and_preserve_switch_contract(
        editor):
    assert editor.source_label.text() == 'Source'
    assert editor.mode_box_btn.property('controlRole') == 'chip'
    assert editor.mode_dps_btn.property('controlRole') == 'chip'
    assert editor.mode_box_btn.property('pickerSelected') == 'true'
    editor._clicked_pal = object()
    editor.selected_pal_slot = ('palbox', 0)

    editor._set_palbox_mode('dps')

    assert editor._palbox_mode == 'dps'
    assert editor._clicked_pal is None
    assert editor.selected_pal_slot is None
    editor._set_palbox_mode('box')


def test_editable_slots_use_shared_pal_card_semantics(editor):
    cards_mod = import_from('palworld_aio.ui.chrome.content_cards')
    party_slot = editor.party_slots[0]
    palbox_slot = editor.palbox_slots[0]

    assert isinstance(party_slot._card_model, cards_mod.PalCardModel)
    assert isinstance(palbox_slot._card_model, cards_mod.PalCardModel)
    assert party_slot.property('cardRole') == 'pal'
    assert palbox_slot.property('cardRole') == 'pal'
    assert party_slot.property('empty') is True
    assert palbox_slot.property('empty') is True
    assert party_slot.accessibleName() == 'Empty party slot'
    assert palbox_slot.accessibleName() == 'Empty Palbox slot'
    assert party_slot.styleSheet() == ''
    assert palbox_slot.styleSheet() == ''


def test_party_selection_keeps_selected_pal_identity(editor, monkeypatch):
    selected_pal = object()
    seen = []
    editor.party_pals[0] = selected_pal
    editor.party_slots[0].pal_data = selected_pal
    monkeypatch.setattr(
        editor.pal_info, 'set_clicked_pal', lambda pal: seen.append(pal))

    editor._on_party_slot_clicked(0)

    assert editor.selected_pal_slot == ('party', 0)
    assert editor._clicked_pal is selected_pal
    assert seen == [selected_pal]
    editor.party_pals.clear()
    editor.party_slots[0].pal_data = None
    editor._clear_party_highlight()
    editor.selected_pal_slot = None


def test_party_hp_is_readable_beside_the_visual_ratio(app):
    from PyQt6.QtCore import Qt

    party_slot_mod = import_from(
        'palworld_aio.editor.pal_editor.party_slot_widget')
    slot = party_slot_mod.PartySlotWidget({
        'data': {
            'CharacterID': {'value': 'SheepBall'},
            'Level': {'value': 12},
            'NickName': {'value': 'Mallow'},
            'Hp': {'value': {'Value': {'value': 54_000}}},
            'MaxHP': {'value': {'Value': {'value': 90_000}}},
        },
    })

    assert slot.hp_bar.isTextVisible() is False
    assert slot.hp_bar.value() == 60
    assert slot.hp_pill.objectName() == 'palHpPill'
    assert slot.hp_pill.text() == '54 / 90'
    assert slot.hp_pill.alignment() == Qt.AlignmentFlag.AlignCenter
    slot.deleteLater()


# ---------------------------------------------- 10.2 computed vs editable

def test_inspector_exposes_distinct_information_sections(info):
    assert info.identity_section.objectName() == 'palInspectorIdentitySection'
    assert info.identity_section.accessibleName() == 'Identity'
    assert info.editable_section.objectName() == 'palInspectorEditableSection'
    assert info.editable_section.accessibleName() == 'Editable values'
    assert info.computed_section.objectName() == 'palInspectorComputedSection'
    assert info.computed_section.accessibleName() == 'Computed stats'
    assert info.active_skills_frame.property(
        'inspectorSection') == 'active-skills'
    assert info.passive_container.property(
        'inspectorSection') == 'passive-skills'
    assert info.work_section.property('inspectorSection') == 'work'
    assert info.technical_section.objectName() == 'palInspectorTechnicalSection'
    assert info.instance_id_lbl.parent() is info.technical_section


def test_inspector_keeps_existing_edit_handlers_on_editable_controls(info):
    controls = (
        (info.name_lbl, '_on_name_click'),
        (info.level_num_lbl, '_on_level_click'),
        (info.ivs_hp_lbl, '_on_talent_click'),
        (info.soul_craft_lbl, '_on_soul_click'),
        (info.trust_bar, '_on_trust_click'),
    )
    for control, handler in controls:
        assert control.property('editableValue') == 'true'
        assert control.property('editHandler') == handler
        assert control.accessibleDescription() == 'Click to edit this value.'
        assert callable(getattr(info, handler))
    assert info.gender_icon.receivers(info.gender_icon.clicked) == 1
    assert info.info_boss_btn.receivers(info.info_boss_btn.clicked) == 1


def test_computed_stat_labels_carry_read_only_class(info):
    for lbl in (info.atk_lbl, info.def_lbl, info.wspd_lbl):
        assert lbl.property('computedValue') == 'true'


def test_computed_stat_labels_have_hint_tooltip(info):
    for lbl in (info.atk_lbl, info.def_lbl, info.wspd_lbl):
        assert 'Calculated from level, IVs and passives' in lbl.toolTip()
        assert 'read-only' in lbl.toolTip()
        assert 'points' in lbl.toolTip()
        assert lbl.property('editHandler') is None


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
