from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
class EmptyState(QWidget):
    """Shared empty-state surface: glyph, title, hint, optional action.

    Replaces the per-tab placeholder-label duplicates and gives panels without
    any empty indication (Missions, Technology) a consistent one.
    """
    action_clicked = pyqtSignal()
    def __init__(self, title, hint='', icon_name='', action_text='', parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 32, 16, 32)
        layout.setSpacing(8)
        layout.addStretch()
        if icon_name and app_icons.has_vector_icon(icon_name):
            icon_label = QLabel()
            pix = app_icons.get_pixmap(
                icon_name, constants.TEXT_DISABLED, constants.ICON_XL)
            if pix is not None:
                icon_label.setPixmap(pix)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet('background: transparent;')
            layout.addWidget(icon_label)
            layout.addSpacing(4)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            f'color: {constants.MUTED}; font-size: {constants.FONT_SIZE_PX_SECTION}px; '
            'font-weight: 600; background: transparent;'
        )
        layout.addWidget(title_label)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setAlignment(Qt.AlignCenter)
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet(
                f'color: {constants.TEXT_DISABLED}; font-size: {constants.FONT_SIZE_PX_SECONDARY}px; '
                'background: transparent;'
            )
            layout.addWidget(hint_label)
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.setFixedHeight(constants.CONTROL_H_MD)
            action_btn.setStyleSheet(
                f'QPushButton {{ background: {constants.ACCENT_BG}; color: {constants.ACCENT}; '
                f'border: 1px solid {constants.ACCENT_BORDER}; border-radius: {constants.RADIUS_MD}px; '
                'padding: 4px 16px; font-weight: 600; font-size: '
                f'{constants.FONT_SIZE_PX_BODY}px; }} '
                f'QPushButton:hover {{ background: {constants.ACCENT_BG_STRONG}; color: {constants.EMPHASIS}; }}'
            )
            action_btn.clicked.connect(self.action_clicked.emit)
            btn_row = QVBoxLayout()
            btn_row.setAlignment(Qt.AlignCenter)
            btn_row.addWidget(action_btn)
            layout.addLayout(btn_row)
        layout.addStretch()
        self._title_label = title_label
    def setText(self, text):
        self._title_label.setText(text)
    def text(self):
        return self._title_label.text()
