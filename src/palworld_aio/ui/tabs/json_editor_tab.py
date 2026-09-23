import os
import json
import copy
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QLineEdit, QFileDialog,
    QHeaderView, QAbstractItemView, QFrame, QStyledItemDelegate,
    QStackedWidget, QPlainTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QFontDatabase, QColor, QCursor, QBrush
from i18n import t
from palworld_aio import constants
from palsav import json_tools
from palworld_aio.ui.chrome.components import MessageDialog as QMessageBox

_JSON_KEY = 'json_editor'


def _type_label(val):
    if isinstance(val, dict):
        return f'dict ({len(val)})'
    if isinstance(val, list):
        return f'list ({len(val)})'
    if isinstance(val, tuple):
        return f'tuple ({len(val)})'
    if isinstance(val, bytes):
        return f'bytes ({len(val)})'
    if isinstance(val, bytearray):
        return f'bytes ({len(val)})'
    return type(val).__name__


def _format_value(val, max_len=200):
    if val is None:
        return 'null'
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (bytes, bytearray)):
        s = val.hex()
        return s if len(s) <= max_len else s[:max_len] + '...'
    if isinstance(val, dict):
        return '{...}'
    if isinstance(val, (list, tuple)):
        return f'[{len(val)} items]'
    s = str(val)
    return s if len(s) <= max_len else s[:max_len] + '...'


class _ClickableCrumb(QLabel):
    """Clickable breadcrumb chip (uiux-audit-remediation 11.1 / D12).
    QLabel has no clicked signal, so clicks are surfaced here."""
    clicked = pyqtSignal()
    _json_path_item: QTreeWidgetItem | None

    def __init__(self, text=''):
        super().__init__(text)
        self._json_path_item = None
        self._armed = False

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._armed = True
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._armed and ev.button() == Qt.MouseButton.LeftButton:
            self._armed = False
            if self.rect().contains(ev.position().toPoint()):
                self.clicked.emit()
        super().mouseReleaseEvent(ev)


class LazyJsonItem(QTreeWidgetItem):
    def __init__(self, parent, key, value):
        super().__init__()
        self._key = key
        self._value = value
        self._children_loaded = False
        self._is_container = isinstance(value, (dict, list))
        if (isinstance(parent, LazyJsonItem)
                and isinstance(parent.raw_value, list)):
            self.setText(0, f'[{key}]')
        else:
            self.setText(0, str(key) if key is not None else '')
        self.setText(2, _type_label(value))
        if self._is_container:
            self.setText(1, _format_value(value))
            self._add_placeholder()
        else:
            self.setText(1, _format_value(value))
            if isinstance(value, (str, int, float, bool)):
                self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)

    def _add_placeholder(self):
        p = QTreeWidgetItem()
        p.setText(0, '...')
        self.addChild(p)

    def load_children(self):
        if self._children_loaded or not self._is_container:
            return
        self._children_loaded = True
        while self.childCount():
            self.removeChild(self.child(0))
        if isinstance(self._value, dict):
            for k, v in self._value.items():
                self.addChild(LazyJsonItem(self, k, v))
        elif isinstance(self._value, list):
            for i, v in enumerate(self._value):
                self.addChild(LazyJsonItem(self, i, v))

    @property
    def raw_value(self):
        return self._value


class _JsonValueDelegate(QStyledItemDelegate):
    """Allow edits only in the Value column of supported scalar rows."""

    def createEditor(self, parent, option, index):
        tree = self.parent()
        item = tree.itemFromIndex(index) if isinstance(
            tree, QTreeWidget) else None
        if (index.column() != 1 or not isinstance(item, LazyJsonItem)
                or isinstance(item.raw_value, (dict, list, tuple, bytes,
                                               bytearray, type(None)))):
            return None
        return super().createEditor(parent, option, index)


class JsonEditorTab(QWidget):
    save_applied = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._loaded_once = False
        self._search_matches = []   # list of matching QTreeWidgetItem
        self._search_idx = -1       # current match index
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._do_search)
        self._updating_item = False
        self._setup_ui()

    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import (
            SegmentedControl, create_page_footer, make_button, make_tool_button,
            set_content_margins,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        view_row = QHBoxLayout()
        set_content_margins(view_row, top=8, bottom=4)
        view_row.addStretch(1)
        self._view_control = SegmentedControl(
            (
                ('tree', t(f'{_JSON_KEY}.view_tree', default='Tree')),
                ('raw', t(f'{_JSON_KEY}.view_raw', default='Raw JSON')),
            ),
            current='tree',
            accessible_name=t(
                f'{_JSON_KEY}.view_mode', default='JSON editor view'),
            parent=self,
        )
        self._view_control.currentChanged.connect(self._on_view_changed)
        view_row.addWidget(self._view_control)
        layout.addLayout(view_row)

        search_bar = QHBoxLayout()
        set_content_margins(search_bar, top=8, bottom=8)
        search_bar.setSpacing(6)
        self._search_input = QLineEdit()
        self._search_input.setObjectName('searchInput')
        self._search_input.setPlaceholderText(t(f'{_JSON_KEY}.search_placeholder') if t else 'Search...')
        self._search_input.textChanged.connect(self._on_search_changed)
        search_bar.addWidget(self._search_input, 1)

        self._search_prev_btn = make_tool_button(
            'chevron_up',
            t(f'{_JSON_KEY}.search_prev') if t else 'Previous match')
        self._search_prev_btn.setFixedSize(28, 28)
        self._search_prev_btn.clicked.connect(self._search_prev)
        self._search_prev_btn.setEnabled(False)
        search_bar.addWidget(self._search_prev_btn)

        self._search_next_btn = make_tool_button(
            'chevron_down',
            t(f'{_JSON_KEY}.search_next') if t else 'Next match')
        self._search_next_btn.setFixedSize(28, 28)
        self._search_next_btn.clicked.connect(self._search_next)
        self._search_next_btn.setEnabled(False)
        search_bar.addWidget(self._search_next_btn)

        self._search_count_label = QLabel('')
        self._search_count_label.setObjectName('searchCount')
        search_bar.addWidget(self._search_count_label)
        self._search_host = QWidget(self)
        self._search_host.setLayout(search_bar)
        layout.addWidget(self._search_host)

        # uiux-audit-remediation 11.1 (D12): persistent clickable path
        # breadcrumb tracking the current/last-visited tree item; clicking a
        # crumb selects and scrolls to that ancestor.
        self._breadcrumb_row = QHBoxLayout()
        self._breadcrumb_row.setContentsMargins(12, 0, 12, 6)
        self._breadcrumb_row.setSpacing(2)
        self._crumb_elide_label = QLabel('')
        self._crumb_elide_label.setObjectName('jsonCrumbMuted')
        self._crumb_elide_label.hide()
        self._breadcrumb_row.addWidget(self._crumb_elide_label)
        self._breadcrumb_crumb_labels: list[_ClickableCrumb] = []
        self._breadcrumb_separator_labels: list[QLabel] = []
        self._breadcrumb_current: QTreeWidgetItem | None = None
        self._breadcrumb_placeholder = QLabel(
            t(f'{_JSON_KEY}.breadcrumb_root') if t else 'root')
        self._breadcrumb_placeholder.setObjectName('jsonCrumbMuted')
        self._breadcrumb_row.addWidget(self._breadcrumb_placeholder)
        self._breadcrumb_row.addStretch(1)
        self._breadcrumb_host = QWidget()
        self._breadcrumb_host.setObjectName('jsonBreadcrumb')
        self._breadcrumb_host.setLayout(self._breadcrumb_row)
        layout.addWidget(self._breadcrumb_host)

        self._tree = QTreeWidget()
        self._tree.setObjectName('jsonTree')
        self._tree.setHeaderLabels([
            t(f'{_JSON_KEY}.col_key') if t else 'Key',
            t(f'{_JSON_KEY}.col_value') if t else 'Value',
            t(f'{_JSON_KEY}.col_type') if t else 'Type',
        ])
        self._tree.header().setStretchLastSection(True)
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tree.header().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._tree.setAlternatingRowColors(True)
        self._tree.setAnimated(True)
        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono.setPointSize(10)
        self._tree.setFont(mono)
        self._tree.setItemDelegate(_JsonValueDelegate(self._tree))
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemSelectionChanged.connect(self._update_breadcrumb)
        self._tree.itemChanged.connect(self._on_item_changed)
        self._tree.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed)
        self._tree.setUniformRowHeights(True)
        self._tree.setWordWrap(False)
        # no-save empty state (top-nav-shell 4.3): overlay hint on the tree
        hint_text = t(f'{_JSON_KEY}.no_save') if t else 'No save loaded'
        self._empty_hint = QLabel(hint_text)
        self._empty_hint.setObjectName('tableEmptyHint')
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._view_stack = QStackedWidget(self)
        self._view_stack.setObjectName('jsonViewStack')
        self._view_stack.addWidget(self._tree)

        self._raw_page = QWidget(self)
        raw_layout = QVBoxLayout(self._raw_page)
        raw_layout.setContentsMargins(12, 8, 12, 8)
        raw_layout.setSpacing(8)
        raw_notice = QLabel(t(
            f'{_JSON_KEY}.raw_notice',
            default=('Raw mode replaces the full in-memory save only after '
                     'JSON and GVAS validation. Saving later creates the '
                     'on-disk backup.')))
        raw_notice.setObjectName('jsonRawNotice')
        raw_notice.setProperty('role', 'warning')
        raw_notice.setWordWrap(True)
        raw_layout.addWidget(raw_notice)
        self._raw_editor = QPlainTextEdit(self._raw_page)
        self._raw_editor.setObjectName('jsonRawEditor')
        self._raw_editor.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap)
        self._raw_editor.setAccessibleName(t(
            f'{_JSON_KEY}.raw_editor_name', default='Raw JSON document'))
        self._raw_editor.textChanged.connect(self._on_raw_text_changed)
        raw_layout.addWidget(self._raw_editor, 1)
        raw_actions = QHBoxLayout()
        self._raw_validation_label = QLabel('')
        self._raw_validation_label.setObjectName('jsonRawValidation')
        raw_actions.addWidget(self._raw_validation_label, 1)
        self._raw_apply_btn = make_button(
            t(f'{_JSON_KEY}.raw_apply', default='Validate & Apply'),
            'warning',
            tooltip=t(
                f'{_JSON_KEY}.raw_apply_help',
                default=('Validate the complete document before replacing '
                         'the in-memory save.')))
        self._raw_apply_btn.setEnabled(False)
        self._raw_apply_btn.clicked.connect(self._apply_raw_json)
        raw_actions.addWidget(self._raw_apply_btn)
        raw_layout.addLayout(raw_actions)
        self._view_stack.addWidget(self._raw_page)
        layout.addWidget(self._view_stack, 1)
        self._empty_hint.setParent(self._tree.viewport())
        self._empty_hint.setGeometry(self._tree.viewport().rect())
        self._tree.resizeEvent = self._tree_resized  # type: ignore[method-assign]

        # shared page footer (top-nav-shell 4.1): actions left, status right
        footer = create_page_footer()
        footer_lay = footer.actions
        self._refresh_btn = make_button(
            t(f'{_JSON_KEY}.refresh') if t else 'Refresh from Save',
            'tertiary',
            tooltip=t(f'{_JSON_KEY}.refresh_help',
                      default='Reload the tree from the in-memory save.'))
        self._refresh_btn.clicked.connect(self._load_from_save)
        footer_lay.addWidget(self._refresh_btn)
        self._export_btn = make_button(
            t(f'{_JSON_KEY}.export') if t else 'Export JSON',
            'secondary',
            tooltip=t(f'{_JSON_KEY}.export_help',
                      default='Write the current in-memory save as JSON.'))
        self._export_btn.clicked.connect(self._export_json)
        footer_lay.addWidget(self._export_btn)
        self._import_btn = make_button(
            t(f'{_JSON_KEY}.import') if t else 'Import JSON',
            'warning',
            tooltip=t(f'{_JSON_KEY}.import_help',
                      default='Validate JSON before replacing the in-memory save.'))
        self._import_btn.clicked.connect(self._import_json)
        footer_lay.addWidget(self._import_btn)
        self._status_label = footer.status_label
        self._status_label.setText(t(f'{_JSON_KEY}.no_save') if t else 'No save loaded')
        layout.addWidget(footer)
        self._raw_source_text = ''
        # theme application is global (ThemeManager); per-tab styles removed

    def _tree_resized(self, event):
        QTreeWidget.resizeEvent(self._tree, event)
        self._empty_hint.setGeometry(self._tree.viewport().rect())

    def _set_empty_hint(self, show: bool) -> None:
        self._empty_hint.setVisible(show)

    @staticmethod
    def _serialize_raw(data) -> str:
        return json.dumps(
            data,
            cls=json_tools.CustomEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )

    def _sync_raw_text(self) -> None:
        root = self._tree.topLevelItem(0)
        if not isinstance(root, LazyJsonItem):
            text = ''
        else:
            try:
                text = self._serialize_raw(root.raw_value)
            except (TypeError, ValueError, OverflowError) as exc:
                self._raw_validation_label.setProperty('role', 'danger')
                self._raw_validation_label.setText(t(
                    f'{_JSON_KEY}.raw_render_error',
                    default='Unable to render raw JSON: {error}',
                    error=str(exc)))
                text = ''
        self._raw_editor.blockSignals(True)
        self._raw_editor.setPlainText(text)
        self._raw_editor.blockSignals(False)
        self._raw_source_text = text
        self._raw_apply_btn.setEnabled(False)
        if text:
            self._raw_validation_label.setProperty('role', 'secondary')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_ready',
                default='Edit the document, then validate before applying.'))

    def _on_view_changed(self, view_id: str) -> None:
        raw = view_id == 'raw'
        self._view_stack.setCurrentWidget(
            self._raw_page if raw else self._tree)
        self._search_host.setVisible(not raw)
        self._breadcrumb_host.setVisible(not raw)
        if raw:
            self._sync_raw_text()

    def _on_raw_text_changed(self) -> None:
        dirty = self._raw_editor.toPlainText() != self._raw_source_text
        loaded = constants.loaded_level_json
        has_validation_boundary = (
            loaded is not None and hasattr(loaded, '_gvas_file'))
        self._raw_apply_btn.setEnabled(dirty and has_validation_boundary)
        if dirty and not has_validation_boundary:
            self._raw_validation_label.setProperty('role', 'warning')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_requires_save',
                default='Load a save before raw changes can be applied.'))
        elif dirty:
            self._raw_validation_label.setProperty('role', 'warning')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_pending',
                default='Raw changes have not been validated or applied.'))

    def _confirm_raw_apply(self) -> bool:
        from palworld_aio.ui.chrome.components import confirm
        return confirm(
            self,
            t(f'{_JSON_KEY}.raw_confirm_title',
              default='Replace in-memory save?'),
            t(
                f'{_JSON_KEY}.raw_confirm_message',
                default=('The complete in-memory save will be replaced by '
                         'this validated JSON. Disk data is unchanged until '
                         'you save, when the normal backup flow applies.')),
            kind='danger',
            confirm_text=t(
                f'{_JSON_KEY}.raw_confirm', default='Replace in-memory save'),
        )

    def _apply_raw_json(self) -> None:
        loaded = constants.loaded_level_json
        if loaded is None or not hasattr(loaded, '_gvas_file'):
            self._raw_validation_label.setProperty('role', 'danger')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_requires_save',
                default='Load a save before raw changes can be applied.'))
            self._raw_apply_btn.setEnabled(False)
            return
        try:
            parsed = json.loads(self._raw_editor.toPlainText())
            candidate = json_tools._decode_byte_tags(parsed)
            new_gvas = self._validate_candidate(candidate)
            if new_gvas is None:
                raise ValueError('GVAS validation is unavailable.')
        except Exception as exc:
            self._raw_validation_label.setProperty('role', 'danger')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_invalid',
                default='Raw JSON was not applied: {error}',
                error=str(exc)))
            return
        if not self._confirm_raw_apply():
            self._raw_validation_label.setProperty('role', 'warning')
            self._raw_validation_label.setText(t(
                f'{_JSON_KEY}.raw_cancelled',
                default='Apply cancelled; the in-memory save is unchanged.'))
            return
        loaded._gvas_file = new_gvas
        self._populate_tree(candidate)
        self._sync_raw_text()
        self._raw_validation_label.setProperty('role', 'success')
        self._raw_validation_label.setText(t(
            f'{_JSON_KEY}.raw_applied',
            default='Validated JSON applied to the in-memory save.'))
        self._status_label.setProperty('role', 'success')
        self._status_label.setText(t(
            f'{_JSON_KEY}.raw_applied',
            default='Validated JSON applied to the in-memory save.'))
        self.save_applied.emit()

    def _on_item_expanded(self, item):
        if isinstance(item, LazyJsonItem):
            item.load_children()

    # ---------------------------------------------------------- breadcrumb
    _BREADCRUMB_MAX_CRUMBS = 6

    def _update_breadcrumb(self):
        """uiux-audit-remediation 11.1 (D12): track the current (or
        last-visited) item path in the clickable breadcrumb. Clicking a crumb
        selects and scrolls to that ancestor."""
        selected = self._tree.selectedItems()
        if selected:
            self._breadcrumb_current = selected[0]
        item = self._breadcrumb_current
        # rebuild crumb labels (root first, last N segments visible)
        chain = []
        while item is not None:
            chain.append(item)
            item = item.parent()
        chain.reverse()
        crumbs = [(c.text(0) or 'root') for c in chain]
        for lbl in self._breadcrumb_crumb_labels + self._breadcrumb_separator_labels:
            lbl.hide()
        if not crumbs:
            self._crumb_elide_label.hide()
            self._breadcrumb_placeholder.show()
            return
        self._breadcrumb_placeholder.hide()
        max_crumbs = self._BREADCRUMB_MAX_CRUMBS
        visible = crumbs[-max_crumbs:]
        hidden_count = len(crumbs) - len(visible)
        col = 0
        if hidden_count > 0:
            self._crumb_elide_label.setText(f'… ({hidden_count})')
            self._crumb_elide_label.show()
            self._breadcrumb_row.insertWidget(col, self._crumb_elide_label)
            col += 1
        else:
            self._crumb_elide_label.hide()
        for idx, text in enumerate(visible):
            chain_item = chain[len(crumbs) - len(visible) + idx]
            if idx > 0 or hidden_count > 0:
                sep_idx = idx - 1 + (1 if hidden_count > 0 else 0)
                if sep_idx < len(self._breadcrumb_separator_labels):
                    sep_lbl = self._breadcrumb_separator_labels[sep_idx]
                else:
                    sep_lbl = QLabel('›')
                    sep_lbl.setObjectName('jsonCrumbMuted')
                    self._breadcrumb_separator_labels.append(sep_lbl)
                    self._breadcrumb_row.insertWidget(col, sep_lbl)
                sep_lbl.show()
                col += 1
            if idx < len(self._breadcrumb_crumb_labels):
                crumb_lbl = self._breadcrumb_crumb_labels[idx]
                crumb_lbl.setText(text)
                self._breadcrumb_row.insertWidget(col, crumb_lbl)
            else:
                crumb_lbl = _ClickableCrumb(text)
                crumb_lbl.setObjectName('jsonCrumb')
                crumb_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                crumb_lbl.clicked.connect(self._on_crumb_clicked)
                self._breadcrumb_crumb_labels.append(crumb_lbl)
                self._breadcrumb_row.insertWidget(col, crumb_lbl)
            crumb_lbl._json_path_item = chain_item
            crumb_lbl.setToolTip(text)
            crumb_lbl.show()
            col += 1
        for extra in self._breadcrumb_crumb_labels[len(visible):]:
            extra.hide()

    def _on_breadcrumb_clicked(self, item):
        if item is None:
            return
        # ensure lazy ancestors are loaded so the item exists in the tree
        parent = item.parent()
        while parent is not None:
            if isinstance(parent, LazyJsonItem):
                parent.load_children()
            parent = parent.parent()
        self._tree.scrollToItem(item)
        self._tree.setCurrentItem(item)

    def _on_crumb_clicked(self):
        crumb = self.sender()
        if crumb not in self._breadcrumb_crumb_labels:
            return
        self._on_breadcrumb_clicked(getattr(crumb, '_json_path_item', None))

    def _on_search_changed(self, text):
        self._search_timer.start()

    def _do_search(self):
        self._clear_search_highlights()
        self._search_matches.clear()
        self._search_idx = -1
        text = self._search_input.text().strip().lower()
        if not text:
            self._search_count_label.setText('')
            self._set_search_navigation_enabled(False)
            return
        root = self._tree.topLevelItem(0)
        if isinstance(root, LazyJsonItem):
            for path in self._matching_paths(root.raw_value, text):
                item = self._item_for_path(path)
                if item is not None:
                    self._search_matches.append(item)
                    self._highlight_item(item, True)
        count = len(self._search_matches)
        if count:
            self._search_idx = 0
            self._jump_to_match(0)
            self._set_search_navigation_enabled(True)
        else:
            self._search_count_label.setText(
                t(f'{_JSON_KEY}.search_no_matches') if t else 'No matches'
            )
            self._set_search_navigation_enabled(False)

    def _matching_paths(self, value, text, path=()):
        matches = []
        if isinstance(value, dict):
            entries = value.items()
        elif isinstance(value, list):
            entries = enumerate(value)
        else:
            return matches
        for key, child in entries:
            child_path = (*path, key)
            display_key = f'[{key}]' if isinstance(value, list) else str(key)
            value_text = '' if isinstance(child, (dict, list)) else str(child)
            if text in display_key.lower() or text in value_text.lower():
                matches.append(child_path)
            if isinstance(child, (dict, list)):
                matches.extend(self._matching_paths(child, text, child_path))
        return matches

    def _item_for_path(self, path):
        item = self._tree.topLevelItem(0)
        if not isinstance(item, LazyJsonItem):
            return None
        for key in path:
            item.load_children()
            match = next(
                (item.child(i) for i in range(item.childCount())
                 if getattr(item.child(i), '_key', object()) == key),
                None,
            )
            if not isinstance(match, LazyJsonItem):
                return None
            item.setExpanded(True)
            item = match
        return item

    def _set_search_navigation_enabled(self, enabled):
        self._search_prev_btn.setEnabled(enabled)
        self._search_next_btn.setEnabled(enabled)

    def _update_search_position(self):
        if not self._search_matches or self._search_idx < 0:
            return
        count = len(self._search_matches)
        key = ('search_position_one' if count == 1 else 'search_position')
        default = ('{current} of {count} match' if count == 1
                   else '{current} of {count} matches')
        self._search_count_label.setText(t(
            f'{_JSON_KEY}.{key}', default=default,
            current=self._search_idx + 1, count=count))

    def _highlight_item(self, item, on):
        # token amber tint (top-nav-shell 4.3): replaced the raw yellow QColor
        previous = self._updating_item
        self._updating_item = True
        try:
            if on:
                from palworld_aio.ui.chrome.tokens import resolve as _resolve
                tint = QColor(_resolve()['accent'])
                tint.setAlpha(50)
                item.setBackground(0, tint)
                item.setBackground(1, tint)
                item.setBackground(2, tint)
            else:
                item.setBackground(0, QBrush())
                item.setBackground(1, QBrush())
                item.setBackground(2, QBrush())
        finally:
            self._updating_item = previous

    def _clear_search_highlights(self):
        for item in self._search_matches:
            self._highlight_item(item, False)

    def _jump_to_match(self, idx):
        if not self._search_matches:
            return
        item = self._search_matches[idx]
        self._tree.scrollToItem(item)
        self._tree.setCurrentItem(item)
        self._update_search_position()

    def _search_next(self):
        if not self._search_matches:
            return
        self._search_idx = (self._search_idx + 1) % len(self._search_matches)
        self._jump_to_match(self._search_idx)

    def _search_prev(self):
        if not self._search_matches:
            return
        self._search_idx = (self._search_idx - 1) % len(self._search_matches)
        self._jump_to_match(self._search_idx)

    @staticmethod
    def _parse_scalar(text, original):
        if isinstance(original, bool):
            lowered = text.strip().lower()
            if lowered not in {'true', 'false'}:
                raise ValueError('Boolean values must be true or false.')
            return lowered == 'true'
        if isinstance(original, int):
            try:
                return int(text.strip())
            except ValueError as exc:
                raise ValueError('Enter a whole number.') from exc
        if isinstance(original, float):
            try:
                value = float(text.strip())
            except ValueError as exc:
                raise ValueError('Enter a number.') from exc
            if not math.isfinite(value):
                raise ValueError('The number must be finite.')
            return value
        if isinstance(original, str):
            return text
        raise ValueError('This JSON value is read-only.')

    @staticmethod
    def _replace_path_value(data, path, value):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    @staticmethod
    def _path_for_item(item):
        path = []
        while isinstance(item, LazyJsonItem) and item.parent() is not None:
            path.append(item._key)
            item = item.parent()
        path.reverse()
        return tuple(path)

    def _validate_candidate(self, data):
        self._serialize_raw(data)
        loaded = constants.loaded_level_json
        if loaded is None or not hasattr(loaded, '_gvas_file'):
            return None
        from palsav.gvas import GvasFile
        return GvasFile.load(data)

    def _on_item_changed(self, item, column):
        if self._updating_item or column != 1 or not isinstance(
                item, LazyJsonItem):
            return
        original = item.raw_value
        if isinstance(original, (dict, list, tuple, bytes, bytearray,
                                 type(None))):
            return
        path = self._path_for_item(item)
        root = self._tree.topLevelItem(0)
        if not path or not isinstance(root, LazyJsonItem):
            return
        try:
            value = self._parse_scalar(item.text(1), original)
            candidate = copy.deepcopy(root.raw_value)
            self._replace_path_value(candidate, path, value)
            new_gvas = self._validate_candidate(candidate)
        except Exception as exc:
            self._updating_item = True
            item.setText(1, _format_value(original))
            self._updating_item = False
            self._status_label.setProperty('role', 'danger')
            self._status_label.setText(t(
                f'{_JSON_KEY}.validation_error',
                default='Invalid value: {error}', error=str(exc)))
            return
        loaded = constants.loaded_level_json
        if new_gvas is not None and loaded is not None:
            loaded._gvas_file = new_gvas
        self._populate_tree(candidate)
        selected = self._item_for_path(path)
        if selected is not None:
            self._tree.setCurrentItem(selected)
        self._status_label.setProperty('role', 'success')
        self._status_label.setText(t(
            f'{_JSON_KEY}.value_applied',
            default='Validated and applied {path}.', path=' › '.join(
                str(part) for part in path)))
        if new_gvas is not None:
            self.save_applied.emit()

    def _get_gvas_dict(self):
        if constants.loaded_level_json is None:
            return None
        try:
            return constants.loaded_level_json._gvas_file.dump()
        except Exception:
            return None

    def _populate_tree(self, data):
        # drop the breadcrumb reference before clear() detaches the items
        self._clear_search_highlights()
        self._search_matches.clear()
        self._search_idx = -1
        self._set_search_navigation_enabled(False)
        self._search_count_label.setText('')
        self._breadcrumb_current = None
        self._updating_item = True
        try:
            self._tree.clear()
            root = LazyJsonItem(self._tree, None, data)
            root.load_children()
            self._tree.addTopLevelItem(root)
            root.setExpanded(True)
        finally:
            self._updating_item = False

    def _load_from_save(self):
        data = self._get_gvas_dict()
        if data is None:
            self._status_label.setText(t(f'{_JSON_KEY}.no_save') if t else 'No save loaded')
            self._set_empty_hint(True)
            return
        try:
            self._populate_tree(data)
            if self._view_control.current() == 'raw':
                self._sync_raw_text()
            self._set_empty_hint(False)
            self._status_label.setText(
                t(f'{_JSON_KEY}.loaded') if t else 'JSON loaded from save'
            )
        except Exception as e:
            self._status_label.setText(f'Error: {e}')

    def _export_json(self):
        if constants.loaded_level_json is None:
            return
        data = self._get_gvas_dict()
        if data is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            t(f'{_JSON_KEY}.export_save') if t else 'Export JSON',
            '',
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return
        try:
            json_tools.dump(data, path, minify=False)
            self._status_label.setText(
                t(f'{_JSON_KEY}.exported', path=os.path.basename(path)) if t else f'Exported to {os.path.basename(path)}'
            )
        except Exception as e:
            self._status_label.setText(f'Export failed: {e}')

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t(f'{_JSON_KEY}.import_save') if t else 'Import JSON',
            '',
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return
        try:
            data = json_tools.load(path)
            from palsav.gvas import GvasFile
            new_gvas = GvasFile.load(data)
        except Exception as e:
            self._status_label.setText(f'Import failed: {e}')
            QMessageBox.warning(
                self,
                'Import Error',
                f'Failed to import:\n{e}'
            )
            return
        if not self._confirm_import(path, data):
            return
        try:
            constants.loaded_level_json._gvas_file = new_gvas
            self._populate_tree(data)
            if self._view_control.current() == 'raw':
                self._sync_raw_text()
            self._loaded_once = True
            self._status_label.setText(
                t(f'{_JSON_KEY}.imported', path=os.path.basename(path)) if t else f'Imported {path}'
            )
            self.save_applied.emit()
        except Exception as e:
            self._status_label.setText(f'Import failed: {e}')
            QMessageBox.warning(
                self,
                'Import Error',
                f'Failed to import:\n{e}'
            )

    def _confirm_import(self, source_path, data) -> bool:
        """Destructive action guard: preview and explicit confirmation before
        the in-memory GVAS file is replaced."""
        import json
        if constants.loaded_level_json is None:
            QMessageBox.warning(
                self,
                'Import',
                'No save is loaded; there is nothing to replace.'
            )
            return False
        try:
            preview = json.dumps(data, ensure_ascii=False)[:2000]
        except Exception:
            preview = str(data)[:2000]
        current_path = constants.current_save_path or 'unknown'
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Confirm Import')
        msg.setText(
            'This replaces the entire in-memory save with the imported file.\n\n'
            f'Source:  {source_path}\n'
            f'Current save:  {current_path}\n\n'
            'Preview (first 2000 characters):\n'
            f'{preview}'
        )
        msg.setDetailedText(
            'The replacement affects the in-memory state only until you save.\n'
            'Saving afterwards writes the imported data to your save file.\n'
            'A backup is created by the save flow before writing.'
        )
        cancel_btn = msg.addButton('Cancel', QMessageBox.RejectRole)
        confirm_btn = msg.addButton('Replace in-memory save', QMessageBox.AcceptRole)
        confirm_btn.setStyleSheet('font-weight: 600;')
        msg.setDefaultButton(cancel_btn)
        msg.exec()
        return msg.clickedButton() is confirm_btn

    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded_once and constants.loaded_level_json is not None:
            self._loaded_once = True
            self._load_from_save()

    def refresh(self):
        if constants.loaded_level_json is not None:
            self._loaded_once = True
            self._load_from_save()

    def refresh_labels(self):
        self._refresh_btn.setText(t(f'{_JSON_KEY}.refresh') if t else 'Refresh from Save')
        self._export_btn.setText(t(f'{_JSON_KEY}.export') if t else 'Export JSON')
        self._import_btn.setText(t(f'{_JSON_KEY}.import') if t else 'Import JSON')
        self._search_input.setPlaceholderText(t(f'{_JSON_KEY}.search_placeholder') if t else 'Search...')
        self._search_prev_btn.setToolTip(t(f'{_JSON_KEY}.search_prev') if t else 'Previous match')
        self._search_next_btn.setToolTip(t(f'{_JSON_KEY}.search_next') if t else 'Next match')
        self._tree.headerItem().setText(0, t(f'{_JSON_KEY}.col_key') if t else 'Key')
        self._tree.headerItem().setText(1, t(f'{_JSON_KEY}.col_value') if t else 'Value')
        self._tree.headerItem().setText(2, t(f'{_JSON_KEY}.col_type') if t else 'Type')
        if constants.loaded_level_json is None:
            self._status_label.setText(t(f'{_JSON_KEY}.no_save') if t else 'No save loaded')
        elif self._tree.topLevelItemCount():
            self._status_label.setText(t(f'{_JSON_KEY}.loaded') if t else 'JSON loaded from save')
