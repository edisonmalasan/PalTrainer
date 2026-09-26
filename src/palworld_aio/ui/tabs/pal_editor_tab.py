from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QApplication
from PyQt6.QtCore import Qt
from i18n import t
from palworld_aio.editor.edit_pals import PalEditorWidget
from palworld_aio.inventory.inventory_manager import get_player_inventory
from palworld_aio import constants
from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_chip, set_picker_selected
from palworld_aio.ui.chrome.tokens import SPACING
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
        self._workspace_context = None
        self._context_unsubscribe = None
        self._applying_workspace_context = False
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(SPACING['sm'])
        self.context_bar = QFrame(self)
        self.context_bar.setObjectName('editorContextBar')
        toolbar_row = QHBoxLayout(self.context_bar)
        toolbar_row.setContentsMargins(
            SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        toolbar_row.setSpacing(SPACING['sm'])
        self.context_label = QLabel(
            t('ui.pal_editor.player_context', default='Player'), self.context_bar)
        self.context_label.setObjectName('editorContextLabel')
        toolbar_row.addWidget(self.context_label)
        self.player_select_btn = make_chip(
            t('inventory.select_player', default='Select Player...'),
            checkable=False,
            parent=self.context_bar,
        )
        self.player_select_btn.setObjectName('workspacePlayerSelector')
        self.player_select_btn.setProperty('contextKind', 'player')
        self.player_select_btn.setMinimumWidth(220)
        self.player_select_btn.setCursor(Qt.PointingHandCursor)
        self.player_select_btn.setIcon(
            app_icons.get_qicon('chevron_down', role='text_secondary'))
        self.player_select_btn.clicked.connect(self._open_player_popup)
        toolbar_row.addWidget(self.player_select_btn)
        self.context_summary = QLabel(t(
            'ui.pal_editor.context_hint',
            default='Party, Palbox, and inspector edits apply to this player.'),
            self.context_bar)
        self.context_summary.setObjectName('editorContextHint')
        self.context_summary.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        toolbar_row.addWidget(self.context_summary)
        toolbar_row.addStretch(1)
        main_layout.addWidget(self.context_bar)
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)
    def _create_content_area(self):
        frame = QFrame()
        frame.setObjectName('palEditorContent')
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            SPACING['sm'], 0, SPACING['sm'], SPACING['sm'])
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
        self._set_selector_copy(uid, name, display)
        self._publish_player_context(uid, name)
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
        self._set_selector_copy(uid, name, display)
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
        self._set_selector_copy(None, '', '')
        self._publish_player_context(None, '')
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
            self._set_selector_copy(None, '', '')
            if hasattr(self.parent_window, 'inventory_tab'):
                self._syncing = True
                self.parent_window.inventory_tab.clear_player()
                self._syncing = False
            self.current_player_uid = None
            self.current_player_name = None
            self._publish_player_context(None, '')
        elif chosen:
            uid = chosen['uid']
            name = chosen['name']
            display = chosen['display']
            self.current_player_uid = uid
            self.current_player_name = name
            self._set_selector_copy(uid, name, display)
            self._publish_player_context(uid, name)
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
        self._reconcile_player_context()

    def bind_workspace_context(self, context) -> None:
        if self._context_unsubscribe is not None:
            self._context_unsubscribe()
        self._workspace_context = context
        self._context_unsubscribe = context.subscribe(
            self._on_workspace_context_changed)
        self._on_workspace_context_changed(context.snapshot)

    def _reconcile_player_context(self) -> None:
        context = self._workspace_context
        valid = {str(player['uid']) for player in self._player_list}
        if context is not None:
            from palworld_aio.ui.routes import ContextKind
            from palworld_aio.ui.workspace_context import ContextSelection
            context.invalidate_missing({ContextKind.PLAYER: valid})
            context.apply_smart_defaults(players=(
                ContextSelection(str(player['uid']), str(player['name']))
                for player in self._player_list
            ))
            selected = context.snapshot.player
            if selected is not None:
                player = next((
                    item for item in self._player_list
                    if str(item['uid']) == selected.identifier), None)
                display = str(player['display']) if player else selected.detail
                self._set_selector_copy(
                    selected.identifier, selected.label, display)
                if (player is not None
                        and str(self.current_player_uid or '')
                        != selected.identifier):
                    self.select_player(
                        selected.identifier, selected.label, display)
                return
        elif len(self._player_list) == 1 and self.current_player_uid is None:
            only = self._player_list[0]
            self.select_player(only['uid'], only['name'], only['display'])
            return
        if self.current_player_uid is not None and str(self.current_player_uid) in valid:
            player = next(
                item for item in self._player_list
                if str(item['uid']) == str(self.current_player_uid))
            self._set_selector_copy(
                str(player['uid']), str(player['name']), str(player['display']))
            return
        self._set_selector_copy(None, '', '')

    def _set_selector_copy(self, uid, name: str, display: str = '') -> None:
        if uid is None:
            label = t('inventory.select_player', default='Select Player...')
            self.player_select_btn.setText(label)
            self.player_select_btn.setAccessibleName(label)
            tooltip = t(
                'ui.pal_editor.change_player', default='Choose or change player')
            self.player_select_btn.setToolTip(tooltip)
            self.player_select_btn.setAccessibleDescription(tooltip)
            set_picker_selected(self.player_select_btn, False)
            self.context_summary.setText(t(
                'ui.pal_editor.context_hint',
                default='Party, Palbox, and inspector edits apply to this player.'))
            return
        label = display or name or str(uid)
        self.player_select_btn.setText(label)
        self.player_select_btn.setAccessibleName(t(
            'ui.pal_editor.player_selected', default='Selected player: {name}',
            name=name or label))
        self.player_select_btn.setToolTip(str(uid))
        self.player_select_btn.setAccessibleDescription(t(
            'ui.pal_editor.player_uid', default='Player ID: {uid}', uid=str(uid)))
        set_picker_selected(self.player_select_btn, True)
        self.context_summary.setText(t(
            'ui.pal_editor.selected_hint',
            default='Editing party and Palbox for {name}.', name=name or label))

    def _publish_player_context(self, uid, name: str) -> None:
        if self._workspace_context is None or self._applying_workspace_context:
            return
        from palworld_aio.ui.workspace_context import ContextSelection
        selection = (
            ContextSelection(str(uid), str(name)) if uid is not None else None)
        self._workspace_context.set_player(selection)

    def _on_workspace_context_changed(self, snapshot) -> None:
        if self._applying_workspace_context:
            return
        selection = snapshot.player
        self._applying_workspace_context = True
        try:
            if selection is None:
                if self.current_player_uid is not None:
                    self.clear_player()
                else:
                    self._set_selector_copy(None, '', '')
                return
            player = next((
                item for item in self._player_list
                if str(item['uid']) == selection.identifier), None)
            display = str(player['display']) if player else selection.detail
            if str(self.current_player_uid or '') != selection.identifier and player:
                self.select_player(selection.identifier, selection.label, display)
            else:
                self._set_selector_copy(
                    selection.identifier, selection.label, display)
        finally:
            self._applying_workspace_context = False
    def load_gps_data(self):
        if not constants.gps_gvas:
            return
        self.pal_editor_widget._load_gps_pals()
        self.pal_editor_widget._update_mode_buttons()
        self.pal_editor_widget._set_palbox_mode('gps')
        self.pal_editor_widget.apply_player_ui()

    def refresh_labels(self):
        if hasattr(self, 'player_select_btn') and (not self.current_player_uid):
            self._set_selector_copy(None, '', '')
        if hasattr(self, 'context_label'):
            self.context_label.setText(t(
                'ui.pal_editor.player_context', default='Player'))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        if hasattr(self, 'pal_editor_widget'):
            self.pal_editor_widget.refresh_labels()
