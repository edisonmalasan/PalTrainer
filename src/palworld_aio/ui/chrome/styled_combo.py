from PyQt6.QtWidgets import QWidget, QPushButton, QFrame, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QEvent
from palworld_aio.ui.chrome.localization import tr
class StyledCombo(QWidget):
    currentIndexChanged = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._current_index = -1
        self._enabled = True
        self._max_visible_items = 12
        self._setup_ui()
    def _setup_ui(self):
        self._button = QPushButton()
        self._button.setObjectName('styledComboButton')
        self._button.setAccessibleName(tr('ui.combo.select', 'Choose an option'))
        self._button.setFixedHeight(24)
        self._button.setCursor(Qt.PointingHandCursor)
        self._button.clicked.connect(self._toggle_popup)
        self._popup = QFrame(self, Qt.Popup)
        self._popup.setObjectName('styledComboPopup')
        self._popup.setFixedWidth(300)
        self._popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self._popup.setAttribute(Qt.WA_TranslucentBackground)
        self._popup.setFocusPolicy(Qt.NoFocus)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)
        self._list = QListWidget()
        self._list.setObjectName('styledComboList')
        self._list.setAccessibleName(tr('ui.combo.options', 'Options'))
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        popup_layout.addWidget(self._list)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._button)
        self._button.installEventFilter(self)
        self._popup.installEventFilter(self)
        self._list.installEventFilter(self)
    def eventFilter(self, obj, event):
        if obj == self._list and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self._list.currentItem()
                if item is not None:
                    self._on_item_clicked(item)
                return True
            if event.key() == Qt.Key.Key_Escape:
                self._hide_popup()
                return True
        if obj == self._button and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self._show_popup()
                return True
        if obj == self._popup:
            if event.type() == QEvent.Type.MouseButtonPress:
                pos = self.mapFromGlobal(event.globalPosition().toPoint())
                if not self._popup.geometry().contains(pos):
                    self._hide_popup()
                    return True
        return super().eventFilter(obj, event)
    def setMaxVisibleItems(self, count):
        self._max_visible_items = count
        self._update_popup_height()
    def _update_popup_height(self):
        item_height = 28
        max_height = self._max_visible_items * item_height + 8
        self._list.setMaximumHeight(max_height)
    def _toggle_popup(self):
        if not self._enabled:
            return
        if self._popup.isVisible():
            self._hide_popup()
        else:
            self._show_popup()
    def _show_popup(self):
        self._update_popup_height()
        self._list.setMinimumWidth(self._button.width() - 8)
        pos = self._button.mapToGlobal(QPoint(0, self._button.height()))
        self._popup.move(pos)
        self._popup.show()
        self._list.setFocus()
    def _hide_popup(self):
        self._popup.hide()
        self._button.setFocus(Qt.FocusReason.PopupFocusReason)
    def _on_item_clicked(self, item):
        index = self._list.row(item)
        if item.flags() & Qt.ItemIsEnabled:
            self._current_index = index
            self._button.setText(item.text())
            self._button.setAccessibleName(item.text())
            self._hide_popup()
            self.currentIndexChanged.emit(index)
    def addItem(self, text, userData=None):
        self._items.append({'text': text, 'userData': userData, 'enabled': True})
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, userData)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self._list.addItem(item)
        if self._current_index == -1:
            self.setCurrentIndex(0)
    def clear(self):
        self._items = []
        self._list.clear()
        self._current_index = -1
        self._button.setText('')
    def currentIndex(self):
        return self._current_index
    def currentData(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]['userData']
        return None
    def setCurrentIndex(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            self._items[index]['text']
            self._button.setText(self._items[index]['text'])
            self._button.setAccessibleName(self._items[index]['text'])
            self._list.setCurrentRow(index)
            return True
        return False
    def count(self):
        return len(self._items)
    def itemData(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]['userData']
        return None
    def setEnabled(self, enabled):
        self._enabled = enabled
        self._button.setEnabled(enabled)
        if not enabled:
            self._button.setText('')
            self._current_index = -1
    def setItemEnabled(self, index, enabled):
        if 0 <= index < len(self._items):
            self._items[index]['enabled'] = enabled
            item = self._list.item(index)
            if item:
                if enabled:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                else:
                    item.setFlags(Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
    def blockSignals(self, block):
        self._list.blockSignals(block)
    def currentText(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]['text']
        return ''
    def setItemText(self, index, text):
        if 0 <= index < len(self._items):
            self._items[index]['text'] = text
            item = self._list.item(index)
            if item:
                item.setText(text)
            if index == self._current_index:
                self._button.setText(text)
                self._button.setAccessibleName(text)
    def model(self):
        return self._list.model()
