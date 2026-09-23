"""Bases workspace built on the shared entity-browser composition."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from palworld_aio.ui.chrome.components import make_button
from palworld_aio.ui.chrome.entity_browser import EntityBrowserFrame
from palworld_aio.ui.chrome.localization import tr


def short_identifier(value: str) -> str:
    return f'{value[:8]}…' if len(value) > 12 else value


@dataclass(frozen=True, slots=True)
class BaseRow:
    base_id: str
    name: str
    guild_id: str
    guild_name: str
    guild_level: int
    location: str = ''
    status: str = 'In save'


class BasesPage(QWidget):
    baseSelected = pyqtSignal(object)
    openInventoryRequested = pyqtSignal(object)
    openMapRequested = pyqtSignal(object)
    openGuildRequested = pyqtSignal(object)
    stateActionRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('basesPage')
        self.setMinimumWidth(0)
        self._records: dict[str, BaseRow] = {}
        self._compact = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.entity_browser = EntityBrowserFrame(
            'deletion.search_bases',
            (
                'ui.bases.column.base', 'deletion.col.guild_name',
                'deletion.col.guild_level', 'ui.bases.column.status',
                'ui.bases.column.location', 'deletion.col.base_id',
                'ui.bases.raw_base_id', 'deletion.col.guild_id',
            ),
            (130, 140, 70, 70, 105, 90, 0, 0),
            parent=self,
        )
        self.browser = self.entity_browser.browser
        self.inspector = self.entity_browser.inspector
        self.browser.set_selection_key(
            lambda item: item.data(0, Qt.ItemDataRole.UserRole))
        self.browser.set_copyable_columns({5})
        self.browser.set_mono_columns({5, 6, 7})
        for column in (6, 7):
            self.browser.tree.setColumnHidden(column, True)

        for label, monospace in (
            (tr('ui.bases.column.status', 'Status'), False),
            (tr('deletion.col.guild_name', 'Guild'), False),
            (tr('deletion.col.guild_level', 'Guild Level'), False),
            (tr('ui.bases.column.location', 'Location'), False),
            (tr('ui.bases.raw_base_id', 'Base ID'), True),
            (tr('ui.bases.raw_guild_id', 'Guild ID'), True),
        ):
            self.entity_browser.add_inspector_row(label, monospace=monospace)
        self.entity_browser.set_detail_provider(self._detail_for_values)
        self.entity_browser.configure_collection_states(
            empty_title=tr('ui.bases.empty_title', 'No bases found'),
            empty_message=tr(
                'ui.bases.empty_message',
                'This loaded save does not contain any base records.'),
            no_result_title=tr(
                'ui.bases.no_result_title', 'No matching bases'),
            no_result_message=tr(
                'ui.bases.no_result_message',
                'No bases match the active search or filters.'),
            loading_message=tr('ui.bases.loading', 'Loading bases…'),
        )
        self.entity_browser.stateActionRequested.connect(
            self.stateActionRequested.emit)
        self.inspector.show_empty(tr(
            'bases.inspector_empty', 'Select a base to view its details'))

        self.inventory_button = make_button(
            tr('ui.bases.open_inventory', 'Inventory'), 'secondary')
        self.map_button = make_button(
            tr('ui.bases.open_map', 'Map'), 'secondary')
        self.guild_button = make_button(
            tr('ui.bases.open_guild', 'Guild'), 'tertiary')
        self.inventory_button.clicked.connect(
            lambda _checked=False: self._emit_for_selected(
                self.openInventoryRequested))
        self.map_button.clicked.connect(
            lambda _checked=False: self._emit_for_selected(
                self.openMapRequested))
        self.guild_button.clicked.connect(
            lambda _checked=False: self._emit_for_selected(
                self.openGuildRequested))
        for button in (
            self.inventory_button, self.map_button, self.guild_button,
        ):
            self.inspector.add_action(button)
        self._set_selection_actions(None)
        root.addWidget(self.entity_browser, 1)

        self.entity_browser.entitySelected.connect(self._on_selected_values)
        self.browser.item_double_clicked.connect(
            lambda _values: self._emit_for_selected(
                self.openInventoryRequested))

    def set_bases(self, bases: tuple[BaseRow, ...]) -> None:
        state = self.capture_view_state()
        self._records = {base.base_id: base for base in bases}
        self.browser.clear()
        for base in bases:
            self.browser.add_item(
                (
                    base.name, base.guild_name, base.guild_level, base.status,
                    base.location or tr('ui.bases.location_unknown', 'Unknown'),
                    short_identifier(base.base_id), base.base_id, base.guild_id,
                ),
                data=base.base_id,
                sort_keys={2: base.guild_level},
                tooltips={5: base.base_id},
            )
        self.restore_view_state(state)
        if not self.browser.tree.selectedItems():
            self.inspector.show_empty(tr(
                'bases.inspector_empty',
                'Select a base to view its details'))
            self._set_selection_actions(None)
        self.entity_browser.set_collection_state('ready')

    def set_loaded(self, loaded: bool) -> None:
        if loaded:
            self.entity_browser.set_collection_state('ready')
            return
        self._records = {}
        self.browser.clear()
        self.inspector.show_empty(tr(
            'bases.inspector_empty', 'Select a base to view its details'))
        self._set_selection_actions(None)
        self.entity_browser.set_collection_state('no_save')

    def set_loading(self) -> None:
        self.entity_browser.set_collection_state(
            'loading', tr('ui.bases.loading', 'Loading bases…'))

    def set_error(self, message: str = '') -> None:
        self.entity_browser.set_collection_state('error', message)

    def selected_base(self) -> BaseRow | None:
        items = self.browser.tree.selectedItems()
        if not items:
            return None
        return self._records.get(str(
            items[0].data(0, Qt.ItemDataRole.UserRole)))

    def capture_view_state(self) -> dict[str, object]:
        return self.entity_browser.capture_view_state()

    def restore_view_state(self, state: Mapping[str, object]) -> None:
        self.entity_browser.restore_view_state(dict(state))

    def refresh_labels(self) -> None:
        self.browser.refresh_labels()
        self.entity_browser.update_collection_state_copy(
            empty_title=tr('ui.bases.empty_title', 'No bases found'),
            empty_message=tr(
                'ui.bases.empty_message',
                'This loaded save does not contain any base records.'),
            no_result_title=tr(
                'ui.bases.no_result_title', 'No matching bases'),
            no_result_message=tr(
                'ui.bases.no_result_message',
                'No bases match the active search or filters.'),
            loading_message=tr('ui.bases.loading', 'Loading bases…'),
        )
        labels = (
            tr('ui.bases.column.status', 'Status'),
            tr('deletion.col.guild_name', 'Guild'),
            tr('deletion.col.guild_level', 'Guild Level'),
            tr('ui.bases.column.location', 'Location'),
            tr('ui.bases.raw_base_id', 'Base ID'),
            tr('ui.bases.raw_guild_id', 'Guild ID'),
        )
        for (label_widget, value_widget), label in zip(
                self.inspector._rows, labels):
            label_widget.setText(label)
            if hasattr(value_widget, 'set_label'):
                value_widget.set_label(label)
        self.inventory_button.setText(tr(
            'ui.bases.open_inventory', 'Inventory'))
        self.map_button.setText(tr('ui.bases.open_map', 'Map'))
        self.guild_button.setText(tr('ui.bases.open_guild', 'Guild'))
        selected = self.selected_base()
        if selected is not None:
            self.inspector.show_details(*self._detail_for_base(selected))

    def _record_for_values(self, values: list[str]) -> BaseRow | None:
        return self._records.get(str(values[6])) if len(values) > 6 else None

    def _detail_for_values(self, values: list[str]) -> tuple[str, dict[int, str]]:
        base = self._record_for_values(values)
        return self._detail_for_base(base) if base is not None else ('', {})

    @staticmethod
    def _detail_for_base(base: BaseRow) -> tuple[str, dict[int, str]]:
        return (base.name, {
            0: base.status,
            1: base.guild_name,
            2: str(base.guild_level),
            3: base.location or tr('ui.bases.location_unknown', 'Unknown'),
            4: base.base_id,
            5: base.guild_id,
        })

    def _on_selected_values(self, values: list[str]) -> None:
        base = self._record_for_values(values)
        if base is not None:
            self._set_selection_actions(base)
            self.baseSelected.emit(base)

    def _set_selection_actions(self, base: BaseRow | None) -> None:
        enabled = base is not None
        self.inventory_button.setEnabled(enabled)
        self.map_button.setEnabled(enabled)
        self.guild_button.setEnabled(enabled and bool(base.guild_id))

    def _emit_for_selected(self, signal) -> None:
        base = self.selected_base()
        if base is not None:
            signal.emit(base)

    def resizeEvent(self, a0) -> None:
        compact = a0.size().width() < 1024
        if compact != self._compact:
            self._compact = compact
            self.entity_browser.set_compact(compact)
            if compact and self.selected_base() is not None:
                self.entity_browser.open_inspector()
        super().resizeEvent(a0)


__all__ = ['BaseRow', 'BasesPage', 'short_identifier']
