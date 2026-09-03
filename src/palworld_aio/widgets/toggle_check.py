from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QMouseEvent
from palworld_aio import constants
from palworld_aio.ui.chrome.sidebar_widget import NerdBtn
from palworld_aio.ui.chrome import tokens as _tokens
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-fa-check': '\uf00c'}


class ToggleCheckBtn(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._checked = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._icon_btn = NerdBtn('')
        self._icon_btn.setFixedSize(20, 20)
        self._icon_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 12))
        self._icon_btn.clicked.connect(lambda: self._toggle(True))
        layout.addWidget(self._icon_btn)
        self._label = QLabel(label)
        self._label.setBackgroundRole(self._label.backgroundRole())
        self._update_style()

    def _toggle(self, from_btn=False):
        self._checked = not self._checked
        self._update_style()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event: QMouseEvent):
        child = self.childAt(event.pos())
        if child is self._label:
            self._toggle()
        super().mousePressEvent(event)

    def _update_style(self):
        t = _tokens.resolve()
        if self._checked:
            self._icon_btn.setText(nf.icons.get('nf-fa-check', '\uf00c'))
            self._icon_btn.setStyleSheet(
                f'NerdBtn {{ background: {t["accent_bg_strong"]}; color: {t["accent"]};'
                f' border: 1px solid {t["accent_border"]}; border-radius: 4px; }}'
            )
        else:
            self._icon_btn.setText('')
            self._icon_btn.setStyleSheet(
                f'NerdBtn {{ background: {_tokens.SURFACE_FAINT};'
                f' border: 1px solid {t["border"]}; border-radius: 4px; }}'
            )

    def setChecked(self, checked):
        self._checked = checked
        self._update_style()

    def isChecked(self):
        return self._checked

    def setText(self, text):
        self._label.setText(text)
