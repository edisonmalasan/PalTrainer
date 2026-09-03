"""Central design tokens for the PalTrainer UI (single source of truth).

The palette is a plain dict per theme; QSS and Python widgets resolve tokens
from here. Game-data colors (rarity/element/rank) are a data contract and are
imported from constants rather than redefined.

Scanner note: this module is whitelisted by scripts/scrs/check_theme_violations.py
because it *is* the theme system.
"""
from __future__ import annotations

try:
    from palworld_aio import constants as _c
except ImportError:  # app-runtime layout: src/palworld_aio is on sys.path
    import constants as _c  # type: ignore[no-redef]

ACCENT = _c.ACCENT
BG = _c.BG
DANGER = _c.DANGER
ERROR = _c.ERROR
INFO = _c.INFO
MUTED = _c.MUTED
SPECIAL = _c.SPECIAL
SUCCESS = _c.SUCCESS
TEXT = _c.TEXT
TEXT_DISABLED = _c.TEXT_DISABLED
WARNING = _c.WARNING


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = f'{alpha:g}'
    return f'rgba({r},{g},{b},{a})'


# ---------------------------------------------------------------------------
# Palettes. Dark ships first; the dict shape is the contract for new themes.
# ---------------------------------------------------------------------------
PALETTES: dict[str, dict[str, str]] = {
    'dark': {
        # surfaces (canvas < surface < raised < input)
        'canvas': '#0A0C10',
        'surface': '#10141B',
        'surface_raised': '#151B24',
        'surface_input': '#1A212C',
        'surface_hover': rgba('#7DD3FC', 0.06),
        'surface_active': rgba('#7DD3FC', 0.10),
        # text
        'text': TEXT,
        'text_secondary': MUTED,
        'text_disabled': TEXT_DISABLED,
        'text_on_accent': '#071018',
        # borders
        'border': rgba('#FFFFFF', 0.09),
        'border_strong': rgba('#FFFFFF', 0.16),
        # accent (interactive/selected/focus only)
        'accent': ACCENT,
        'accent_hover': '#A5E3FD',
        'accent_pressed': '#58BCE8',
        'accent_bg': rgba(ACCENT, 0.10),
        'accent_bg_strong': rgba(ACCENT, 0.18),
        'accent_border': rgba(ACCENT, 0.30),
        'accent_border_strong': rgba(ACCENT, 0.50),
        # semantic
        'success': SUCCESS,
        'success_bg': rgba(SUCCESS, 0.12),
        'success_border': rgba(SUCCESS, 0.35),
        'warning': WARNING,
        'warning_bg': rgba(WARNING, 0.12),
        'warning_border': rgba(WARNING, 0.35),
        'danger': DANGER,
        'danger_bg': rgba(DANGER, 0.12),
        'danger_border': rgba(DANGER, 0.35),
        'info': INFO,
        'info_bg': rgba(INFO, 0.12),
        'info_border': rgba(INFO, 0.30),
        'special': SPECIAL,
        'special_bg': rgba(SPECIAL, 0.12),
        'special_border': rgba(SPECIAL, 0.30),
        # legacy alias (kept so old code resolving ERROR/ALERT keeps meaning)
        'error': ERROR,
        # floating layers
        'tooltip_bg': rgba('#151B24', 0.98),
        'menu_bg': rgba('#10141B', 0.98),
        'overlay_scrim': rgba('#05070A', 0.60),
    },
}

DEFAULT_THEME = 'dark'


def resolve(theme: str = DEFAULT_THEME) -> dict[str, str]:
    palette = PALETTES.get(theme)
    if palette is None:
        raise KeyError(f'unknown theme {theme!r}; known: {sorted(PALETTES)}')
    return palette


# ---------------------------------------------------------------------------
# Typography scale: token -> (px, weight). Fonts live in chrome/fonts.py.
# ---------------------------------------------------------------------------
TYPE: dict[str, tuple[int, int]] = {
    'display': (20, 600),
    'title': (15, 600),
    'section': (13, 600),
    'body': (12, 400),
    'secondary': (11, 400),
    'micro': (10, 400),
    'mono': (11, 400),
}

# ---------------------------------------------------------------------------
# Spacing / radius / control heights (4px grid).
# ---------------------------------------------------------------------------
SPACING: dict[str, int] = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    'xxl': 32,
}

RADIUS: dict[str, int] = {
    'sm': 4,
    'md': 6,
    'lg': 8,
    'pill': 9999,
}

HEIGHT: dict[str, int] = {
    'compact': 24,
    'default': 28,
    'comfortable': 32,
    'cta': 36,
}

ROW: dict[str, int] = {
    'dense': 28,
    'standard': 32,
}

# ---------------------------------------------------------------------------
# Transitional composite aliases. Existing modules (chrome/styles.py and
# ~400 constants.* consumers) import these names; screen plans migrate them
# to resolve()-based access. Values derive from the dark palette so there is
# exactly one source of truth.
# ---------------------------------------------------------------------------
_DARK = PALETTES['dark']

ACCENT_BG = _DARK['accent_bg']
ACCENT_BG_STRONG = _DARK['accent_bg_strong']
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
DANGER_BG = rgba(DANGER, 0.12)
DANGER_BG_STRONG = rgba(DANGER, 0.2)
DANGER_BORDER = rgba(DANGER, 0.3)
INFO_BG = rgba(INFO, 0.15)
INFO_BORDER = rgba(INFO, 0.3)
SPECIAL_BG = rgba(SPECIAL, 0.12)
SPECIAL_BORDER = rgba(SPECIAL, 0.3)
SURFACE = rgba('#121418', 0.65)
SURFACE_SOLID = rgba('#121418', 0.95)
SURFACE_ELEVATED_SOLID = rgba('#161A20', 0.98)
SURFACE_FAINT = rgba('#FFFFFF', 0.03)
SURFACE_FAINTER = rgba('#FFFFFF', 0.05)
BORDER_FAINT = rgba('#FFFFFF', 0.08)
BORDER_FAINTER = rgba('#FFFFFF', 0.05)

ACCENT_HEX = ACCENT
TEXT_HEX = TEXT
TEXT_MUTED_HEX = MUTED
TEXT_DISABLED_HEX = TEXT_DISABLED
BG_HEX = BG
SUCCESS_HEX = SUCCESS
WARNING_HEX = WARNING
DANGER_HEX = DANGER
INFO_HEX = INFO
SPECIAL_HEX = SPECIAL
