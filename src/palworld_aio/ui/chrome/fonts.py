"""Font loading and family stacks for the PalTrainer UI.

Strategy (plan 019 §6, bundled-font mandate):
- display/headings/nav: Hanken Grotesk (bundled TTF), Segoe UI fallback
- body/controls/tables: Inter (bundled TTF), Segoe UI fallback
- data/mono: Cascadia Mono with Consolas system fallback (no ligatures)
- icons: bundled token-colored SVG set via chrome/icons.py (``get_qicon``);
  no icon-font dependency

Every TTF/OTF under resources/assets/fonts is registered at startup once;
per-widget font loading is banned (see design-context §9).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt6.QtGui import QFont, QFontDatabase

FONT_BODY_STACK = ['Inter 28pt', 'Inter', 'Segoe UI']
FONT_HEADING_STACK = ['Hanken Grotesk', 'Segoe UI']
FONT_MONO_STACK = ['Cascadia Mono', 'Consolas']

# Real bundled weights (Regular/Medium/SemiBold files ship in
# resources/assets/fonts — synthetic bold is banned for primary typography).
FONT_WEIGHTS = {
    400: QFont.Weight.Normal,
    500: QFont.Weight.Medium,
    600: QFont.Weight.DemiBold,   # SemiBold
}

BUNDLED_FONT_FILES: tuple[str, ...] = (
    'HankenGrotesk-Regular.ttf',
    'HankenGrotesk-Medium.ttf',
    'HankenGrotesk-SemiBold.ttf',
    'Inter_28pt-Regular.ttf',
    'Inter_28pt-Medium.ttf',
    'Inter_28pt-SemiBold.ttf',
)

_REGISTERED = False


def font_family_qss(stack: Sequence[str]) -> str:
    return ','.join(f"'{name}'" for name in stack)


def _font_directory() -> Path:
    try:
        from boot_paths import ASSETS_DIR
        return Path(ASSETS_DIR) / 'fonts'
    except ImportError:
        return Path(__file__).resolve().parents[4] / 'resources' / 'assets' / 'fonts'


def bundled_font_paths() -> tuple[Path, ...]:
    """Return the deterministic local font manifest used at application boot."""
    directory = _font_directory()
    return tuple(directory / name for name in BUNDLED_FONT_FILES)


def load_app_fonts() -> list[str]:
    """Register bundled fonts once. Returns the list of new family names."""
    global _REGISTERED
    if _REGISTERED:
        return []
    _REGISTERED = True
    loaded: list[str] = []
    for path in bundled_font_paths():
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id == -1:
            print(f'Warning: failed to load font {path.name}')
            continue
        loaded.extend(QFontDatabase.applicationFontFamilies(font_id))
    return loaded


def _make(stack: list[str], px: int, weight: int) -> QFont:
    font = QFont()
    font.setFamilies(stack)
    font.setPixelSize(px)
    # Real bundled weights: Medium/SemiBold/Bold TTFs are registered, so Qt
    # picks the matching face instead of synthesizing bold from Regular.
    # The bundle deliberately ships Regular, Medium and SemiBold only. Map
    # heavier requests to the real SemiBold face instead of synthesizing Bold.
    resolved_weight = min(FONT_WEIGHTS, key=lambda candidate: abs(candidate - weight))
    font.setWeight(FONT_WEIGHTS[resolved_weight])
    return font


def body_font(px: int = 12, weight: int = 400) -> QFont:
    return _make(FONT_BODY_STACK, px, weight)


def heading_font(px: int = 17, weight: int = 600) -> QFont:
    return _make(FONT_HEADING_STACK, px, weight)


def mono_font(px: int = 11, weight: int = 400) -> QFont:
    return _make(FONT_MONO_STACK, px, weight)
