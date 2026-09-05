from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal
from i18n import t
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from palworld_aio.ui.chrome.components import BaseDialog, make_button
from palworld_aio.ui.chrome import tokens as ui_tokens
from palworld_aio.editor.pal_editor.icons import _get_pal_icon_path, _get_cached_pixmap

_CARD_TOKENS = ui_tokens.resolve()


def _polish(widget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()

class PalRowWidget(QFrame):
    def __init__(self, pal_data, parent=None):
        super().__init__(parent)
        self.setProperty('palRow', True)
        self.pal_data = pal_data
        self._setup_ui()
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(6, 3, 6, 3)
        main.setSpacing(2)
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        icon_path = _get_pal_icon_path(self.pal_data.get('cid', ''))
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        if icon_path:
            pix = _get_cached_pixmap(icon_path, 22)
            if pix and not pix.isNull():
                icon_lbl.setPixmap(pix)
        top_row.addWidget(icon_lbl)
        nick = self.pal_data.get('nickname', '')
        name_text = nick if nick else self.pal_data.get('name', 'Unknown')
        lvl = self.pal_data.get('level', 1)
        rank = self.pal_data.get('rank', 1)
        stars = rank - 1 if rank > 1 else 0
        info_parts = [f'Lv.{lvl}']
        if stars:
            info_parts.append(f'{stars}â˜…')
        info_text = ' '.join(info_parts)
        ivs = f"IVs {self.pal_data.get('talent_hp', 0)}/{self.pal_data.get('talent_shot', 0)}/{self.pal_data.get('talent_defense', 0)}"
        souls = f"Souls {self.pal_data.get('rank_hp', 0)}/{self.pal_data.get('rank_attack', 0)}/{self.pal_data.get('rank_defense', 0)}/{self.pal_data.get('rank_craftspeed', 0)}"
        detail = f'{info_text} | {ivs} | {souls} | {self.pal_data.get("location", "")}'
        line_label = QLabel(f'{name_text} â€” {detail}')
        line_label.setStyleSheet(f'color: {_CARD_TOKENS["text"]}; font-size: 11px;')
        top_row.addWidget(line_label, 1)
        main.addLayout(top_row)
        markers = self.pal_data.get('illegal_markers', [])
        if markers:
            marker_text = '  '.join(f'[{m}]' for m in markers)
            marker_lbl = QLabel(marker_text)
            marker_lbl.setStyleSheet(
                f'color: {_CARD_TOKENS["warning"]}; font-size: 10px; font-weight: 700; '
                f'padding: 1px 8px; background: {_CARD_TOKENS["warning_bg"]}; '
                f'border: 1px solid {_CARD_TOKENS["warning_border"]}; border-radius: 4px;')
            marker_lbl.setWordWrap(True)
            main.addWidget(marker_lbl)
class PlayerCardWidget(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, uid, data, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.data = data
        self._selected = False
        self._setup_ui()
    def _setup_ui(self):
        self.setFixedHeight(48)
        self.setProperty('playerCard', True)
        self.setProperty('selected', False)
        self.setCursor(Qt.PointingHandCursor)
        card = QHBoxLayout(self)
        card.setContentsMargins(8, 4, 8, 4)
        card.setSpacing(6)
        self.checkbox = ToggleCheckBtn('')
        self.checkbox.setChecked(True)
        card.addWidget(self.checkbox)
        text_w = QWidget()
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(1)
        name = self.data.get('player_name', 'Unknown')
        guild = self.data.get('guild_name', 'Unknown')
        level = self.data.get('level', 1)
        count = self.data['pal_count']
        name_lbl = QLabel(f'{name} (Lv.{level})')
        name_lbl.setStyleSheet(f'color: {_CARD_TOKENS["text"]}; font-size: 12px; font-weight: 600;')
        text_l.addWidget(name_lbl)
        extra_lbl = QLabel(f'{guild}  [{count} illegal]')
        extra_lbl.setStyleSheet(f'color: {_CARD_TOKENS["text_secondary"]}; font-size: 10px;')
        text_l.addWidget(extra_lbl)
        card.addWidget(text_w, 1)
    def _update_style(self):
        self.setProperty('selected', self._selected)
        _polish(self)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.uid)
        super().mousePressEvent(event)
    def set_selected(self, selected):
        self._selected = selected
        self._update_style()
    def is_checked(self):
        return self.checkbox.isChecked()
    def set_checked(self, checked):
        self.checkbox.setChecked(checked)

class FixIllegalPalDialog(BaseDialog):
    """Illegal-pal fix workspace on the shared dialog scaffold (Phase 4).

    Card/row selection is property-driven (`playerCard`/`palRow` rules in
    qss_builder). All scan/selection/fix logic unchanged.
    """
    def __init__(self, scan_data, parent=None):
        title = t('fix_illegal_pal.title') if t else 'Fix Illegal Pals'
        super().__init__(title, parent, min_size=(1000, 550))
        self.setWindowTitle(title)
        self.scan_data = scan_data
        self._player_cards = {}
        self._player_pal_rows = {}
        self._selected_uid = None
        self._setup_ui()
        self._populate_players()
        self._populate_all_pal_rows()
        self._select_first_player()
    def _setup_ui(self):
        layout = self.content_layout
        self._header = QLabel(t('fix_illegal_pal.description') if t else 'Players to fix:')
        self._header.setProperty('role', 'secondary')
        self._header.setWordWrap(True)
        layout.addWidget(self._header)
        self.summary_label = QLabel('')
        self.summary_label.setProperty('role', 'warning')
        layout.addWidget(self.summary_label)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        left_panel = QFrame()
        left_panel.setProperty('class', 'panel')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(4)
        left_header = QLabel(t('fix_illegal_pal.players_header') if t else 'Players')
        left_header.setObjectName('sectionHeader')
        left_layout.addWidget(left_header)
        left_btn_row = QHBoxLayout()
        left_sel_all = QPushButton(t('player_item.select_all') if t else 'All')
        left_sel_all.setFixedHeight(22)
        left_sel_all.setStyleSheet(
            f'QPushButton {{ background: {_CARD_TOKENS["success_bg"]}; color: {_CARD_TOKENS["success"]}; '
            f'border: 1px solid {_CARD_TOKENS["success_border"]}; border-radius: 4px; '
            'padding: 2px 8px; font-weight: 600; font-size: 11px; }} '
            f'QPushButton:hover {{ background: {_CARD_TOKENS["success_border"]}; }}')
        left_sel_all.clicked.connect(lambda: self._set_all_players(True))
        left_btn_row.addWidget(left_sel_all)
        left_sel_none = QPushButton(t('player_item.deselect_all') if t else 'None')
        left_sel_none.setFixedHeight(22)
        left_sel_none.setStyleSheet(
            f'QPushButton {{ background: {_CARD_TOKENS["danger_bg"]}; color: {_CARD_TOKENS["danger"]}; '
            f'border: 1px solid {_CARD_TOKENS["danger_border"]}; border-radius: 4px; '
            'padding: 2px 8px; font-weight: 600; font-size: 11px; }} '
            f'QPushButton:hover {{ background: {_CARD_TOKENS["danger_border"]}; }}')
        left_sel_none.clicked.connect(lambda: self._set_all_players(False))
        left_btn_row.addWidget(left_sel_none)
        left_btn_row.addStretch()
        left_layout.addLayout(left_btn_row)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.left_content = QWidget()
        self.left_layout_inner = QVBoxLayout(self.left_content)
        self.left_layout_inner.setContentsMargins(0, 0, 0, 0)
        self.left_layout_inner.setSpacing(2)
        left_scroll.setWidget(self.left_content)
        left_layout.addWidget(left_scroll, 1)
        right_panel = QFrame()
        right_panel.setProperty('class', 'panel')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(4)
        self.right_header = QLabel(t('fix_illegal_pal.pals_header') if t else 'Illegal Pals')
        self.right_header.setObjectName('sectionHeader')
        right_layout.addWidget(self.right_header)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.right_content = QWidget()
        self.right_layout_inner = QVBoxLayout(self.right_content)
        self.right_layout_inner.setContentsMargins(0, 0, 0, 0)
        self.right_layout_inner.setSpacing(2)
        right_scroll.setWidget(self.right_content)
        right_layout.addWidget(right_scroll, 1)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])
        layout.addWidget(splitter, 1)
        sep = QFrame()
        sep.setProperty('class', 'divider')
        sep.setFrameShape(QFrame.Shape.NoFrame)
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        self.fix_btn = make_button(t('fix_illegal_pal.fix_selected') if t else 'Fix Selected', 'primary')
        self.fix_btn.clicked.connect(self._on_fix)
        self.footer.addWidget(self.fix_btn)
        self.status_label = QLabel('')
        self.status_label.setProperty('role', 'success')
        self.footer.insertWidget(1, self.status_label, stretch=1)
        self.cancel_btn.setText(t('button.close') if t else 'Close')
    def _update_summary(self):
        total_players = sum(1 for d in self.scan_data.values() if d['pal_count'] > 0)
        total_illegals = sum(d['pal_count'] for d in self.scan_data.values() if d['pal_count'] > 0)
        self.summary_label.setText(t('fix_illegal_pal.summary').format(players=total_players, pals=total_illegals) if t else f'Found {total_players} player(s) with {total_illegals} illegal pal(s)')
    def _select_first_player(self):
        for uid in sorted(self._player_cards.keys()):
            self._select_player(uid)
            return
    def _populate_players(self):
        self._player_cards = {}
        for uid_clean, data in sorted(self.scan_data.items(), key=lambda x: x[1].get('player_name', '')):
            if data['pal_count'] <= 0:
                continue
            card = PlayerCardWidget(uid_clean, data)
            card.clicked.connect(self._select_player)
            self.left_layout_inner.addWidget(card)
            self._player_cards[uid_clean] = card
        self.left_layout_inner.addStretch(1)
        self._update_summary()
        if self._player_cards:
            self.fix_btn.setEnabled(True)
    def _populate_all_pal_rows(self):
        for uid_clean, data in self.scan_data.items():
            u_rows = []
            for pal in data.get('illegals', []):
                row = PalRowWidget(pal)
                row.setVisible(False)
                self.right_layout_inner.addWidget(row)
                u_rows.append(row)
            self._player_pal_rows[uid_clean] = u_rows
        self.right_layout_inner.addStretch(1)
    def _select_player(self, uid):
        if self._selected_uid == uid:
            return
        if self._selected_uid and self._selected_uid in self._player_cards:
            self._player_cards[self._selected_uid].set_selected(False)
        for old_uid, rows in self._player_pal_rows.items():
            for r in rows:
                r.setVisible(False)
        self._selected_uid = uid
        if uid in self._player_cards:
            self._player_cards[uid].set_selected(True)
        data = self.scan_data.get(uid, {})
        pname = data.get('player_name', uid)
        self.right_header.setText(t('fix_illegal_pal.pals_for_header', name=pname) if t else f'Illegal Pals â€” {pname}')
        for r in self._player_pal_rows.get(uid, []):
            r.setVisible(True)
    def _set_all_players(self, checked):
        for card in self._player_cards.values():
            card.set_checked(checked)
    def _get_selected_uids(self):
        return [uid for uid, card in self._player_cards.items() if card.is_checked()]
    def _on_fix(self):
        uids = self._get_selected_uids()
        if not uids:
            self.status_label.setText(t('fix_illegal_pal.no_selection') if t else 'No players checked for fixing.')
            self.status_label.setProperty('role', 'danger')
            _polish(self.status_label)
            return
        self.accept()
