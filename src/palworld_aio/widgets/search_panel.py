from typing import Callable, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QAbstractItemView, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor, QKeySequence
from i18n import t
from palworld_aio import constants
_SORT_ROLE = Qt.UserRole + 1
# modernize-tab-ui 5.2: full GUID stored per column when the display text is
# shortened; selection signals, context-menu readers, search and sort resolve
# this role so behavior matches the pre-shortening text exactly.
GUID_ROLE = Qt.UserRole + 2
# uiux-audit-remediation 4.3: per-column copyable identifiers — set with
# ``panel.set_copyable_columns({0, 1})``; the display stays the shortened
# text, Ctrl+C copies the full GUID from GUID_ROLE, and the tree font goes
# monospace when every copyable column is covered (Bases: ID columns only).
COPY_ROLE = Qt.UserRole + 3


class _CopyableTree(QTreeWidget):
    """QTreeWidget + Ctrl+C copies the full value of copyable columns
    (GUID_ROLE when set, else display text). Selection/context menus are
    the parent policy's — this only adds a keyboard copy."""

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self._panel = panel

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            copied = False
            for item in self.selectedItems():
                values = []
                for col in range(item.columnCount()):
                    if col in self._panel._copyable_columns:
                        values.append(str(item.data(col, GUID_ROLE)
                                          or _display_value(item, col)))
                if values:
                    QApplication.clipboard().setText('\t'.join(values))
                    copied = True
            if copied:
                event.accept()
                return
        super().keyPressEvent(event)
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
        self._copyable_columns: set[int] = set()
        self._mono_columns: set[int] = set()
        self._filter_predicates: dict[str, Callable[[QTreeWidgetItem], bool]] = {}
        self._selection_key: Callable[[QTreeWidgetItem], object] = self._default_selection_key
        self._empty_widget = None
        self._no_result_widget = None
        self._forced_state_widget = None
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # filter row: title chip + inline search + result count (ribbon grammar).
        # Window controls live in the app bar (shell v3), so rows span the
        # full canvas width — no right reserve needed.
        search_layout = QHBoxLayout()
        self.search_layout = search_layout
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
        self.filter_slot = QHBoxLayout()
        self.filter_slot.setSpacing(8)
        search_layout.addLayout(self.filter_slot)
        self.count_label = QLabel('0')
        self.count_label.setObjectName('searchCount')
        search_layout.addWidget(self.count_label)
        layout.addLayout(search_layout)
        hairline = QFrame()
        hairline.setObjectName('bandZoneRule')
        hairline.setFixedHeight(1)
        layout.addWidget(hairline)
        # full-bleed dense table
        self.tree = _CopyableTree(self)
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
            for widget in _panel._state_widgets():
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

    def set_copyable_columns(self, columns: set[int]) -> None:
        """uiux-audit-remediation 4.3: mark identifier columns copyable —
        Ctrl+C copies the full GUID (GUID_ROLE) of the selected rows for
        these columns."""
        self._copyable_columns = set(columns)

    def add_filter_widget(self, widget: QWidget) -> None:
        """Place a shared filter control beside search without page-local layout."""
        self.filter_slot.addWidget(widget)

    def set_filter(
        self,
        name: str,
        predicate: Optional[Callable[[QTreeWidgetItem], bool]],
    ) -> None:
        """Install or clear a named row predicate and refresh the visible count."""
        if predicate is None:
            self._filter_predicates.pop(name, None)
        else:
            self._filter_predicates[name] = predicate
        self._apply_filters()

    def set_selection_key(self, key: Callable[[QTreeWidgetItem], object]) -> None:
        self._selection_key = key

    def set_mono_columns(self, columns: set[int]) -> None:
        """uiux-audit-remedination 4.3: render these columns' values in the
        mono token family (identifier cells); per-column via item fonts, so
        prose columns keep the proportional family."""
        self._mono_columns = set(columns)
        for item in self._all_items:
            self._apply_mono_fonts(item)

    def _apply_mono_fonts(self, item) -> None:
        from palworld_aio.ui.chrome import fonts as _chrome_fonts
        for col in getattr(self, '_mono_columns', ()):  # type: ignore[attr-defined]
            if col < item.columnCount():
                item.setFont(col, _chrome_fonts.mono_font(
                    px=constants.FONT_SIZE_PX_BODY))

    def set_empty_state_widget(self, widget) -> None:
        """modernize-tab-ui 5.3: rich EmptyState overlay replacing the plain
        hint for this panel's no-rows state (e.g. Guilds members pane).
        Pass None to detach and fall back to the plain hint."""
        self._set_state_widget('_empty_widget', widget)

    def set_no_result_state_widget(self, widget) -> None:
        """Use a distinct rich state when filters hide a populated collection."""
        self._set_state_widget('_no_result_widget', widget)

    def set_forced_state_widget(self, widget) -> None:
        """Temporarily replace table content with loading, prerequisite, or error."""
        self._set_state_widget('_forced_state_widget', widget)

    def _set_state_widget(self, attribute: str, widget) -> None:
        previous = getattr(self, attribute, None)
        setattr(self, attribute, widget)
        if widget is not None:
            widget.setParent(self.tree.viewport())
            widget.setGeometry(self.tree.viewport().rect())
        if previous is not None and previous is not widget:
            previous.hide()
        self._refresh_empty_state()

    def _state_widgets(self):
        widgets = []
        for attribute in (
            '_empty_widget', '_no_result_widget', '_forced_state_widget',
        ):
            widget = getattr(self, attribute, None)
            if widget is not None and widget not in widgets:
                widgets.append(widget)
        return widgets

    def _show_empty_overlay(self, message: str, widget=None) -> None:
        if widget is not None:
            self._empty_label.hide()
            for candidate in self._state_widgets():
                candidate.setVisible(candidate is widget)
            widget.setGeometry(self.tree.viewport().rect())
            widget.raise_()
            widget.show()
        else:
            for candidate in self._state_widgets():
                candidate.hide()
            self._empty_label.setText(message)
            self._empty_label.setGeometry(self.tree.viewport().rect())
            self._empty_label.show()

    def _hide_empty_overlay(self) -> None:
        self._empty_label.hide()
        for widget in self._state_widgets():
            widget.hide()

    def _refresh_empty_state(self) -> None:
        forced = getattr(self, '_forced_state_widget', None)
        if forced is not None:
            self._show_empty_overlay('', forced)
            return
        visible = sum(0 if self.tree.topLevelItem(i).isHidden() else 1
                      for i in range(self.tree.topLevelItemCount()))
        if visible == 0:
            searched = self.search_input.text().strip()
            has_filter = bool(searched or self._filter_predicates)
            if has_filter and self.tree.topLevelItemCount() > 0:
                message = t('search.no_matches') if t else 'No matches'
                widget = getattr(self, '_no_result_widget', None)
            elif self.tree.topLevelItemCount() == 0:
                message = getattr(self, '_empty_message', '') or (t('status.no_save_data') if t else 'No data — load a save first.')
                widget = getattr(self, '_empty_widget', None)
            else:
                message = t('search.no_matches') if t else 'No matches'
                widget = getattr(self, '_no_result_widget', None)
            self._show_empty_overlay(message, widget)
        else:
            self._hide_empty_overlay()

    def clear_filters(self) -> None:
        """Clear shared text and predicate filters from a no-result action."""
        self._filter_predicates.clear()
        self.search_input.clear()
        self._apply_filters()
    def _update_count(self):
        total = self.tree.topLevelItemCount()
        visible = sum(0 if self.tree.topLevelItem(i).isHidden() else 1 for i in range(total))
        # uiux-audit-remediation 4.4: labeled result count, never a bare
        # numeral — filtered subsets show "X of Y results".
        if total != visible:
            text = (t('search.results_filtered', x=visible, y=total)
                    if t else f'{visible} of {total} results')
        elif total == 1:
            text = t('search.results_one') if t else '1 result'
        else:
            text = (t('search.results_many', n=total)
                    if t else f'{total} results')
        self.count_label.setText(text)
        if hasattr(self, '_empty_label'):
            self._refresh_empty_state()
    def _apply_filters(self) -> None:
        text = self.search_input.text().strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            search_match = not text
            for col in range(item.columnCount()):
                searchable = (
                    item.text(col),
                    item.toolTip(col),
                    str(item.data(col, GUID_ROLE) or ''),
                )
                if any(text in value.lower() for value in searchable):
                    search_match = True
                    break
            predicate_match = all(predicate(item) for predicate in self._filter_predicates.values())
            item.setHidden(not (search_match and predicate_match))
        self._update_count()

    def _on_search(self, text):
        # Preserve the long-standing direct-call contract used by page code and
        # tests while keeping one filtering path for textChanged emissions.
        if text != self.search_input.text():
            self.search_input.setText(text)
            return
        self._apply_filters()
        self.search_requested.emit(text)

    @staticmethod
    def _default_selection_key(item: QTreeWidgetItem) -> object:
        data = item.data(0, Qt.UserRole)
        return data if isinstance(data, (str, int, float, tuple)) else _display_value(item, 0)

    def capture_view_state(self) -> dict[str, object]:
        """Capture serializable browser state for route-history restoration."""
        selected = [self._selection_key(item) for item in self.tree.selectedItems()]
        return {
            'search': self.search_input.text(),
            'sort_column': self.tree.sortColumn(),
            'sort_order': self.tree.header().sortIndicatorOrder().value,
            'selected': selected,
            'scroll': self.tree.verticalScrollBar().value(),
        }

    def restore_view_state(self, state: dict[str, object]) -> None:
        self.search_input.setText(str(state.get('search', '')))
        column = int(state.get('sort_column', 0))
        try:
            order = Qt.SortOrder(int(state.get('sort_order', Qt.SortOrder.AscendingOrder.value)))
        except (TypeError, ValueError):
            order = Qt.SortOrder.AscendingOrder
        if 0 <= column < self.tree.columnCount():
            self.tree.sortItems(column, order)
        selected = set(state.get('selected', []))
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            item.setSelected(self._selection_key(item) in selected and not item.isHidden())
        self.tree.verticalScrollBar().setValue(max(0, int(state.get('scroll', 0))))
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
        self._apply_mono_fonts(item)
        self.tree.addTopLevelItem(item)
        self._all_items.append(item)
        self._apply_filters()
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
