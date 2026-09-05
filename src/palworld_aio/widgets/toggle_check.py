from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome import tokens as _tokens


class ToggleCheckBtn(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._checked = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._icon_btn = QPushButton()
        self._icon_btn.setFixedSize(20, 20)
        self._icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._icon_btn.clicked.connect(lambda: self._toggle(True))
        layout.addWidget(self._icon_btn)
        self._label = QLabel(label)
        self._label.setBackgroundRole(self._label.backgroundRole())
        layout.addWidget(self._label, 1)
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
            self._icon_btn.setIcon(app_icons.get_qicon('check', role='accent'))
            self._icon_btn.setStyleSheet(
                f'QPushButton {{ background: {t["accent_bg_strong"]};'
                f' border: 1px solid {t["accent_border"]}; border-radius: 4px; }}'
            )
        else:
            self._icon_btn.setIcon(app_icons.get_qicon('check', role='text_disabled'))
            self._icon_btn.setStyleSheet(
                f'QPushButton {{ background: {_tokens.SURFACE_FAINT};'
                f' border: 1px solid {t["border"]}; border-radius: 4px; }}'
            )

    def setChecked(self, checked):
        self._checked = checked
        self._update_style()

    def isChecked(self):
        return self._checked

    def setText(self, text):
        self._label.setText(text)
