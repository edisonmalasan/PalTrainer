"""NavStrip — shell v3 two-tier top navigation (uiux-audit-remediation 1.1-1.3).

Primary tier: the zone destinations Tools, World, Edit and Reference.
Activating Tools navigates directly to the Tools page; activating World,
Edit or Reference navigates to the last-visited destination in that zone,
falling back to the zone's first child. Secondary tier: a contextual row
showing only the active zone's children (the Start/Tools zone has none).
ZONES stays the single source of membership truth.

Contracts preserved from the rail and the flat strip: page IDs, the
`nav_changed(str)` signal, `set_active(id)`, keyboard shortcut routing
(main_window activates pages via set_active) and i18n keys. Overflow per
tier: labels compact first, then least-relevant destinations collapse into
the `»` menu; Start/Tools never collapses and the active destination is
always kept directly visible.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QToolButton,
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

START_ZONE = ZONES[0][0]

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
# a tier must contract.
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

# Trailing caret marks zone destinations (they open a contextual secondary
# row) as distinct from direct destinations like Tools.
ZONE_CARET = ' \u25be'

# Fixed collapse priority for the primary tier: least-relevant zones first.
# Start/Tools never collapses and the active zone is always kept visible.
_PRIMARY_COLLAPSE_PRIORITY = ('nav.zone.reference', 'nav.zone.edit', 'nav.zone.world')


def nav_full_label(page_id: str) -> str:
    key = NAV_LABEL_KEYS.get(page_id, page_id)
    return t(key) if t else page_id.replace('_', ' ').title()


def nav_compact_label(page_id: str) -> str:
    fallback = COMPACT_ENGLISH.get(page_id, page_id.replace('_', ' ').title())
    return t(COMPACT_KEYS.get(page_id, ''), default=fallback) if t else fallback


def nav_zone_caption(zone_key: str, fallback: str) -> str:
    return _txt(zone_key, fallback)


class NavTab(QPushButton):
    """One secondary destination: icon + label, amber underline when active."""

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


class ZoneTab(QPushButton):
    """Primary-tier zone destination; amber text while its zone is active."""

    def __init__(self, zone_key: str, zone_fallback: str,
                 page_ids: tuple[str, ...], parent=None):
        super().__init__(parent)
        self._zone_key = zone_key
        self._zone_fallback = zone_fallback
        self._page_ids = tuple(page_ids)
        self.setObjectName('navZoneTab')
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(28)
        self._compact = False
        self.refresh_labels()

    @property
    def zone_key(self) -> str:
        return self._zone_key

    @property
    def page_ids(self) -> tuple[str, ...]:
        return self._page_ids

    def _apply_label(self) -> None:
        label = nav_zone_caption(self._zone_key, self._zone_fallback)
        self.setText(label if self._compact else label + ZONE_CARET)

    def set_compact(self, compact: bool) -> None:
        if self._compact != compact:
            self._compact = compact
            self._apply_label()

    def refresh_labels(self) -> None:
        self._apply_label()
        caption = nav_zone_caption(self._zone_key, self._zone_fallback)
        self.setToolTip(caption)
        self.setAccessibleName(caption)


class NavStrip(QWidget):
    """Two-tier top navigation. Signal contract matches the rail:
    `nav_changed(str)` with the same page ids; `set_active(id)`."""

    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('navStrip')
        self.setFixedHeight(72)
        self._active_id: str | None = None
        self._displayed_zone: str | None = None
        self._tabs: dict[str, NavTab] = {}
        self._tab_zone: dict[str, str] = {}
        self._zone_children: dict[str, tuple[str, ...]] = {}
        self._zone_keys: dict[str, tuple[str, str]] = {}
        self._zone_tabs: dict[str, ZoneTab] = {}
        self._zone_last: dict[str, str] = {}
        self._primary_collapsed: set[str] = set()
        self._secondary_collapsed: set[str] = set()
        self._secondary_compact = False
        self._overflow_zone_actions: dict[str, object] = {}
        self._overflow_page_actions: dict[str, object] = {}

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        # primary tier: Tools destination + zone destinations
        self._primary_row = QWidget(self)
        primary = QHBoxLayout(self._primary_row)
        primary.setContentsMargins(8, 5, 8, 3)
        primary.setSpacing(2)
        for zone_key, zone_fallback, page_ids in ZONES:
            self._zone_keys[zone_key] = (zone_key, zone_fallback)
            self._zone_children[zone_key] = page_ids
            if zone_key == START_ZONE:
                # Start zone's sole child is promoted to a primary
                # destination and navigates directly.
                pid = page_ids[0]
                tab = NavTab(pid)
                tab.clicked.connect(lambda checked=False, pid=pid: self._on_tab(pid))
                self._tabs[pid] = tab
                self._tab_zone[pid] = zone_key
                primary.addWidget(tab)
                continue
            zone_tab = ZoneTab(zone_key, zone_fallback, page_ids)
            zone_tab.clicked.connect(lambda checked=False, zk=zone_key: self._on_zone_tab(zk))
            self._zone_tabs[zone_key] = zone_tab
            primary.addWidget(zone_tab)
            for page_id in page_ids:
                tab = NavTab(page_id)
                tab.clicked.connect(lambda checked=False, pid=page_id: self._on_tab(pid))
                self._tabs[page_id] = tab
                self._tab_zone[page_id] = zone_key
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
        primary.addStretch(1)
        primary.addWidget(self._overflow_btn)
        self._root.addWidget(self._primary_row)

        # secondary tier: the active zone's children only
        self._secondary_row = QWidget(self)
        secondary = QHBoxLayout(self._secondary_row)
        secondary.setContentsMargins(8, 3, 8, 5)
        secondary.setSpacing(2)
        for zone_key, _fb, page_ids in ZONES:
            if zone_key == START_ZONE:
                continue  # no secondary children
            for page_id in page_ids:
                secondary.addWidget(self._tabs[page_id])
        secondary.addStretch(1)
        self._root.addWidget(self._secondary_row)
        self._apply_secondary_visibility()

    # ------------------------------------------------------- interactions
    def _zone_target(self, zone_key: str) -> str:
        """Last-visited destination in the zone, first child as fallback."""
        last = self._zone_last.get(zone_key)
        if last in self._tabs and self._tab_zone.get(last) == zone_key:
            return last
        return self._zone_children[zone_key][0]

    def _on_zone_tab(self, zone_key: str) -> None:
        self._on_tab(self._zone_target(zone_key))

    def _on_tab(self, page_id: str) -> None:
        self.set_active(page_id)
        self.nav_changed.emit(page_id)

    def set_active(self, page_id: str) -> None:
        if page_id not in self._tabs:
            return
        zone_key = self._tab_zone[page_id]
        self._active_id = page_id
        self._zone_last[zone_key] = page_id
        if self._displayed_zone != zone_key:
            self._displayed_zone = zone_key
            self._apply_secondary_visibility()
            self._relayout_for_width()
        elif page_id in self._secondary_collapsed:
            self._relayout_for_width()
        for pid, tab in self._tabs.items():
            checked = pid == page_id
            if tab.isChecked() != checked:
                tab.setChecked(checked)
            tab.setIcon(app_icons.get_qicon(
                pid, role='accent' if checked else 'text_secondary'))
        for zk, zone_tab in self._zone_tabs.items():
            checked = zk == zone_key
            if zone_tab.isChecked() != checked:
                zone_tab.setChecked(checked)

    def active_id(self) -> str | None:
        return self._active_id

    def refresh_labels(self) -> None:
        for tab in self._tabs.values():
            tab.refresh_labels()
        for zone_tab in self._zone_tabs.values():
            zone_tab.refresh_labels()
        self._overflow_btn.setToolTip(_txt('nav.overflow', 'More pages'))

    # ---------------------------------------------------------- overflow
    def setOverflowHidden(self, hidden_ids: set[str]) -> None:
        """(Compatibility shim — prefer collapse_zones.)"""
        self.collapse_zones(hidden_ids)

    def collapse_zones(self, zone_keys: set[str]) -> None:
        """Manually collapse primary zone destinations into the overflow
        menu. Empty selection clears the collapsed state. Start/Tools is
        never collapsible."""
        self._primary_collapsed = {
            zk for zk in zone_keys if zk in self._zone_tabs}
        self._primary_collapsed.discard(START_ZONE)
        for zk, zone_tab in self._zone_tabs.items():
            zone_tab.setHidden(zk in self._primary_collapsed)
        self._rebuild_overflow_menu()
        self._overflow_btn.setVisible(
            bool(self._primary_collapsed or self._secondary_collapsed))

    def _rebuild_overflow_menu(self) -> None:
        self._overflow_menu.clear()
        self._overflow_zone_actions = {}
        self._overflow_page_actions = {}
        for zone_key, _fb, page_ids in ZONES:
            if zone_key not in self._primary_collapsed:
                continue
            action = self._overflow_menu.addAction(
                app_icons.get_qicon(page_ids[0], role='text_secondary'),
                nav_zone_caption(*self._zone_keys[zone_key]))
            action.triggered.connect(
                lambda checked=False, zk=zone_key: self._on_tab(self._zone_target(zk)))
            self._overflow_zone_actions[zone_key] = action
        if self._primary_collapsed and self._secondary_collapsed:
            self._overflow_menu.addSeparator()
        for page_id in self._zone_children.get(self._displayed_zone or '', ()):
            if page_id not in self._secondary_collapsed:
                continue
            action = self._overflow_menu.addAction(
                app_icons.get_qicon(page_id, role='text_secondary'),
                nav_full_label(page_id))
            action.triggered.connect(
                lambda checked=False, pid=page_id: self._on_tab(pid))
            self._overflow_page_actions[page_id] = action

    # ------------------------------------------------------ responsiveness
    def resizeEvent(self, a0) -> None:  # Qt stub param name
        super().resizeEvent(a0)
        self._relayout_for_width()

    def _primary_width_needed(self, collapsed: set[str]) -> int:
        fm = self.fontMetrics()
        total = fm.horizontalAdvance(nav_full_label('tools')) + 46
        for zone_key in self._zone_tabs:
            if zone_key in collapsed:
                continue
            label = nav_zone_caption(*self._zone_keys[zone_key]) + ZONE_CARET
            total += fm.horizontalAdvance(label) + 46
        return total

    def _secondary_width_needed(self, compact: bool, collapsed: set[str]) -> int:
        if not self._displayed_zone:
            return 0
        fm = self.fontMetrics()
        total = 0
        for pid in self._zone_children.get(self._displayed_zone, ()):
            if pid in collapsed:
                continue
            label = nav_compact_label(pid) if compact else nav_full_label(pid)
            total += fm.horizontalAdvance(label) + 46
        return total

    def _relayout_for_width(self) -> None:
        """Per tier: compact labels first, then collapse destinations into
        the overflow menu. Start/Tools never collapses; the active zone's
        primary tab and the active page's tab stay directly visible."""
        available = max(self.width() - 40, 200)

        primary_collapsed: set[str] = set()
        active_zone = self._tab_zone.get(self._active_id, '') if self._active_id else ''
        for zone_key in _PRIMARY_COLLAPSE_PRIORITY:
            if self._primary_width_needed(primary_collapsed) <= available:
                break
            if zone_key == active_zone:
                continue
            primary_collapsed.add(zone_key)

        secondary_collapsed: set[str] = set()
        secondary_compact = False
        if self._secondary_width_needed(False, secondary_collapsed) > available:
            secondary_compact = True
            if self._secondary_width_needed(True, secondary_collapsed) > available:
                # collapse in zone order so trailing destinations (e.g.
                # Exclusions) stay directly visible the longest
                for pid in self._zone_children.get(self._displayed_zone or '', ()):
                    if self._secondary_width_needed(True, secondary_collapsed) <= available:
                        break
                    if pid == self._active_id:
                        continue
                    secondary_collapsed.add(pid)
        self._apply_layout_state(secondary_compact, primary_collapsed, secondary_collapsed)

    def _apply_layout_state(self, compact: bool, primary_collapsed: set[str],
                            secondary_collapsed: set[str]) -> None:
        if compact != self._secondary_compact:
            self._secondary_compact = compact
            for tab in self._tabs.values():
                tab.set_compact(compact)
            for zone_tab in self._zone_tabs.values():
                zone_tab.set_compact(compact)
        if primary_collapsed != self._primary_collapsed:
            self._primary_collapsed = set(primary_collapsed)
            for zk, zone_tab in self._zone_tabs.items():
                zone_tab.setHidden(zk in primary_collapsed)
        if secondary_collapsed != self._secondary_collapsed:
            self._secondary_collapsed = set(secondary_collapsed)
            self._apply_secondary_visibility()
        self._rebuild_overflow_menu()
        self._overflow_btn.setVisible(
            bool(self._primary_collapsed or self._secondary_collapsed))

    def _apply_secondary_visibility(self) -> None:
        """Show only the displayed zone's children that are not collapsed."""
        for pid, zone in self._tab_zone.items():
            if zone == START_ZONE:
                continue  # primary destination, never hidden by tier logic
            tab = self._tabs[pid]
            visible = (zone == self._displayed_zone
                       and pid not in self._secondary_collapsed)
            tab.setVisible(visible)
