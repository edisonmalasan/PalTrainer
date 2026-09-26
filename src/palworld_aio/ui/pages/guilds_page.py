"""Guilds workspace built on the shared entity-browser composition."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from palworld_aio.ui.chrome.components import make_button
from palworld_aio.ui.chrome.entity_browser import EntityBrowserFrame
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.widgets.search_panel import SearchPanel


def short_identifier(value: str) -> str:
    return f'{value[:8]}…' if len(value) > 12 else value


@dataclass(frozen=True, slots=True)
class GuildRow:
    guild_id: str
    name: str
    level: int
    member_count: int
    base_count: int = 0


@dataclass(frozen=True, slots=True)
class GuildMemberRow:
    uid: str
    name: str
    role: str
    level: int
    pals: int
    last_seen: str
    is_leader: bool = False
    role_value: int = 3
    last_seen_sort: float | None = None


class GuildsPage(QWidget):
    guildSelected = pyqtSignal(object)
    memberSelected = pyqtSignal(object)
    openPlayersRequested = pyqtSignal(object)
    openBasesRequested = pyqtSignal(object)
    stateActionRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('guildsPage')
        self.setMinimumWidth(0)
        self._guilds: dict[str, GuildRow] = {}
        self._members: dict[str, GuildMemberRow] = {}
        self._compact = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.entity_browser = EntityBrowserFrame(
            'deletion.search_guilds',
            (
                'deletion.col.guild_name', 'deletion.col.guild_level',
                'deletion.col.members', 'ui.guilds.column.bases',
                'deletion.col.guild_id', 'ui.guilds.raw_guild_id',
            ),
            (220, 75, 75, 65, 95, 0),
            parent=self,
        )
        self.browser = self.entity_browser.browser
        self.inspector = self.entity_browser.inspector
        self.browser.set_selection_key(
            lambda item: item.data(0, Qt.ItemDataRole.UserRole))
        self.browser.set_copyable_columns({4})
        self.browser.set_mono_columns({4, 5})
        self.browser.tree.setColumnHidden(5, True)

        for label, monospace in (
            (tr('deletion.col.guild_level', 'Guild Level'), False),
            (tr('deletion.col.members', 'Members'), False),
            (tr('ui.guilds.column.bases', 'Bases'), False),
            (tr('ui.guilds.raw_guild_id', 'Guild ID'), True),
        ):
            self.entity_browser.add_inspector_row(label, monospace=monospace)
        self.entity_browser.set_detail_provider(self._detail_for_values)
        self.entity_browser.configure_collection_states(
            empty_title=tr('ui.guilds.empty_title', 'No guilds found'),
            empty_message=tr(
                'ui.guilds.empty_message',
                'This loaded save does not contain any guild records.'),
            no_result_title=tr(
                'ui.guilds.no_result_title', 'No matching guilds'),
            no_result_message=tr(
                'ui.guilds.no_result_message',
                'No guilds match the active search or filters.'),
            loading_message=tr('ui.guilds.loading', 'Loading guilds…'),
        )
        self.entity_browser.stateActionRequested.connect(
            self.stateActionRequested.emit)
        self.inspector.show_empty(tr(
            'ui.guilds.row_prerequisite',
            'Click a guild row to view its members and details.'))

        self.members_browser = SearchPanel(
            'deletion.guild_members',
            (
                'deletion.col.member', 'deletion.col.role',
                'deletion.col.level', 'deletion.col.pals',
                'deletion.col.last_seen', 'deletion.col.uid',
            ),
            (125, 75, 48, 48, 0, 0),
            parent=self.inspector,
        )
        self.members_browser.setObjectName('guildMembersBrowser')
        self.members_browser.set_selection_key(
            lambda item: item.data(0, Qt.ItemDataRole.UserRole))
        self.members_browser.set_copyable_columns({5})
        self.members_browser.set_mono_columns({5})
        self.members_browser.tree.setColumnHidden(4, True)
        self.members_browser.tree.setColumnHidden(5, True)
        self.members_browser.set_empty_state(tr(
            'ui.guilds.members_empty', 'This guild has no members.'))
        self.inspector.add_content_widget(self.members_browser, stretch=1)

        self.players_button = make_button(
            tr('ui.guilds.open_players', 'Players'), 'secondary')
        self.bases_button = make_button(
            tr('ui.guilds.open_bases', 'Bases'), 'secondary')
        self.players_button.clicked.connect(
            lambda _checked=False: self._emit_for_selected(
                self.openPlayersRequested))
        self.bases_button.clicked.connect(
            lambda _checked=False: self._emit_for_selected(
                self.openBasesRequested))
        self.inspector.add_action(self.players_button)
        self.inspector.add_action(self.bases_button)
        self._set_selection_actions(False)
        root.addWidget(self.entity_browser, 1)

        self.entity_browser.entitySelected.connect(self._on_guild_values)
        self.members_browser.item_selected.connect(self._on_member_values)

    def set_guilds(self, guilds: tuple[GuildRow, ...]) -> None:
        state = self.capture_view_state()
        self._guilds = {guild.guild_id: guild for guild in guilds}
        self.browser.clear()
        self.clear_members()
        for guild in guilds:
            self.browser.add_item(
                (
                    guild.name, guild.level, guild.member_count,
                    guild.base_count, short_identifier(guild.guild_id),
                    guild.guild_id,
                ),
                data=guild.guild_id,
                sort_keys={
                    1: guild.level, 2: guild.member_count,
                    3: guild.base_count,
                },
                tooltips={4: guild.guild_id},
            )
        self.restore_view_state(state)
        if not self.browser.tree.selectedItems():
            self.inspector.show_empty(tr(
                'ui.guilds.row_prerequisite',
                'Click a guild row to view its members and details.'))
            self._set_selection_actions(False)
        self.entity_browser.set_collection_state('ready')

    def set_loaded(self, loaded: bool) -> None:
        if loaded:
            self.entity_browser.set_collection_state('ready')
            return
        self._guilds = {}
        self.browser.clear()
        self.clear_members()
        self.inspector.show_empty(tr(
            'ui.guilds.row_prerequisite',
            'Click a guild row to view its members and details.'))
        self._set_selection_actions(False)
        self.entity_browser.set_collection_state('no_save')

    def set_loading(self) -> None:
        self.entity_browser.set_collection_state(
            'loading', tr('ui.guilds.loading', 'Loading guilds…'))

    def set_error(self, message: str = '') -> None:
        self.entity_browser.set_collection_state('error', message)

    def set_members(
        self, guild_id: str, members: tuple[GuildMemberRow, ...],
    ) -> None:
        selected = self.selected_guild()
        if selected is None or selected.guild_id != guild_id:
            return
        member_state = self.members_browser.capture_view_state()
        self._members = {member.uid: member for member in members}
        self.members_browser.clear()
        for member in members:
            display_name = (
                tr('ui.guilds.leader_prefix', default='Leader · {name}',
                   name=member.name)
                if member.is_leader else member.name
            )
            self.members_browser.add_item(
                (
                    display_name, member.role, member.level, member.pals,
                    member.last_seen, short_identifier(member.uid),
                ),
                data=member.uid,
                sort_keys={
                    2: member.level, 3: member.pals,
                    4: (member.last_seen_sort
                        if member.last_seen_sort is not None else float('inf')),
                    1: member.role_value,
                },
                tooltips={5: member.uid},
            )
        self.members_browser.restore_view_state(member_state)

    def clear_members(self) -> None:
        self._members = {}
        self.members_browser.clear()

    def selected_guild(self) -> GuildRow | None:
        items = self.browser.tree.selectedItems()
        if not items:
            return None
        return self._guilds.get(str(
            items[0].data(0, Qt.ItemDataRole.UserRole)))

    def selected_member(self) -> GuildMemberRow | None:
        items = self.members_browser.tree.selectedItems()
        if not items:
            return None
        return self._members.get(str(
            items[0].data(0, Qt.ItemDataRole.UserRole)))

    def capture_view_state(self) -> dict[str, object]:
        state = self.entity_browser.capture_view_state()
        state['members'] = self.members_browser.capture_view_state()
        return state

    def restore_view_state(self, state: Mapping[str, object]) -> None:
        self.entity_browser.restore_view_state(dict(state))
        member_state = state.get('members')
        if isinstance(member_state, dict):
            self.members_browser.restore_view_state(member_state)

    def refresh_labels(self) -> None:
        self.browser.refresh_labels()
        self.members_browser.refresh_labels()
        self.entity_browser.update_collection_state_copy(
            empty_title=tr('ui.guilds.empty_title', 'No guilds found'),
            empty_message=tr(
                'ui.guilds.empty_message',
                'This loaded save does not contain any guild records.'),
            no_result_title=tr(
                'ui.guilds.no_result_title', 'No matching guilds'),
            no_result_message=tr(
                'ui.guilds.no_result_message',
                'No guilds match the active search or filters.'),
            loading_message=tr('ui.guilds.loading', 'Loading guilds…'),
        )
        labels = (
            tr('deletion.col.guild_level', 'Guild Level'),
            tr('deletion.col.members', 'Members'),
            tr('ui.guilds.column.bases', 'Bases'),
            tr('ui.guilds.raw_guild_id', 'Guild ID'),
        )
        for (label_widget, value_widget), label in zip(
                self.inspector._rows, labels):
            label_widget.setText(label)
            if hasattr(value_widget, 'set_label'):
                value_widget.set_label(label)
        self.players_button.setText(tr('ui.guilds.open_players', 'Players'))
        self.bases_button.setText(tr('ui.guilds.open_bases', 'Bases'))
        selected = self.selected_guild()
        if selected is not None:
            self.inspector.show_details(*self._detail_for_guild(selected))

    def _record_for_values(self, values: list[str]) -> GuildRow | None:
        return self._guilds.get(str(values[5])) if len(values) > 5 else None

    def _detail_for_values(self, values: list[str]) -> tuple[str, dict[int, str]]:
        guild = self._record_for_values(values)
        return self._detail_for_guild(guild) if guild is not None else ('', {})

    @staticmethod
    def _detail_for_guild(guild: GuildRow) -> tuple[str, dict[int, str]]:
        return (guild.name, {
            0: str(guild.level),
            1: str(guild.member_count),
            2: str(guild.base_count),
            3: guild.guild_id,
        })

    def _on_guild_values(self, values: list[str]) -> None:
        guild = self._record_for_values(values)
        if guild is not None:
            self.clear_members()
            self._set_selection_actions(True)
            self.guildSelected.emit(guild)

    def _set_selection_actions(self, enabled: bool) -> None:
        self.players_button.setEnabled(enabled)
        self.bases_button.setEnabled(enabled)

    def _on_member_values(self, _values: list[str]) -> None:
        member = self.selected_member()
        if member is not None:
            self.memberSelected.emit(member)

    def _emit_for_selected(self, signal) -> None:
        guild = self.selected_guild()
        if guild is not None:
            signal.emit(guild)

    def resizeEvent(self, a0) -> None:
        compact = a0.size().width() < 1024
        if compact != self._compact:
            self._compact = compact
            self.entity_browser.set_compact(compact)
            if compact:
                self.entity_browser.inspector_host.setMaximumHeight(390)
            if compact and self.selected_guild() is not None:
                self.entity_browser.open_inspector()
        super().resizeEvent(a0)


__all__ = [
    'GuildMemberRow', 'GuildRow', 'GuildsPage', 'short_identifier',
]
