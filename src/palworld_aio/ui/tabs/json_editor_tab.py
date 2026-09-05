import os
import json
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox,
    QHeaderView, QTreeWidgetItemIterator, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QFontDatabase, QColor, QCursor, QBrush
from palworld_aio.ui.chrome import icons as app_icons
from i18n import t
from palworld_aio import constants
from palsav import json_tools

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


class LazyJsonItem(QTreeWidgetItem):
    def __init__(self, parent, key, value):
        super().__init__()
        self._key = key
        self._value = value
        self._children_loaded = False
        self._is_container = isinstance(value, (dict, list))
        self.setText(0, str(key) if key is not None else '')
        self.setText(2, _type_label(value))
        if self._is_container:
            self.setText(1, _format_value(value))
            self._add_placeholder()
        else:
            self.setText(1, _format_value(value))

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
                self.addChild(LazyJsonItem(self, f'[{i}]', v))

    @property
    def raw_value(self):
        return self._value


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
        self._setup_ui()

    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import create_page_ribbon, set_content_margins
        from palworld_aio.ui.chrome.styles import ThemeManager
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(create_page_ribbon(t(f'{_JSON_KEY}.tab') if t else 'JSON Editor', (t('sidebar.section.editing') if t else 'Editing').upper(), self))

        search_bar = QHBoxLayout()
        set_content_margins(search_bar, top=8, bottom=8)
        search_bar.setSpacing(6)
        self._search_input = QLineEdit()
        self._search_input.setObjectName('searchInput')
        self._search_input.setPlaceholderText(t(f'{_JSON_KEY}.search_placeholder') if t else 'Search...')
        self._search_input.textChanged.connect(self._on_search_changed)
        search_bar.addWidget(self._search_input, 1)

        self._search_prev_btn = QPushButton()
        self._search_prev_btn.setIcon(
            app_icons.get_qicon('chevron_up', role='text_secondary'))
        self._search_prev_btn.setObjectName('toolButton')
        self._search_prev_btn.setFixedSize(28, 28)
        self._search_prev_btn.setToolTip(t(f'{_JSON_KEY}.search_prev') if t else 'Previous match')
        self._search_prev_btn.clicked.connect(self._search_prev)
        search_bar.addWidget(self._search_prev_btn)

        self._search_next_btn = QPushButton()
        self._search_next_btn.setIcon(
            app_icons.get_qicon('chevron_down', role='text_secondary'))
        self._search_next_btn.setObjectName('toolButton')
        self._search_next_btn.setFixedSize(28, 28)
        self._search_next_btn.setToolTip(t(f'{_JSON_KEY}.search_next') if t else 'Next match')
        self._search_next_btn.clicked.connect(self._search_next)
        search_bar.addWidget(self._search_next_btn)

        self._search_count_label = QLabel('')
        self._search_count_label.setObjectName('searchCount')
        search_bar.addWidget(self._search_count_label)
        layout.addLayout(search_bar)

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
        self._tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self._tree, 1)

        footer = QFrame()
        footer.setObjectName('tableFooter')
        footer_lay = QHBoxLayout(footer)
        set_content_margins(footer_lay, top=6, bottom=6)
        footer_lay.setSpacing(8)
        self._refresh_btn = QPushButton(t(f'{_JSON_KEY}.refresh') if t else 'Refresh from Save')
        self._refresh_btn.setObjectName('ghostBtn')
        self._refresh_btn.clicked.connect(self._load_from_save)
        footer_lay.addWidget(self._refresh_btn)
        self._export_btn = QPushButton(t(f'{_JSON_KEY}.export') if t else 'Export JSON')
        self._export_btn.setObjectName('ghostBtn')
        self._export_btn.clicked.connect(self._export_json)
        footer_lay.addWidget(self._export_btn)
        self._import_btn = QPushButton(t(f'{_JSON_KEY}.import') if t else 'Import JSON')
        self._import_btn.setObjectName('ghostBtn')
        self._import_btn.clicked.connect(self._import_json)
        footer_lay.addWidget(self._import_btn)
        footer_lay.addStretch()
        self._status_label = QLabel(t(f'{_JSON_KEY}.no_save') if t else 'No save loaded')
        self._status_label.setObjectName('bulkHintLabel')
        footer_lay.addWidget(self._status_label)
        layout.addWidget(footer)
        # theme application is global (ThemeManager); per-tab styles removed

    def _on_item_expanded(self, item):
        if isinstance(item, LazyJsonItem):
            item.load_children()

    def _on_search_changed(self, text):
        self._search_timer.start()

    def _do_search(self):
        self._clear_search_highlights()
        self._search_matches.clear()
        self._search_idx = -1
        text = self._search_input.text().strip().lower()
        if not text:
            self._search_count_label.setText('')
            return
        it = QTreeWidgetItemIterator(self._tree)
        while it.value():
            item = it.value()
            for col in range(2):
                if text in item.text(col).lower():
                    self._search_matches.append(item)
                    self._highlight_item(item, True)
                    break
            it += 1
        count = len(self._search_matches)
        if count:
            self._search_idx = 0
            self._jump_to_match(0)
            self._search_count_label.setText(
                t(f'{_JSON_KEY}.search_count', count=count) if t else f'{count} matches'
            )
        else:
            self._search_count_label.setText(
                t(f'{_JSON_KEY}.search_no_matches') if t else 'No matches'
            )

    def _highlight_item(self, item, on):
        if on:
            item.setBackground(0, QColor(255, 235, 59, 50))
            item.setBackground(1, QColor(255, 235, 59, 50))
            item.setBackground(2, QColor(255, 235, 59, 50))
        else:
            item.setBackground(0, QBrush())
            item.setBackground(1, QBrush())
            item.setBackground(2, QBrush())

    def _clear_search_highlights(self):
        for item in self._search_matches:
            self._highlight_item(item, False)

    def _jump_to_match(self, idx):
        if not self._search_matches:
            return
        item = self._search_matches[idx]
        self._tree.scrollToItem(item)
        self._tree.setCurrentItem(item)

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

    def _get_gvas_dict(self):
        if constants.loaded_level_json is None:
            return None
        try:
            return constants.loaded_level_json._gvas_file.dump()
        except Exception:
            return None

    def _populate_tree(self, data):
        self._tree.clear()
        root = LazyJsonItem(self._tree, None, data)
        root.load_children()
        self._tree.addTopLevelItem(root)
        root.setExpanded(True)

    def _load_from_save(self):
        data = self._get_gvas_dict()
        if data is None:
            self._status_label.setText(t(f'{_JSON_KEY}.no_save') if t else 'No save loaded')
            return
        try:
            self._populate_tree(data)
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
