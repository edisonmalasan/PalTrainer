"""NexusBand — the Deck Operations instrument rail (plan 020).

Replaces the old left sidebar + global header + right results dock with one
76px vertical rail on the right edge of the canvas. Altitudes, top to bottom:

- masthead: app monogram (click = menu popup) + dirty dot + update pulse
- navigate: 12 page destinations grouped into mission zones
- tray: save state / selection / metrics (see instrument_tray.py)
- utilities: console, tab guide, warnings, about

Legacy compatibility: MainWindow exposes facades so the historical
`sidebar.*` / `header_widget.*` call sites keep working while screens
migrate (see design-context §9.5).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QCursor, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QScrollArea, QFrame, QStyleOptionButton, QStylePainter, QStyle,
)

from i18n import t
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.instrument_tray import InstrumentTray

BAND_W = 76
ITEM_H = 40

ZONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('sidebar.section.inspect', ('tools', 'map')),
    ('sidebar.section.world', ('base_inventory', 'players', 'guilds', 'bases', 'exclusions')),
    ('sidebar.section.editing', ('player_inventory', 'pal_editor', 'json_editor')),
    ('sidebar.section.reference', ('breeding', 'docs')),
)

_NAV_LABEL_KEYS = {
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


def _nav_label(page_id: str) -> str:
    key = _NAV_LABEL_KEYS.get(page_id, page_id)
    return t(key) if t else page_id.replace('_', ' ').title()


# Rail micro-labels (ui-modernization Phase 1): one short word per
# destination so the 76px rail never clips to a shared first word
# ("Search" x3). Resolved via `nav.rail.<page_id>` so translators can
# override; English ships as code defaults. The full `_nav_label` stays
# as tooltip + accessible name.
_RAIL_SHORT_ENGLISH: dict[str, str] = {
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


def _rail_short(page_id: str) -> str:
    fallback = _RAIL_SHORT_ENGLISH.get(page_id, page_id.replace('_', ' ').title())
    text = t(f'nav.rail.{page_id}', default=fallback) if t else fallback
    return text


def _txt(key: str, fallback: str) -> str:
    return t(key, default=fallback) if t else fallback


class _TrayScroll(QScrollArea):
    """Frameless vertical scroll host for the tray on short windows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


class BandItem(QPushButton):
    """Navigation destination: icon stacked over a micro-label."""

    clicked_with_id = pyqtSignal(str)

    def __init__(self, page_id: str, parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._label = _nav_label(page_id)
        self._short = _rail_short(page_id)
        self.setProperty('bandItem', True)
        self.setFixedSize(BAND_W, ITEM_H)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(self._label)
        self.setAccessibleName(self._label)
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._page_id))

    def set_label(self, text: str) -> None:
        self.set_labels(self._short, text)

    def set_labels(self, short: str, text: str) -> None:
        self._short = short
        self._label = text
        self.setToolTip(text)
        self.setAccessibleName(text)
        self.update()

    def paintEvent(self, event) -> None:
        active = self.property('active') is True
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.ControlElement.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # vector icon (SVG factory) centered above the micro label
        color = app_icons.role_color('text_secondary' if not active else 'accent')
        pix = app_icons.get_pixmap(self._page_id, color, 16,
                                   dpr=self.devicePixelRatioF())
        if pix is not None:
            ix = (self.width() - pix.width()) // 2
            iy = 6
            p.drawPixmap(int(ix), int(iy), pix)
        # micro label: single elided line (never wrapped — wrapping clipped
        # multi-word labels to their shared first word, e.g. "Search" x3)
        label_font = QFont(constants.FONT_FAMILY, 10)
        p.setFont(label_font)
        p.setPen(self.palette().color(self.foregroundRole()))
        elided = QFontMetrics(label_font).elidedText(
            self._short, Qt.TextElideMode.ElideRight, self.width() - 8)
        flags = int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        rect = self.rect().adjusted(4, 20, -4, 0)
        p.drawText(rect, flags, elided)
        # active corner notch: amber wedge on the right edge, pointing inward
        if active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(constants.ACCENT))
            path = QPainterPath()
            path.moveTo(float(self.width()), float(self.height() // 2 - 9))
            path.lineTo(float(self.width() - 6), float(self.height() // 2))
            path.lineTo(float(self.width()), float(self.height() // 2 + 9))
            path.closeSubpath()
            p.drawPath(path)
        p.end()


class BandUtilityBtn(QPushButton):
    """Icon-only utility button (console / guide / warn / about)."""

    def __init__(self, glyph: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setProperty('bandUtility', True)
        self.setFixedSize(BAND_W - 16, 26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        # glyph param kept for call-site compatibility; icon comes from the
        # SVG factory keyed by the same name.
        self.setIcon(app_icons.get_qicon(glyph, role='text_secondary'))


class ZoneRule(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('bandZoneRule')
        self.setFixedHeight(1)


class ZoneCaption(QLabel):
    """Mission-zone caption above a rail nav group (ui-modernization Phase 1).

    Paints a short tag (INSPECT/WORLD/EDIT/REF) rather than the full zone
    name, which can never fit 76px. Full zone name stays in the tooltip.
    """

    SHORT_ENGLISH: dict[str, str] = {
        'inspect': 'INSPECT',
        'world': 'WORLD',
        'editing': 'EDIT',
        'reference': 'REF',
    }

    def __init__(self, zone_key: str, parent=None):
        super().__init__(parent)
        self._zone_key = zone_key
        self._suffix = zone_key.split('.')[-1]
        self.setObjectName('bandZoneCaption')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(False)
        self.setToolTip(_txt(zone_key, zone_key))
        self.refresh()

    def refresh(self) -> None:
        fallback = self.SHORT_ENGLISH.get(self._suffix, self._suffix.upper())
        short = t(f'nav.rail.zone.{self._suffix}', default=fallback) if t else fallback
        self.setText(short)
        self.setToolTip(_txt(self._zone_key, self._zone_key))


class NexusBand(QWidget):
    """Right-edge instrument rail: navigation + save state + tray + utilities."""

    nav_changed = pyqtSignal(str)
    console_toggled = pyqtSignal()
    about_clicked = pyqtSignal()
    guide_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    masthead_clicked = pyqtSignal()
    tray_expand_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('nexusBand')
        self._items: dict[str, BandItem] = {}
        self._active_id: str | None = None
        self._dirty = False
        self._pulse_timer: QTimer | None = None
        self._pulse_on = False
        self._setup_ui()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 6)
        root.setSpacing(0)

        # masthead: monogram button + dirty dot overlay (property-driven)
        mast_row = QHBoxLayout()
        mast_row.setContentsMargins(0, 0, 0, 4)
        mast_row.setSpacing(0)
        self.masthead_btn = BandUtilityBtn('save', _txt('deletion.title', 'PalTrainer'))
        self.masthead_btn.setObjectName('bandMasthead')
        self.masthead_btn.setFixedSize(BAND_W, 30)
        self.masthead_btn.clicked.connect(self.masthead_clicked.emit)
        mast_row.addWidget(self.masthead_btn)
        root.addLayout(mast_row)
        # dirty dot paints over the masthead (custom child, not a button)
        self._dirty_dot = QLabel(self.masthead_btn)
        self._dirty_dot.setObjectName('bandDirtyDot')
        self._dirty_dot.setFixedSize(8, 8)
        self._dirty_dot.setVisible(False)
        self._dirty_dot.move(self.masthead_btn.width() - 14, 4)

        # scrollable middle: nav zones + tray
        self._scroll = _TrayScroll(self)
        middle = QWidget()
        middle.setObjectName('bandMiddle')
        mid_layout = QVBoxLayout(middle)
        mid_layout.setContentsMargins(0, 2, 0, 2)
        mid_layout.setSpacing(0)
        self._zone_captions: list[ZoneCaption] = []
        for zone_key, page_ids in ZONES:
            caption = ZoneCaption(zone_key)
            self._zone_captions.append(caption)
            mid_layout.addWidget(caption)
            for page_id in page_ids:
                item = BandItem(page_id)
                item.clicked_with_id.connect(self._on_item_clicked)
                self._items[page_id] = item
                mid_layout.addWidget(item)
            rule = ZoneRule()
            mid_layout.addWidget(rule)
        self.tray = InstrumentTray()
        self.tray.save_clicked.connect(self.save_clicked.emit)
        self.tray.expand_requested.connect(self._on_tray_expand)
        mid_layout.addWidget(self.tray)
        mid_layout.addStretch(1)
        self._scroll.setWidget(middle)
        root.addWidget(self._scroll, stretch=1)

        # utilities
        self._console_btn = BandUtilityBtn('console', _txt('console.detach', 'Console'))
        self._console_btn.clicked.connect(self.console_toggled.emit)
        root.addWidget(self._console_btn)
        self._guide_btn = BandUtilityBtn('toolbox', _txt('tab_guide.tooltip', 'Tab Usage Guide'))
        self._guide_btn.clicked.connect(self.guide_clicked.emit)
        root.addWidget(self._guide_btn)
        self.warn_btn = BandUtilityBtn('warning', _txt('warning.title', 'Warnings'))
        self.warn_btn.setObjectName('bandWarnBtn')
        self.warn_btn.setVisible(False)
        self.warn_btn.clicked.connect(self._noop_warn)
        root.addWidget(self.warn_btn)
        self._about_btn = BandUtilityBtn('info', _txt('about.title', 'About PalTrainer'))
        self._about_btn.clicked.connect(self.about_clicked.emit)
        root.addWidget(self._about_btn)
        self._warn_slot = None

    def _noop_warn(self) -> None:
        if self._warn_slot is not None:
            self._warn_slot()

    # ------------------------------------------------------- interactions
    def _on_item_clicked(self, page_id: str) -> None:
        self.set_active(page_id)
        self.nav_changed.emit(page_id)

    def _on_tray_expand(self) -> None:
        # expand affordance forwarded to MainWindow through the facade signal
        self.tray_expand_toggled.emit(not self.tray.is_expanded())

    def set_active(self, page_id: str) -> None:
        if page_id not in self._items:
            return
        self._active_id = page_id
        for pid, item in self._items.items():
            active = pid == page_id
            if item.property('active') != active:
                item.setProperty('active', active)
                item.style().unpolish(item)
                item.style().polish(item)
                item.update()

    def set_console_visible(self, visible: bool) -> None:
        self._console_btn.setProperty('active', visible)
        self._console_btn.style().unpolish(self._console_btn)
        self._console_btn.style().polish(self._console_btn)

    def set_right_panel_visible(self, visible: bool) -> None:
        # legacy mapping: results dock toggle == tray drawer expanded
        self.tray.set_expanded(visible)

    def set_lock_state(self, locked: bool) -> bool:
        return True

    def set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self._dirty_dot.setVisible(bool(dirty))
        self._dirty_dot.style().unpolish(self._dirty_dot)
        self._dirty_dot.style().polish(self._dirty_dot)

    # ------------------------------------------------------- update pulse
    def start_pulse_animation(self, latest_version=None) -> None:
        if self._pulse_timer is not None:
            return
        self.masthead_btn.setProperty('pulse', 'true')
        self.masthead_btn.setToolTip(_txt('update.latest', 'Update available'))
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        self._pulse_timer.start(500)

    def _toggle_pulse(self) -> None:
        self._pulse_on = not self._pulse_on
        self.masthead_btn.setProperty('pulse', 'true' if self._pulse_on else 'false')
        self.masthead_btn.style().unpolish(self.masthead_btn)
        self.masthead_btn.style().polish(self.masthead_btn)
        self.masthead_btn.update()

    def stop_pulse_animation(self) -> None:
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
            self._pulse_timer = None
        self._pulse_on = False
        self.masthead_btn.setProperty('pulse', 'false')
        self.masthead_btn.style().unpolish(self.masthead_btn)
        self.masthead_btn.style().polish(self.masthead_btn)

    def update_version_text(self, local_version: str, latest_version=None) -> None:
        # version chip lives on the Start masthead (plan 021); band keeps tooltip
        pass

    # ------------------------------------------------------------ labels
    def refresh_labels(self) -> None:
        for pid, item in self._items.items():
            item.set_labels(_rail_short(pid), _nav_label(pid))
        for caption in self._zone_captions:
            caption.refresh()
        self._console_btn.setToolTip(_txt('console.detach', 'Console'))
        self._guide_btn.setToolTip(_txt('tab_guide.tooltip', 'Tab Usage Guide'))
        self.warn_btn.setToolTip(_txt('warning.title', 'Warnings'))
        self._about_btn.setToolTip(_txt('about.title', 'About PalTrainer'))
        self.tray.refresh_labels()

    # ------------------------------------------------------------ window
    def set_warning_slot(self, slot) -> None:
        """Route the warnings dialog (replaces old header warn button)."""
        self._warn_slot = slot

    def show_warning(self, show: bool = True) -> None:
        self.warn_btn.setVisible(show)
