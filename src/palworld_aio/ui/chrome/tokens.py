"""QSS-derived token strings built from constants.py values.

This module is theme-system infrastructure (scanner-whitelisted). It exists so
stylesheets can embed rgba composites and gradients that reference a single
source of truth for the hue values.
"""
from constants import (
    ACCENT,
    BG,
    BORDER,
    INFO,
    MUTED,
    SPECIAL,
    SUCCESS,
    SURFACE_ELEVATED,
    TEXT,
    TEXT_DISABLED,
    WARNING,
)

ACCENT_RGB = '125,211,252'
ACCENT_R = 125
ACCENT_G = 211
ACCENT_B = 252


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = f'{alpha:g}'
    return f'rgba({r},{g},{b},{a})'


ACCENT_BG = rgba(ACCENT, 0.12)
ACCENT_BG_STRONG = rgba(ACCENT, 0.2)
ACCENT_BG_FAINT = rgba(ACCENT, 0.08)
ACCENT_BG_SOLID = rgba(ACCENT, 0.3)
ACCENT_BORDER = rgba(ACCENT, 0.2)
ACCENT_BORDER_SUBTLE = rgba(ACCENT, 0.15)
ACCENT_BORDER_FAINT = rgba(ACCENT, 0.08)
ACCENT_BORDER_HOVER = rgba(ACCENT, 0.35)
ACCENT_BORDER_FOCUS = rgba(ACCENT, 0.4)
ACCENT_BORDER_STRONG = rgba(ACCENT, 0.25)
ACCENT_GLOW = rgba(ACCENT, 0.1)
TEXT_DIM = rgba(TEXT, 0.7)
SUCCESS_BG = rgba(SUCCESS, 0.15)
SUCCESS_BORDER = rgba(SUCCESS, 0.3)
WARNING_BG = rgba(WARNING, 0.15)
WARNING_BORDER = rgba(WARNING, 0.35)
DANGER_BG = rgba('#FB7185', 0.12)
DANGER_BG_STRONG = rgba('#FB7185', 0.2)
DANGER_BORDER = rgba('#FB7185', 0.3)
INFO_BG = rgba(INFO, 0.15)
INFO_BORDER = rgba(INFO, 0.3)
SPECIAL_BG = rgba(SPECIAL, 0.12)
SPECIAL_BORDER = rgba(SPECIAL, 0.3)
SURFACE = rgba('#121418', 0.65)
SURFACE_SOLID = rgba('#121418', 0.95)
SURFACE_ELEVATED_SOLID = rgba(SURFACE_ELEVATED, 0.98)
SURFACE_INPUT = rgba('#FFFFFF', 0.06)
SURFACE_FAINT = rgba('#FFFFFF', 0.03)
SURFACE_FAINTER = rgba('#FFFFFF', 0.05)
BORDER_FAINT = rgba('#FFFFFF', 0.08)
BORDER_FAINTER = rgba('#FFFFFF', 0.05)
HEADER_GRADIENT = (f'qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0, '
                   f'stop:0 rgba(7,8,10,1), stop:0.5 rgba(8,16,26,1), stop:1 rgba(5,6,10,1))')
DIALOG_GRADIENT = (f'qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0, '
                   f'stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98))')
ACCENT_HEX = ACCENT
TEXT_HEX = TEXT
TEXT_MUTED_HEX = MUTED
TEXT_DISABLED_HEX = TEXT_DISABLED
BG_HEX = BG
BORDER_HEX = BORDER
SUCCESS_HEX = SUCCESS
WARNING_HEX = WARNING
DANGER_HEX = '#FB7185'
INFO_HEX = INFO
SPECIAL_HEX = SPECIAL
