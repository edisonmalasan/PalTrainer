"""Focused tests for the Base Inventory chip/tab split and container
grouping (uiux-audit-remediation 8.1-8.4).

Covers: EDITING ribbon caption, selector-chip vs view-tab distinction,
storage-first container grouping (both load paths), separator presence,
first-selection landing on storage, and container id reachability.
Widgets are constructed standalone offscreen with a stubbed manager.
"""
from __future__ import annotations

import os
import inspect
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

bi_mod = import_from('palworld_aio.ui.tabs.base_inventory_tab')
qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')

_app = None


def test_memory_autosave_records_pending_base_inventory_change():
    recorded = []
    tab = SimpleNamespace(
        manager=SimpleNamespace(
            inventory_container=object(), save_changes=lambda: True),
        _main_window=SimpleNamespace(
            record_pending_change=lambda *args, **kwargs: recorded.append(
                (args, kwargs))),
        _current_base_name='Coastal Base',
        _current_guild_name='Guild',
    )

    bi_mod.BaseInventoryTab._auto_save_changes(tab)

    assert recorded == [
        (('Base inventory updated',), {'context': 'Coastal Base'}),
    ]


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod = import_from('i18n')
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture
def app():
    return _app_instance()


@pytest.fixture
def tab(app):
    """A real BaseInventoryTab built with a stubbed save_manager, so the
    Qt object graph exists without save data."""
    import types
    from PyQt6.QtCore import QObject, pyqtSignal

    class _SM(QObject):
        load_finished = pyqtSignal(bool)

        def __init__(self):
            QObject.__init__(self)
            self.current_base = None

        def load_guilds(self):
            return []

        def load_bases_for_guild(self, gid):
            return []

        def load_containers_for_base(self, bid):
            return []

    sm_stub = types.ModuleType('palworld_aio.managers.save_manager')
    sm_stub.save_manager = _SM()
    previous = sys.modules.get('palworld_aio.managers.save_manager')
    sys.modules['palworld_aio.managers.save_manager'] = sm_stub
    try:
        bi_mod2 = import_from('palworld_aio.ui.tabs.base_inventory_tab')
        t = bi_mod2.BaseInventoryTab(None)
    finally:
        if previous is not None:
            sys.modules['palworld_aio.managers.save_manager'] = previous
    yield t
    t.close()
    t.deleteLater()
    app.processEvents()


# ------------------------------------------------------------ 8.1 caption

def test_ribbon_caption_reads_editing(app):
    i18n_mod = import_from('i18n')
    i18n_mod.load_resources('en_US')
    components_mod = import_from('palworld_aio.ui.chrome.components')
    create_page_ribbon = components_mod.create_page_ribbon
    ribbon = create_page_ribbon(
        'Base Inventory',
        (i18n_mod.t('sidebar.section.editing') or 'Editing').upper(), None)
    zone_labels = ribbon.findChildren(__import__('PyQt6.QtWidgets',
                                             fromlist=['QLabel']).QLabel)
    texts = [lbl.text() for lbl in zone_labels]
    assert 'EDITING' in texts
    assert 'WORLD DATA' not in texts


# --------------------------------------------------- 8.2 chips vs tabs

def test_selector_chips_and_view_tabs_distinct_objects(tab):
    assert tab.guild_button.objectName() == 'selectorChip'
    assert tab.base_button.objectName() == 'selectorChip'
    assert tab.inv_tab_btn.objectName() == 'viewTabBtn'
    assert tab.pals_tab_btn.objectName() == 'viewTabBtn'
    # the kinds do not share one objectName
    assert tab.guild_button.objectName() != tab.inv_tab_btn.objectName()


def test_context_is_hierarchical_and_views_have_their_own_group(tab):
    assert tab.context_bar.objectName() == 'editorContextBar'
    assert tab.guild_context_label.text() == 'Guild'
    assert tab.base_context_label.text() == 'Base'
    assert tab.guild_button.property('contextKind') == 'guild'
    assert tab.base_button.property('contextKind') == 'base'
    assert tab.context_hierarchy_separator.text() == '›'
    assert tab.view_tabs.objectName() == 'workspaceViewTabs'
    assert tab.inv_tab_btn.parent() is tab.view_tabs
    assert tab.pals_tab_btn.parent() is tab.view_tabs


def test_selector_chips_have_chevron_icons(app):
    from PyQt6.QtGui import QIcon
    chevron = bi_mod.app_icons.get_qicon('chevron_down', role='text_secondary')
    assert chevron is not None
    assert not chevron.pixmap(32, 32).isNull()
    for btn in (tab().guild_button,) if False else ():
        pass


def test_chips_carry_chevron_icons(tab):
    chevron = bi_mod.app_icons.get_qicon('chevron_down', role='text_secondary')
    for btn in (tab.guild_button, tab.base_button):
        assert not btn.icon().pixmap(32, 32).isNull()
        assert btn.icon().pixmap(32, 32).toImage() == chevron.pixmap(32, 32).toImage()


def test_view_tabs_checked_state_driven_by_switch(tab):
    tab._switch_tab(1)
    assert tab.pals_tab_btn.isChecked()
    assert not tab.inv_tab_btn.isChecked()
    tab._switch_tab(0)
    assert tab.inv_tab_btn.isChecked()
    assert not tab.pals_tab_btn.isChecked()


def test_single_guild_and_base_become_smart_defaults(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    guild = {'id': 'guild-1', 'name': 'Wayfarers', 'level': 19}
    base = {'id': 'base-1', 'guild_id': 'guild-1'}

    monkeypatch.setattr(
        bi_mod, 'run_with_loading',
        lambda on_finished, task, **_kwargs: on_finished(task()))
    monkeypatch.setattr(tab.manager, 'load_guilds', lambda: [guild])
    monkeypatch.setattr(
        tab.manager, 'load_bases_for_guild',
        lambda guild_id: [base] if guild_id == 'guild-1' else [])
    monkeypatch.setattr(tab.manager, 'load_containers_for_base', lambda _base_id: [])

    tab.bind_workspace_context(context)
    tab._load_guilds()

    assert context.snapshot.guild == context_mod.ContextSelection(
        'guild-1', 'Wayfarers', 'Level 19')
    assert context.snapshot.base == context_mod.ContextSelection(
        'base-1', 'Base 1')
    assert tab._current_guild_id == 'guild-1'
    assert tab._current_base_id == 'base-1'
    assert tab.guild_button.text() == 'Wayfarers (Level 19)'
    assert tab.base_button.text() == 'Base 1'
    assert tab.guild_button.isEnabled()
    assert tab.base_button.isEnabled()


def test_multiple_guilds_do_not_choose_an_arbitrary_default(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    guilds = [
        {'id': 'guild-1', 'name': 'Wayfarers', 'level': 19},
        {'id': 'guild-2', 'name': 'Marshals', 'level': 12},
    ]

    monkeypatch.setattr(
        bi_mod, 'run_with_loading',
        lambda on_finished, task, **_kwargs: on_finished(task()))
    monkeypatch.setattr(tab.manager, 'load_guilds', lambda: guilds)
    monkeypatch.setattr(
        tab.manager, 'load_bases_for_guild',
        lambda guild_id: [{'id': f'base-{guild_id[-1]}',
                           'guild_id': guild_id}])

    tab.bind_workspace_context(context)
    tab._load_guilds()

    assert context.snapshot.guild is None
    assert context.snapshot.base is None
    assert tab._current_guild_id is None
    assert tab.guild_button.text() == bi_mod.t('base_inventory.select_guild')
    assert not tab.base_button.isEnabled()


def test_guild_context_change_invalidates_old_base_and_container(tab, monkeypatch):
    context_mod = import_from('palworld_aio.ui.workspace_context')
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity(
        'synthetic', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    guilds = [
        {'id': 'guild-1', 'name': 'Wayfarers', 'level': 19},
        {'id': 'guild-2', 'name': 'Marshals', 'level': 12},
    ]
    bases = {
        'guild-1': [{'id': 'base-1', 'guild_id': 'guild-1'}],
        'guild-2': [{'id': 'base-2', 'guild_id': 'guild-2'}],
    }

    monkeypatch.setattr(
        bi_mod, 'run_with_loading',
        lambda on_finished, task, **_kwargs: on_finished(task()))
    monkeypatch.setattr(tab.manager, 'load_guilds', lambda: guilds)
    monkeypatch.setattr(
        tab.manager, 'load_bases_for_guild', lambda guild_id: bases[guild_id])
    monkeypatch.setattr(tab.manager, 'load_containers_for_base', lambda _base_id: [])

    tab.bind_workspace_context(context)
    tab._load_guilds()
    context.set_guild(context_mod.ContextSelection('guild-1', 'Wayfarers'))
    tab.manager.current_container = {'id': 'old-container'}
    tab.manager.inventory_container = object()
    tab.manager.containers = [{'id': 'old-container'}]
    context.set_container(context_mod.ContextSelection(
        'old-container', 'Old Storage'))

    context.set_guild(context_mod.ContextSelection('guild-2', 'Marshals'))

    assert context.snapshot.guild.identifier == 'guild-2'
    assert context.snapshot.base.identifier == 'base-2'
    assert context.snapshot.container is None
    assert tab._current_guild_id == 'guild-2'
    assert tab._current_base_id == 'base-2'
    assert tab.manager.current_container is None
    assert tab.manager.inventory_container is None
    assert tab.manager.containers == []


def test_built_qss_has_underline_tab_and_chip_classes(app):
    qss = qss_mod.build_qss('dark')
    assert 'QPushButton#viewTabBtn:checked' in qss
    assert 'border-bottom: 2px solid' in qss  # underline treatment
    assert 'QPushButton#selectorChip' in qss
    assert 'QPushButton#selectorChip[pickerSelected="true"]' in qss


# --------------------------------------------- 8.3 container grouping

GUILD_CHEST = {'id': 'chest-1', 'name': 'Guild Chest', 'slot_count': 54,
               'is_guild_chest': True, 'map_object_id': 'StorageChest',
               'type': 'StorageChest'}
DROP_1 = {'id': 'drop-1', 'name': 'Dropped Items', 'slot_count': 1,
          'is_guild_chest': False, 'map_object_id': '3D/CommonDropItem',
          'type': '3D/CommonDropItem'}
DROP_2 = {'id': 'drop-2', 'name': 'Dropped Items', 'slot_count': 1,
          'is_guild_chest': False, 'map_object_id': '3D/CommonDropItem',
          'type': '3D/CommonDropItem'}
STORAGE_BOX = {'id': 'box-1', 'name': 'Storage Box', 'slot_count': 20,
               'is_guild_chest': False, 'map_object_id': 'WoodChest',
               'type': 'WoodChest'}


def _populate(tab, containers):
    for c in containers:
        tab.container_list.add_container(c)


def _load(tab, containers):
    """Route through the real load path (storage-first grouping applies)."""
    tab.manager.containers = list(containers)
    tab._load_containers_for_base('base-1', containers=containers)


def _row_ids(tab):
    from PyQt6.QtCore import Qt
    return [tab.container_list.topLevelItem(i).data(0, Qt.UserRole)
            for i in range(tab.container_list.topLevelItemCount())]


def test_storage_containers_ordered_before_debris(tab):
    _load(tab, [DROP_1, DROP_2, GUILD_CHEST, STORAGE_BOX])
    ids = _row_ids(tab)
    assert ids[0] == 'chest-1'
    assert ids[1] == 'box-1'
    assert ids[-2:] == ['drop-1', 'drop-2']


def test_separator_row_present_and_non_selectable(tab):
    _load(tab, [GUILD_CHEST, DROP_1, DROP_2])
    from PyQt6.QtCore import Qt
    items = [tab.container_list.topLevelItem(i)
             for i in range(tab.container_list.topLevelItemCount())]
    separators = [it for it in items
                  if it.data(0, Qt.UserRole + 1) == 'separator']
    assert len(separators) == 1
    sep = separators[0]
    assert sep.text(0) == 'Dropped Items'
    assert not (sep.flags() & Qt.ItemFlag.ItemIsSelectable)
    # debris rows sit below the separator
    assert tab.container_list.indexOfTopLevelItem(sep) == 1


def test_first_selection_lands_on_storage_container(tab):
    _load(tab, [DROP_1, DROP_2, GUILD_CHEST, STORAGE_BOX])
    current = tab.container_list.currentItem()
    from PyQt6.QtCore import Qt
    assert current.data(0, Qt.UserRole) == 'chest-1'


def test_grouping_applies_to_filtered_path(tab):
    seen = []

    def _on_selected(container_id):
        seen.append(container_id)
    tab.container_list.container_selected.connect(_on_selected)
    # the filtered path requires _item_locations keyed by guild/base
    from PyQt6.QtCore import Qt
    tab._item_locations = {
        'guild1': {'base1': {'chest1', 'box1', 'drop1', 'drop2'}}}
    tab._current_guild_id = 'GUILD-1'
    tab._current_base_id = 'base-1'
    tab._current_tab = 0
    tab._load_containers_for_base_filtered(
        'base-1',
        containers=[DROP_1, GUILD_CHEST, DROP_2, STORAGE_BOX])
    ids = _row_ids(tab)
    # separator row carries no id; storage first, debris last
    assert ids == ['chest-1', 'box-1', None, 'drop-1', 'drop-2']
    assert seen == ['chest-1']  # default selection = first storage container


def test_all_container_ids_still_selectable(tab):
    from PyQt6.QtCore import Qt
    _load(tab, [DROP_1, GUILD_CHEST, DROP_2, STORAGE_BOX])
    listed = set()
    for i in range(tab.container_list.topLevelItemCount()):
        item = tab.container_list.topLevelItem(i)
        cid = item.data(0, Qt.UserRole)
        if cid is not None:
            listed.add(cid)
            tab.container_list.setCurrentItem(item)
            assert tab.container_list.currentItem() is item
    assert listed == {'chest-1', 'box-1', 'drop-1', 'drop-2'}


def test_all_debris_base_skips_separator_for_default_selection(tab):
    _load(tab, [DROP_1, DROP_2])
    current = tab.container_list.currentItem()
    from PyQt6.QtCore import Qt
    assert current is not None
    assert current.data(0, Qt.UserRole) == 'drop-1'


def test_storage_only_base_has_no_separator(tab):
    _load(tab, [GUILD_CHEST, STORAGE_BOX])
    from PyQt6.QtCore import Qt
    items = [tab.container_list.topLevelItem(i)
             for i in range(tab.container_list.topLevelItemCount())]
    separators = [it for it in items
                  if it.data(0, Qt.UserRole + 1) == 'separator']
    assert separators == []


def test_duplicate_container_names_receive_one_based_indexes(tab):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel

    first = dict(STORAGE_BOX, id='box-1')
    second = dict(STORAGE_BOX, id='box-2')
    _load(tab, [first, second])
    labels = []
    for index in range(tab.container_list.topLevelItemCount()):
        item = tab.container_list.topLevelItem(index)
        if item.data(0, Qt.UserRole) is None:
            continue
        row = tab.container_list.itemWidget(item, 0)
        labels.append(row.findChild(QLabel, 'containerName').text())

    assert labels == ['Storage Box 1', 'Storage Box 2']


def test_container_search_matches_human_name_raw_asset_and_identifier(tab):
    from PyQt6.QtCore import Qt

    _load(tab, [DROP_1, DROP_2, GUILD_CHEST, STORAGE_BOX])
    tab.container_search_input.setText('woodchest')
    assert tab.container_list.visible_selectable_count() == 1
    visible = [
        tab.container_list.topLevelItem(index)
        for index in range(tab.container_list.topLevelItemCount())
        if (tab.container_list.topLevelItem(index).data(0, Qt.UserRole)
            is not None
            and not tab.container_list.topLevelItem(index).isHidden())
    ]
    assert visible[0].data(0, Qt.UserRole) == 'box-1'
    separator = next(
        tab.container_list.topLevelItem(index)
        for index in range(tab.container_list.topLevelItemCount())
        if tab.container_list.topLevelItem(index).data(
            0, Qt.UserRole + 1) == 'separator')
    assert separator.isHidden()

    tab.container_search_input.setText('drop-2')
    assert tab.container_list.visible_selectable_count() == 1
    assert not separator.isHidden()
    assert tab.container_selection_summary.text() == '1 of 4 · 1 selected'

    tab.container_search_input.clear()
    assert tab.container_list.visible_selectable_count() == 4
    assert tab.container_selection_summary.text() == (
        '4 containers · 1 selected')


def test_container_selection_summary_appears_once_and_raw_ids_stay_in_tooltips(tab):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel

    _load(tab, [GUILD_CHEST, STORAGE_BOX])
    summaries = tab.findChildren(QLabel, 'containerSelectionSummary')
    assert len(summaries) == 1
    assert summaries[0].text() == '2 containers · 1 selected'
    first = tab.container_list.topLevelItem(0)
    assert first.data(0, Qt.UserRole) == 'chest-1'
    assert 'StorageChest' in first.toolTip(0)
    assert 'chest-1' in first.toolTip(0)
    assert 'chest-1' not in summaries[0].text()


def test_container_navigator_uses_shared_theme_rules(tab):
    qss = qss_mod.build_qss('dark')
    assert tab.container_list.styleSheet() == ''
    assert 'QTreeWidget#containerNavigator' in qss
    assert 'QLabel#containerSelectionSummary' in qss


def test_base_inventory_uses_shared_grid_filters_and_action_tiers(tab):
    inventory_mod = import_from('palworld_aio.ui.tabs.inventory_tab')

    assert isinstance(
        tab.inventory_grid.grid_widget, inventory_mod.SharedInventoryGrid)
    assert tab.inventory_grid.toolbar.property('class') == 'stickyToolbar'
    assert tab.item_button.property('controlRole') == 'chip'
    assert tab.item_button.property('filterKind') == 'item'
    assert tab.structure_button.property('controlRole') == 'chip'
    assert tab.structure_button.property('filterKind') == 'structure'
    assert tab.clear_item_button.property('controlRole') == 'icon'
    assert tab.clear_structure_button.property('controlRole') == 'icon'
    assert tab.replace_button.property('controlRole') == 'secondary'
    assert tab.base_add_item_btn.property('controlRole') == 'primary'
    assert tab.base_modify_slots_btn.property('controlRole') == 'secondary'
    assert tab.base_inv_loadout_btn.property('controlRole') == 'secondary'
    assert tab.inventory_grid.sort_btn.property('controlRole') == 'tertiary'
    assert tab.base_inv_clear_btn.property('controlRole') == 'destructive'
    assert all(button.styleSheet() == '' for button in (
        tab.item_button,
        tab.structure_button,
        tab.clear_item_button,
        tab.clear_structure_button,
        tab.replace_button,
        tab.base_add_item_btn,
        tab.base_modify_slots_btn,
        tab.base_inv_loadout_btn,
        tab.inventory_grid.sort_btn,
        tab.base_inv_clear_btn,
    ))


def test_base_grid_renders_real_capacity_with_shared_slot_models(tab):
    content_mod = import_from('palworld_aio.ui.chrome.content_cards')
    item = {
        'slot_index': 0,
        'item_id': 'Wood',
        'item_name': 'Wood',
        'stack_count': 824,
        'rarity': 2,
        'description': 'Building material',
    }

    tab.inventory_grid.load_items([item], max_slots=20)

    assert tab.inventory_grid.max_visible_slots == 20
    assert len(tab.inventory_grid.slots) == 20
    assert all(isinstance(slot, content_mod.InventorySlot)
               for slot in tab.inventory_grid.slots.values())
    occupied = tab.inventory_grid.slots[0]
    final_empty = tab.inventory_grid.slots[19]
    assert occupied.model.name == 'Wood'
    assert occupied.model.quantity == 824
    assert occupied.property('rarity') == 2
    assert final_empty.model.slot_label == 'Slot 20'
    assert 'Slot 20' in final_empty.accessibleName()


def test_base_inventory_uses_distinct_shared_states(tab):
    states = {
        tab.inventory_prerequisite_state: 'prerequisite',
        tab.container_loading_state: 'loading',
        tab.container_empty_state: 'configured_empty',
        tab.container_no_result_state: 'no_result',
        tab.container_no_selection_state: 'prerequisite',
        tab.unknown_structure_state: 'unknown',
        tab.container_error_state: 'error',
    }
    assert tab.inventory_state_stack.currentWidget() is (
        tab.inventory_prerequisite_state)
    for widget, kind in states.items():
        assert widget.property('stateKind') == kind
        assert widget.accessibleName()
        assert widget.accessibleDescription()
    assert tab.container_error_state.action_button.text() == 'Retry'


def test_empty_container_and_unknown_structure_have_specific_states(tab):
    tab._current_base_id = 'base-1'
    tab._load_containers_for_base('base-1', containers=[])
    assert tab.inventory_state_stack.currentWidget() is tab.container_empty_state

    tab.container_list.add_structure_entry(
        'Wood Foundation', 'structure-1', 'WoodFoundation')
    tab._on_container_selected('structure-1')
    assert tab.inventory_state_stack.currentWidget() is (
        tab.unknown_structure_state)
    assert not tab.base_add_item_btn.isEnabled()


def test_missing_container_selection_has_recovery_action(tab, app):
    tab._current_base_id = 'base-1'
    tab._on_container_selected('missing-container')
    assert tab.inventory_state_stack.currentWidget() is (
        tab.container_no_selection_state)
    tab.show()
    app.processEvents()
    tab.container_no_selection_state.action_button.click()
    app.processEvents()
    assert tab.inventory_state_stack.currentWidget() is (
        tab.inventory_content_host)
    assert tab.container_list.hasFocus()


def test_base_pals_states_distinguish_prerequisite_loading_empty_and_error(
        tab, monkeypatch):
    widget = tab.base_pals_widget
    assert widget.state_stack.currentWidget() is widget.prerequisite_state

    widget.show_loading('base-1')
    assert widget.state_stack.currentWidget() is widget.loading_state

    widget.set_pals([], 'base-1')
    assert widget.state_stack.currentWidget() is widget.empty_state

    widget.show_error('base-1')
    assert widget.state_stack.currentWidget() is widget.error_state
    assert widget.error_state.action_button.text() == 'Retry'

    monkeypatch.setattr(widget, '_update_page', lambda: None)
    widget.set_pals([{'character_entry': {}}], 'base-1')
    assert widget.state_stack.currentWidget() is widget.content_widget


def test_base_pal_loading_is_local_and_keeps_context_controls_usable(
        tab, monkeypatch):
    calls = []

    def deferred(on_finished, task, **kwargs):
        calls.append((on_finished, task, kwargs))

    monkeypatch.setattr(bi_mod, 'run_with_loading', deferred)
    tab._current_base_id = 'base-1'
    tab.guild_button.setEnabled(True)
    tab.base_button.setEnabled(True)

    tab._load_base_pals()

    assert tab.base_pals_widget.state_stack.currentWidget() is (
        tab.base_pals_widget.loading_state)
    assert tab.guild_button.isEnabled()
    assert tab.base_button.isEnabled()
    assert len(calls) == 1
    assert calls[0][2]['local_state'] is True
    assert calls[0][2]['parent'] is tab

    calls[0][2]['on_error']('Traceback: synthetic')
    assert tab.base_pals_widget.state_stack.currentWidget() is (
        tab.base_pals_widget.error_state)


def test_container_loading_failure_is_local_and_preserves_base_context(
        tab, monkeypatch):
    calls = []

    def deferred(on_finished, task, **kwargs):
        calls.append((on_finished, task, kwargs))

    monkeypatch.setattr(bi_mod, 'run_with_loading', deferred)
    tab._guilds_data = [{'id': 'guild-1', 'name': 'Wayfarers', 'level': 19}]
    tab._bases_data = [{'id': 'base-1', 'guild_id': 'guild-1'}]
    tab._current_guild_id = 'guild-1'
    tab.guild_button.setEnabled(True)
    tab.base_button.setEnabled(True)

    tab._on_base_changed('base-1')

    assert tab.inventory_state_stack.currentWidget() is (
        tab.container_loading_state)
    assert tab._current_base_id == 'base-1'
    assert tab.guild_button.isEnabled()
    assert tab.base_button.isEnabled()
    assert calls[0][2]['local_state'] is True

    calls[0][2]['on_error']('Traceback: synthetic')
    assert tab.inventory_state_stack.currentWidget() is (
        tab.container_error_state)
    assert tab._current_base_id == 'base-1'


def test_base_toolbar_and_picker_actions_keep_existing_handlers(app, monkeypatch):
    called = []
    handlers = {
        '_show_item_picker': 'item-picker',
        '_show_structure_picker': 'structure-picker',
        '_show_replace_dialog': 'replace',
        '_add_item': 'add',
        '_modify_container_slots': 'modify-slots',
        '_on_inventory_loadout': 'loadout',
        '_on_base_sort_requested': 'sort',
        '_clear_container': 'clear',
    }
    for method_name, label in handlers.items():
        monkeypatch.setattr(
            bi_mod.BaseInventoryTab,
            method_name,
            lambda self, *_args, key=label: called.append(key),
        )
    action_tab = bi_mod.BaseInventoryTab(None)
    action_tab.replace_button.setEnabled(True)
    action_tab._set_container_actions_enabled(True)

    action_tab.item_button.click()
    action_tab.structure_button.click()
    action_tab.replace_button.click()
    action_tab.base_add_item_btn.click()
    action_tab.base_modify_slots_btn.click()
    action_tab.base_inv_loadout_btn.click()
    action_tab.inventory_grid.sort_btn.click()
    action_tab.base_inv_clear_btn.click()

    assert called == [
        'item-picker', 'structure-picker', 'replace', 'add',
        'modify-slots', 'loadout', 'sort', 'clear',
    ]
    action_tab.close()
    action_tab.deleteLater()
    app.processEvents()


def test_item_picker_find_updates_shared_filter_state(tab, monkeypatch):
    filtered = []
    monkeypatch.setattr(tab, '_get_item_name', lambda _item_id: 'Wood')
    monkeypatch.setattr(
        tab, '_filter_guilds_and_bases_by_item', lambda: filtered.append(True))

    tab._on_item_action_selected('Wood', 'find')

    assert tab.selected_item_id == 'Wood'
    assert tab.selected_item_name == 'Wood'
    assert tab.item_button.text() == 'Wood'
    assert tab.item_button.property('pickerSelected') == 'true'
    assert tab.clear_item_button.isVisibleTo(tab)
    assert filtered == [True]


def test_item_economy_action_keeps_stats_dialog_contract(tab, monkeypatch):
    manager_mod = import_from('palworld_aio.inventory.base_inventory_manager')
    opened = []
    stats = {'total': 12, 'guilds': 1, 'average': 12.0}

    monkeypatch.setattr(
        manager_mod, 'get_item_economy_stats', lambda item_id: stats)
    monkeypatch.setattr(tab, '_get_item_name', lambda _item_id: 'Wood')

    class _EconomyDialog:
        def __init__(self, received_stats, item_name, parent):
            opened.append((received_stats, item_name, parent))

        def exec(self):
            opened.append('exec')

    monkeypatch.setattr(bi_mod, 'EconomyStatsDialog', _EconomyDialog)

    tab._on_item_action_selected('Wood', 'economy')

    assert opened == [(stats, 'Wood', tab), 'exec']


def test_direct_item_removal_keeps_manager_operation(tab, monkeypatch):
    removed = []
    refreshed = []
    tab.manager.inventory_container = object()
    tab.manager.current_container = {
        'id': 'container-1', 'booth_type': None,
    }
    monkeypatch.setattr(
        tab.manager, 'remove_item',
        lambda slot_index, count: removed.append((slot_index, count)) or True)
    monkeypatch.setattr(
        tab, '_refresh_after_remove', lambda: refreshed.append(True))

    tab._remove_item_from_slot({
        'slot_index': 7, 'item_id': 'Wood', 'item_name': 'Wood',
    })
    _app_instance().processEvents()

    assert removed == [(7, 999999)]
    assert refreshed == [True]


def test_slot_modification_keeps_manager_operation_contract(tab, monkeypatch):
    applied = []
    autosaved = []
    tab.manager.inventory_container = object()
    tab.manager.current_container = {
        'id': 'container-1', 'slot_count': 20,
    }
    tab._current_base_id = 'base-1'
    monkeypatch.setattr(
        tab.manager, 'select_container',
        lambda _container_id: tab.manager.inventory_container)
    monkeypatch.setattr(tab.manager, 'get_items_count', lambda: 4)
    monkeypatch.setattr(
        tab.manager, 'expand_container_capacity',
        lambda container_id, count: applied.append((container_id, count)) or True)
    monkeypatch.setattr(tab, '_trigger_auto_save', lambda: autosaved.append(True))
    monkeypatch.setattr(bi_mod.constants, 'invalidate_container_lookup', lambda: None)

    class _SlotDialog:
        def __init__(self, parent, current_slots, current_items):
            assert parent is tab
            assert (current_slots, current_items) == (20, 4)

        def exec(self):
            return bi_mod.QDialog.DialogCode.Accepted

        def get_slot_count(self):
            return 28

    monkeypatch.setattr(bi_mod, 'ContainerSlotModificationDialog', _SlotDialog)

    tab._modify_container_slots()

    assert applied == [('container-1', 28)]
    assert autosaved == [True]
    assert tab._pending_slot_mod == ('container-1', 'base-1')


def test_structure_entries_untouched_by_grouping(tab):
    from PyQt6.QtCore import Qt
    tab.container_list.add_structure_entry('Wood Foundation', 'inst-1',
                                           structure_asset='woodfoundation')
    first = tab.container_list.topLevelItem(0)
    assert first.data(0, Qt.UserRole) == 'inst-1'
    assert first.data(0, Qt.UserRole + 1) == 'structure'


def test_separator_right_click_does_not_open_menu_or_emit(tab, monkeypatch):
    """Edge fix: the non-selectable separator is an item but not a container;
    right-clicking it must not open the container context menu or route
    container_id=None into the CRUD handlers."""
    from PyQt6.QtCore import Qt, QPoint
    _load(tab, [DROP_1, GUILD_CHEST, DROP_2])
    sep = next(tab.container_list.topLevelItem(i)
               for i in range(tab.container_list.topLevelItemCount())
               if tab.container_list.topLevelItem(i).data(0, Qt.UserRole + 1) == 'separator')
    assert sep.data(0, Qt.UserRole) is None
    opened = []

    class _NeverOpened:
        def add_item(self, *a, **k):
            opened.append('add_item')
        def add_sep(self):
            opened.append('sep')
        def exec(self, pos):
            opened.append('exec')
            return None
    monkeypatch.setattr(
        'palworld_aio.widgets.scrollable_context_menu.ScrollableContextMenu',
        _NeverOpened)
    # locate the separator row inside the viewport and right-click it
    rect = tab.container_list.visualItemRect(sep)
    assert rect.isValid()
    seen = []
    tab.container_list.container_selected.connect(seen.append)
    tab.container_list._show_context_menu(QPoint(rect.center()))
    assert opened == []  # the menu never opened for the separator
    assert seen == []    # no container_selected(None) emission


def _dispose_dialogs(app, *dialogs):
    for dialog in dialogs:
        dialog.close()
        dialog.deleteLater()
    app.processEvents()


def test_base_inventory_dialog_families_use_shared_scaffold():
    components_mod = import_from('palworld_aio.ui.chrome.components')
    dialog_types = (
        bi_mod.GuildItemPickerDialog,
        bi_mod.GuildStructurePickerDialog,
        bi_mod.EconomyStatsDialog,
        bi_mod.ContainerSlotModificationDialog,
        bi_mod.ReplaceStructureDialog,
    )

    assert all(issubclass(dialog_type, components_mod.BaseDialog)
               for dialog_type in dialog_types)


def test_inline_base_inventory_dialogs_use_shared_scaffold():
    remove_source = inspect.getsource(
        bi_mod.GuildItemPickerDialog._on_remove_item)
    percentage_source = inspect.getsource(
        bi_mod.GuildItemPickerDialog._do_remove_pct)
    details_source = inspect.getsource(
        bi_mod.ContainerListWidget._view_container_details)

    assert 'BaseDialog(' in remove_source
    assert 'BaseDialog(' in percentage_source
    assert 'BaseDialog(' in details_source
    assert 'QInputDialog(' not in percentage_source
    assert 'setStyleSheet(' not in (
        remove_source + percentage_source + details_source)


def test_container_slot_dialog_keeps_value_contract(app):
    dialog = bi_mod.ContainerSlotModificationDialog(
        current_slots=20, current_items=7)
    dialog.slot_spinbox.setValue(24)

    assert dialog.get_slot_count() == 24
    assert dialog.ok_button.isEnabled()
    assert dialog.objectName() == 'baseDialog'
    assert dialog.styleSheet() == ''
    _dispose_dialogs(app, dialog)


def test_base_picker_and_economy_dialogs_keep_shared_footer_contracts(
        app, monkeypatch):
    monkeypatch.setattr(bi_mod.ItemData, 'get_all_items', lambda: [])
    monkeypatch.setattr(
        bi_mod.GuildStructurePickerDialog, '_load_structure_data',
        lambda self: None)
    item_picker = bi_mod.GuildItemPickerDialog()
    structure_picker = bi_mod.GuildStructurePickerDialog()
    economy = bi_mod.EconomyStatsDialog({
        'total_count': 14,
        'guilds_with_item': 2,
        'avg_per_guild': 7,
        'guild_details': [],
    }, item_name='Wood')

    assert item_picker.find_btn.property('controlRole') == 'primary'
    assert structure_picker.find_btn.property('controlRole') == 'primary'
    assert structure_picker.delete_btn.property('controlRole') == 'destructive'
    assert all(dialog.styleSheet() == '' for dialog in (
        item_picker, structure_picker, economy))
    economy.cancel_btn.click()
    assert economy.result() == economy.DialogCode.Accepted
    _dispose_dialogs(app, item_picker, structure_picker, economy)


def test_replace_structure_dialog_keeps_confirmation_signal(
        app, monkeypatch):
    monkeypatch.setattr(
        bi_mod.ReplaceStructureDialog, '_populate_left', lambda self: None)
    dialog = bi_mod.ReplaceStructureDialog(
        None, 'base-1', 'Hilltop', [], {})
    confirmed = []
    dialog.replacement_confirmed.connect(
        lambda source, target, count: confirmed.append(
            (source, target, count)))
    dialog._source_asset = 'WoodWall'
    dialog._target_asset = 'StoneWall'
    dialog._source_count = 3

    dialog._on_confirm()

    assert confirmed == [('WoodWall', 'StoneWall', 3)]
    assert dialog.result() == dialog.DialogCode.Rejected
    assert dialog.confirm_btn.property('controlRole') == 'primary'
    assert dialog.styleSheet() == ''
    _dispose_dialogs(app, dialog)
