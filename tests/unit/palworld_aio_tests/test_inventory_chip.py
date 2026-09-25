"""Player Inventory workspace context and editor-view contracts."""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

inventory_mod = import_from('palworld_aio.ui.tabs.inventory_tab')
qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
i18n_mod = import_from('i18n')

_app = None


def test_failed_inventory_memory_save_does_not_record_pending_change():
    recorded = []
    errors = []
    emitted = []
    tab = SimpleNamespace(
        inventory=SimpleNamespace(save=lambda: False),
        current_player_uid='player-1',
        parent_window=SimpleNamespace(
            record_pending_change=lambda *args, **kwargs: recorded.append(
                (args, kwargs))),
        _save_stats_to_raw_data=lambda: None,
        _show_error=errors.append,
        saved=SimpleNamespace(emit=lambda: emitted.append(True)),
    )

    inventory_mod.PlayerInventoryTab._save_changes(tab)

    assert errors
    assert not recorded
    assert not emitted


def test_successful_inventory_memory_save_records_pending_change(monkeypatch):
    recorded = []
    emitted = []
    monkeypatch.setattr(inventory_mod.QMessageBox, 'information',
                        lambda *args, **kwargs: None)
    tab = SimpleNamespace(
        inventory=SimpleNamespace(save=lambda: True),
        current_player_uid='player-1',
        parent_window=SimpleNamespace(
            record_pending_change=lambda *args, **kwargs: recorded.append(
                (args, kwargs))),
        _save_stats_to_raw_data=lambda: None,
        saved=SimpleNamespace(emit=lambda: emitted.append(True)),
    )

    inventory_mod.PlayerInventoryTab._save_changes(tab)

    assert recorded == [
        (('Player inventory updated',), {'context': 'player-1'}),
    ]
    assert emitted == [True]


def test_player_stat_edit_records_pending_change():
    recorded = []
    tab = SimpleNamespace(
        current_player_uid='player-1',
        _save_stats_to_raw_data=lambda: None,
        _update_player_dropdown_level=lambda: None,
        parent_window=SimpleNamespace(
            record_pending_change=lambda *args, **kwargs: recorded.append(
                (args, kwargs))),
    )

    inventory_mod.PlayerInventoryTab._on_stats_changed(tab)

    assert recorded == [
        (('Player stats updated',), {'context': 'player-1'}),
    ]


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


@pytest.fixture
def tab(app):
    widget = inventory_mod.PlayerInventoryTab(None)
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_player_picker_uses_workspace_context_chip(tab):
    assert tab.context_bar.objectName() == 'editorContextBar'
    assert tab.player_select_btn.objectName() == 'workspacePlayerSelector'
    assert tab.player_select_btn.property('controlRole') == 'chip'
    assert tab.player_select_btn.property('contextKind') == 'player'


def test_player_picker_has_chevron_icon(tab):
    chevron = inventory_mod.app_icons.get_qicon('chevron_down',
                                                role='text_secondary')
    assert chevron is not None
    assert not chevron.pixmap(32, 32).isNull()
    assert not tab.player_select_btn.icon().pixmap(32, 32).isNull()
    assert (tab.player_select_btn.icon().pixmap(32, 32).toImage()
            == chevron.pixmap(32, 32).toImage())


def test_picker_selected_rule_covers_workspace_selector(app):
    qss = qss_mod.build_qss('dark')
    assert 'QPushButton#workspacePlayerSelector[pickerSelected="true"]' in qss
    components_mod = import_from('palworld_aio.ui.chrome.components')
    tab = inventory_mod.PlayerInventoryTab(None)
    components_mod.set_picker_selected(tab.player_select_btn, True)
    assert tab.player_select_btn.property('pickerSelected') == 'true'
    components_mod.set_picker_selected(tab.player_select_btn, False)
    assert tab.player_select_btn.property('pickerSelected') is None
    tab.close()
    tab.deleteLater()
    app.processEvents()


def test_inventory_has_distinct_workspace_views_without_page_ribbon(tab):
    labels = [tab.inv_tabs.tabText(i) for i in range(tab.inv_tabs.count())]
    assert labels == [
        'Inventory', 'Equipment', 'Key Items', 'Stats', 'Missions',
        'Technology', 'Palpedia',
    ]
    assert not tab.findChildren(
        inventory_mod.QFrame, 'pageRibbon')


def test_popup_handler_unchanged(tab, app):
    """The picker still opens through the existing popup flow."""
    assert callable(tab._open_player_popup)
    meta = tab.player_select_btn.metaObject()
    clicked = meta.method(meta.indexOfMethod('clicked()'))
    assert tab.player_select_btn.isSignalConnected(clicked)


def test_single_player_becomes_workspace_smart_default(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    selected = []

    def select_player(uid, name, display):
        selected.append((uid, name, display))
        tab.current_player_uid = uid
        tab.current_player_name = name

    monkeypatch.setattr(tab, 'select_player', select_player)
    tab.bind_workspace_context(context)
    tab._player_list = [{
        'uid': 'player-1', 'name': 'Hathaway', 'level': 55,
        'display': 'Hathaway (Lv.55)',
    }]

    tab._reconcile_player_context()

    assert context.snapshot.player == context_mod.ContextSelection(
        'player-1', 'Hathaway')
    assert selected == [('player-1', 'Hathaway', 'Hathaway (Lv.55)')]


def test_workspace_context_switches_inventory_player(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    tab._player_list = [
        {'uid': 'p1', 'name': 'Hathaway', 'level': 55,
         'display': 'Hathaway (Lv.55)'},
        {'uid': 'p2', 'name': 'Juniper', 'level': 47,
         'display': 'Juniper (Lv.47)'},
    ]
    selected = []

    def select_player(uid, name, display):
        selected.append((uid, name, display))
        tab.current_player_uid = uid
        tab.current_player_name = name

    monkeypatch.setattr(tab, 'select_player', select_player)
    tab.bind_workspace_context(context)

    context.set_player(context_mod.ContextSelection('p2', 'Juniper'))

    assert selected == [('p2', 'Juniper', 'Juniper (Lv.47)')]
    assert tab.player_select_btn.text() == 'Juniper (Lv.47)'
    assert tab.player_select_btn.accessibleName() == 'Selected player: Juniper'


def test_inventory_grid_search_and_filter_compact_matching_slots(app):
    grid = inventory_mod.InventoryGridWidget('main')
    grid.load_items([
        {
            'slot_index': 0, 'item_id': 'Wood', 'item_name': 'Wood',
            'stack_count': 12,
        },
        {
            'slot_index': 7, 'item_id': 'LegendSword',
            'item_name': 'Legendary Sword', 'stack_count': 1,
        },
    ], max_slots=42)

    grid.search_input.setText('sword')

    assert not grid.slots[7].isHidden()
    assert grid.slots[0].isHidden()
    assert grid.slots[1].isHidden()
    assert grid.grid_layout.indexOf(grid.slots[7]) >= 0
    assert grid.filter_count_label.text() == '1 of 42 slots'

    grid.search_input.clear()
    grid.filter_buttons['empty'].click()

    assert grid.slots[0].isHidden()
    assert grid.slots[7].isHidden()
    assert not grid.slots[1].isHidden()
    assert grid.filter_count_label.text() == '40 of 42 slots'


def test_inventory_toolbar_uses_shared_sticky_controls(tab):
    grid = tab.main_grid

    assert grid.toolbar.objectName() == 'inventoryGridToolbar'
    assert grid.toolbar.property('class') == 'stickyToolbar'
    assert grid.search_frame.property('controlRole') == 'search'
    assert all(button.property('controlRole') == 'filter'
               for button in grid.filter_buttons.values())
    assert grid.layout().indexOf(grid.toolbar) < grid.layout().indexOf(grid.scroll)
    assert tab.inv_modify_slots_btn.property('controlRole') == 'secondary'
    assert tab.inv_loadout_btn.property('controlRole') == 'secondary'
    assert grid.sort_btn.property('controlRole') == 'tertiary'
    assert tab.unlock_all_map_btn.property('controlRole') == 'warning'
    assert all(button.styleSheet() == '' for button in (
        tab.inv_modify_slots_btn, tab.inv_loadout_btn, grid.sort_btn,
        tab.unlock_all_map_btn,
    ))


def test_inventory_utility_actions_keep_existing_handlers(app, monkeypatch):
    called = []
    monkeypatch.setattr(
        inventory_mod.PlayerInventoryTab, '_on_modify_inventory_slots',
        lambda self: called.append('modify'))
    monkeypatch.setattr(
        inventory_mod.PlayerInventoryTab, '_on_inventory_loadout',
        lambda self: called.append('loadout'))
    monkeypatch.setattr(
        inventory_mod.PlayerInventoryTab, '_on_sort_requested',
        lambda self: called.append('sort'))
    monkeypatch.setattr(
        inventory_mod.PlayerInventoryTab, '_on_unlock_all_map_clicked',
        lambda self: called.append('fast-travel'))
    action_tab = inventory_mod.PlayerInventoryTab(None)

    action_tab.inv_modify_slots_btn.click()
    action_tab.inv_loadout_btn.click()
    action_tab.main_grid.sort_btn.click()
    action_tab.unlock_all_map_btn.click()

    assert called == ['modify', 'loadout', 'sort', 'fast-travel']
    action_tab.close()
    action_tab.deleteLater()
    app.processEvents()


def test_item_slots_use_shared_grid_semantics_and_keep_rarity_when_selected(app):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    grid = inventory_mod.InventoryGridWidget('main')
    grid.load_items([{
        'slot_index': 0,
        'item_id': 'LegendSword',
        'item_name': 'Legendary Sword With A Deliberately Long Display Name',
        'stack_count': 2,
        'rarity': 4,
        'description': 'A rare blade used to verify full-detail access.',
    }], max_slots=43)
    slot = grid.slots[0]

    assert isinstance(slot, inventory_mod.InventorySlot)
    assert slot.objectName() == 'auditInventorySlot'
    assert slot.property('rarity') == 4
    assert slot.name_label.toolTip() == (
        'Legendary Sword With A Deliberately Long Display Name')
    assert 'LegendSword' in slot.toolTip()
    assert 'full-detail access' in slot.toolTip()

    QTest.keyClick(slot, Qt.Key.Key_Space)

    assert slot.selected
    assert slot.property('selected') is True
    assert slot.property('rarity') == 4
    assert not grid.preview_label.isHidden()
    assert grid.preview_label.text().endswith('×2')
    grid.close()
    grid.deleteLater()
    app.processEvents()


def _dispose_dialogs(app, *dialogs):
    for dialog in dialogs:
        dialog.close()
        dialog.deleteLater()
    app.processEvents()


def test_player_inventory_dialog_families_use_shared_scaffold():
    components_mod = import_from('palworld_aio.ui.chrome.components')
    dialog_types = (
        inventory_mod.ItemPickerDialog,
        inventory_mod.ModifyInventorySlotsDialog,
        inventory_mod.QuantityDialog,
        inventory_mod.InventoryLoadoutDialog,
    )

    assert all(issubclass(dialog_type, components_mod.BaseDialog)
               for dialog_type in dialog_types)


def test_quantity_and_player_slot_dialogs_keep_value_contracts(app):
    quantity = inventory_mod.QuantityDialog(current_qty=7, max_val=100)
    slots = inventory_mod.ModifyInventorySlotsDialog(
        current_slots=42, current_items=12)

    quantity.qty_input.setText('33')
    slots.slot_spinbox.setValue(54)

    assert quantity.get_quantity() == 33
    assert slots.get_slot_count() == 54
    assert slots.ok_button.isEnabled()
    assert quantity.objectName() == slots.objectName() == 'baseDialog'
    assert quantity.styleSheet() == slots.styleSheet() == ''
    _dispose_dialogs(app, quantity, slots)


def test_item_picker_keeps_selected_item_signal_contract(app, monkeypatch):
    monkeypatch.setattr(inventory_mod.ItemData, 'get_all_items', lambda: [])
    dialog = inventory_mod.ItemPickerDialog()
    selected = []
    dialog.item_selected.connect(
        lambda asset, quantity: selected.append((asset, quantity)))
    dialog.selected_item = 'Wood'
    dialog.qty_input.setText('17')

    dialog.add_button.click()

    assert selected == [('Wood', 17)]
    assert dialog.result() == dialog.DialogCode.Accepted
    _dispose_dialogs(app, dialog)


def test_loadout_dialog_keeps_apply_callback_and_close_result(
        app, monkeypatch, tmp_path):
    loading_mod = import_from('loading_manager')
    monkeypatch.setattr(loading_mod, 'show_information', lambda *_args: None)
    applied = []
    dialog = inventory_mod.InventoryLoadoutDialog(
        None,
        get_current_items_fn=lambda: [],
        apply_loadout_fn=lambda regular, keys, equipment: applied.append(
            (regular, keys, equipment)),
        loadouts_path=str(tmp_path / 'loadouts.json'),
    )
    dialog._loadouts = {
        'Builder': {
            'regular': [{'id': 'Wood', 'qty': 10}],
            'key_items': [],
            'equipment': {'weapon': 'Pickaxe'},
        },
    }
    dialog._refresh_list()
    dialog.list_widget.setCurrentRow(0)

    dialog._do_load()

    assert applied == [(
        [{'id': 'Wood', 'qty': 10}], [], {'weapon': 'Pickaxe'})]
    dialog.cancel_btn.click()
    assert dialog.result() == dialog.DialogCode.Accepted
    _dispose_dialogs(app, dialog)


def test_partial_inventory_row_keeps_real_capacity_and_useful_empty_slot(app):
    grid = inventory_mod.InventoryGridWidget('main')
    grid.set_max_slots(43)
    grid.resize(720, 480)
    grid.show()
    app.processEvents()

    assert grid.max_visible_slots == 43
    assert len(grid.slots) == 43
    assert grid.grid_layout.itemAtPosition(7, 0).widget() is grid.slots[42]
    assert grid.grid_layout.itemAtPosition(7, 1) is None
    assert grid.slots[42].name_label.toolTip() == 'Slot 43'
    assert grid.slots[42].accessibleName() == 'Slot 43 is empty'
    assert grid.slots[42].width() == grid.slots[36].width()
    grid.close()
    grid.deleteLater()
    app.processEvents()


def test_equipment_slots_share_card_details_and_keyboard_preview(app):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    slot = inventory_mod.EquipmentSlotWidget('weapon1', 'W1')
    previews = []
    slot.preview_requested.connect(previews.append)
    slot.set_item({
        'item_id': 'LaserRifle',
        'item_name': 'Legendary Laser Rifle With A Long Display Name',
        'stack_count': 1,
        'rarity': 4,
        'description': 'High-output weapon.',
    })

    assert isinstance(slot, inventory_mod.InventorySlot)
    assert slot.property('equipmentSlot') is True
    assert slot.maximumWidth() == 220
    assert slot.badge_label.text() == 'W1'
    assert slot.property('rarity') == 4
    assert slot.name_label.toolTip() == (
        'Legendary Laser Rifle With A Long Display Name')
    assert 'LaserRifle' in slot.toolTip()

    QTest.keyClick(slot, Qt.Key.Key_Space)

    assert slot.selected
    assert previews == [slot]
    assert slot.property('rarity') == 4
    slot.close()
    slot.deleteLater()
    app.processEvents()


def test_equipment_workspace_exposes_structured_categories_and_preview(tab):
    expected = {
        'weapon', 'accessory', 'food', 'head', 'body', 'shield', 'glider',
        'module',
    }
    headers = tab.equip_wrapper.findChildren(
        inventory_mod.QLabel, 'equipmentCategoryHeader')

    assert {header.property('categoryKind') for header in headers} == expected
    slot = tab.equip_slots['head']
    slot.set_item({
        'item_id': 'Helmet', 'item_name': 'Pal Metal Helm',
        'stack_count': 1, 'rarity': 3,
    })
    tab._on_equipment_preview(slot)
    assert not tab.equip_preview_label.isHidden()
    assert tab.equip_preview_label.text() == 'H1 · Pal Metal Helm ×1'
