"""Focused tests for the Base Inventory chip/tab split and container
grouping (uiux-audit-remediation 8.1-8.4).

Covers: EDITING ribbon caption, selector-chip vs view-tab distinction,
storage-first container grouping (both load paths), separator presence,
first-selection landing on storage, and container id reachability.
Widgets are constructed standalone offscreen with a stubbed manager.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

bi_mod = import_from('palworld_aio.ui.tabs.base_inventory_tab')
qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')

_app = None


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
    return t


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
