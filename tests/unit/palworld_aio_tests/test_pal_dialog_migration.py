from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from
from tests.test_registry import PROJECT_ROOT

components = import_from('palworld_aio.ui.chrome.components')
create_dialogs = import_from(
    'palworld_aio.editor.pal_editor.create_dialogs')
fix_illegal = import_from('palworld_aio.ui.dialogs.fix_illegal_pal_dialog')
skill_picker = import_from('palworld_aio.ui.dialogs.skill_picker')
widgets = import_from('palworld_aio.editor.pal_editor.widgets')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture
def app():
    return _app_instance()


def _top_level_bases(path: Path) -> dict[str, set[str]]:
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    return {
        node.name: {
            base.id for base in node.bases if isinstance(base, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def test_pal_dialog_inventory_has_no_live_legacy_scaffold_entries():
    pal_editor = PROJECT_ROOT / 'src' / 'palworld_aio' / 'editor' / 'pal_editor'
    target_paths = [
        pal_editor / 'create_dialogs.py',
        pal_editor / 'pal_editor_bulk_ops.py',
        pal_editor / 'pal_editor_widget.py',
    ]

    for path in target_paths:
        source = path.read_text(encoding='utf-8-sig')
        assert 'FramelessDialog' not in source, path

    bases = _top_level_bases(target_paths[0])
    assert bases['PalCreateDialog'] == {'BaseDialog'}
    for name in (
        'BulkSyncPalDialog',
        'BulkSyncAllDialog',
        'BulkSpeciesDialog',
        'FoodPickerDialog',
        'CloneBulkDialog',
    ):
        assert bases[name] == {'PalEditorDialog'}

    editor_bases = _top_level_bases(target_paths[2])
    assert editor_bases['EditPalsDialog'] == {'PalEditorDialog'}
    assert _top_level_bases(
        PROJECT_ROOT / 'src' / 'palworld_aio' / 'ui' / 'dialogs'
        / 'fix_illegal_pal_dialog.py'
    )['FixIllegalPalDialog'] == {'BaseDialog'}


def test_pal_dialog_adapter_supplies_shared_keyboard_and_accessibility(app):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    dialog = widgets.PalEditorDialog('edit_pals.title')
    assert isinstance(dialog, components.BaseDialog)
    assert dialog.property('dialogFamily') == 'palEditor'
    assert dialog.accessibleName()
    assert dialog.accessibleDescription()
    assert dialog.content_layout is not None
    dialog.setWindowTitle('Selected Pal — Lamball')
    assert dialog.title_label.text() == 'Selected Pal — Lamball'
    assert dialog.accessibleName() == 'Selected Pal — Lamball'

    dialog.show()
    app.processEvents()
    QTest.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.result() == dialog.DialogCode.Rejected
    dialog.deleteLater()


def test_pal_create_keeps_created_item_cancel_contract(app, monkeypatch):
    monkeypatch.setattr(create_dialogs.PalFrame, '_NAMEMAP', {})
    editor = SimpleNamespace()

    dialog = create_dialogs.PalCreateDialog(editor, True, 2)

    assert isinstance(dialog, components.BaseDialog)
    assert dialog.created_item is None
    assert dialog.is_party is True
    assert dialog.slot_index == 2
    dialog.reject()
    assert dialog.created_item is None
    dialog.deleteLater()


def test_clone_bulk_keeps_counts_and_capacity_contract(app):
    dialog = create_dialogs.CloneBulkDialog([], 3)

    assert isinstance(dialog, widgets.PalEditorDialog)
    assert dialog.counts is None
    assert dialog._free == 3
    assert dialog._total() == 0
    assert not dialog._ok.isEnabled()
    dialog._on_accept()
    assert dialog.counts is None
    dialog.deleteLater()


def test_skill_picker_is_accessible_and_escape_cancels(app):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    picker = skill_picker.SkillPicker()
    assert picker.accessibleName() == 'Skill picker'
    assert picker._search.accessibleName() == 'Search skills'
    assert picker._list.accessibleName() == 'Skill results'

    picker._result = 'would-change'
    picker.show()
    app.processEvents()
    QTest.keyClick(picker, Qt.Key.Key_Escape)
    assert picker._result is None
    assert not picker.isVisible()
    picker.deleteLater()


def test_fix_illegal_pal_uses_shared_scaffold_and_preserves_selection(app):
    dialog = fix_illegal.FixIllegalPalDialog({})

    assert isinstance(dialog, components.BaseDialog)
    assert dialog._get_selected_uids() == []
    assert not dialog.fix_btn.isEnabled()
    dialog.reject()
    dialog.deleteLater()


def test_pal_picker_return_fields_remain_present_in_source():
    source = (PROJECT_ROOT / 'src' / 'palworld_aio' / 'editor'
              / 'pal_editor' / 'create_dialogs.py').read_text(
                  encoding='utf-8-sig')

    assert 'self.created_item = None' in source
    assert 'self.selected_food = None' in source
    assert 'self.selected_foods = []' in source
    assert 'self.counts = None' in source
    assert 'def ask(pals, free_slots, parent=None):' in source


def test_large_pal_dialogs_fit_the_supported_minimum_workspace():
    source = (PROJECT_ROOT / 'src' / 'palworld_aio' / 'editor'
              / 'pal_editor' / 'create_dialogs.py').read_text(
                  encoding='utf-8-sig')
    editor_source = (PROJECT_ROOT / 'src' / 'palworld_aio' / 'editor'
                     / 'pal_editor' / 'pal_editor_widget.py').read_text(
                         encoding='utf-8-sig')

    assert 'setMinimumSize(740, 750)' not in source
    assert 'setMinimumSize(1200, 800)' not in editor_source
    assert 'setMinimumSize(980, 640)' in editor_source
