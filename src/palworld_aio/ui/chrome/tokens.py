"""Central design tokens for the PalTrainer UI (single source of truth).

The palette is a plain dict per theme; QSS and Python widgets resolve tokens
from here. Game-data colors (rarity/element/rank) are a data contract and are
imported from constants rather than redefined.

FROZEN by the ui-modernization change (Phase 0): do not add parallel
palettes, ad-hoc hex colors, or per-screen color constants. New surfaces
derive from ``PALETTES`` via ``resolve()``; new themes add a dict entry.
Retired colors are listed in ``RETIRED_COLORS`` below and must not be used
in new or migrated UI.

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
    # Deck Operations palette (plan 019): warm dark, opaque, amber accent,
    # teal success. Cyan #7DD3FC and glass translucency are retired.
    'dark': {
        # surfaces (canvas < surface < raised < input) — warm, opaque
        'canvas': '#141312',
        'surface': '#1B1917',
        'surface_raised': '#211E1B',
        'surface_input': '#262220',
        'surface_hover': rgba('#F59E0B', 0.07),
        'surface_active': rgba('#F59E0B', 0.12),
        # text (warm grays)
        'text': '#ECE7E0',
        'text_secondary': '#A69F94',
        'text_disabled': '#5C564E',
        'text_on_accent': '#1C1206',
        # borders
        'border': rgba('#ECE7E0', 0.10),
        'border_strong': rgba('#ECE7E0', 0.18),
        # accent (interactive/selected/focus only)
        'accent': '#F59E0B',
        'accent_hover': '#F7B03A',
        'accent_pressed': '#D98A06',
        'accent_bg': rgba('#F59E0B', 0.10),
        'accent_bg_strong': rgba('#F59E0B', 0.18),
        'accent_border': rgba('#F59E0B', 0.30),
        'accent_border_strong': rgba('#F59E0B', 0.50),
        # semantic
        'success': '#2DD4BF',
        'success_bg': rgba('#2DD4BF', 0.10),
        'success_border': rgba('#2DD4BF', 0.30),
        'warning': '#E8B44C',
        'warning_bg': rgba('#E8B44C', 0.12),
        'warning_border': rgba('#E8B44C', 0.35),
        'danger': '#F87171',
        'danger_bg': rgba('#F87171', 0.12),
        'danger_border': rgba('#F87171', 0.35),
        'info': '#93B7DD',
        'info_bg': rgba('#93B7DD', 0.10),
        'info_border': rgba('#93B7DD', 0.30),
        'special': '#C084FC',
        'special_bg': rgba('#C084FC', 0.12),
        'special_border': rgba('#C084FC', 0.30),
        # legacy alias (kept so old code resolving ERROR/ALERT keeps meaning)
        'error': '#F87171',
        # floating layers
        'tooltip_bg': rgba('#211E1B', 0.98),
        'menu_bg': rgba('#1B1917', 0.98),
        'overlay_scrim': rgba('#0D0C0B', 0.62),
    },
}

DEFAULT_THEME = 'dark'


# ---------------------------------------------------------------------------
# Retired palettes (ui-modernization Phase 0: frozen).
# These colors MUST NOT be used in new or migrated UI. The theme scanner
# (scripts/scrs/check_theme_violations.py) flags them as `retired-palette`
# errors. Remaining occurrences elsewhere in the codebase are migration debt
# tracked by the ui-modernization change (Phase 4), not a pattern to copy.
# ---------------------------------------------------------------------------
RETIRED_COLORS: tuple[str, ...] = (
    '#7DD3FC',  # retired cyan accent (pre-Deck-Ops); use accent #F59E0B
    '#4A90E2',  # retired info blue (tab-guide only); use info #93B7DD
)
# Retired cyan in rgba() form, e.g. rgba(125,211,252,0.3).
RETIRED_RGBA_PREFIX = 'rgba(125,211,252'


def resolve(theme: str = DEFAULT_THEME) -> dict[str, str]:
    palette = PALETTES.get(theme)
    if palette is None:
        raise KeyError(f'unknown theme {theme!r}; known: {sorted(PALETTES)}')
    return palette


# ---------------------------------------------------------------------------
# Typography scale: token -> (px, weight). Fonts live in chrome/fonts.py.
# Deck Operations scale (plan 019 §6): Hanken display/heading/nav, Inter body.
# ---------------------------------------------------------------------------
TYPE: dict[str, tuple[int, int]] = {
    'display': (19, 700),
    'title': (14, 700),
    'section': (12, 600),
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
    'sm': 3,
    'md': 5,
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
# exactly one source of truth (plan 019: warm amber/teal family).
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
TEXT_DIM = rgba('#ECE7E0', 0.7)
SUCCESS_BG = _DARK['success_bg']
SUCCESS_BORDER = _DARK['success_border']
WARNING_BG = _DARK['warning_bg']
WARNING_BORDER = _DARK['warning_border']
DANGER_BG = _DARK['danger_bg']
DANGER_BG_STRONG = rgba('#F87171', 0.2)
DANGER_BORDER = _DARK['danger_border']
INFO_BG = _DARK['info_bg']
INFO_BORDER = _DARK['info_border']
SPECIAL_BG = _DARK['special_bg']
SPECIAL_BORDER = _DARK['special_border']
SURFACE = _DARK['surface']
SURFACE_SOLID = rgba('#1B1917', 0.95)
SURFACE_ELEVATED_SOLID = rgba('#211E1B', 0.98)
SURFACE_FAINT = rgba('#ECE7E0', 0.03)
SURFACE_FAINTER = rgba('#ECE7E0', 0.05)
BORDER_FAINT = _DARK['border']
BORDER_FAINTER = rgba('#ECE7E0', 0.06)

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
