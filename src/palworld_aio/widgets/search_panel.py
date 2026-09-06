from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from i18n import t
from palworld_aio import constants
_SORT_ROLE = Qt.UserRole + 1
# modernize-tab-ui 5.2: full GUID stored per column when the display text is
# shortened; selection signals, context-menu readers, search and sort resolve
# this role so behavior matches the pre-shortening text exactly.
GUID_ROLE = Qt.UserRole + 2
def _display_value(item, col):
    value = item.data(col, GUID_ROLE)
    return str(value) if value not in (None, '') else item.text(col)
class _SortableTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        a = self.data(col, _SORT_ROLE)
        b = other.data(col, _SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return _display_value(self, col) < _display_value(other, col)
class SearchPanel(QWidget):
    """Dense full-bleed table workspace (plan 023).

    Public API unchanged (add_item/clear/set_items/get_*/signals); layout is
    now: filter row + full-bleed dense tree + footer context strip. The old
    per-panel TREE_WIDGET_QSS application is removed (global table QSS owns
    presentation).
    """
    item_selected = pyqtSignal(object)
    item_double_clicked = pyqtSignal(object)
    search_requested = pyqtSignal(str)
    def __init__(self, label_key, column_keys, column_widths=None, parent=None, selection_mode=QAbstractItemView.SingleSelection):
        super().__init__(parent)
        self.label_key = label_key
        self.column_keys = column_keys
        self.column_widths = column_widths or []
        self._selection_mode = selection_mode
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # filter row: title chip + inline search + result count (ribbon grammar).
        # Window controls live in the app bar (shell v3), so rows span the
        # full canvas width — no right reserve needed.
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(8)
        self.search_label = QLabel(t(self.label_key) if t else self.label_key)
        self.search_label.setObjectName('missionZone')
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('searchInput')
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input, stretch=1)
        self.count_label = QLabel('0')
        self.count_label.setObjectName('searchCount')
        search_layout.addWidget(self.count_label)
        layout.addLayout(search_layout)
        hairline = QFrame()
        hairline.setObjectName('bandZoneRule')
        hairline.setFixedHeight(1)
        layout.addWidget(hairline)
        # full-bleed dense table
        self.tree = QTreeWidget()
        self.tree.setObjectName('searchTree')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(self._selection_mode)
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.tree.header()
        for i, width in enumerate(self.column_widths):
            if i < len(self.columns):
                self.tree.setColumnWidth(i, width)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, stretch=1)
        # empty-state overlay (top-nav-shell 4.2): no-save / no-results hints
        self._empty_label = QLabel('')
        self._empty_label.setObjectName('tableEmptyHint')
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._empty_label.hide()
        self._empty_label.setParent(self.tree.viewport())
        self._empty_label.setGeometry(self.tree.viewport().rect())
        tree_resize = self.tree.resizeEvent

        def _tree_resized(event, _tree=self.tree, _label=self._empty_label, _panel=self, _orig=tree_resize):
            QTreeWidget.resizeEvent(_tree, event)
            _label.setGeometry(_tree.viewport().rect())
            # the viewport is a C++-created widget, so its resizeEvent cannot
            # be overridden from Python; track the empty-state overlay here
            widget = getattr(_panel, '_empty_widget', None)
            if widget is not None:
                widget.setGeometry(_tree.viewport().rect())
            if _orig:
                _orig(event)
        self.tree.resizeEvent = _tree_resized  # type: ignore[method-assign]
        # footer context strip
        footer = QFrame()
        footer.setObjectName('tableFooter')
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 4, 12, 4)
        footer_layout.setSpacing(8)
        self.hint_label = QLabel('')
        self.hint_label.setObjectName('bulkHintLabel')
        footer_layout.addWidget(self.hint_label)
        footer_layout.addStretch(1)
        self.footer_slot = footer_layout
        layout.addWidget(footer)
        self._update_count()
        self._all_items = []
        self.set_empty_state(t('status.no_save_data') if t else 'No data — load a save first.')

    def set_empty_state(self, message: str) -> None:
        """Show a centered hint over the table when it has no rows."""
        self._empty_message = message
        if not message:
            self._empty_label.hide()
            return
        self._empty_label.setText(message)
        self._empty_label.setGeometry(self.tree.viewport().rect())
        self._empty_label.show()

    def set_empty_state_widget(self, widget) -> None:
        """modernize-tab-ui 5.3: rich EmptyState overlay replacing the plain
        hint for this panel's no-rows state (e.g. Guilds members pane).
        Pass None to detach and fall back to the plain hint."""
        previous = getattr(self, '_empty_widget', None)
        self._empty_widget = widget
        if widget is not None:
            widget.setParent(self.tree.viewport())
            widget.setGeometry(self.tree.viewport().rect())
        if previous is not None and previous is not widget:
            previous.hide()
        # re-evaluate: the previous overlay (if any) may have been visible
        self._refresh_empty_state()

    def _show_empty_overlay(self, message: str) -> None:
        widget = getattr(self, '_empty_widget', None)
        if widget is not None:
            self._empty_label.hide()
            widget.setGeometry(self.tree.viewport().rect())
            widget.show()
        else:
            self._empty_label.setText(message)
            self._empty_label.setGeometry(self.tree.viewport().rect())
            self._empty_label.show()

    def _hide_empty_overlay(self) -> None:
        self._empty_label.hide()
        widget = getattr(self, '_empty_widget', None)
        if widget is not None:
            widget.hide()

    def _refresh_empty_state(self) -> None:
        visible = sum(0 if self.tree.topLevelItem(i).isHidden() else 1
                      for i in range(self.tree.topLevelItemCount()))
        if visible == 0:
            searched = self.search_input.text().strip()
            if searched and self.tree.topLevelItemCount() > 0:
                message = t('search.no_matches') if t else 'No matches'
            elif self.tree.topLevelItemCount() == 0:
                message = getattr(self, '_empty_message', '') or (t('status.no_save_data') if t else 'No data — load a save first.')
            else:
                message = t('search.no_matches') if t else 'No matches'
            self._show_empty_overlay(message)
        else:
            self._hide_empty_overlay()
    def _update_count(self):
        total = self.tree.topLevelItemCount()
        visible = sum(0 if self.tree.topLevelItem(i).isHidden() else 1 for i in range(total))
        self.count_label.setText(f'{visible}/{total}' if total != visible else str(total))
        if hasattr(self, '_empty_label'):
            self._refresh_empty_state()
    def _on_search(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = False
            for col in range(item.columnCount()):
                if text in item.text(col).lower() or text in item.toolTip(col).lower():
                    match = True
                    break
            item.setHidden(not match)
        self._update_count()
    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            data = [_display_value(item, i) for i in range(item.columnCount())]
            self.item_selected.emit(data)
    def _on_double_click(self, item, column):
        data = [_display_value(item, i) for i in range(item.columnCount())]
        self.item_double_clicked.emit(data)
    def clear(self):
        self.tree.clear()
        self._all_items = []
        self._update_count()
    def add_item(self, values, data=None, sort_keys=None, tooltips=None):
        item = _SortableTreeWidgetItem([str(v) for v in values])
        if data:
            item.setData(0, Qt.UserRole, data)
        if sort_keys:
            for col, key in sort_keys.items():
                item.setData(col, _SORT_ROLE, key)
        # modernize-tab-ui 5.2: per-column tooltip; the tooltip text is also
        # stored in GUID_ROLE when it differs from the displayed (shortened)
        # text, so readers of the row resolve the full value.
        if tooltips:
            for col, tip in tooltips.items():
                if col < item.columnCount() and tip:
                    item.setToolTip(col, str(tip))
                    if str(tip) != item.text(col):
                        item.setData(col, GUID_ROLE, str(tip))
        self.tree.addTopLevelItem(item)
        self._all_items.append(item)
        self._update_count()
        return item
    def get_selected_items(self):
        return self.tree.selectedItems()
    def get_selected_item(self):
        items = self.tree.selectedItems()
        if items:
            return items[0]
        return None
    def get_selected_data(self):
        item = self.get_selected_item()
        if item:
            return [_display_value(item, i) for i in range(item.columnCount())]
        return None
    def get_selected_data_all(self):
        return [[_display_value(item, i) for i in range(item.columnCount())] for item in self.tree.selectedItems()]
    def set_items(self, items_data):
        self.clear()
        for values in items_data:
            self.add_item(values)
    def refresh_labels(self):
        self.search_label.setText(t(self.label_key) if t else self.label_key)
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)
        self._refresh_empty_state()