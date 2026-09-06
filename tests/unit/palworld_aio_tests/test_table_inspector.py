"""Focused tests for table-page inspector + labeled result count
(uiux-audit-remediation 4.1-4.6, Bases slice).

Covers: InspectorPanel populate/empty/copy affordance, Bases page layout
(inspector column present, selection populates, capped table container),
CopyValueRow feedback, SearchPanel labeled result count, and ID-column
copy/mono treatment. Widgets are constructed standalone offscreen.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

components = import_from('palworld_aio.ui.chrome.components')
search_panel_mod = import_from('palworld_aio.widgets.search_panel')
main_window_mod = import_from('palworld_aio.ui.main_window')
tools_tab_mod = import_from('palworld_aio.ui.tabs.tools_tab')  # noqa: F401 (pairing)

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


# ------------------------------------------------------- 4.1 InspectorPanel

def test_inspector_shows_empty_state_first(app):
    inspector = components.InspectorPanel()
    assert inspector._empty.isVisibleTo(inspector)
    assert not inspector._grid_host.isVisibleTo(inspector)
    assert not inspector._title.isVisibleTo(inspector)


def test_inspector_populate_and_return_to_empty(app):
    inspector = components.InspectorPanel()
    inspector.add_row('Guild')
    inspector.add_row('Base ID', monospace=True)
    inspector.show_details('Base 1', {0: 'Unnamed Guild', 1: 'ABC-123'})
    assert inspector._title.text() == 'Base 1'
    assert inspector._title.isVisibleTo(inspector)
    assert inspector._grid_host.isVisibleTo(inspector)
    assert not inspector._empty.isVisibleTo(inspector)
    mono = inspector._rows[1][1]
    assert mono.value() == 'ABC-123'
    inspector.show_empty('Select a base')
    assert inspector._empty.isVisibleTo(inspector)
    assert not inspector._grid_host.isVisibleTo(inspector)


def test_inspector_hides_rows_with_no_value(app):
    inspector = components.InspectorPanel()
    inspector.add_row('Guild')
    inspector.show_details('Base 1', {0: ''})
    label_lbl, value = inspector._rows[0]
    assert not label_lbl.isVisibleTo(inspector)
    assert not value.isVisibleTo(inspector)


def test_inspector_side_column_fixed_width(app):
    column = components.InspectorSideColumn(340)
    assert column.width() == 340
    assert isinstance(column.panel, components.InspectorPanel)


# ----------------------------------------------------- CopyValueRow (4.2/4.3)

def test_copy_value_row_copies_full_value_with_feedback(app):
    row = components.CopyValueRow()
    row.set_label('Base ID')
    row.set_value('B7D8465740F80E0E7AC081991A033220')
    row._value.click()
    from PyQt6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == 'B7D8465740F80E0E7AC081991A033220'
    assert row._value.toolTip() == 'B7D8465740F80E0E7AC081991A033220'
    row._reset_feedback()
    assert row.value() == 'B7D8465740F80E0E7AC081991A033220'


def test_copy_value_row_hidden_when_empty(app):
    row = components.CopyValueRow()
    row.set_value('')
    assert not row._value.isVisibleTo(row)


# --------------------------------------------------- 4.2 Bases page layout

@pytest.fixture
def window(app):
    """MainWindow shell without the full boot (no save loaded)."""
    from PyQt6.QtWidgets import QStackedWidget
    win = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    win.stacked_widget = QStackedWidget()
    return win


def test_bases_layout_has_inspector_column(window, app):
    window._setup_bases_tab()
    assert hasattr(window, 'bases_panel')
    assert isinstance(window._bases_inspector_column, components.InspectorSideColumn)
    assert window._bases_inspector_column.width() == 340
    assert window._bases_inspector_column.parent() is not None
    # inspector starts in the empty presentation naming the prerequisite
    assert window._bases_inspector._empty.isVisibleTo(window._bases_inspector)
    assert 'Select a base' in window._bases_inspector._empty.text()


def test_bases_inspector_open_inventory_action_registered(window, app):
    window._setup_bases_tab()
    assert window._bases_open_inventory_btn.parent() is not None
    assert window._bases_open_inventory_btn.toolTip() == ''


def test_bases_inspector_populates_on_selection(window, app, monkeypatch):
    window._setup_bases_tab()
    base_id = 'B7D8465740F80E0E7AC081991A033220'
    guild_id = '707E7DCC8C7B7D4C9A2E0B1A3F4D5E60'
    window.bases_panel.add_item(
        ['B7D84657…', '707E7DCC…', 'Unnamed Guild', 1],
        tooltips={0: base_id, 1: guild_id})
    window.bases_panel.tree.setCurrentItem(window.bases_panel.tree.topLevelItem(0))
    item = window.bases_panel.get_selected_item()
    assert item is not None

    class _Ctx:
        def set_base(self, v):
            context_calls.append(('base', v))
        def set_guild(self, v):
            context_calls.append(('guild', v))
    context_calls = []
    import types
    window.app_bar = types.SimpleNamespace(context=_Ctx())

    class _FakeDataManger:
        @staticmethod
        def get_bases():
            return [{'id': base_id, 'guild_id': guild_id,
                     'guild_name': 'Unnamed Guild'}]
    monkeypatch.setattr(main_window_mod, 'get_bases',
                        _FakeDataManger.get_bases)
    window._on_base_selected(['B7D84657…', '707E7DCC…', 'Unnamed Guild', '1'])
    inspector = window._bases_inspector
    assert inspector._title.text() == 'Base 1'
    assert inspector._rows[0][1].text() == 'Unnamed Guild'
    assert inspector._rows[2][1].value() == base_id
    assert inspector._rows[3][1].value() == guild_id
    assert not inspector._empty.isVisibleTo(inspector)
    assert context_calls[0] == ('base', 'B7D84657…')


def test_bases_inspector_clears_when_refreshed(window, app):
    window._setup_bases_tab()
    inspector = window._bases_inspector
    inspector.show_details('Base 1', {0: 'g'})
    window._refresh_bases()  # no save loaded -> empty table + empty inspector
    assert inspector._empty.isVisibleTo(inspector)
    assert not inspector._grid_host.isVisibleTo(inspector)


# --------------------------------------------- 4.4 labeled result count

def _make_panel(rows: int = 0):
    panel = search_panel_mod.SearchPanel(
        'deletion.search_bases', ['a', 'b'], [100, 100])
    for i in range(rows):
        panel.add_item([f'r{i}', f'g{i}'])
    return panel


def test_count_label_single_result(app):
    panel = _make_panel(1)
    assert panel.count_label.text() == '1 result'


def test_count_label_many_results(app):
    panel = _make_panel(5)
    assert panel.count_label.text() == '5 results'


def test_count_label_filtered_subset(app):
    panel = _make_panel(5)
    panel._on_search('r1')
    assert panel.count_label.text() == '1 of 5 results'
    panel._on_search('')
    assert panel.count_label.text() == '5 results'


def test_count_label_updates_live(app):
    panel = _make_panel(0)
    assert panel.count_label.text() == '0 results'
    panel.add_item(['x', 'y'])
    assert panel.count_label.text() == '1 result'
    panel.add_item(['z', 'w'])
    assert panel.count_label.text() == '2 results'
    panel.clear()
    assert panel.count_label.text() == '0 results'


# ------------------------------------- 4.3 ID columns copy/mono treatment

def test_bases_id_columns_copyable_and_mono(window, app):
    window._setup_bases_tab()
    assert window.bases_panel._copyable_columns == {0, 1}
    assert window.bases_panel._mono_columns == {0, 1}
    base_id = 'B7D8465740F80E0E7AC081991A033220'
    window.bases_panel.add_item(['B7D84657…', '707E7DCC…', 'g', 1],
                                tooltips={0: base_id, 1: 'G' * 32})
    window.bases_panel.tree.setCurrentItem(window.bases_panel.tree.topLevelItem(0))
    item = window.bases_panel.get_selected_item()
    assert item.data(0, search_panel_mod.GUID_ROLE) == base_id


def test_copyable_tree_ctrl_c_copies_full_guid(window, app):
    from PyQt6.QtGui import QKeySequence, QKeyEvent
    from PyQt6.QtCore import Qt as _Qt
    from PyQt6.QtWidgets import QApplication
    window._setup_bases_tab()
    base_id = 'B7D8465740F80E0E7AC081991A033220'
    window.bases_panel.add_item(['B7D84657…', 'x', 'g', 1],
                                tooltips={0: base_id})
    window.bases_panel.tree.setCurrentItem(window.bases_panel.get_selected_item())
    event = QKeyEvent(QKeyEvent.Type.KeyPress, _Qt.Key.Key_C,
                      _Qt.KeyboardModifier.ControlModifier)
    window.bases_panel.tree.keyPressEvent(event)
    assert QApplication.clipboard().text() == base_id


# ------------------------------------------------ 4.5 open in base inventory

def test_open_in_base_inventory_routes_and_targets_guild(window, app):
    window._setup_bases_tab()
    guild_id = '707E7DCC8C7B7D4C9A2E0B1A3F4D5E60'
    window.bases_panel.add_item(['B7D84657…', '707E7DCC…', 'g', 1],
                                tooltips={0: 'B' * 32, 1: guild_id})
    window.bases_panel.tree.setCurrentItem(window.bases_panel.tree.topLevelItem(0))
    nav_calls, guild_calls = [], []

    class _Tab:
        def select_guild(self, gid):
            guild_calls.append(gid)
    window.base_inventory_tab = _Tab()
    window._activate_nav = lambda pid: nav_calls.append(pid)
    window._open_base_in_inventory()
    assert nav_calls == ['base_inventory']
    assert guild_calls == [guild_id]


def test_base_inventory_select_guild_queues_when_not_loaded(app):
    bi_mod = import_from('palworld_aio.ui.tabs.base_inventory_tab')
    tab = bi_mod.BaseInventoryTab.__new__(bi_mod.BaseInventoryTab)
    tab._guilds_data = []
    tab._pending_guild_selection = None
    tab._on_guild_changed = lambda gid: (_ for _ in ()).throw(
        AssertionError('should not run before guild data loads'))
    tab.select_guild('some-guild-id')
    assert tab._pending_guild_selection == 'some-guild-id'


def test_base_inventory_select_guild_routes_when_loaded(app):
    bi_mod = import_from('palworld_aio.ui.tabs.base_inventory_tab')
    tab = bi_mod.BaseInventoryTab.__new__(bi_mod.BaseInventoryTab)
    tab._guilds_data = [{'id': 'g1'}, {'id': 'g2'}]
    calls = []
    tab._on_guild_changed = lambda gid: calls.append(gid)
    tab.select_guild('g2')
    assert calls == ['g2']
