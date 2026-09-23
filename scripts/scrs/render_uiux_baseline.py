"""Render synthetic UI/UX baseline states without reading a Palworld save.

The output directory is required so verification never writes screenshots or
logs into the repository accidentally.
"""
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


def _capture(app, widget, path: Path, width: int, height: int) -> dict:
    widget.resize(width, height)
    widget.show()
    app.processEvents()
    pixmap = widget.grab()
    if pixmap.isNull() or not pixmap.save(str(path), 'PNG'):
        raise RuntimeError(f'Could not render {path.name}')
    result = {
        'file': path.name,
        'width': pixmap.width(),
        'height': pixmap.height(),
        'bytes': path.stat().st_size,
    }
    widget.hide()
    widget.deleteLater()
    app.processEvents()
    return result


def _build_shell_sample(loaded: bool):
    from palworld_aio.ui.tabs.tools_tab import ToolsTab
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.workspace_context import (
        PendingChangesSummary, SaveIdentity, SavePlatform, WorkspaceContext,
    )

    context = WorkspaceContext()
    if loaded:
        context.finish_load(SaveIdentity(
            'synthetic-world', 'Synthetic World',
            r'C:\Synthetic\Palworld\Saved\SaveGames\World01\Level.sav',
            SavePlatform.STEAM,
        ))
    host = WorkspaceShell(context)
    tools = ToolsTab(host.page_host)
    host.register_page('tools', tools)
    host.navigate('tools')

    if loaded:
        synthetic_path = r'C:\Synthetic\Palworld\Saved\SaveGames\World01\Level.sav'
        context.set_pending_changes(PendingChangesSummary(2, 'Synthetic edits'))
        tools._set_save_status('loaded')
        tools._save_status_label.setText('Synthetic World')
        tools._save_path_label.setText(synthetic_path)
        tools._save_path_label.setToolTip(synthetic_path)
        tools._copy_path_btn.setVisible(True)
        for key, value in {'players': '1', 'guilds': '1', 'bases': '1', 'pals': '220'}.items():
            tools._stat_cards[key].setText(value)
    return host


def _build_selected_entity_sample():
    from palworld_aio.ui.chrome.entity_browser import EntityBrowserFrame
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.workspace_context import (
        ContextSelection, SaveIdentity, SavePlatform, WorkspaceContext,
    )
    context = WorkspaceContext()
    context.finish_load(SaveIdentity(
        'synthetic-world', 'Synthetic World', 'C:/Synthetic/Level.sav',
        SavePlatform.STEAM))
    host = WorkspaceShell(context)
    panel = EntityBrowserFrame(
        'Players',
        ['deletion.col.player_name', 'deletion.col.level', 'deletion.col.uid'],
        parent=host.page_host,
    )
    uid = '0E656D544A2B4C3D8E9F0A1B2C3D4E5F'
    panel.add_inspector_row('Level')
    panel.add_inspector_row('Guild')
    panel.add_inspector_row('Player UID', monospace=True)
    panel.set_detail_provider(lambda values: (
        values[0], {0: values[1], 1: 'Unnamed Guild', 2: uid}))
    panel.browser.add_item(['Hathaway', 55, '0E656D54…'], data=uid,
                           tooltips={2: uid})
    panel.browser.tree.setCurrentItem(panel.browser.tree.topLevelItem(0))
    context.set_player(ContextSelection(uid, 'Hathaway'))
    host.register_page('players', panel)
    host.navigate('players')
    return host


def _build_editor_sample():
    from palworld_aio.ui.tabs.json_editor_tab import JsonEditorTab
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.workspace_context import SaveIdentity, WorkspaceContext

    context = WorkspaceContext()
    context.finish_load(SaveIdentity(
        'synthetic-world', 'Synthetic World', 'C:/Synthetic/Level.sav'))
    host = WorkspaceShell(context)
    editor = JsonEditorTab(host.page_host)
    host.register_page('json_editor', editor)
    host.navigate('json_editor')
    return host


def _build_dialog_sample():
    from PyQt6.QtWidgets import QLabel
    from palworld_aio.ui.chrome.components import BaseDialog

    dialog = BaseDialog('Baseline confirmation', min_size=(620, 360))
    dialog.content_layout.addWidget(
        QLabel('Review the selected save operation before continuing.')
    )
    return dialog


def render_baseline(output_dir: Path) -> dict:
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
        'no_save_1024x700': (_build_shell_sample(False), 1024, 700),
        'loaded_synthetic_1024x700': (_build_shell_sample(True), 1024, 700),
        'selected_entity_1024x700': (_build_selected_entity_sample(), 1024, 700),
        'editor_no_save_1024x700': (_build_editor_sample(), 1024, 700),
        'dialog_synthetic_620x360': (_build_dialog_sample(), 620, 360),
    }
    rendered = {}
    for name, (widget, width, height) in states.items():
        rendered[name] = _capture(app, widget, output_dir / f'{name}.png', width, height)

    manifest = {
        'synthetic_data_only': True,
        'real_save_files_read': False,
        'states': rendered,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2), encoding='utf-8'
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = render_baseline(args.output_dir)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
