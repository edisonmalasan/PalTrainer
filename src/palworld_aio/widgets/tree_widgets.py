from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from palworld_aio.ui.chrome.localization import tr


class SortableTreeWidget(QTreeWidget):
    context_menu_requested = pyqtSignal(object, object)
    def __init__(self, columns, column_widths=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.column_widths = column_widths or []
        self._setup_ui()
    def _setup_ui(self):
        self.setObjectName('dataTree')
        self.setAccessibleName(tr('ui.table.accessible', 'Data table'))
        self.setHeaderLabels(self.columns)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        header = self.header()
        for i, width in enumerate(self.column_widths):
            if i < len(self.columns):
                self.setColumnWidth(i, width)
        header.setStretchLastSection(True)
    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            self.setCurrentItem(item)
            global_pos = self.viewport().mapToGlobal(pos)
            self.context_menu_requested.emit(item, global_pos)
    def add_item(self, values, data=None):
        item = QTreeWidgetItem([str(v) for v in values])
        if data:
            item.setData(0, Qt.UserRole, data)
        self.addTopLevelItem(item)
        return item
    def get_selected_values(self):
        items = self.selectedItems()
        if items:
            item = items[0]
            return [item.text(i) for i in range(item.columnCount())]
        return None
    def get_selected_data(self):
        items = self.selectedItems()
        if items:
            return items[0].data(0, Qt.UserRole)
        return None
