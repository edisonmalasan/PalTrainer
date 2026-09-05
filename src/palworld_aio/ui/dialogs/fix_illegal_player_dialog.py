from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QAbstractItemView, QFrame
from PyQt6.QtCore import pyqtSignal, QSize
from i18n import t
from palworld_aio import constants
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from palworld_aio.ui.chrome.components import BaseDialog, make_button

class FixIllegalPlayerDialog(BaseDialog):
    """Illegal-player fix list on the shared dialog scaffold (Phase 4).

    Fix is the primary confirm (accepts, then emits); Close cancels.
    Selection/status styling is property-driven. Logic unchanged.
    """
    fix_requested = pyqtSignal(list)
    def __init__(self, scan_data, parent=None):
        title = t('fix_illegal_player.title') if t else 'Fix Illegal Players'
        super().__init__(title, parent, min_size=(700, 450))
        self.setWindowTitle(title)
        self.scan_data = scan_data
        self._setup_ui()
        self._populate_players()
    def _setup_ui(self):
        layout = self.content_layout
        self._header = QLabel(t('fix_illegal_player.description') if t else 'Select players with illegal stats to fix:')
        self._header.setProperty('role', 'secondary')
        self._header.setWordWrap(True)
        layout.addWidget(self._header)
        self.summary_label = QLabel('')
        self.summary_label.setProperty('role', 'warning')
        layout.addWidget(self.summary_label)
        btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton(t('player_item.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all)
        self.select_all_btn.setEnabled(False)
        btn_row.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('player_item.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.deselect_all_btn.setEnabled(False)
        btn_row.addWidget(self.deselect_all_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.player_list)
        sep = QFrame()
        sep.setProperty('class', 'divider')
        sep.setFrameShape(QFrame.Shape.NoFrame)
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        self.fix_btn = make_button(t('fix_illegal_player.fix_selected') if t else 'Fix Selected', 'primary')
        self.fix_btn.clicked.connect(self._on_fix)
        self.fix_btn.setEnabled(False)
        self.footer.addWidget(self.fix_btn)
        self.status_label = QLabel('')
        self.status_label.setProperty('role', 'success')
        self.footer.insertWidget(1, self.status_label, stretch=1)
        self.cancel_btn.setText(t('button.close') if t else 'Close')
    def refresh_labels(self):
        title = t('fix_illegal_player.title') if t else 'Fix Illegal Players'
        self.setWindowTitle(title)
        self.title_label.setText(title)
        self._header.setText(t('fix_illegal_player.description') if t else 'Select players with illegal stats to fix:')
        self.select_all_btn.setText(t('player_item.select_all') if t else 'Select All')
        self.deselect_all_btn.setText(t('player_item.deselect_all') if t else 'Deselect All')
        self.fix_btn.setText(t('fix_illegal_player.fix_selected') if t else 'Fix Selected')
        self.cancel_btn.setText(t('button.close') if t else 'Close')
        self._update_summary()
    def _update_summary(self):
        total_players = sum(1 for d in self.scan_data.values() if d['stat_count'] > 0)
        total_stats = sum(d['stat_count'] for d in self.scan_data.values() if d['stat_count'] > 0)
        self.summary_label.setText(t('fix_illegal_player.summary').format(players=total_players, stats=total_stats) if t else f'Found {total_players} player(s) with {total_stats} illegal stat(s)')
    def _populate_players(self):
        self.player_list.clear()
        self._player_widgets = {}
        total_players = 0
        total_stats = 0
        for uid_clean, data in sorted(self.scan_data.items(), key=lambda x: x[1].get('player_name', '')):
            if data['stat_count'] <= 0:
                continue
            total_players += 1
            total_stats += data['stat_count']
            stat_details = ', '.join([f'{k}={v}' for k, v in data['illegal_stats'].items()])
            display = f"{data['player_name']} (Lv.{data['level']}) - {data['guild_name']}"
            display += f'  [{stat_details}]'
            checkbox = ToggleCheckBtn(display)
            checkbox.setProperty('uid', uid_clean)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._on_check_toggled)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            self.player_list.addItem(item)
            self.player_list.setItemWidget(item, checkbox)
            self._player_widgets[uid_clean] = checkbox
        self._update_summary()
        if total_players > 0:
            self.select_all_btn.setEnabled(True)
            self.deselect_all_btn.setEnabled(True)
            self.fix_btn.setEnabled(True)
    def _on_check_toggled(self, checked=False):
        any_checked = any((w.isChecked() for w in self._player_widgets.values()))
        self.fix_btn.setEnabled(any_checked)
    def _select_all(self):
        for w in self._player_widgets.values():
            w.setChecked(True)
        self.fix_btn.setEnabled(True)
    def _deselect_all(self):
        for w in self._player_widgets.values():
            w.setChecked(False)
        self.fix_btn.setEnabled(False)
    def _get_selected_uids(self):
        uids = []
        for uid, w in self._player_widgets.items():
            if w.isChecked():
                uids.append(uid)
        return uids
    def _on_fix(self):
        uids = self._get_selected_uids()
        if not uids:
            self.status_label.setText(t('fix_illegal_player.no_selection') if t else 'No players selected.')
            self.status_label.setProperty('role', 'danger')
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            return
        self.accept()
        self.fix_requested.emit(uids)
