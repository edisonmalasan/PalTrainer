from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / 'scripts' / 'scrs' / 'render_world_workspaces.py'


def test_renders_world_matrix_at_default_and_minimum_sizes(tmp_path):
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
    assert manifest['real_save_files_read'] is False
    assert len(manifest['states']) == 18
    assert {
        name.rsplit('_', 2)[-2] for name in manifest['states']
    } == {'default', 'minimum'}
    for state in manifest['states'].values():
        image = tmp_path / state['file']
        assert image.suffix == '.png'
        assert image.stat().st_size == state['bytes'] > 0
        assert (state['width'], state['height']) in {(1450, 800), (1024, 700)}
    assert not list(tmp_path.rglob('*.sav'))
