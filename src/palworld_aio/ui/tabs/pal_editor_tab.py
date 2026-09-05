from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from i18n import t
from palworld_aio.editor.edit_pals import PalEditorWidget
from palworld_aio.inventory.inventory_manager import get_player_inventory
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import CONTENT_PANEL_STYLE
from import_libs import run_with_loading
from loading_manager import is_loading_active
from palworld_aio.widgets.player_select_popup import show_player_select_popup
class PalEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_player_uid = None
        self.current_player_name = None
        self._player_list = []
        self._syncing = False
        self._setup_ui()
    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import (
            create_page_ribbon, set_content_margins,
        )
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # top-nav-shell 4.4: picker lives in a standard toolbar row below the
        # page header (ribbon keeps title/zone + a spacer for compatibility).
        ribbon = create_page_ribbon(t('pal_editor.title'), (t('sidebar.section.editing') if t else 'Editing').upper(), self)
        main_layout.addWidget(ribbon)
        toolbar_row = QHBoxLayout()
        set_content_margins(toolbar_row, top=6, bottom=6)
        toolbar_row.setSpacing(6)
        self.player_select_btn = QPushButton(t('inventory.select_player', default='Select Player...'))
        self.player_select_btn.setObjectName('ghostBtn')
        self.player_select_btn.setMinimumWidth(200)
        self.player_select_btn.setCursor(Qt.PointingHandCursor)
        self.player_select_btn.clicked.connect(self._open_player_popup)
        toolbar_row.addWidget(self.player_select_btn)
        toolbar_row.addStretch(1)
        main_layout.addLayout(toolbar_row)
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area)
    def _create_content_area(self):
        frame = QFrame()
        frame.setObjectName('palEditorContent')
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet(f'QFrame#palEditorContent {{ {CONTENT_PANEL_STYLE} }}')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        from palworld_aio.widgets.empty_state import EmptyState
        self.placeholder_label = EmptyState(
            t('pal_editor.select_player_hint', default='Select a player to edit their pals'),
            icon_name='pal_editor',
            action_text=t('inventory.select_player', default='Select Player...'),
        )
        self.placeholder_label.action_clicked.connect(self._open_player_popup)
        layout.addWidget(self.placeholder_label, 1)
        self.pal_editor_widget = PalEditorWidget()
        self.pal_editor_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pal_editor_widget.hide()
        layout.addWidget(self.pal_editor_widget)
        return frame
    def select_player(self, uid, name, display):
        from ui_debug import log
        log('paltab.select_player.enter', uid=uid, syncing=self._syncing)
        if self._syncing:
            return
        self.current_player_uid = uid
        self.current_player_name = name
        self.player_select_btn.setText(display)
        gen = self._selection_generation = getattr(self, '_selection_generation', 0) + 1

        def task():
            log('paltab.select_player.task_begin', uid=uid, gen=gen)
            self.pal_editor_widget.set_player(uid, name)
            log('paltab.select_player.task_done', uid=uid, gen=gen)

        def on_finished(_):
            if self._selection_generation != gen:
                log('paltab.select_player.stale_skipped', uid=uid, gen=gen, current=self._selection_generation)
                return
            log('paltab.select_player.ui_apply', uid=uid, gen=gen)
            self.placeholder_label.hide()
            self.pal_editor_widget.show()
            self.pal_editor_widget.apply_player_ui()
        run_with_loading(on_finished, task)
    def make_current(self):
        self.placeholder_label.hide()
        self.pal_editor_widget.show()
        self.pal_editor_widget.apply_player_ui()
    def _select_player_ref_only(self, uid, name, display):
        if self._syncing:
            return
        self.current_player_uid = uid
        self.current_player_name = name
        self.player_select_btn.setText(display)
        self.placeholder_label.hide()
        self.pal_editor_widget.show()
    def clear_player(self):
        if self._syncing:
            return
        # A selection worker may still be parsing a player save.  Its result
        # must not be allowed to repaint this tab after the user clears it.
        self._selection_generation = getattr(self, '_selection_generation', 0) + 1
        self.current_player_name = None
        self.current_player_uid = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        self._clear_editor()
    def _open_player_popup(self):
        from ui_debug import log
        log('paltab.popup.open', list_n=len(getattr(self, '_player_list', []) or []))
        if not self._player_list:
            self._load_players()
        chosen = show_player_select_popup(self.player_select_btn, self._player_list, self.current_player_uid)
        log('paltab.popup.chosen', uid=(chosen or {}).get('uid') if isinstance(chosen, dict) else chosen)
        if chosen == '__clear__':
            self._selection_generation = getattr(self, '_selection_generation', 0) + 1
            self._clear_editor()
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
            if hasattr(self.parent_window, 'inventory_tab'):
                self._syncing = True
                self.parent_window.inventory_tab.clear_player()
                self._syncing = False
            self.current_player_uid = None
            self.current_player_name = None
        elif chosen:
            uid = chosen['uid']
            name = chosen['name']
            display = chosen['display']
            self.current_player_uid = uid
            self.current_player_name = name
            self.player_select_btn.setText(display)
            if hasattr(self.parent_window, 'inventory_tab'):
                self._syncing = True
                self.parent_window.inventory_tab._select_player_ref_only(uid, name, display)
                self._syncing = False
            if is_loading_active():
                def task():
                    self.pal_editor_widget.set_player(uid, name)
                    if hasattr(self.parent_window, 'inventory_tab'):
                        return get_player_inventory(uid)
                    return None
                def on_loaded(inv):
                    if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                        return
                    self.placeholder_label.hide()
                    self.pal_editor_widget.show()
                    self.pal_editor_widget.apply_player_ui()
                    if hasattr(self.parent_window, 'inventory_tab') and inv is not None:
                        self._syncing = True
                        self.parent_window.inventory_tab.select_player(uid, name, display)
                        self._syncing = False
                run_with_loading(on_loaded, task)
                return
            def task():
                self.pal_editor_widget.set_player(uid, name)
                if hasattr(self.parent_window, 'inventory_tab'):
                    return get_player_inventory(uid)
                return None
            def on_loaded(inv):
                if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                    return
                self.make_current()
                if hasattr(self.parent_window, 'inventory_tab') and inv is not None:
                    self._syncing = True
                    self.parent_window.inventory_tab.make_current(inv)
                    self._syncing = False
            run_with_loading(on_loaded, task)
    def _clear_editor(self):
        self.pal_editor_widget.hide()
        self.pal_editor_widget.clear()
        self.placeholder_label.show()
    def refresh(self):
        prev_uid = self.current_player_uid
        prev_name = self.current_player_name
        self._load_players()
        if prev_uid:
            for p in self._player_list:
                if p['uid'] == prev_uid:
                    # Reload data through the worker path: set_player may
                    # decompress the player save and must never run on the
                    # GUI thread (refresh() is called from refresh_all after
                    # every load_finished).
                    self.select_player(prev_uid, prev_name or p['name'], p['display'])
                    break
    def _load_players(self):
        self._selection_generation = getattr(self, '_selection_generation', 0) + 1
        self._player_list = []
        self._clear_editor()
        if constants.loaded_level_json:
            from palworld_aio.managers.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level, *_ in players:
                display_name = f'{name} (Lv.{level})'
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
    def load_gps_data(self):
        if not constants.gps_gvas:
            return
        self.pal_editor_widget._load_gps_pals()
        self.pal_editor_widget._update_mode_buttons()
        self.pal_editor_widget._set_palbox_mode('gps')
        self.pal_editor_widget.apply_player_ui()

    def refresh_labels(self):
        if hasattr(self, 'player_select_btn') and (not self.current_player_uid):
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        if hasattr(self, 'pal_editor_widget'):
            self.pal_editor_widget.refresh_labels()
