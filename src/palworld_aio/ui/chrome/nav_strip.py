"""NavStrip — shell v3 top navigation (top-nav-shell tasks 3.1-3.2).

A 38px strip of zone-grouped checkable tab buttons replacing the right
NexusBand rail. Zones follow the confirmed grouping:

- Start: Tools
- World: Map, Bases, Players, Guilds, Exclusions
- Edit: Player Inventory, Base Inventory, Pal Editor, JSON Editor
- Reference: Breeding, Docs

Internal navigation IDs and the `nav_changed` signal contract are unchanged
from the rail. Overflow: labels compact first, then least-recently-relevant
zone groups collapse into a `»` overflow menu. Active state = amber text +
2px amber underline.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QMenu, QToolButton,
    QSizePolicy,
)

from i18n import t
from palworld_aio.ui.chrome import icons as app_icons


def _txt(key: str, fallback: str) -> str:
    return t(key, default=fallback) if t else fallback


# Zone order and membership: (zone label key, zone short fallback, page ids)
ZONES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ('nav.zone.start', 'Start', ('tools',)),
    ('nav.zone.world', 'World', ('map', 'bases', 'players', 'guilds', 'exclusions')),
    ('nav.zone.edit', 'Edit', ('player_inventory', 'base_inventory', 'pal_editor', 'json_editor')),
    ('nav.zone.reference', 'Reference', ('breeding', 'docs')),
)

NAV_LABEL_KEYS = {
    'tools': 'tools_tab',
    'map': 'map.viewer',
    'base_inventory': 'base_inventory.tab',
    'player_inventory': 'inventory.tab',
    'pal_editor': 'pal_editor.tab',
    'players': 'deletion.search_players',
    'guilds': 'deletion.search_guilds',
    'bases': 'deletion.search_bases',
    'exclusions': 'deletion.menu.exclusions',
    'json_editor': 'json_editor.tab',
    'breeding': 'breeding.tab',
    'docs': 'docs.tab',
}

# Compact single-word forms (reused from the rail's i18n keys) — used when
# the strip must contract.
COMPACT_ENGLISH = {
    'tools': 'Tools',
    'map': 'Map',
    'base_inventory': 'Base',
    'players': 'Players',
    'guilds': 'Guilds',
    'bases': 'Bases',
    'exclusions': 'Excl.',
    'player_inventory': 'Player',
    'pal_editor': 'Pal',
    'json_editor': 'JSON',
    'breeding': 'Breeding',
    'docs': 'Docs',
}

COMPACT_KEYS = {
    'tools': 'nav.rail.tools',
    'map': 'nav.rail.map',
    'base_inventory': 'nav.rail.base_inventory',
    'players': 'nav.rail.players',
    'guilds': 'nav.rail.guilds',
    'bases': 'nav.rail.bases',
    'exclusions': 'nav.rail.exclusions',
    'player_inventory': 'nav.rail.player_inventory',
    'pal_editor': 'nav.rail.pal_editor',
    'json_editor': 'nav.rail.json_editor',
    'breeding': 'nav.rail.breeding',
    'docs': 'nav.rail.docs',
}


def nav_full_label(page_id: str) -> str:
    key = NAV_LABEL_KEYS.get(page_id, page_id)
    return t(key) if t else page_id.replace('_', ' ').title()


def nav_compact_label(page_id: str) -> str:
    fallback = COMPACT_ENGLISH.get(page_id, page_id.replace('_', ' ').title())
    return t(COMPACT_KEYS.get(page_id, ''), default=fallback) if t else fallback


def nav_zone_caption(zone_key: str, fallback: str) -> str:
    return _txt(zone_key, fallback)


class NavTab(QPushButton):
    """One destination: icon + label, amber underline when active."""

    def __init__(self, page_id: str, parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self.setObjectName('navTab')
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setIcon(app_icons.get_qicon(page_id, role='text_secondary'))
        self.setToolTip(nav_full_label(page_id))
        self.setAccessibleName(nav_full_label(page_id))
        self.setMinimumHeight(28)
        self._compact = False
        self._apply_label()

    @property
    def page_id(self) -> str:
        return self._page_id

    def _apply_label(self) -> None:
        text = nav_compact_label(self._page_id) if self._compact else nav_full_label(self._page_id)
        self.setText(text)

    def set_compact(self, compact: bool) -> None:
        if self._compact != compact:
            self._compact = compact
            self._apply_label()

    def refresh_labels(self) -> None:
        self.setIcon(app_icons.get_qicon(self._page_id, role='text_secondary'))
        self.setToolTip(nav_full_label(self._page_id))
        self.setAccessibleName(nav_full_label(self._page_id))
        self._apply_label()


class ZoneSeparator(QFrame):
    """1px vertical rule between zone groups."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('navZoneRule')
        self.setFixedWidth(1)


class ZoneCaption(QLabel):
    """Muted zone label rendered above/inline before its group."""

    def __init__(self, zone_key: str, zone_fallback: str, parent=None):
        super().__init__(parent)
        self._zone_key = zone_key
        self._zone_fallback = zone_fallback
        self.setObjectName('navZoneCaption')
        self.refresh_labels()

    def refresh_labels(self) -> None:
        self.setText(nav_zone_caption(self._zone_key, self._zone_fallback))
        tool = _txt(self._zone_key, self._zone_fallback)
        self.setToolTip(tool)


class NavStrip(QWidget):
    """Zone-grouped top navigation. Signal contract matches the rail:
    `nav_changed(str)` with the same page ids; `set_active(id)`."""

    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('navStrip')
        self.setFixedHeight(38)
        self._active_id: str | None = None
        self._tabs: dict[str, NavTab] = {}
        self._tab_zone: dict[str, str] = {}
        self._zone_keys: dict[str, tuple[str, str]] = {}
        self._hidden_zones: set[str] = set()
        self._compact = False

        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(8, 3, 8, 3)
        self._root.setSpacing(2)

        for zone_key, zone_fallback, page_ids in ZONES:
            caption = ZoneCaption(zone_key, zone_fallback)
            self._root.addWidget(caption)
            sep_before = ZoneSeparator()
            self._root.addWidget(sep_before)
            for order, page_id in enumerate(page_ids):
                tab = NavTab(page_id)
                tab.clicked.connect(lambda checked=False, pid=page_id: self._on_tab(pid))
                self._tabs[page_id] = tab
                self._tab_zone[page_id] = zone_key
                self._root.addWidget(tab)
            # remember trailing rule per zone
            trailing = ZoneSeparator()
            self._root.addWidget(trailing)
            self._zone_keys[zone_key] = (zone_key, zone_fallback)

        self._overflow_btn = QToolButton()
        self._overflow_btn.setObjectName('navOverflowBtn')
        self._overflow_btn.setText('»')
        self._overflow_btn.setToolTip(_txt('nav.overflow', 'More pages'))
        self._overflow_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._overflow_btn.setFixedHeight(28)
        self._overflow_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._overflow_menu = QMenu(self)
        self._overflow_btn.setMenu(self._overflow_menu)
        self._overflow_btn.hide()
        self._root.addWidget(self._overflow_btn)
        self._root.addStretch(1)

    # ------------------------------------------------------- interactions
    def _on_tab(self, page_id: str) -> None:
        self.set_active(page_id)
        self.nav_changed.emit(page_id)

    def set_active(self, page_id: str) -> None:
        if page_id not in self._tabs:
            return
        self._active_id = page_id
        for pid, tab in self._tabs.items():
            checked = pid == page_id
            if tab.isChecked() != checked:
                tab.setChecked(checked)
            tab.setIcon(app_icons.get_qicon(
                pid, role='accent' if checked else 'text_secondary'))

    def active_id(self) -> str | None:
        return self._active_id

    # ---------------------------------------------------------- overflow
    def setOverflowHidden(self, hidden_ids: set[str]) -> None:
        """(Compatibility shim — prefer collapse_zones.)"""
        self.collapse_zones(hidden_ids)

    def collapse_zones(self, zone_keys: set[str]) -> None:
        """Hide the given zone groups from the strip and surface them in the
        overflow menu. Empty selection clears the overflow state."""
        self._hidden_zones = set(zone_keys)
        for zone_key in self._zone_keys:
            hidden = zone_key in self._hidden_zones
            for pid, zone in self._tab_zone.items():
                if zone == zone_key:
                    self._tabs[pid].setHidden(hidden)
        self._rebuild_overflow_menu()
        has_hidden = bool(self._hidden_zones)
        self._overflow_btn.setVisible(has_hidden)

    def _rebuild_overflow_menu(self) -> None:
        self._overflow_menu.clear()
        for zone_key, _zone_fallback, page_ids in ZONES:
            if zone_key not in self._hidden_zones:
                continue
            zone_caption = nav_zone_caption(*self._zone_keys[zone_key])
            for page_id in page_ids:
                action = self._overflow_menu.addAction(
                    app_icons.get_qicon(page_id, role='text_secondary'),
                    nav_full_label(page_id))
                action.triggered.connect(
                    lambda checked=False, pid=page_id: self._on_tab(pid))

    # ------------------------------------------------------ responsiveness
    def resizeEvent(self, a0) -> None:  # Qt stub param name
        super().resizeEvent(a0)
        self._relayout_for_width()

    def _visible_width_needed(self, collapsed: set[str], compact: bool) -> int:
        fm = self.fontMetrics()
        total = 0
        for pid, tab in self._tabs.items():
            if self._tab_zone[pid] in collapsed:
                continue
            label = nav_compact_label(pid) if compact else nav_full_label(pid)
            total += fm.horizontalAdvance(label) + 46
        return total

    def _relayout_for_width(self) -> None:
        """Compact labels when tight; collapse least-priority zones last.
        Start (Tools) is never collapsed."""
        available = max(self.width() - 40, 200)
        collapsed: set[str] = set()
        compact = False
        priority = ['nav.zone.reference', 'nav.zone.edit', 'nav.zone.world']
        # pass 1: full labels
        if self._visible_width_needed(collapsed, False) > available:
            compact = True
            # pass 2: compact labels, then collapse zones in priority order
            for zone_key in priority:
                if self._visible_width_needed(collapsed, compact) <= available:
                    break
                collapsed.add(zone_key)
        # never collapse Start
        collapsed.discard('nav.zone.start')
        self._apply_layout_state(compact, collapsed)

    def _apply_layout_state(self, compact: bool, collapsed: set[str]) -> None:
        if compact != self._compact:
            self._compact = compact
            for tab in self._tabs.values():
                tab.set_compact(compact)
        if collapsed != self._hidden_zones:
            self._hidden_zones = collapsed
            for pid, zone in self._tab_zone.items():
                hidden = zone in collapsed
                tab = self._tabs[pid]
                tab.setHidden(hidden)
            self._rebuild_overflow_menu()
            self._overflow_btn.setVisible(bool(collapsed))
