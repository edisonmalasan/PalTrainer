from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / 'scripts' / 'scrs' / 'render_phase8_surfaces.py'


def test_renders_phase8_matrix_without_running_operations_or_reading_saves(tmp_path):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    result = subprocess.run(
        [sys.executable, str(SCRIPT), '--output-dir', str(tmp_path)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['synthetic_data_only'] is True
    assert manifest['operations_executed'] is False
    assert manifest['real_save_files_read'] is False
    assert set(manifest['states']) == {
        'tool_center_no_save', 'save_gated_players', 'conversion_choice',
        'repair_review', 'repair_result', 'transfer_review', 'transfer_failure',
        'settings', 'about_update_available', 'diagnostics',
    }
    for state in manifest['states'].values():
        image = tmp_path / state['file']
        assert image.suffix == '.png'
        assert image.stat().st_size == state['bytes'] > 0
        assert state['width'] >= 520 and state['height'] >= 340
    assert not list(tmp_path.rglob('*.sav'))
