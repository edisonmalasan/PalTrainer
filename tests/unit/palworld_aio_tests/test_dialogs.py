"""Contracts for the final simple-dialog and popup migration inventory."""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

components = import_from('palworld_aio.ui.chrome.components')
dialogs = import_from('palworld_aio.editor.dialogs')
worldoption = import_from('palworld_aio.editor.worldoption_editor')

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_INVENTORY = (
    PROJECT_ROOT
    / 'openspec'
    / 'changes'
    / 'implement-audit-uiux-rehaul'
    / 'migration-inventory.md'
)
_app = None


@pytest.fixture(scope='module')
def app():
    global _app
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    import_from('i18n').load_resources('en_US')
    return _app


@pytest.mark.parametrize(
    'dialog',
    [
        lambda: dialogs.InputDialog('Name', 'Enter a name'),
        lambda: dialogs.DaysInputDialog('Days', 'Enter days'),
        dialogs.InactiveFilterDialog,
        lambda: dialogs.LevelInputDialog('Level', 'Enter level', 12),
        lambda: dialogs.GameDaysInputDialog('Game days', 'Enter days'),
        dialogs.KillNearestBaseDialog,
        lambda: dialogs.ConfirmDialog('Confirm', 'Continue?'),
        lambda: dialogs.RadiusInputDialog('Radius', 'New radius', 3500),
        lambda: dialogs.ScrollableGuildSelectionDialog({}),
        lambda: dialogs.GuildSelectionDialog({}),
        lambda: dialogs.ZoneManagementDialog(2),
        dialogs.NudgeInputDialog,
    ],
)
def test_general_editor_dialogs_use_shared_scaffold(app, dialog):
    from PyQt6.QtWidgets import QPushButton

    widget = dialog()
    assert isinstance(widget, components.BaseDialog)
    assert widget.content_layout is not None
    assert widget.accessibleName()
    widget.show()
    app.processEvents()
    for button in widget.findChildren(QPushButton):
        if button.isVisibleTo(widget):
            assert button.property('controlRole')
            assert button.accessibleName()
    widget.reject()


def test_world_option_editor_uses_shared_scaffold(app):
    data = {
        'properties': {
            'OptionWorldData': {
                'value': {'Settings': {'value': {}}},
            },
        },
    }
    dialog = worldoption.WorldOptionEditorDialog(data)
    assert isinstance(dialog, components.BaseDialog)
    assert dialog.title_label.text() == 'WorldOption Settings Editor'
    dialog.reject()


def test_live_dialog_imports_use_shared_adapters():
    roots = [PROJECT_ROOT / 'src']
    offenders = []
    for root in roots:
        for path in root.rglob('*.py'):
            if path.name == 'components.py':
                continue
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module != 'PyQt6.QtWidgets':
                    continue
                names = {alias.name for alias in node.names}
                legacy = names & {'QMessageBox', 'QInputDialog'}
                if legacy:
                    offenders.append((path.relative_to(PROJECT_ROOT), legacy))
    assert offenders == []


def test_no_unowned_simple_qdialog_or_popup_styles_remain():
    source_root = PROJECT_ROOT / 'src'
    allowed_qdialog_classes = {
        ('palworld_aio/ui/chrome/components.py', 'BaseDialog'),
        # Task 8.3 explicitly owns this dedicated complex workspace.
        ('palworld_toolsets/slot_injector.py', 'SlotNumUpdaterApp'),
    }
    found = set()
    direct_instances = []
    for path in source_root.rglob('*.py'):
        relative = path.relative_to(source_root).as_posix()
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = {
                    base.id for base in node.bases if isinstance(base, ast.Name)
                }
                if 'QDialog' in bases:
                    found.add((relative, node.name))
            elif (isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name)
                  and node.func.id == 'QDialog'):
                direct_instances.append((relative, node.lineno))
    assert found == allowed_qdialog_classes
    assert direct_instances == []

    for relative in (
        'palworld_aio/widgets/menu_popup.py',
        'palworld_aio/widgets/scrollable_context_menu.py',
        'palworld_aio/widgets/base_hover_overlay.py',
        'palworld_aio/widgets/player_hover_overlay.py',
    ):
        source = (source_root / relative).read_text(encoding='utf-8-sig')
        assert 'setStyleSheet(' not in source


def _expression_identity(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _expression_identity(node.value)
        return f'{owner}.{node.attr}' if owner else node.attr
    return None


def test_all_native_qmenus_use_the_centralized_context_surface():
    """Direct Qt menus may not bypass the shared token-driven QSS identity."""
    missing_identity = []
    source_root = PROJECT_ROOT / 'src' / 'palworld_aio'
    for path in source_root.rglob('*.py'):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for function in (
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            targets = []
            configured = set()
            for node in ast.walk(function):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    call_name = _expression_identity(node.value.func)
                    if call_name == 'QMenu':
                        targets.extend(
                            identity for identity in (
                                _expression_identity(target)
                                for target in node.targets
                            ) if identity
                        )
                if not isinstance(node, ast.Call):
                    continue
                method = _expression_identity(node.func)
                if not method or not method.endswith('.setObjectName'):
                    continue
                if (node.args and isinstance(node.args[0], ast.Constant)
                        and node.args[0].value == 'appContextMenu'):
                    configured.add(method.removesuffix('.setObjectName'))
            for target in targets:
                if target not in configured:
                    missing_identity.append((relative, function.name, target))
    assert missing_identity == []


def test_every_context_workflow_is_named_in_the_migration_inventory():
    inventory = MIGRATION_INVENTORY.read_text(encoding='utf-8')
    workflow_names = set()
    source_root = PROJECT_ROOT / 'src' / 'palworld_aio'
    for path in source_root.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if (('context_menu' in node.name and node.name != '_create_context_menu')
                    or node.name in {
                        '_on_marker_right_clicked',
                        '_on_empty_space_right_clicked',
                        '_on_zone_right_click',
                        'build_pal_context_menu',
                    }):
                workflow_names.add(node.name)
    missing = sorted(name for name in workflow_names if name not in inventory)
    assert missing == []


def test_generic_context_tree_uses_shared_table_styling():
    source = (
        PROJECT_ROOT / 'src' / 'palworld_aio' / 'widgets' / 'tree_widgets.py'
    ).read_text(encoding='utf-8-sig')
    assert "setObjectName('dataTree')" in source
    assert "tr('ui.table.accessible'" in source
    assert 'setStyleSheet(' not in source
