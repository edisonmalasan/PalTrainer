#!/usr/bin/env python3
"""Assemble resources/ui/themes/darkmode.qss from the QSS builder."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src' / 'palworld_aio'))
sys.path.insert(0, str(ROOT / 'src'))

from palworld_aio.ui.chrome.qss_builder import build_qss  # noqa: E402

THEMES_DIR = ROOT / 'resources' / 'ui' / 'themes'
HEADER = (
    '/* GENERATED FILE — do not edit by hand.\n'
    '   Global rules: src/palworld_aio/ui/chrome/qss_builder.py (edit there).\n'
    '   Rebuild: uv run python scripts/scrs/build_theme.py */\n'
)


def main() -> int:
    qss = build_qss('dark')
    out = THEMES_DIR / 'darkmode.qss'
    out.write_text(HEADER + qss, encoding='utf-8')
    print(f'wrote {out} ({len(qss)} chars)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
