"""Shared helpers for maintenance scripts.

Plan 009: consolidate version/dependency configuration, UTF-8 output,
and structured logging for scripts.  Scripts must never auto-install
dependencies or delete/rewrite lockfiles — they report a clear error and
let the developer run ``uv sync`` explicitly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, ValueError):
    pass


def app_version() -> str:
    """Read the authoritative version from ``src/common.py``."""
    common_py = PROJECT_ROOT / 'src' / 'common.py'
    try:
        for line in common_py.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if stripped.startswith('APP_VERSION'):
                return stripped.split('=')[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return 'unknown'


def require_deep_translator():
    """Import GoogleTranslator without auto-installing anything.

    Raises ``RuntimeError`` with setup guidance if the dependency is not
    available.
    """
    try:
        from deep_translator import GoogleTranslator  # noqa: F401
    except ImportError:
        raise RuntimeError(
            'deep-translator is not installed. Run `uv sync` (or '
            '`uv add deep-translator`) from the project root, then retry.'
        )
    return GoogleTranslator
