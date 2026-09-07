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
