"""StatsDrawer — canvas-local statistics overlay (top-nav-shell 5.1).

Formerly ``TrayDrawer`` in ``instrument_tray.py``; the instrument tray was
retired with the right rail, and this drawer survives as the on-demand
statistics popover for the app-bar context indicator. Esc / scrim click
close it (MainWindow wires).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect,
)

from i18n import t
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.widgets.stats_panel import StatsPanel


def _txt(key: str, fallback: str) -> str:
    return t(key, default=fallback) if t else fallback


class StatsDrawer(QFrame):

    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('trayDrawer')
        self.setFixedWidth(360)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        head = QHBoxLayout()
        title = QLabel(_txt('deletion.stats_panel', 'Statistics'))
        title.setObjectName('drawerTitle')
        head.addWidget(title)
        head.addStretch(1)
        close_btn = QPushButton()
        close_btn.setIcon(app_icons.get_qicon('close', role='text_secondary'))
        close_btn.setObjectName('drawerCloseBtn')
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setToolTip(_txt('button.close', 'Close'))
        close_btn.clicked.connect(self.close_requested.emit)
        head.addWidget(close_btn)
        lay.addLayout(head)
        self.stats_panel = StatsPanel()
        self.stats_panel.setObjectName('statsGrid')
        lay.addWidget(self.stats_panel, stretch=1)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 130))
        self.setGraphicsEffect(shadow)

    def refresh_labels(self) -> None:
        self.stats_panel.refresh_labels()


# Backwards-compat alias for the pre-rename import path.
TrayDrawer = StatsDrawer
