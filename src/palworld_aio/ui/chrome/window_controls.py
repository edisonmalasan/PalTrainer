"""WindowControls — min/max/close cluster for the frameless window (plan 020).

In shell v2 there is no global header bar; the controls float pinned at the
window's top-right corner above the page canvas (repositioned on resize).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

from i18n import t
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons


def _txt(key: str, fallback: str) -> str:
    return t(key, default=fallback) if t else fallback


class WindowControls(QWidget):
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('windowControls')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        self.minimize_btn = QPushButton()
        self.minimize_btn.setIcon(app_icons.get_qicon('minimize', role='text_secondary'))
        self.minimize_btn.setObjectName('windowControlBtn')
        self.minimize_btn.setFixedSize(30, 24)
        self.minimize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimize_btn.setToolTip(_txt('button.minimize', 'Minimize'))
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        self.maximize_btn = QPushButton()
        self.maximize_btn.setIcon(app_icons.get_qicon('maximize', role='text_secondary'))
        self.maximize_btn.setObjectName('windowControlBtn')
        self.maximize_btn.setFixedSize(30, 24)
        self.maximize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.maximize_btn.setToolTip(_txt('button.maximize', 'Maximize'))
        self.maximize_btn.clicked.connect(self.maximize_clicked.emit)
        self.close_btn = QPushButton()
        self.close_btn.setIcon(app_icons.get_qicon('close', role='danger'))
        self.close_btn.setObjectName('windowControlBtn')
        self.close_btn.setProperty('danger', True)
        self.close_btn.setFixedSize(30, 24)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setToolTip(_txt('button.close', 'Close'))
        self.close_btn.clicked.connect(self.close_clicked.emit)
        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            lay.addWidget(btn)

    def refresh_labels(self) -> None:
        self.minimize_btn.setToolTip(_txt('button.minimize', 'Minimize'))
        self.maximize_btn.setToolTip(_txt('button.maximize', 'Maximize'))
        self.close_btn.setToolTip(_txt('button.close', 'Close'))
