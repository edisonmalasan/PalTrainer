"""Central icon registry.

Self-authored SVG assets under ``resources/assets/icons/svg`` are rendered to
token-colored QIcon/QPixmap instances through one local-only pipeline. There is
no icon-font or network fallback: an unknown name returns ``None`` so callers
can provide accessible text when appropriate.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Vector backend
# ---------------------------------------------------------------------------
def _svg_dir() -> Path:
    try:
        from boot_paths import ASSETS_DIR
        return Path(ASSETS_DIR) / 'icons' / 'svg'
    except ImportError:
        return Path(__file__).resolve().parents[4] / 'resources' / 'assets' / 'icons' / 'svg'


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

# Destination aliases: the Base Inventory nav destination renders the bundled
# container glyph so it reads as an open container instead of a second house
# beside Bases (uiux-audit-remediation 1.4 / design D2).
_SVG_ALIASES: dict[str, str] = {
    'base_inventory': 'container',
}


def _resolve_svg_name(name: str) -> str:
    return _SVG_ALIASES.get(name, name)


def role_color(role: str = 'text', theme: str | None = None) -> str:
    """Resolve a semantic role to a palette hex color."""
    from . import tokens as _tokens
    palette = _tokens.resolve(theme) if theme else _tokens.resolve()
    token_key = ROLE_COLORS.get(role)
    return palette.get(token_key, palette['text']) if token_key else (theme or palette['text'])


def _svg_source(name: str) -> str | None:
    """Load and memoize an SVG file, with a color placeholder left intact."""
    name = _resolve_svg_name(name)
    if name in _svg_cache:
        return _svg_cache[name]
    path = _svg_dir() / f'{name}.svg'
    if not path.is_file():
        return None
    try:
        _svg_cache[name] = path.read_text(encoding='utf-8')
    except OSError:
        return None
    return _svg_cache[name]


def has_vector_icon(name: str) -> bool:
    return (_svg_dir() / f'{_resolve_svg_name(name)}.svg').is_file()


def available_vector_icons() -> frozenset[str]:
    """Return locally bundled icon names; aliases are included as public names."""
    names = {path.stem for path in _svg_dir().glob('*.svg')}
    names.update(_SVG_ALIASES)
    return frozenset(names)


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
