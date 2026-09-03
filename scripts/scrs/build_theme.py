#!/usr/bin/env python3
"""Assemble resources/ui/themes/darkmode.qss from the QSS builder.

The deployed file = generated global stylesheet (chrome/qss_builder.py) +
transitional extras (legacy-dark.qss) that still style objectName/property-
specific surfaces not yet migrated (UI overhaul plans 004-016). When all
screens migrate, the extras file is deleted and this script only writes the
generated part.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src' / 'palworld_aio'))
sys.path.insert(0, str(ROOT / 'src'))

from palworld_aio.ui.chrome.qss_builder import build_qss  # noqa: E402

THEMES_DIR = ROOT / 'resources' / 'ui' / 'themes'
EXTRAS_NAME = 'legacy-dark.qss'
HEADER = (
    '/* GENERATED FILE — do not edit by hand.\n'
    '   Global rules: src/palworld_aio/ui/chrome/qss_builder.py (edit there).\n'
    '   Screen-specific rules: resources/ui/themes/legacy-dark.qss (transitional).\n'
    '   Rebuild: uv run python scripts/scrs/build_theme.py */\n'
)


def main() -> int:
    qss = build_qss('dark')
    extras_path = THEMES_DIR / EXTRAS_NAME
    if extras_path.exists():
        qss += '\n\n' + extras_path.read_text(encoding='utf-8')
    out = THEMES_DIR / 'darkmode.qss'
    out.write_text(HEADER + qss, encoding='utf-8')
    print(f'wrote {out} ({len(qss)} chars)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
