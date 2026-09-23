"""Players workspace built on the shared entity-browser composition."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QVBoxLayout, QWidget

from palworld_aio.ui.chrome.components import create_page_footer, make_button
from palworld_aio.ui.chrome.entity_browser import EntityBrowserFrame
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING


@dataclass(frozen=True, slots=True)
class PlayerRow:
    uid: str
    name: str
    last_seen: str
    level: int
    pals: int
    guild_name: str
    guild_id: str
    guild_level: int
    is_leader: bool = False
    last_seen_sort: float | None = None

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def role(self) -> str:
        if not self.guild_id:
            return tr('ui.players.role.none', 'No guild')
        return tr(
            'ui.players.role.leader', 'Guild Master') if self.is_leader else tr(
                'ui.players.role.member', 'Member')


class PlayersPage(QWidget):
    playerSelected = pyqtSignal(object)
    openInventoryRequested = pyqtSignal(str, str)
    openPalEditorRequested = pyqtSignal(str, str)
    openGuildRequested = pyqtSignal(str)
    changeGuildRequested = pyqtSignal(object)
    bulkItemsRequested = pyqtSignal(object)
    bulkPalsRequested = pyqtSignal(object)
    bulkTechnologyRequested = pyqtSignal(object)
    bulkGuildRequested = pyqtSignal(object)
    stateActionRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('playersPage')
        self.setMinimumWidth(0)
        self._records: dict[str, PlayerRow] = {}
        self._compact = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['sm'])

        self.entity_browser = EntityBrowserFrame(
            'deletion.search_players',
            (
                'deletion.col.player_name', 'deletion.col.level',
                'deletion.col.last_seen', 'deletion.col.guild_name',
                'deletion.col.pals', 'ui.players.column.role',
                'deletion.col.uid', 'deletion.col.guild_id',
                'deletion.col.guild_level',
            ),
            (140, 55, 95, 140, 50, 90, 0, 0, 0),
            selection_mode=QAbstractItemView.SelectionMode.ExtendedSelection,
            parent=self,
        )
        self.browser = self.entity_browser.browser
        self.inspector = self.entity_browser.inspector
        self.browser.set_selection_key(
            lambda item: item.data(0, Qt.ItemDataRole.UserRole))
        self.browser.set_copyable_columns({6, 7})
        self.browser.set_mono_columns({6, 7})
        for column in (6, 7, 8):
            self.browser.tree.setColumnHidden(column, True)
        self.entity_browser.add_inspector_row(
            tr('deletion.col.level', 'Level'))
        self.entity_browser.add_inspector_row(
            tr('deletion.col.last_seen', 'Last Seen'))
        self.entity_browser.add_inspector_row(
            tr('deletion.col.pals', 'Pals'))
        self.entity_browser.add_inspector_row(
            tr('deletion.col.guild_name', 'Guild'))
        self.entity_browser.add_inspector_row(
            tr('ui.players.column.role', 'Role'))
        self.entity_browser.add_inspector_row(
            tr('ui.players.player_uid', 'Player UID'), monospace=True)
        self.entity_browser.add_inspector_row(
            tr('ui.players.guild_uid', 'Guild ID'), monospace=True)
        self.entity_browser.set_detail_provider(self._detail_for_values)
        self.entity_browser.configure_collection_states(
            empty_title=tr('ui.players.empty_title', 'No players found'),
            empty_message=tr(
                'ui.players.empty_message',
                'This loaded save does not contain any player records.'),
            no_result_title=tr(
                'ui.players.no_result_title', 'No matching players'),
            no_result_message=tr(
                'ui.players.no_result_message',
                'No players match the active search or filters.'),
            loading_message=tr(
                'ui.players.loading', 'Loading players…'),
        )
        self.entity_browser.stateActionRequested.connect(
            self.stateActionRequested.emit)
        self.inspector.show_empty(tr(
            'players.inspector_empty',
            'Select a player to view their details'))

        self.inventory_button = make_button(
            tr('ui.players.open_inventory', 'Inventory'), 'secondary')
        self.inventory_button.clicked.connect(self._open_inventory)
        self.inspector.add_action(self.inventory_button)
        self.pal_editor_button = make_button(
            tr('ui.players.open_pal_editor', 'Pal Editor'), 'secondary')
        self.pal_editor_button.clicked.connect(self._open_pal_editor)
        self.inspector.add_action(self.pal_editor_button)
        self.guild_button = make_button(
            tr('ui.players.open_guild', 'Guild'), 'tertiary')
        self.guild_button.clicked.connect(self._open_guild)
        self.inspector.add_action(self.guild_button)
        self._set_selection_actions(None)
        root.addWidget(self.entity_browser, 1)

        self.bulk_footer = create_page_footer(parent=self)
        self.bulk_footer.status_label.setText(tr(
            'ui.players.bulk_empty', 'Select players to enable bulk actions.'))
        self.bulk_item_button = make_button(
            tr('ui.players.bulk.items', 'Items'), 'secondary')
        self.bulk_pal_button = make_button(
            tr('ui.players.bulk.pals', 'Pals'), 'secondary')
        self.bulk_technology_button = make_button(
            tr('ui.players.bulk.technology', 'Technology'), 'secondary')
        self.bulk_guild_button = make_button(
            tr('ui.players.bulk.guild', 'Guild'), 'secondary')
        for button in (
            self.bulk_item_button, self.bulk_pal_button,
            self.bulk_technology_button, self.bulk_guild_button,
        ):
            button.setEnabled(False)
            self.bulk_footer.actions.addWidget(button)
        self.bulk_item_button.clicked.connect(
            lambda _checked=False: self.bulkItemsRequested.emit(
                self.selected_uids()))
        self.bulk_pal_button.clicked.connect(
            lambda _checked=False: self.bulkPalsRequested.emit(
                self.selected_uids()))
        self.bulk_technology_button.clicked.connect(
            lambda _checked=False: self.bulkTechnologyRequested.emit(
                self.selected_uids()))
        self.bulk_guild_button.clicked.connect(
            lambda _checked=False: self.bulkGuildRequested.emit(
                self.selected_uids()))
        root.addWidget(self.bulk_footer)

        self.entity_browser.entitySelected.connect(self._on_selected_values)
        self.browser.tree.itemSelectionChanged.connect(
            self._update_bulk_context)
        self.browser.item_double_clicked.connect(self._open_default)

    def set_players(self, players: tuple[PlayerRow, ...]) -> None:
        state = self.capture_view_state()
        self._records = {player.uid: player for player in players}
        self.browser.clear()
        for player in players:
            self.browser.add_item(
                (
                    player.display_name, player.level, player.last_seen,
                    player.guild_name, player.pals, player.role,
                    player.uid, player.guild_id, player.guild_level,
                ),
                data=player.uid,
                sort_keys={
                    1: player.level,
                    2: (player.last_seen_sort
                        if player.last_seen_sort is not None else float('inf')),
                    4: player.pals,
                    8: player.guild_level,
                },
            )
        self.restore_view_state(state)
        if not self.browser.tree.selectedItems():
            self.inspector.show_empty(tr(
                'players.inspector_empty',
                'Select a player to view their details'))
            self._set_selection_actions(None)
        self._update_bulk_context()
        self.entity_browser.set_collection_state('ready')

    def set_loaded(self, loaded: bool) -> None:
        if loaded:
            self.entity_browser.set_collection_state('ready')
            return
        self._records = {}
        self.browser.clear()
        self.inspector.show_empty(tr(
            'players.inspector_empty',
            'Select a player to view their details'))
        self._set_selection_actions(None)
        self._update_bulk_context()
        self.entity_browser.set_collection_state('no_save')

    def set_loading(self) -> None:
        self.entity_browser.set_collection_state(
            'loading', tr('ui.players.loading', 'Loading players…'))

    def set_error(self, message: str = '') -> None:
        self.entity_browser.set_collection_state('error', message)

    def selected_uids(self) -> tuple[str, ...]:
        return tuple(
            str(item.data(0, Qt.ItemDataRole.UserRole))
            for item in self.browser.tree.selectedItems()
        )

    def selected_player(self) -> PlayerRow | None:
        selected = self.selected_uids()
        return self._records.get(selected[0]) if selected else None

    def capture_view_state(self) -> dict[str, object]:
        return self.entity_browser.capture_view_state()

    def restore_view_state(self, state: Mapping[str, object]) -> None:
        self.entity_browser.restore_view_state(dict(state))

    def refresh_labels(self) -> None:
        self.browser.refresh_labels()
        self.entity_browser.update_collection_state_copy(
            empty_title=tr('ui.players.empty_title', 'No players found'),
            empty_message=tr(
                'ui.players.empty_message',
                'This loaded save does not contain any player records.'),
            no_result_title=tr(
                'ui.players.no_result_title', 'No matching players'),
            no_result_message=tr(
                'ui.players.no_result_message',
                'No players match the active search or filters.'),
            loading_message=tr('ui.players.loading', 'Loading players…'),
        )
        labels = (
            tr('deletion.col.level', 'Level'),
            tr('deletion.col.last_seen', 'Last Seen'),
            tr('deletion.col.pals', 'Pals'),
            tr('deletion.col.guild_name', 'Guild'),
            tr('ui.players.column.role', 'Role'),
            tr('ui.players.player_uid', 'Player UID'),
            tr('ui.players.guild_uid', 'Guild ID'),
        )
        for (label_widget, value_widget), label in zip(
                self.inspector._rows, labels):
            label_widget.setText(label)
            if hasattr(value_widget, 'set_label'):
                value_widget.set_label(label)
        self.inventory_button.setText(tr(
            'ui.players.open_inventory', 'Inventory'))
        self.pal_editor_button.setText(tr(
            'ui.players.open_pal_editor', 'Pal Editor'))
        self.guild_button.setText(tr('ui.players.open_guild', 'Guild'))
        self.bulk_item_button.setText(tr('ui.players.bulk.items', 'Items'))
        self.bulk_pal_button.setText(tr('ui.players.bulk.pals', 'Pals'))
        self.bulk_technology_button.setText(tr(
            'ui.players.bulk.technology', 'Technology'))
        self.bulk_guild_button.setText(tr('ui.players.bulk.guild', 'Guild'))
        player = self.selected_player()
        if player is not None:
            self.inspector.show_details(*self._detail_for_player(player))
        self._update_bulk_context()

    def _record_for_values(self, values: list[str]) -> PlayerRow | None:
        return self._records.get(str(values[6])) if len(values) > 6 else None

    def _detail_for_values(self, values: list[str]) -> tuple[str, dict[int, str]]:
        player = self._record_for_values(values)
        if player is None:
            return ('', {})
        return self._detail_for_player(player)

    @staticmethod
    def _detail_for_player(player: PlayerRow) -> tuple[str, dict[int, str]]:
        return (player.display_name, {
            0: str(player.level),
            1: player.last_seen,
            2: str(player.pals),
            3: player.guild_name,
            4: player.role,
            5: player.uid,
            6: player.guild_id,
        })

    def _on_selected_values(self, values: list[str]) -> None:
        player = self._record_for_values(values)
        if player is not None:
            self._set_selection_actions(player)
            self.playerSelected.emit(player)

    def _set_selection_actions(self, player: PlayerRow | None) -> None:
        enabled = player is not None
        self.inventory_button.setEnabled(enabled)
        self.pal_editor_button.setEnabled(enabled)
        self.guild_button.setEnabled(enabled and bool(player.guild_id))

    def _update_bulk_context(self) -> None:
        count = len(self.selected_uids())
        self.bulk_footer.status_label.setText(
            (tr('ui.players.bulk_selected_one', '1 player selected')
             if count == 1 else tr(
                 'ui.players.bulk_selected', '{count} players selected', count=count))
            if count else tr(
                'ui.players.bulk_empty',
                'Select players to enable bulk actions.'))
        for button in (
            self.bulk_item_button, self.bulk_pal_button,
            self.bulk_technology_button, self.bulk_guild_button,
        ):
            button.setEnabled(count > 0)

    def _open_inventory(self) -> None:
        player = self.selected_player()
        if player is not None:
            self.openInventoryRequested.emit(player.uid, player.name)

    def _open_pal_editor(self) -> None:
        player = self.selected_player()
        if player is not None:
            self.openPalEditorRequested.emit(player.uid, player.name)

    def _open_guild(self) -> None:
        player = self.selected_player()
        if player is not None and player.guild_id:
            self.openGuildRequested.emit(player.guild_id)

    def _open_default(self, values: list[str]) -> None:
        player = self._record_for_values(values)
        if player is not None:
            self.openInventoryRequested.emit(player.uid, player.name)

    def resizeEvent(self, a0) -> None:
        compact = a0.size().width() < 900
        if compact != self._compact:
            self._compact = compact
            self.entity_browser.set_compact(compact)
            if compact and self.selected_uids():
                self.entity_browser.open_inspector()
        super().resizeEvent(a0)


__all__ = ['PlayerRow', 'PlayersPage']
