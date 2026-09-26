"""Entity-aware global search over loaded-save and bundled reference records."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QWidget

from palworld_aio.ui.chrome.components import BaseDialog
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.routes import ContextKind
from palworld_aio.ui.router import NavigationResult, WorkspaceRouter
from palworld_aio.ui.workspace_context import ContextSelection


class SearchEntityType(StrEnum):
    PLAYER = 'player'
    GUILD = 'guild'
    BASE = 'base'
    PAL = 'pal'
    ITEM = 'item'
    SKILL = 'skill'
    TECHNOLOGY = 'technology'
    WORLD = 'world'


_TYPE_LABELS = {
    SearchEntityType.PLAYER: 'Player',
    SearchEntityType.GUILD: 'Guild',
    SearchEntityType.BASE: 'Base',
    SearchEntityType.PAL: 'Pal',
    SearchEntityType.ITEM: 'Item',
    SearchEntityType.SKILL: 'Skill',
    SearchEntityType.TECHNOLOGY: 'Technology',
    SearchEntityType.WORLD: 'World data',
}


@dataclass(frozen=True, slots=True)
class GlobalSearchRecord:
    entity_type: SearchEntityType
    identifier: str
    label: str
    detail: str
    route_id: str
    context: Mapping[ContextKind, ContextSelection]
    view_state: Mapping[str, object]
    keywords: tuple[str, ...] = ()

    @property
    def type_label(self) -> str:
        fallback = _TYPE_LABELS[self.entity_type]
        return tr(f'ui.search.type.{self.entity_type.value}', fallback)

    @property
    def search_text(self) -> str:
        return ' '.join((
            self.label, self.identifier, self.detail, *self.keywords,
        )).casefold()


class GlobalSearchIndex:
    def __init__(self, records: Iterable[GlobalSearchRecord] = ()) -> None:
        self.replace(records)

    def replace(self, records: Iterable[GlobalSearchRecord]) -> None:
        ordered = tuple(records)
        identities = [(record.entity_type, record.identifier) for record in ordered]
        if len(identities) != len(set(identities)):
            raise ValueError('global search entity identifiers must be unique per type')
        self._records = ordered

    @property
    def records(self) -> tuple[GlobalSearchRecord, ...]:
        return self._records

    def search(self, query: str, *, limit: int = 50) -> tuple[GlobalSearchRecord, ...]:
        terms = tuple(part for part in query.casefold().split() if part)
        if not terms:
            return self._records[:limit]
        matches = []
        for order, record in enumerate(self._records):
            text = record.search_text
            if all(term in text for term in terms):
                score = sum(text.index(term) for term in terms)
                matches.append((score, order, record))
        matches.sort(key=lambda item: (item[0], item[1]))
        return tuple(item[2] for item in matches[:limit])

    def activate(
        self, record: GlobalSearchRecord, router: WorkspaceRouter,
    ) -> NavigationResult:
        return router.navigate(
            record.route_id,
            context=record.context,
            view_state=record.view_state,
        )


def build_search_records(
    *,
    players: Iterable[Mapping[str, object]] = (),
    guilds: Iterable[Mapping[str, object]] = (),
    bases: Iterable[Mapping[str, object]] = (),
    pals: Iterable[Mapping[str, object]] = (),
    items: Iterable[Mapping[str, object]] = (),
    skills: Iterable[Mapping[str, object]] = (),
    technologies: Iterable[Mapping[str, object]] = (),
    world_data: Iterable[Mapping[str, object]] = (),
) -> tuple[GlobalSearchRecord, ...]:
    records: list[GlobalSearchRecord] = []

    def value(row: Mapping[str, object], *keys: str) -> str:
        for key in keys:
            candidate = row.get(key)
            if candidate not in (None, ''):
                return str(candidate)
        return ''

    for row in players:
        identifier, label = value(row, 'uid', 'id'), value(row, 'name', 'label')
        records.append(GlobalSearchRecord(
            SearchEntityType.PLAYER, identifier, label or identifier,
            value(row, 'guild_name', 'detail'), 'players',
            {ContextKind.PLAYER: ContextSelection(identifier, label or identifier)},
            {'selected': [identifier]}, ('player',),
        ))
    for row in guilds:
        identifier, label = value(row, 'id'), value(row, 'name', 'label')
        records.append(GlobalSearchRecord(
            SearchEntityType.GUILD, identifier, label or identifier,
            value(row, 'member_count', 'detail'), 'guilds',
            {ContextKind.GUILD: ContextSelection(identifier, label or identifier)},
            {'selected': [identifier]}, ('guild',),
        ))
    for row in bases:
        identifier = value(row, 'id', 'base_id')
        label = value(row, 'name', 'label') or f'Base {identifier[:8]}'
        linked = {ContextKind.BASE: ContextSelection(identifier, label)}
        guild_id = value(row, 'guild_id')
        if guild_id:
            guild_label = value(row, 'guild_name') or guild_id
            linked[ContextKind.GUILD] = ContextSelection(guild_id, guild_label)
        records.append(GlobalSearchRecord(
            SearchEntityType.BASE, identifier, label,
            value(row, 'guild_name', 'detail'), 'bases', linked,
            {'selected': [identifier]}, ('base',),
        ))
    reference_groups = (
        (pals, SearchEntityType.PAL, 'pal_editor', 'pals'),
        (items, SearchEntityType.ITEM, 'docs', 'items'),
        (skills, SearchEntityType.SKILL, 'docs', 'skills'),
        (technologies, SearchEntityType.TECHNOLOGY, 'docs', 'technologies'),
        (world_data, SearchEntityType.WORLD, 'map', 'world'),
    )
    for rows, entity_type, route_id, section in reference_groups:
        for row in rows:
            identifier = value(row, 'id', 'asset', 'instance_id')
            label = value(row, 'name', 'label', 'nickname') or identifier
            linked = {}
            owner_id = value(row, 'owner_uid', 'player_uid')
            if entity_type is SearchEntityType.PAL and owner_id:
                linked[ContextKind.PLAYER] = ContextSelection(
                    owner_id, value(row, 'owner_name') or owner_id)
            records.append(GlobalSearchRecord(
                entity_type, identifier, label, value(row, 'detail', 'description'),
                route_id, linked,
                {'section': section, 'selected_id': identifier},
                (section,),
            ))
    return tuple(records)


class GlobalSearchDialog(BaseDialog):
    resultActivated = pyqtSignal(object)

    def __init__(
        self,
        index: GlobalSearchIndex,
        router: WorkspaceRouter,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(tr('ui.search.global_title', 'Search everything'), parent,
                         min_size=(680, 480))
        self.setObjectName('globalSearchDialog')
        self.index = index
        self.router = router
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(
            tr('ui.search.global_placeholder', 'Search players, guilds, Pals, items, and more…'))
        self.result_list = QListWidget(self)
        self.result_list.itemActivated.connect(self._activate_item)
        self.result_list.itemDoubleClicked.connect(self._activate_item)
        self.content_layout.addWidget(self.search_input)
        self.content_layout.addWidget(self.result_list, 1)
        self.search_input.textChanged.connect(self.refresh_results)
        self.refresh_results('')

    def refresh_results(self, query: str) -> None:
        self.result_list.clear()
        for record in self.index.search(query):
            item = QListWidgetItem(
                f'{record.label}  ·  {record.type_label}'
                + (f'  ·  {record.detail}' if record.detail else ''))
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.result_list.addItem(item)
        if self.result_list.count():
            self.result_list.setCurrentRow(0)

    def open_search(self) -> None:
        self.search_input.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _activate_item(self, item: QListWidgetItem) -> None:
        record = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(record, GlobalSearchRecord):
            self.accept()
            self.index.activate(record, self.router)
            self.resultActivated.emit(record)


__all__ = [
    'GlobalSearchDialog',
    'GlobalSearchIndex',
    'GlobalSearchRecord',
    'SearchEntityType',
    'build_search_records',
]
