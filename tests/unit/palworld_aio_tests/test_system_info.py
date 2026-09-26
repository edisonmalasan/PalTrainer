from __future__ import annotations

from tests.dynamic_importer import import_from


system_info = import_from('palworld_aio.application.system_info')


def test_diagnostics_report_contains_bounded_environment_and_paths():
    info = system_info.DiagnosticsInfo(
        app_version='2.4.0', game_version='1.0.3', python_version='3.13.0',
        qt_version='6.9.0', pyqt_version='6.9.0', operating_system='Fixture OS',
        architecture='x86_64', packaged=False,
        paths={'application': 'C:/PalTrainer', 'configuration': 'C:/Config'},
    )
    report = info.report()
    assert 'Application version: 2.4.0' in report
    assert 'Supported game version: 1.0.3' in report
    assert 'Application: C:/PalTrainer' in report
    assert 'Development checkout' in report
    assert 'save data' in report


def test_runtime_builder_never_reads_or_exports_loaded_save_content():
    constants = import_from('palworld_aio.constants')
    previous_json = constants.loaded_level_json
    previous_path = constants.current_save_path
    marker = 'SECRET_PLAYER_MARKER_8142'
    try:
        constants.loaded_level_json = {'player': marker}
        constants.current_save_path = f'C:/private/{marker}/Level.sav'
        report = system_info.build_diagnostics_info().report()
        assert marker not in report
        assert 'current_save_path' not in report
    finally:
        constants.loaded_level_json = previous_json
        constants.current_save_path = previous_path
