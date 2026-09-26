from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / 'scripts' / 'scrs' / 'render_uiux_baseline.py'


def test_renders_synthetic_baseline_matrix_without_save_files(tmp_path):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    result = subprocess.run(
        [sys.executable, str(SCRIPT), '--output-dir', str(tmp_path)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['synthetic_data_only'] is True
    assert manifest['real_save_files_read'] is False
    assert set(manifest['states']) == {
        'no_save_1024x700',
        'loaded_synthetic_1024x700',
        'selected_entity_1024x700',
        'editor_no_save_1024x700',
        'dialog_synthetic_620x360',
    }
    for state in manifest['states'].values():
        image = tmp_path / state['file']
        assert image.suffix == '.png'
        assert image.stat().st_size == state['bytes'] > 0
        assert state['width'] > 0 and state['height'] > 0
    assert not list(tmp_path.rglob('*.sav'))
