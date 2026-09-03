"""Font loading and family stacks for the PalTrainer UI.

Strategy (see docs/plan/ui/000-design-context.md):
- body/UI: Segoe UI Variable Text with Segoe UI fallback (installed on Windows)
- headings: Segoe UI Variable Display with Segoe UI fallback
- data/mono: Cascadia Mono with Consolas fallback (no ligatures in Mono)
- icons: bundled Hack Nerd Font (resources/assets/fonts)

Every TTF/OTF under resources/assets/fonts is registered at startup so a future
font bundle works without code changes.
"""
from __future__ import annotations

import os

from PyQt6.QtGui import QFont, QFontDatabase

FONT_BODY_STACK = ['Segoe UI Variable Text', 'Segoe UI']
FONT_HEADING_STACK = ['Segoe UI Variable Display', 'Segoe UI']
FONT_MONO_STACK = ['Cascadia Mono', 'Consolas']
FONT_ICON = 'Hack Nerd Font'
FONT_ICON_STACK = [FONT_ICON]

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
    font.setWeight(QFont.Weight(weight))
    return font


def body_font(px: int = 12, weight: int = 400) -> QFont:
    return _make(FONT_BODY_STACK, px, weight)


def heading_font(px: int = 15, weight: int = 600) -> QFont:
    return _make(FONT_HEADING_STACK, px, weight)


def mono_font(px: int = 11, weight: int = 400) -> QFont:
    return _make(FONT_MONO_STACK, px, weight)


def icon_font(px: int = 14) -> QFont:
    return _make([FONT_ICON], px, 400)
