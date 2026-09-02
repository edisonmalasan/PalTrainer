"""Central Nerd Font icon registry.

Single source for UI glyphs. Replaces the per-file fallback dicts and all
emoji fallbacks. Resolution order: `nerdfont` package (if installed) →
canonical codepoint below. A missing key yields the documented '?' placeholder,
never an emoji.
"""
from __future__ import annotations

try:
    import nerdfont as _nf
except ImportError:
    _nf = None

UNKNOWN = '?'

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
