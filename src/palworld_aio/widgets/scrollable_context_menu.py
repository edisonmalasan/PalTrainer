from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGraphicsDropShadowEffect, QLabel, QScrollArea, QMenu
from PyQt6.QtCore import Qt, QPoint, QEvent, QEventLoop, QTimer, QRect
from PyQt6.QtGui import QColor, QCursor, QFont
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_button

class _GroupHeader(QWidget):
    def __init__(self, name, idx):
        super().__init__()
        self._idx = idx
        self.setObjectName('popupGroupHeader')
        self.setAccessibleName(name)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(180)
        self.setMinimumHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        self.icon_label = QLabel('')
        self.icon_label.setFont(QFont(constants.FONT_FAMILY, 11))
        layout.addWidget(self.icon_label)
        self.text_label = QLabel(name)
        self.text_label.setFont(QFont(constants.FONT_FAMILY, 11))
        layout.addWidget(self.text_label)
        layout.addStretch()
        self.chevron_label = QLabel()
        self.chevron_label.setPixmap(
            app_icons.get_pixmap('chevron_right', size=12,
                                  role='text_secondary'))
        layout.addWidget(self.chevron_label)
        self._update_theme()

    def _update_theme(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_hovered(self, hovered):
        self.setProperty('hovered', hovered)
        self.style().unpolish(self)
        self.style().polish(self)

class ScrollableContextMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._loop = None
        self.setObjectName('popupSurface')
        self.setAccessibleName('Context actions')
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        self.container = QFrame(self)
        self.container.setObjectName('popupSurface')
        _shadow = QGraphicsDropShadowEffect(self.container)
        _shadow.setBlurRadius(20)
        _shadow.setOffset(3, 3)
        _shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(_shadow)
        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        self.scroll_area = QScrollArea(self.container)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setMaximumHeight(160)
        self.scroll_area.setObjectName('contextMenuScroll')
        self.content_widget = QWidget()
        self.content_widget.setObjectName('popupContent')
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.content_widget.setMinimumWidth(200)
        self.scroll_area.setWidget(self.content_widget)
        cl.addWidget(self.scroll_area)
        main_layout.addWidget(self.container)
        self.setMinimumWidth(220)
        self._groups = []
        self._active_group = -1
        self._sub_popup = None
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._check_cursor)
        self._cursor_timer.setInterval(50)
        self._in_group = False
        self._group_items = []
        self._hiding_sub = False

    def add_group_end(self):
        self._in_group = False
        self._group_items = []

    def add_group_start(self, name, expanded=True):
        self._in_group = True
        self._group_items = []
        idx = len(self._groups)
        hdr = _GroupHeader(name, idx)
        self._groups.append((hdr, self._group_items))
        self.layout.addWidget(hdr)

    def _is_over_widget(self, widget, cursor_pos):
        if not widget or not widget.isVisible():
            return False
        tl = widget.mapToGlobal(QPoint(0, 0))
        rect = QRect(tl, widget.size())
        return rect.contains(cursor_pos)

    def _show_group(self, idx):
        if self._sub_popup or getattr(self, '_skip_header', -1) == idx:
            return
        hdr, items = self._groups[idx]
        qmenu = QMenu(self)
        qmenu.setObjectName('appContextMenu')
        qmenu.installEventFilter(self)
        for key, text, checkable, checked in items:
            if key == '---':
                qmenu.addSeparator()
                continue
            action = qmenu.addAction(text)
            action.setCheckable(checkable)
            action.setChecked(checked)
            action.setData(key)
        self._sub_popup = qmenu
        qmenu.popup(hdr.mapToGlobal(QPoint(hdr.width(), 0)))
        qmenu.triggered.connect(self._on_sub_triggered)
        qmenu.aboutToHide.connect(self._on_sub_hide)
        self._active_group = idx
        hdr.set_active(True)

    def _on_sub_triggered(self, action):
        self._result = action.data()
        self.close()

    def _on_sub_hide(self):
        self._skip_header = self._active_group
        QTimer.singleShot(200, self._clear_skip_header)
        self._hide_sub()

    def _clear_skip_header(self):
        self._skip_header = -1

    def _hide_sub(self):
        if self._sub_popup:
            self._sub_popup.blockSignals(True)
            self._sub_popup.hide()
            self._sub_popup.setParent(None)
            self._sub_popup = None
        for idx, (hdr, items) in enumerate(self._groups):
            hdr.set_active(False)
        self._active_group = -1

    def _check_cursor(self):
        pos = QCursor.pos()
        over_sub = self._sub_popup and self._is_over_widget(self._sub_popup, pos)
        over_header = None
        for idx, (hdr, items) in enumerate(self._groups):
            hov = self._is_over_widget(hdr, pos)
            hdr.set_hovered(hov)
            if hov:
                over_header = idx
                if self._active_group != idx:
                    self._show_group(idx)
        if over_header is None and not over_sub:
            self._hide_sub()

    def eventFilter(self, a0, a1):
        if a1.type() == QEvent.Wheel and a0 is self._sub_popup:
            if self.scroll_area and self.scroll_area.isVisible():
                self.scroll_area.wheelEvent(a1)
                return True
        return super().eventFilter(a0, a1)

    def add_item(self, key, text, checkable=False, checked=False):
        if self._in_group:
            self._group_items.append((key, text, checkable, checked))
            return
        btn = make_button(text, 'tertiary')
        btn.setObjectName('popupMenuItem')
        btn.setAccessibleName(text)
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn.setCheckable(checkable)
        btn.setChecked(checked)
        btn.setMinimumHeight(34)
        btn.clicked.connect(lambda: self._select(key))
        self.layout.addWidget(btn)
        return btn

    def add_sep(self):
        if self._in_group:
            self._group_items.append(('---', '', False, False))
            return
        sep = QFrame()
        sep.setObjectName('popupSeparator')
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        self.layout.addWidget(sep)

    def add_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName('popupMenuLabel')
        self.layout.addWidget(lbl)

    def add_action(self, action):
        btn = make_button(action.text(), 'tertiary')
        btn.setObjectName('popupMenuItem')
        btn.setAccessibleName(action.text())
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn.setMinimumHeight(34)
        btn.clicked.connect(action.trigger)
        self.layout.addWidget(btn)
        return btn

    def addSeparator(self):
        self.add_sep()

    def _select(self, key):
        self._result = key
        self.close()

    def exec(self, pos):
        self._result = None
        self.move(pos)
        self.adjustSize()
        self.show()
        self.raise_()
        self.activateWindow()
        self._cursor_timer.start()
        loop = QEventLoop()
        self._loop = loop
        self.destroyed.connect(loop.quit)
        loop.exec()
        return self._result

    def closeEvent(self, a0):
        self._cursor_timer.stop()
        self._hide_sub()
        if self._loop and self._loop.isRunning():
            self._loop.quit()
        super().closeEvent(a0)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()
            a0.accept()
            return
        super().keyPressEvent(a0)
