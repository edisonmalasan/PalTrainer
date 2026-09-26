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
import types

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

components = import_from('palworld_aio.ui.chrome.components')
search_panel_mod = import_from('palworld_aio.widgets.search_panel')
main_window_mod = import_from('palworld_aio.ui.main_window')
bases_page_mod = import_from('palworld_aio.ui.pages.bases_page')
guilds_page_mod = import_from('palworld_aio.ui.pages.guilds_page')
guild_manager_mod = import_from('palworld_aio.managers.guild_manager')
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
    class _Ctx:
        def set_base(self, v):
            context_calls.append(('base', v.identifier))
        def set_guild(self, v):
            context_calls.append(('guild', v.identifier))
    context_calls = []
    window.workspace_context = _Ctx()
    record = bases_page_mod.BaseRow(
        base_id, 'Base 1', guild_id, 'Unnamed Guild', 1,
        'X 10, Y 20')
    window.bases_page.set_bases((record,))
    window.bases_panel.tree.setCurrentItem(
        window.bases_panel.tree.topLevelItem(0))
    inspector = window._bases_inspector
    assert inspector._title.text() == 'Base 1'
    assert inspector._rows[1][1].text() == 'Unnamed Guild'
    assert inspector._rows[4][1].value() == base_id
    assert inspector._rows[5][1].value() == guild_id
    assert not inspector._empty.isVisibleTo(inspector)
    window._on_base_record_selected(record)
    assert context_calls == [('guild', guild_id), ('base', base_id)]


def test_bases_inspector_clears_when_refreshed(window, app):
    window._setup_bases_tab()
    inspector = window._bases_inspector
    inspector.show_details('Base 1', {0: 'g'})
    window._refresh_bases()  # no save loaded -> empty table + empty inspector
    assert inspector._empty.isVisibleTo(inspector)
    assert not inspector._grid_host.isVisibleTo(inspector)


def test_bases_refresh_builds_human_names_and_location_metadata(
        window, app, monkeypatch):
    window._setup_bases_tab()
    monkeypatch.setattr(main_window_mod.constants, 'loaded_level_json', {'loaded': True})
    data_manager = import_from('palworld_aio.managers.data_manager')
    monkeypatch.setattr(main_window_mod, 'get_bases', lambda: [
        {'id': 'b1', 'guild_id': 'g1', 'guild_name': 'Builders'},
        {'id': 'b2', 'guild_id': 'g1', 'guild_name': 'Builders'},
        {'id': 'b3', 'guild_id': 'g2', 'guild_name': 'Explorers'},
    ])
    monkeypatch.setattr(
        data_manager, 'get_base_coords',
        lambda base_id: (10.4, -20.6) if base_id == 'b1' else (None, None))
    monkeypatch.setattr(
        main_window_mod.save_manager, 'get_guild_level_by_id',
        lambda guild_id: 12 if guild_id == 'g1' else 7)

    window._refresh_bases()

    records = window.bases_page._records
    assert records['b1'].name == 'Base 1'
    assert records['b2'].name == 'Base 2'
    assert records['b3'].name == 'Base 1'
    assert records['b1'].location == 'X 10, Y -21'
    assert records['b1'].guild_level == 12


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
    assert window.bases_panel._copyable_columns == {5}
    assert window.bases_panel._mono_columns == {5, 6, 7}
    base_id = 'B7D8465740F80E0E7AC081991A033220'
    window.bases_page.set_bases((bases_page_mod.BaseRow(
        base_id, 'Base 1', 'G' * 32, 'g', 1),))
    window.bases_panel.tree.setCurrentItem(window.bases_panel.tree.topLevelItem(0))
    item = window.bases_panel.get_selected_item()
    assert item.data(5, search_panel_mod.GUID_ROLE) == base_id


def test_copyable_tree_ctrl_c_copies_full_guid(window, app):
    from PyQt6.QtGui import QKeySequence, QKeyEvent
    from PyQt6.QtCore import Qt as _Qt
    from PyQt6.QtWidgets import QApplication
    window._setup_bases_tab()
    base_id = 'B7D8465740F80E0E7AC081991A033220'
    window.bases_page.set_bases((bases_page_mod.BaseRow(
        base_id, 'Base 1', '', 'g', 1),))
    window.bases_panel.tree.setCurrentItem(window.bases_panel.get_selected_item())
    event = QKeyEvent(QKeyEvent.Type.KeyPress, _Qt.Key.Key_C,
                      _Qt.KeyboardModifier.ControlModifier)
    window.bases_panel.tree.keyPressEvent(event)
    assert QApplication.clipboard().text() == base_id


# ------------------------------------------------ 4.5 open in base inventory

def test_open_in_base_inventory_routes_and_targets_guild(window, app):
    window._setup_bases_tab()
    guild_id = '707E7DCC8C7B7D4C9A2E0B1A3F4D5E60'
    nav_calls, guild_calls = [], []

    class _Context:
        def set_base(self, _value):
            pass
        def set_guild(self, _value):
            pass
    window.workspace_context = _Context()
    window.bases_page.set_bases((bases_page_mod.BaseRow(
        'B' * 32, 'Base 1', guild_id, 'g', 1),))
    window.bases_panel.tree.setCurrentItem(window.bases_panel.tree.topLevelItem(0))

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


# ------------------------------------------ Task 5: Players page slice

@pytest.fixture
def pwindow(app):
    """MainWindow shell with the Players page set up (no save loaded)."""
    from PyQt6.QtWidgets import QStackedWidget
    win = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    win.stacked_widget = QStackedWidget()
    win._setup_players_tab()
    return win


def test_players_layout_has_inspector_column(pwindow):
    assert hasattr(pwindow, 'players_panel')
    assert isinstance(pwindow._players_inspector_column,
                      components.InspectorSideColumn)
    assert pwindow._players_inspector_column.width() == 340
    assert pwindow._players_inspector._empty.isVisibleTo(pwindow._players_inspector)
    assert 'Select a player' in pwindow._players_inspector._empty.text()


def test_players_inspector_populates_on_selection(pwindow, app):
    import types
    uid = '0E656D544A2B4C3D8E9F0A1B2C3D4E5F'
    guild_id = '707E7DCC8C7B7D4C9A2E0B1A3F4D5E60'

    class _Ctx:
        def set_player(self, v):
            pass
        def set_guild(self, v):
            pass
    pwindow.app_bar = types.SimpleNamespace(context=_Ctx())
    pwindow.players_panel.add_item(
        ['Tester', '2h', 30, 12, '0E656D54…', 'Guild A', '707E7DCC…', 5],
        tooltips={4: uid})
    pwindow.players_panel.tree.setCurrentItem(
        pwindow.players_panel.tree.topLevelItem(0))
    # GUID_ROLE for guild_id: SearchPanel stores the tooltip there
    pwindow.players_panel.add_item(
        ['Other', '5h', 12, 3, 'AAAA1111…', 'Guild A', '707E7DCC…', 5],
        tooltips={4: 'AAAA1111BBBB4C3D8E9F0A1B2C3D4E5F'})
    pwindow.players_panel.tree.setCurrentItem(
        pwindow.players_panel.tree.topLevelItem(0))
    pwindow._on_player_selected(['Tester', '2h', '30', '12', '0E656D54…',
                                 'Guild A', '707E7DCC…', '5'])
    inspector = pwindow._players_inspector
    assert inspector._title.text() == 'Tester'
    assert inspector._rows[0][1].text() == '30'
    assert inspector._rows[1][1].text() == '2h'
    assert inspector._rows[2][1].text() == '12'
    assert inspector._rows[3][1].text() == 'Guild A'
    assert inspector._rows[5][1].value() == uid
    assert inspector._rows[6][1].value() == '707E7DCC…'  # no tooltip -> display
    assert not inspector._empty.isVisibleTo(inspector)


def test_players_inspector_clears_when_refreshed(pwindow, app):
    pwindow._players_inspector.show_details('Tester', {0: 'x'})
    pwindow._refresh_players()  # no save loaded -> empty table + empty inspector
    assert pwindow._players_inspector._empty.isVisibleTo(pwindow._players_inspector)
    assert not pwindow._players_inspector._grid_host.isVisibleTo(pwindow._players_inspector)


def test_bulk_footer_below_shared_entity_browser(pwindow, app):
    """The contextual bulk bar follows the complete shared browser."""
    bulk = pwindow._players_bulk_frame
    players_page = pwindow.players_page
    assert bulk.parentWidget() is players_page
    column_layout = players_page.layout()
    idx_panel = column_layout.indexOf(players_page.entity_browser)
    idx_bulk = column_layout.indexOf(bulk)
    assert idx_bulk == idx_panel + 1


def test_bulk_buttons_exist_with_same_handlers(pwindow, app):
    expected = {
        'bulk_item_btn': '_open_bulk_player_item_dialog',
        'bulk_pal_btn': '_open_bulk_player_pal_dialog',
        'bulk_tech_btn': '_open_bulk_technology_dialog',
        'bulk_guild_btn': '_open_guild_assign_dialog',
    }
    for attr, handler in expected.items():
        btn = getattr(pwindow, attr)
        assert btn is not None
        assert hasattr(pwindow, handler)
        assert callable(getattr(pwindow, handler))
    assert pwindow.bulk_label.objectName() == 'bulkHintLabel'


def test_players_uid_guild_columns_copyable_and_mono(pwindow, app):
    assert pwindow.players_panel._copyable_columns == {6, 7}
    assert pwindow.players_panel._mono_columns == {6, 7}
    assert pwindow.players_panel.tree.isColumnHidden(6)
    assert pwindow.players_panel.tree.isColumnHidden(7)


def test_players_table_fills_shared_browser_workspace(pwindow, app):
    pwindow._refresh_players()
    assert pwindow.players_panel.maximumHeight() == 16777215
    assert pwindow.players_page.layout().stretch(0) == 1
    # The legacy cap helper remains for World pages not yet migrated.
    assert main_window_mod.MainWindow._cap_search_table_height is not None
    assert hasattr(main_window_mod.MainWindow, '_cap_bases_table_height')


def test_shared_cap_helper_caps_both_panels(pwindow, app):
    base_win = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    from PyQt6.QtWidgets import QStackedWidget
    base_win.stacked_widget = QStackedWidget()
    base_win._setup_bases_tab()
    helper = main_window_mod.MainWindow._cap_search_table_height
    helper(base_win, base_win.bases_panel, '_x_chrome', 200)
    helper(pwindow, pwindow.players_panel, '_y_chrome', 200)
    assert base_win.bases_panel.maximumHeight() >= 180
    assert pwindow.players_panel.maximumHeight() >= 180


# ------------------------------------------ Task 6: Guilds page slice

@pytest.fixture
def gwindow(app):
    """MainWindow shell with the Guilds page set up (no save loaded)."""
    from PyQt6.QtWidgets import QStackedWidget
    win = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    win.stacked_widget = QStackedWidget()
    win._setup_guilds_tab()
    return win


def test_guilds_layout_has_inspector_column(gwindow):
    assert hasattr(gwindow, 'guilds_panel')
    assert isinstance(gwindow._guilds_inspector_column,
                      components.InspectorSideColumn)
    assert gwindow._guilds_inspector_column.width() == 340
    assert gwindow._guilds_inspector._empty.isVisibleTo(gwindow._guilds_inspector)
    assert 'Click a guild row' in gwindow._guilds_inspector._empty.text()
    assert gwindow.guild_members_panel.isHidden()


def test_guilds_inspector_populates_on_selection(gwindow, app, monkeypatch):
    guild_id = '707E7DCC8C7B7D4C9A2E0B1A3F4D5E60'

    class _Ctx:
        def set_guild(self, v):
            pass
    gwindow.workspace_context = _Ctx()
    monkeypatch.setattr(main_window_mod, 'get_guild_members', lambda gid: [])
    gwindow.guilds_page.set_guilds((
        guilds_page_mod.GuildRow(guild_id, 'Guild A', 5, 12, 2),
    ))
    gwindow.guilds_panel.tree.setCurrentItem(
        gwindow.guilds_panel.tree.topLevelItem(0))
    inspector = gwindow._guilds_inspector
    assert inspector._title.text() == 'Guild A'
    assert inspector._rows[0][1].text() == '5'
    assert inspector._rows[1][1].text() == '12'
    assert inspector._rows[2][1].text() == '2'
    assert inspector._rows[3][1].value() == guild_id
    assert not inspector._empty.isVisibleTo(inspector)


def test_guilds_inspector_clears_when_refreshed(gwindow, app):
    gwindow._guilds_inspector.show_details('Guild A', {0: 'x'})
    gwindow._refresh_guilds()  # no save loaded -> empty table + empty inspector
    assert gwindow._guilds_inspector._empty.isVisibleTo(gwindow._guilds_inspector)
    assert not gwindow._guilds_inspector._grid_host.isVisibleTo(gwindow._guilds_inspector)


def test_members_empty_state_uses_row_level_wording(gwindow, app, monkeypatch):
    """ui-pages delta: no-selection copy describes the row interaction and
    never implies no global selection was made."""
    empty = gwindow._guilds_inspector._empty
    assert 'Click a guild row' in empty.text()
    monkeypatch.setattr(main_window_mod, 'get_guilds', lambda: [])
    monkeypatch.setattr(main_window_mod, 'get_bases', lambda: [])
    gwindow._refresh_guilds()
    assert 'Click a guild row' in empty.text()
    assert gwindow.guild_members_panel.isHidden()


def test_guilds_id_columns_copyable_and_mono(gwindow, app):
    assert gwindow.guilds_panel._copyable_columns == {4}
    assert gwindow.guilds_panel._mono_columns == {4, 5}
    assert gwindow.guild_members_panel._copyable_columns == {5}
    assert gwindow.guild_members_panel._mono_columns == {5}


def test_guild_members_browser_is_nested_in_inspector(gwindow, app):
    assert gwindow.guild_members_panel.parentWidget() is gwindow._guilds_inspector
    assert gwindow.guild_members_panel in gwindow._guilds_inspector._content_widgets


def test_guilds_refresh_adds_base_counts(gwindow, app, monkeypatch):
    monkeypatch.setattr(main_window_mod.constants, 'loaded_level_json', {'loaded': True})
    monkeypatch.setattr(main_window_mod, 'get_guilds', lambda: [{
        'id': 'GUILD-1', 'name': 'Guild A', 'level': 8, 'member_count': 2,
    }])
    monkeypatch.setattr(main_window_mod, 'get_bases', lambda: [
        {'guild_id': 'GUILD-1'}, {'guild_id': 'GUILD-1'},
    ])
    gwindow._refresh_guilds()
    record = gwindow.guilds_page._guilds['GUILD-1']
    assert record.name == 'Guild A'
    assert record.base_count == 2
    assert gwindow.guilds_panel.tree.topLevelItem(0).text(0) == 'Guild A'


def test_guild_and_member_selection_propagate_identifiers(
        gwindow, app, monkeypatch):
    updates = {}

    class _Context:
        def set_guild(self, selection):
            updates['guild'] = selection

        def set_player(self, selection):
            updates['player'] = selection

    gwindow.workspace_context = _Context()
    monkeypatch.setattr(main_window_mod, 'get_guild_members', lambda gid: [{
        'uid': 'PLAYER-1', 'name': 'Ada', 'role_label': 'Guild Master',
        'level': 55, 'pals': 40, 'lastseen': '2h ago', 'is_leader': True,
        'role': 1, 'last_sort': 7200,
    }])
    guild = guilds_page_mod.GuildRow('GUILD-1', 'Guild A', 8, 1, 2)
    gwindow.guilds_page.set_guilds((guild,))
    gwindow.guilds_panel.tree.topLevelItem(0).setSelected(True)
    gwindow._on_guild_record_selected(guild)
    assert updates['guild'].identifier == 'GUILD-1'
    assert gwindow.guild_members_panel.tree.topLevelItemCount() == 1
    gwindow.guild_members_panel.tree.setCurrentItem(
        gwindow.guild_members_panel.tree.topLevelItem(0))
    gwindow._on_guild_member_record_selected(
        gwindow.guilds_page._members['PLAYER-1'])
    assert updates['player'].identifier == 'PLAYER-1'


def test_guild_role_mutation_uses_selected_guild_and_refreshes_members(
        gwindow, app, monkeypatch):
    calls = []
    class _Context:
        def set_guild(self, _selection):
            pass

    gwindow.workspace_context = _Context()
    monkeypatch.setattr(main_window_mod, 'get_guild_members', lambda gid: [])
    guild = guilds_page_mod.GuildRow('GUILD-1', 'Guild A', 8, 1, 0)
    gwindow.guilds_page.set_guilds((guild,))
    gwindow.guilds_panel.tree.setCurrentItem(
        gwindow.guilds_panel.tree.topLevelItem(0))
    monkeypatch.setattr(
        guild_manager_mod, 'set_member_role',
        lambda gid, uid, role: calls.append((gid, uid, role)))
    gwindow.refresh_all = lambda: None
    gwindow._show_info = lambda *args: None

    gwindow._set_guild_member_role('GUILD-1', 'PLAYER-1', 2)
    assert calls == [('GUILD-1', 'PLAYER-1', 2)]
    assert gwindow.guild_members_panel.tree.topLevelItemCount() == 0


def test_guild_related_links_navigate_with_precise_guild_filter(gwindow, app):
    updates = []
    routes = []
    player_filters = []
    base_filters = []

    class _Context:
        def set_guild(self, selection):
            updates.append(selection)

    class _Search:
        def __init__(self, target):
            self._target = target

        def setText(self, value):
            self._target.append(value)

    gwindow.workspace_context = _Context()
    gwindow._activate_nav = routes.append
    gwindow.players_page = types.SimpleNamespace(
        browser=types.SimpleNamespace(search_input=_Search(player_filters)))
    gwindow.bases_page = types.SimpleNamespace(
        browser=types.SimpleNamespace(search_input=_Search(base_filters)))
    guild = guilds_page_mod.GuildRow('GUILD-1', 'Guild A', 8, 1, 2)

    gwindow._open_guild_players(guild)
    gwindow._open_guild_bases(guild)
    assert routes == ['players', 'bases']
    assert player_filters == ['GUILD-1']
    assert base_filters == ['GUILD-1']
    assert [selection.identifier for selection in updates] == [
        'GUILD-1', 'GUILD-1',
    ]


# ------------------------------------------ Task 7: Exclusions add affordance

class _FakeInputDialog:
    result = ('', False)

    def __init__(self, result):
        _FakeInputDialog.result = result

    @staticmethod
    def getText(parent, title, label):
        return _FakeInputDialog.result


@pytest.fixture
def ewindow(app):
    """MainWindow shell with the Exclusions page set up."""
    from PyQt6.QtWidgets import QStackedWidget
    win = main_window_mod.MainWindow.__new__(main_window_mod.MainWindow)
    win.stacked_widget = QStackedWidget()
    win._setup_exclusions_tab()
    return win


def test_each_panel_has_add_affordance(ewindow, app):
    panels = {
        'players': ewindow.excl_players_panel,
        'guilds': ewindow.excl_guilds_panel,
        'bases': ewindow.excl_bases_panel,
    }
    for key, panel in panels.items():
        btn = ewindow._excl_add_buttons[key]
        assert btn.parent() is not None
        assert panel.footer_slot.indexOf(btn) >= 0  # lives in the panel footer
        assert '+ Add Exclusion' in btn.text()


def test_add_button_visible_in_empty_state_condition(ewindow, app):
    """The affordance lives in the panel footer, outside the empty-state
    overlay covering the tree viewport."""
    panel = ewindow.excl_players_panel
    btn = ewindow._excl_add_buttons['players']
    overlay = panel._empty_label
    assert overlay.parent() is panel.tree.viewport()
    assert btn.parentWidget() is not panel.tree.viewport()


def test_add_flow_routes_into_add_exclusion(ewindow, app, monkeypatch):
    calls = []
    monkeypatch.setattr(ewindow, '_add_exclusion',
                        lambda excl_type, value: calls.append((excl_type, value)))
    for key, value in (('players', 'UID-123'), ('guilds', 'GID-456'),
                       ('bases', 'BID-789')):
        calls.clear()
        monkeypatch.setattr(main_window_mod, 'QInputDialog',
                            _FakeInputDialog((f'  {value}  ', True)))
        ewindow._add_exclusion_via_prompt(key)
        assert calls == [(key, value)]  # trimmed value, correct excl_type


def test_add_flow_rejects_empty_and_cancel(ewindow, app, monkeypatch):
    calls = []
    monkeypatch.setattr(ewindow, '_add_exclusion',
                        lambda excl_type, value: calls.append((excl_type, value)))
    monkeypatch.setattr(main_window_mod, 'QInputDialog',
                        _FakeInputDialog(('   ', True)))
    ewindow._add_exclusion_via_prompt('players')
    monkeypatch.setattr(main_window_mod, 'QInputDialog',
                        _FakeInputDialog(('UID-1', False)))
    ewindow._add_exclusion_via_prompt('players')
    monkeypatch.setattr(main_window_mod, 'QInputDialog',
                        _FakeInputDialog(('', True)))
    ewindow._add_exclusion_via_prompt('players')
    assert calls == []  # empty/whitespace/cancelled input never adds
