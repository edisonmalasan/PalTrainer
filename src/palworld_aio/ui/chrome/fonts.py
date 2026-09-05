"""Font loading and family stacks for the PalTrainer UI.

Strategy (plan 019 §6, bundled-font mandate):
- display/headings/nav: Hanken Grotesk (bundled TTF), Segoe UI fallback
- body/controls/tables: Inter (bundled TTF), Segoe UI fallback
- data/mono: Cascadia Mono with Consolas fallback (no ligatures in Mono)
- icons: bundled token-colored SVG set via chrome/icons.py (``get_qicon``);
  no icon-font dependency

Every TTF/OTF under resources/assets/fonts is registered at startup once;
per-widget font loading is banned (see design-context §9).
"""
from __future__ import annotations

import os

from PyQt6.QtGui import QFont, QFontDatabase

FONT_BODY_STACK = ['Inter 28pt', 'Inter', 'Segoe UI']
FONT_HEADING_STACK = ['Hanken Grotesk', 'Segoe UI']
FONT_MONO_STACK = ['Cascadia Mono', 'Consolas']

# Real bundled weights (Regular/Medium/SemiBold files ship in
# resources/assets/fonts — synthetic bold is banned for primary typography).
FONT_WEIGHTS = {
    400: QFont.Weight.Normal,
    500: QFont.Weight.DemiBold,   # Medium (Qt maps 500 to the nearest heavier face)
    600: QFont.Weight.DemiBold,   # SemiBold
    700: QFont.Weight.Bold,
}

_REGISTERED = False


def font_family_qss(stack: list[str]) -> str:
    return ','.join(f"'{name}'" for name in stack)


def load_app_fonts() -> list[str]:
    """Register bundled fonts once. Returns the list of new family names."""
    global _REGISTERED
    if _REGISTERED:
        return []
    _REGISTERED = True
    loaded: list[str] = []
    try:
        from boot_paths import ASSETS_DIR
        fonts_dir = str(ASSETS_DIR / 'fonts')
    except ImportError:
        fonts_dir = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'resources', 'assets', 'fonts'))
    if not os.path.isdir(fonts_dir):
        return loaded
    for name in sorted(os.listdir(fonts_dir)):
        if not name.lower().endswith(('.ttf', '.otf')):
            continue
        font_id = QFontDatabase.addApplicationFont(os.path.join(fonts_dir, name))
        if font_id == -1:
            print(f'Warning: failed to load font {name}')
            continue
        loaded.extend(QFontDatabase.applicationFontFamilies(font_id))
    return loaded


def _make(stack: list[str], px: int, weight: int) -> QFont:
    font = QFont()
    font.setFamilies(stack)
    font.setPixelSize(px)
    # Real bundled weights: Medium/SemiBold/Bold TTFs are registered, so Qt
    # picks the matching face instead of synthesizing bold from Regular.
    font.setWeight(FONT_WEIGHTS.get(weight, QFont.Weight(weight)))
    return font


def body_font(px: int = 12, weight: int = 400) -> QFont:
    return _make(FONT_BODY_STACK, px, weight)


def heading_font(px: int = 14, weight: int = 700) -> QFont:
    return _make(FONT_HEADING_STACK, px, weight)


def mono_font(px: int = 11, weight: int = 400) -> QFont:
    return _make(FONT_MONO_STACK, px, weight)
