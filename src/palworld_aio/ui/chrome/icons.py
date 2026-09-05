"""Central icon registry.

Two backends share one string-key namespace:

- Vector (preferred): self-authored SVG set under ``resources/assets/icons/svg``
  rendered to token-colored QIcon/QPixmap via QSvgRenderer (``get_qicon`` /
  ``get_pixmap``). No icon-font dependency; colors come from the frozen palette.
- Glyph (legacy): Nerd-Font codepoints (``get_icon``) kept only for surfaces not
  yet migrated. New code must use ``get_qicon``.

Resolution order for glyphs: `nerdfont` package (if installed) → canonical
codepoint below. A missing key yields the documented '?' placeholder,
never an emoji.
"""
from __future__ import annotations

import os

try:
    import nerdfont as _nf
except ImportError:
    _nf = None

UNKNOWN = '?'

# ---------------------------------------------------------------------------
# Vector backend
# ---------------------------------------------------------------------------
_SVG_DIR_CANDIDATES = (
    os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  '..', '..', '..', '..', 'resources', 'assets', 'icons', 'svg')),
)


def _svg_dir() -> str:
    try:
        from boot_paths import ASSETS_DIR
        return str(ASSETS_DIR / 'icons' / 'svg')
    except ImportError:
        pass
    for candidate in _SVG_DIR_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    return _SVG_DIR_CANDIDATES[0]


# Semantic color roles -> palette token keys (resolved lazily so the theme
# stays the single source of truth).
ROLE_COLORS: dict[str, str] = {
    'text': 'text',
    'text_secondary': 'text_secondary',
    'text_disabled': 'text_disabled',
    'accent': 'accent',
    'success': 'success',
    'warning': 'warning',
    'danger': 'danger',
    'info': 'info',
    'special': 'special',
    'text_on_accent': 'text_on_accent',
}

_pixmap_cache: dict[tuple[str, str, int, int], 'object'] = {}
_svg_cache: dict[str, str] = {}


def role_color(role: str = 'text', theme: str | None = None) -> str:
    """Resolve a semantic role to a palette hex color."""
    from . import tokens as _tokens
    palette = _tokens.resolve(theme) if theme else _tokens.resolve()
    token_key = ROLE_COLORS.get(role)
    return palette.get(token_key, palette['text']) if token_key else (theme or palette['text'])


def _svg_source(name: str) -> str | None:
    """Load and memoize an SVG file, with a color placeholder left intact."""
    if name in _svg_cache:
        return _svg_cache[name]
    path = os.path.join(_svg_dir(), f'{name}.svg')
    if not os.path.isfile(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            _svg_cache[name] = fh.read()
    except OSError:
        return None
    return _svg_cache[name]


def has_vector_icon(name: str) -> bool:
    return os.path.isfile(os.path.join(_svg_dir(), f'{name}.svg'))


def get_pixmap(name: str, color: str | None = None, size: int = 16,
               dpr: float = 1.0, role: str | None = None):
    """Render an SVG icon to a QPixmap tinted with ``color`` (or a role color)."""
    from PyQt6.QtCore import QByteArray, Qt
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtSvg import QSvgRenderer

    resolved = color if color else role_color(role or 'text')
    key = (name, resolved, size, round(dpr * 100))
    cached = _pixmap_cache.get(key)
    if cached is not None:
        return cached
    source = _svg_source(name)
    if source is None:
        return None
    renderer = QSvgRenderer(QByteArray(source.replace('__COLOR__', resolved).encode('utf-8')))
    if not renderer.isValid():
        return None
    pix = QPixmap(int(size * dpr), int(size * dpr))
    pix.fill(Qt.GlobalColor.transparent)
    from PyQt6.QtGui import QPainter
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    pix.setDevicePixelRatio(dpr)
    _pixmap_cache[key] = pix
    return pix


def get_qicon(name: str, color: str | None = None, role: str | None = None):
    """Token-colored QIcon from the bundled SVG set (None if unknown)."""
    from PyQt6.QtGui import QIcon
    resolved = color if color else role_color(role or 'text')
    pix = get_pixmap(name, resolved, 64, 1.0)
    return QIcon(pix) if pix is not None else None

_ICONS: dict[str, tuple[str | None, str]] = {
    # header / window controls
    'github': ('nf-cod-github', '\ue708'),
    'save': ('nf-fa-save', '\uf0c7'),
    'menu': ('nf-md-menu', '\U000f035c'),
    'info': ('nf-md-information', '\U000f02fd'),
    'close': ('nf-fa-close', '\uf00d'),
    'discord': ('nf-fa-discord', '\uf392'),
    'toolbox': ('nf-fa-toolbox', '\uee1b'),
    'warning': ('nf-fa-warning', '\uf071'),
    'minimize': ('nf-md-circle_medium', '\U000f09df'),
    'maximize': ('nf-fa-window_maximize', '\uf2d0'),
    'cog': ('nf-md-cog', '\U000f0493'),
    'theme': ('nf-md-theme_light_dark', '\U000f0cde'),
    'triangle_left': ('nf-cod-triangle_left', '\ueb9b'),
    'triangle_right': ('nf-cod-triangle_right', '\ueb9c'),
    # navigation
    'tools': ('nf-fa-wrench', '\uf0ad'),
    'map': ('nf-fa-map', '\uf279'),
    'base_inventory': ('nf-fa-warehouse', '\ued92'),
    'player_inventory': ('nf-fa-suitcase', '\uf0f2'),
    'pal_editor': ('nf-fa-dragon', '\ueef8'),
    'players': ('nf-fa-users', '\uf0c0'),
    'guilds': ('nf-fa-shield', '\uf132'),
    'bases': ('nf-fa-home', '\uf015'),
    'exclusions': ('nf-fa-ban', '\uf05e'),
    'json_editor': ('nf-cod-json', '\uf1c9'),
    'breeding': ('nf-md-egg', '\U000f00fb'),
    'docs': ('nf-fa-book', '\uf02d'),
    'console': ('nf-fa-terminal', '\uf120'),
    'collapse_open': ('nf-fa-chevron_right', '\uf054'),
    'collapse_close': ('nf-fa-chevron_left', '\uf053'),
    'sidebar_expand': (None, '\uf054\uf054'),
    'sidebar_collapse': (None, '\uf053\uf053'),
    # menu categories (replaces emoji fallbacks)
    'file': ('nf-md-file', '\U000f0216'),
    'function': ('nf-md-function', '\U000f0199'),
    'playlist_remove': ('nf-md-playlist_remove', '\U000f07a2'),
    'translate': ('nf-md-translate', '\U000f05b0'),
    'update': ('nf-md-update', '\U000f06b4'),
    'chevron_right': ('nf-md-chevron_right', '\U000f0142'),
    # generic actions
    'copy': ('nf-fa-copy', '\uf0c5'),
    'search': ('nf-fa-search', '\uf002'),
    'plus': ('nf-fa-plus', '\uf067'),
    'minus': ('nf-fa-minus', '\uf068'),
    'check': ('nf-fa-check', '\uf00c'),
    'lock': ('nf-fa-lock', '\uf023'),
    'unlock': ('nf-fa-unlock', '\uf09c'),
    'trash': ('nf-fa-trash', '\uf1f8'),
    'folder': ('nf-fa-folder', '\uf07b'),
    'arrow_up': ('nf-fa-arrow_up', '\uf062'),
    'arrow_down': ('nf-fa-arrow_down', '\uf063'),
    'chevron_up': ('nf-fa-chevron_up', '\uf077'),
    'chevron_down': ('nf-fa-chevron_down', '\uf078'),
    'refresh': ('nf-fa-refresh', '\uf021'),
    'external_link': ('nf-fa-external_link', '\uf08e'),
    'paw': ('nf-fa-paw', '\uf1b0'),
    'star': ('nf-fa-star', '\uf005'),
    'heart': ('nf-fa-heart', '\uf004'),
    'dna': ('nf-md-dna', '\U000f03c9'),
    'fire': ('nf-fa-fire', '\uf06d'),
}


def get_icon(name: str) -> str:
    """Resolve an icon name to a glyph string."""
    entry = _ICONS.get(name)
    if entry is None:
        return UNKNOWN
    key, fallback = entry
    if key and _nf is not None:
        glyph = _nf.icons.get(key)
        if isinstance(glyph, str) and glyph:
            return glyph
    return fallback


def has_icon(name: str) -> bool:
    return name in _ICONS
