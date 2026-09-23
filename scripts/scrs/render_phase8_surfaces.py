"""Render deterministic Phase 8 tool, dialog, and System surfaces."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / 'src'
for entry in (
    SRC_ROOT,
    SRC_ROOT / 'i18n',
    PROJECT_ROOT / 'resources',
    SRC_ROOT / 'palworld_coord',
    SRC_ROOT / 'palsav',
    SRC_ROOT / 'palworld_xgp_import',
    SRC_ROOT / 'palworld_aio',
):
    if entry.is_dir() and str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def _capture(app, widget, path: Path, width: int, height: int) -> dict[str, int | str]:
    widget.resize(width, height)
    widget.show()
    app.processEvents()
    pixmap = widget.grab()
    if pixmap.isNull() or not pixmap.save(str(path), 'PNG'):
        raise RuntimeError(f'Could not render {path.name}')
    result: dict[str, int | str] = {
        'file': path.name,
        'width': pixmap.width(),
        'height': pixmap.height(),
        'bytes': path.stat().st_size,
    }
    widget.hide()
    widget.deleteLater()
    app.processEvents()
    return result


def _system_shell(route_id: str):
    from palworld_aio.application.system_info import DiagnosticsInfo, ProductInfo
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.pages.about_page import AboutPage
    from palworld_aio.ui.pages.diagnostics_page import DiagnosticsPage
    from palworld_aio.ui.pages.settings_page import SettingsPage
    from palworld_aio.ui.user_preferences import UserPreferences
    from palworld_aio.ui.workspace_context import WorkspaceContext

    context = WorkspaceContext()
    shell = WorkspaceShell(context)
    if route_id == 'settings':
        page = SettingsPage(UserPreferences().to_mapping())
    elif route_id == 'about':
        page = AboutPage(ProductInfo('2.4.0', 'v0.6.6'))
        page.set_update_state('available', latest='2.5.0', current='2.4.0')
    else:
        page = DiagnosticsPage(DiagnosticsInfo(
            app_version='2.4.0', game_version='v0.6.6',
            python_version='3.13.7', qt_version='6.9.1', pyqt_version='6.9.1',
            operating_system='Windows 11', architecture='AMD64', packaged=False,
            paths={
                'application': r'C:\Synthetic\PalTrainer',
                'configuration': r'C:\Synthetic\PalTrainer\Config',
                'data': r'C:\Synthetic\PalTrainer\Data',
                'backups': r'C:\Synthetic\PalTrainer\Backups',
            },
        ))
        page.set_console_text(
            'Application started\nSynthetic diagnostic event\nNo save data loaded')
    page.setParent(shell.page_host)
    shell.register_page(route_id, page)
    shell.navigate(route_id)
    return shell


def _tool_center_shell():
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.pages.tool_center_page import ToolCenterPage
    from palworld_aio.ui.workspace_context import WorkspaceContext

    context = WorkspaceContext()
    shell = WorkspaceShell(context)
    page = ToolCenterPage(context, parent=shell.page_host)
    shell.register_page('tools', page)
    shell.navigate('tools')
    return shell


def _gated_route_shell():
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.workspace_context import WorkspaceContext

    shell = WorkspaceShell(WorkspaceContext())
    shell.navigate('players')
    return shell


def _conversion_dialog():
    from palworld_aio.ui.tabs.tools_tab import ConversionOptionsDialog

    return ConversionOptionsDialog()


def _repair_dialog(*, result: bool = False):
    from palworld_aio.ui.dialogs.repair_workflow_dialog import (
        RepairWorkflowDialog, RepairWorkflowSpec,
    )

    dialog = RepairWorkflowDialog(
        RepairWorkflowSpec(
            title='Repair invalid item records',
            affected='14 records detected',
            review='Invalid item references will be removed from the loaded save.',
            backup='Recovery: the load-time backup remains unchanged.',
            risk='This changes in-memory save data.',
            confirm_text='Run repair',
        ),
        lambda: 14,
        lambda count: f'Repair complete. {count} records were corrected.',
    )
    if result:
        dialog._on_done(14)
    return dialog


def _transfer_dialog(*, failed: bool = False):
    from palworld_aio.ui.dialogs.transfer_workflow_dialog import (
        TransferWorkflowDialog, TransferWorkflowSpec,
    )

    dialog = TransferWorkflowDialog(
        TransferWorkflowSpec(
            title='Transfer character',
            source='Source world / Hathaway',
            target='Target world / Player slot 2',
            review='Player, inventory, party, and Pal ownership records will move.',
            backup='Both selected folders remain recoverable from their backups.',
            risk='Review both worlds before continuing.',
            confirm_text='Transfer character',
        ),
        lambda: True,
        lambda _result: 'Character transfer completed.',
    )
    if failed:
        dialog._on_error(RuntimeError(
            'Synthetic validation stopped the operation before mutation.'))
    return dialog


def render_phase8_surfaces(output_dir: Path) -> dict[str, object]:
    from PyQt6.QtWidgets import QApplication
    from i18n import init_language
    from palworld_aio.ui.chrome.fonts import load_app_fonts
    from palworld_aio.ui.chrome.styles import ThemeManager

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    init_language('en_US')
    load_app_fonts()
    ThemeManager.apply_global()

    states = {
        'tool_center_no_save': (_tool_center_shell, 1024, 700),
        'save_gated_players': (_gated_route_shell, 1024, 700),
        'conversion_choice': (_conversion_dialog, 520, 340),
        'repair_review': (_repair_dialog, 720, 500),
        'repair_result': (lambda: _repair_dialog(result=True), 720, 500),
        'transfer_review': (_transfer_dialog, 740, 540),
        'transfer_failure': (
            lambda: _transfer_dialog(failed=True), 740, 540),
        'settings': (lambda: _system_shell('settings'), 1024, 700),
        'about_update_available': (
            lambda: _system_shell('about'), 1024, 700),
        'diagnostics': (lambda: _system_shell('diagnostics'), 1024, 700),
    }
    rendered: dict[str, dict[str, int | str]] = {}
    for state_name, (builder, width, height) in states.items():
        filename = f'{state_name}_{width}x{height}.png'
        rendered[state_name] = _capture(
            app, builder(), output_dir / filename, width, height)

    manifest: dict[str, object] = {
        'synthetic_data_only': True,
        'operations_executed': False,
        'real_save_files_read': False,
        'states': rendered,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render_phase8_surfaces(args.output_dir), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
