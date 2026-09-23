"""Safe localization access for reusable chrome components."""
from __future__ import annotations

from typing import Any


def tr(key: str, default: str, **values: Any) -> str:
    """Translate a chrome key while remaining usable before i18n bootstraps."""
    try:
        from i18n import t
        translated = t(key, default=default, **values)
        if translated and translated != key:
            return translated
    except Exception:
        pass
    try:
        return default.format(**values)
    except (KeyError, ValueError):
        return default
