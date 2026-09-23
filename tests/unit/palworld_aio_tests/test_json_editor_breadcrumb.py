"""Focused tests for the JSON Editor path breadcrumb
(uiux-audit-remediation 7.3 / design D12). Widgets are constructed
standalone offscreen.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

tab_mod = import_from('palworld_aio.ui.tabs.json_editor_tab')
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
def tab(app):
    return tab_mod.JsonEditorTab(None)


def _populate(tab, data):
    tab._populate_tree(data)
    return tab._tree.topLevelItem(0)


def _descend(node, depth):
    """Walk `depth` levels down, expanding lazy containers along the way."""
    for _ in range(depth):
        if isinstance(node, tab_mod.LazyJsonItem):
            node.setExpanded(True)
            node.load_children()
        node = node.child(0)
    return node


def _visible_crumb_texts(tab):
    return [lbl.text() for lbl in tab._breadcrumb_crumb_labels
            if not lbl.isHidden()]


# -------------------------------------------------- breadcrumb updates

def test_breadcrumb_shows_path_on_selection(tab):
    root = _populate(tab, {'a': {'b': {'c': 1}}})
    child = _descend(root, 3)
    assert child.text(0) == 'c'
    tab._tree.setCurrentItem(child)
    assert _visible_crumb_texts(tab) == ['root', 'a', 'b', 'c']
    # crumbs are up, so the root placeholder must be retired
    assert tab._breadcrumb_placeholder.isHidden()


def test_breadcrumb_placeholder_on_empty_tree(tab):
    tab._populate_tree({})  # exercises the clear() repopulation path
    tab._tree.clear()
    tab._breadcrumb_current = None
    tab._update_breadcrumb()
    assert not tab._breadcrumb_placeholder.isHidden()
    assert all(lbl.isHidden() for lbl in tab._breadcrumb_crumb_labels)


def test_breadcrumb_uses_last_visited_item_when_selection_cleared(tab):
    root = _populate(tab, {'a': {'b': 1}})
    child = root.child(0)
    tab._tree.setCurrentItem(child)
    tab._tree.clearSelection()
    tab._update_breadcrumb()
    assert _visible_crumb_texts(tab) == ['root', 'a']


def test_repopulate_does_not_crash_on_stale_breadcrumb_item(tab):
    root = _populate(tab, {'a': {'b': 1}})
    tab._tree.setCurrentItem(root.child(0))
    _populate(tab, {'fresh': 1})  # clear() invalidates the old items
    assert tab._breadcrumb_current is None
    assert not tab._breadcrumb_placeholder.isHidden()


# -------------------------------------------------- click navigation

def test_clicking_crumb_selects_ancestor(tab):
    root = _populate(tab, {'a': {'b': {'c': 1}}})
    deep = _descend(root, 3)
    tab._tree.setCurrentItem(deep)
    ancestor_lbl = tab._breadcrumb_crumb_labels[1]  # 'a' crumb
    assert ancestor_lbl._json_path_item is root.child(0)
    ancestor_lbl.clicked.emit()
    assert tab._tree.currentItem() is root.child(0)


def test_lazy_ancestors_load_on_crumb_click(tab):
    root = _populate(tab, {'a': {'b': {'c': 1}}})
    deep = _descend(root, 3)
    mid = deep.parent()  # 'b', attached but flagged as never-expanded
    assert mid.text(0) == 'b'
    mid._children_loaded = False
    tab._on_breadcrumb_clicked(deep)  # must load ancestors, not raise
    assert mid._children_loaded
    assert mid.childCount() > 0


def test_crumb_without_item_reference_is_noop(tab):
    root = _populate(tab, {'a': 1})
    tab._tree.setCurrentItem(root.child(0))
    orphan = tab_mod._ClickableCrumb('stray')
    orphan.clicked.emit()
    assert tab._tree.currentItem() is root.child(0)


# -------------------------------------------------- elision

def test_deep_path_elides_beyond_max_crumbs(tab):
    deep_data = current = {}
    for i in range(10):
        nxt = {}
        current[f'k{i}'] = nxt
        current = nxt
    root = _populate(tab, deep_data)
    node = _descend(root, 10)
    assert node is not None
    tab._tree.setCurrentItem(node)
    visible = _visible_crumb_texts(tab)
    assert len(visible) == tab._BREADCRUMB_MAX_CRUMBS
    assert visible[-1] == 'k9'
    assert 'k3' not in visible
    assert not tab._crumb_elide_label.isHidden()
    assert '(5)' in tab._crumb_elide_label.text()


# -------------------------------------------------- QSS / i18n wiring

def test_breadcrumb_styled_via_qss_not_inline(tab):
    qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
    built = qss_mod.build_qss('dark')
    assert 'QLabel#jsonCrumb' in built
    assert 'QLabel#jsonCrumbMuted' in built
    assert 'QWidget#jsonBreadcrumb' in built
    assert tab._breadcrumb_host.objectName() == 'jsonBreadcrumb'
    assert tab._breadcrumb_host.styleSheet() == ''


def test_breadcrumb_root_label_uses_i18n_key():
    assert i18n_mod.t('json_editor.breadcrumb_root') == 'root'


def test_crumb_labels_are_clickable_qlabel_subclass(tab):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel
    assert issubclass(tab_mod._ClickableCrumb, QLabel)
    root = _populate(tab, {'a': 1})
    tab._tree.setCurrentItem(root.child(0))
    for lbl in tab._breadcrumb_crumb_labels:
        if not lbl.isHidden():
            assert isinstance(lbl, tab_mod._ClickableCrumb)
            assert lbl.cursor().shape() == Qt.CursorShape.PointingHandCursor
            assert lbl.receivers(lbl.clicked) > 0


# -------------------------------------------------- search navigation

def test_search_finds_unexpanded_nested_values_and_reports_position(tab):
    _populate(tab, {'closed': {'deeper': {'target': 'needle'}}})
    tab._search_input.setText('needle')
    tab._do_search()

    assert len(tab._search_matches) == 1
    assert tab._tree.currentItem().text(0) == 'target'
    assert tab._search_count_label.text() == '1 of 1 match'
    assert tab._search_prev_btn.isEnabled()
    assert tab._search_next_btn.isEnabled()


def test_search_next_previous_wrap_and_update_explicit_count(tab):
    _populate(tab, {
        'first_match': 1,
        'nested': {'second_match': 2},
    })
    tab._search_input.setText('match')
    tab._do_search()

    assert tab._search_count_label.text() == '1 of 2 matches'
    first = tab._tree.currentItem()
    tab._search_next()
    assert tab._tree.currentItem() is not first
    assert tab._search_count_label.text() == '2 of 2 matches'
    tab._search_next()
    assert tab._tree.currentItem() is first
    assert tab._search_count_label.text() == '1 of 2 matches'
    tab._search_prev()
    assert tab._search_count_label.text() == '2 of 2 matches'


def test_empty_search_disables_match_navigation(tab):
    _populate(tab, {'name': 'Lamball'})
    tab._search_input.setText('missing')
    tab._do_search()
    assert tab._search_count_label.text() == 'No matches'
    assert not tab._search_prev_btn.isEnabled()
    assert not tab._search_next_btn.isEnabled()


# -------------------------------------------------- inline validation

def test_valid_scalar_edit_preserves_type_and_updates_tree_model(
        tab, monkeypatch):
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', None)
    root = _populate(tab, {'count': 3})
    item = root.child(0)

    item.setText(1, '7')

    rebuilt_root = tab._tree.topLevelItem(0)
    assert rebuilt_root.raw_value == {'count': 7}
    assert rebuilt_root.child(0).raw_value == 7
    assert rebuilt_root.child(0).text(2) == 'int'
    assert tab._status_label.property('role') == 'success'


def test_invalid_scalar_edit_is_rejected_without_mutating_data(
        tab, monkeypatch):
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', None)
    root = _populate(tab, {'count': 3})
    item = root.child(0)

    item.setText(1, 'not-a-number')

    assert root.raw_value == {'count': 3}
    assert item.raw_value == 3
    assert item.text(1) == '3'
    assert tab._status_label.property('role') == 'danger'
    assert tab._status_label.text().startswith('Invalid value:')


def test_loaded_save_edit_applies_only_the_validated_gvas(
        tab, monkeypatch):
    from types import SimpleNamespace

    gvas_mod = import_from('palsav.gvas')
    validated = object()
    loaded = SimpleNamespace(_gvas_file=object())
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)
    monkeypatch.setattr(gvas_mod.GvasFile, 'load', lambda data: validated)
    applied = []
    tab.save_applied.connect(lambda: applied.append(True))
    root = _populate(tab, {'enabled': False})

    root.child(0).setText(1, 'true')

    assert loaded._gvas_file is validated
    assert tab._tree.topLevelItem(0).raw_value == {'enabled': True}
    assert applied == [True]


def test_schema_validation_failure_keeps_loaded_gvas_and_tree_data(
        tab, monkeypatch):
    from types import SimpleNamespace

    gvas_mod = import_from('palsav.gvas')
    original_gvas = object()
    loaded = SimpleNamespace(_gvas_file=original_gvas)
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)

    def reject_candidate(_data):
        raise ValueError('schema mismatch')

    monkeypatch.setattr(gvas_mod.GvasFile, 'load', reject_candidate)
    root = _populate(tab, {'count': 3})
    item = root.child(0)

    item.setText(1, '4')

    assert loaded._gvas_file is original_gvas
    assert root.raw_value == {'count': 3}
    assert item.text(1) == '3'
    assert 'schema mismatch' in tab._status_label.text()


def test_container_rows_are_read_only_and_scalar_rows_are_editable(tab):
    from PyQt6.QtCore import Qt

    root = _populate(tab, {'container': {'value': 1}, 'leaf': 'text'})
    container = root.child(0)
    leaf = root.child(1)
    assert not container.flags() & Qt.ItemFlag.ItemIsEditable
    assert leaf.flags() & Qt.ItemFlag.ItemIsEditable


def test_json_actions_expose_refresh_export_import_hierarchy(tab):
    assert tab._refresh_btn.property('controlRole') == 'tertiary'
    assert tab._export_btn.property('controlRole') == 'secondary'
    assert tab._import_btn.property('controlRole') == 'warning'
    assert tab._refresh_btn.accessibleDescription()
    assert tab._export_btn.accessibleDescription()
    assert tab._import_btn.accessibleDescription()


def test_json_editor_no_longer_adds_a_legacy_page_ribbon():
    import inspect

    source = inspect.getsource(tab_mod.JsonEditorTab._setup_ui)
    assert 'create_page_ribbon' not in source


# -------------------------------------------------- guarded raw mode

def test_raw_mode_uses_shared_switch_and_hides_tree_search(
        tab, monkeypatch):
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', None)
    _populate(tab, {'name': 'Lamball'})

    tab._view_control.set_current('raw')

    assert tab._view_stack.currentWidget() is tab._raw_page
    assert not tab._search_host.isVisible()
    assert not tab._breadcrumb_host.isVisible()
    assert '"Lamball"' in tab._raw_editor.toPlainText()
    assert not tab._raw_apply_btn.isEnabled()

    tab._view_control.set_current('tree')
    assert tab._view_stack.currentWidget() is tab._tree


def test_invalid_raw_json_never_reaches_confirmation_or_loaded_save(
        tab, monkeypatch):
    from types import SimpleNamespace

    original_gvas = object()
    loaded = SimpleNamespace(_gvas_file=original_gvas)
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)
    _populate(tab, {'count': 3})
    tab._view_control.set_current('raw')
    tab._raw_editor.setPlainText('{ invalid json')
    monkeypatch.setattr(
        tab, '_confirm_raw_apply',
        lambda: pytest.fail('invalid JSON must not reach confirmation'))

    tab._apply_raw_json()

    assert loaded._gvas_file is original_gvas
    assert tab._tree.topLevelItem(0).raw_value == {'count': 3}
    assert tab._raw_validation_label.property('role') == 'danger'
    assert 'not applied' in tab._raw_validation_label.text()


def test_raw_schema_failure_never_reaches_confirmation_or_apply(
        tab, monkeypatch):
    from types import SimpleNamespace

    original_gvas = object()
    loaded = SimpleNamespace(_gvas_file=original_gvas)
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)
    _populate(tab, {'count': 3})
    tab._view_control.set_current('raw')
    tab._raw_editor.setPlainText('{"count": 4}')
    monkeypatch.setattr(
        tab, '_validate_candidate',
        lambda _data: (_ for _ in ()).throw(ValueError('schema mismatch')))
    monkeypatch.setattr(
        tab, '_confirm_raw_apply',
        lambda: pytest.fail('invalid schema must not reach confirmation'))

    tab._apply_raw_json()

    assert loaded._gvas_file is original_gvas
    assert tab._tree.topLevelItem(0).raw_value == {'count': 3}
    assert 'schema mismatch' in tab._raw_validation_label.text()


def test_cancelling_validated_raw_apply_preserves_loaded_save_and_edit(
        tab, monkeypatch):
    from types import SimpleNamespace

    original_gvas = object()
    validated_gvas = object()
    loaded = SimpleNamespace(_gvas_file=original_gvas)
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)
    _populate(tab, {'count': 3})
    tab._view_control.set_current('raw')
    tab._raw_editor.setPlainText('{"count": 4}')
    monkeypatch.setattr(
        tab, '_validate_candidate', lambda _data: validated_gvas)
    monkeypatch.setattr(tab, '_confirm_raw_apply', lambda: False)

    tab._apply_raw_json()

    assert loaded._gvas_file is original_gvas
    assert tab._tree.topLevelItem(0).raw_value == {'count': 3}
    assert tab._raw_editor.toPlainText() == '{"count": 4}'
    assert tab._raw_apply_btn.isEnabled()
    assert 'unchanged' in tab._raw_validation_label.text()


def test_validated_confirmed_raw_apply_swaps_gvas_once(
        tab, monkeypatch):
    from types import SimpleNamespace
    from PyQt6.QtTest import QSignalSpy

    original_gvas = object()
    validated_gvas = object()
    loaded = SimpleNamespace(_gvas_file=original_gvas)
    monkeypatch.setattr(tab_mod.constants, 'loaded_level_json', loaded)
    _populate(tab, {'count': 3})
    tab._view_control.set_current('raw')
    tab._raw_editor.setPlainText('{"count": 4}')
    monkeypatch.setattr(
        tab, '_validate_candidate', lambda _data: validated_gvas)
    monkeypatch.setattr(tab, '_confirm_raw_apply', lambda: True)
    applied = QSignalSpy(tab.save_applied)

    tab._apply_raw_json()

    assert loaded._gvas_file is validated_gvas
    assert tab._tree.topLevelItem(0).raw_value == {'count': 4}
    assert len(applied) == 1
    assert not tab._raw_apply_btn.isEnabled()
    assert tab._raw_validation_label.property('role') == 'success'
