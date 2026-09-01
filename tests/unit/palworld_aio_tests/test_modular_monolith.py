from __future__ import annotations

import ast
from pathlib import Path

from tests.dynamic_importer import import_from
from tests.test_registry import SRC_DIR


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_legacy_facades_preserve_canonical_object_identity():
    canonical_session = import_from('palworld_aio.application.save_session')
    legacy_session = import_from('palworld_aio.managers.save_session')
    canonical_projections = import_from('palworld_aio.world.projections')
    legacy_projections = import_from('palworld_aio.read_models')
    canonical_operations = import_from('palworld_aio.world.operations')
    legacy_operations = import_from('palworld_aio.managers.operations')

    assert legacy_session.SaveSession is canonical_session.SaveSession
    assert legacy_session.save_session is canonical_session.save_session
    assert legacy_projections.SaveProjections is canonical_projections.SaveProjections
    assert legacy_operations.OperationResult is canonical_operations.OperationResult
    assert legacy_operations.collect_death_bag_ids is canonical_operations.collect_death_bag_ids


def test_canonical_core_modules_do_not_depend_on_presentation_or_legacy_managers():
    canonical_paths = (
        SRC_DIR / 'palworld_aio' / 'application' / 'save_session.py',
        SRC_DIR / 'palworld_aio' / 'application' / 'derived_state.py',
        SRC_DIR / 'palworld_aio' / 'world' / 'projections.py',
        SRC_DIR / 'palworld_aio' / 'world' / 'operations.py',
        SRC_DIR / 'palworld_aio' / 'world' / 'indexes.py',
    )
    forbidden_prefixes = ('PyQt6', 'palworld_aio.ui', 'palworld_aio.editor', 'palworld_aio.managers')

    for path in canonical_paths:
        imports = _imported_modules(path)
        assert not any(
            imported.startswith(forbidden_prefixes)
            for imported in imports
        ), path
def test_active_core_consumers_use_canonical_module_paths():
    consumer_paths = (
        SRC_DIR / 'palworld_aio' / 'main.py',
        SRC_DIR / 'palworld_aio' / 'managers' / 'data_manager.py',
        SRC_DIR / 'palworld_aio' / 'managers' / 'func_manager.py',
        SRC_DIR / 'palworld_aio' / 'managers' / 'save_manager.py',
    )
    legacy_paths = (
        'palworld_aio.managers.save_session',
        'palworld_aio.managers.operations',
        'palworld_aio.read_models',
    )

    for path in consumer_paths:
        imports = _imported_modules(path)
        assert not any(
            imported == legacy_path or imported.startswith(f'{legacy_path}.')
            for imported in imports
            for legacy_path in legacy_paths
        ), path
