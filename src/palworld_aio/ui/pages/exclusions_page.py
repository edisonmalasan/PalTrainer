"""Segmented exclusions workspace using one shared entity browser."""
from __future__ import annotations

from typing import Mapping, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from palworld_aio.ui.chrome.components import SegmentedControl, make_button
from palworld_aio.ui.chrome.entity_browser import EntityBrowserFrame
from palworld_aio.ui.chrome.localization import tr


_KINDS = ('players', 'guilds', 'bases')


class ExclusionsPage(QWidget):
    addRequested = pyqtSignal(str)
    removeRequested = pyqtSignal(str, str)
    stateActionRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('exclusionsPage')
        self._current_kind = 'players'
        self._loaded = False
        self._compact = False
        self._records: dict[str, tuple[str, ...]] = {
            kind: () for kind in _KINDS
        }
        self._view_states: dict[str, dict[str, object]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        switch_row = QHBoxLayout()
        switch_row.addStretch(1)
        self.segmented = SegmentedControl(
            (
                ('players', tr('ui.exclusions.players', 'Players')),
                ('guilds', tr('ui.exclusions.guilds', 'Guilds')),
                ('bases', tr('ui.exclusions.bases', 'Bases')),
            ),
            current='players',
            accessible_name=tr(
                'ui.exclusions.view', 'Exclusion type'),
            parent=self,
        )
        self.segmented.currentChanged.connect(self.switch_view)
        switch_row.addWidget(self.segmented)
        root.addLayout(switch_row)

        self.entity_browser = EntityBrowserFrame(
            'ui.exclusions.search',
            ('ui.exclusions.column.identifier',),
            (520,),
            parent=self,
        )
        self.browser = self.entity_browser.browser
        self.inspector = self.entity_browser.inspector
        self.browser.set_copyable_columns({0})
        self.browser.set_mono_columns({0})
        self.entity_browser.add_inspector_row(
            tr('ui.exclusions.type', 'Type'))
        self.entity_browser.add_inspector_row(
            tr('ui.exclusions.column.identifier', 'Identifier'),
            monospace=True)
        self.entity_browser.set_detail_provider(self._detail_for_values)
        self.entity_browser.configure_collection_states(
            empty_title=tr(
                'ui.exclusions.empty_title', 'No exclusions configured'),
            empty_message=tr(
                'ui.exclusions.empty',
                'No player exclusions configured. Use Add Exclusion to create one.',
                type='player'),
            no_result_title=tr(
                'ui.exclusions.no_result_title', 'No matching exclusions'),
            no_result_message=tr(
                'ui.exclusions.no_result_message',
                'No exclusions match the active search or filters.'),
            loading_message=tr(
                'ui.exclusions.loading', 'Loading exclusions…'),
            empty_action_text=tr(
                'deletion.exclusions.add', '+ Add Exclusion'),
        )
        self.entity_browser.stateActionRequested.connect(
            self._on_state_action)
        self.inspector.show_empty(tr(
            'ui.exclusions.select',
            'Select an exclusion to view its identifier.'))

        self.add_button = make_button(
            tr('deletion.exclusions.add', '+ Add Exclusion'), 'secondary')
        self.add_button.clicked.connect(
            lambda _checked=False: self.addRequested.emit(self._current_kind))
        self.browser.footer_slot.addWidget(self.add_button)
        self.remove_button = make_button(
            tr('ui.exclusions.remove', 'Remove'), 'warning')
        self.remove_button.clicked.connect(self._request_remove_selected)
        self.remove_button.setEnabled(False)
        self.inspector.add_action(self.remove_button)
        root.addWidget(self.entity_browser, 1)
        self.entity_browser.entitySelected.connect(
            lambda _values: self.remove_button.setEnabled(True))
        self._render_current()

    @property
    def current_kind(self) -> str:
        return self._current_kind

    def set_exclusions(self, records: Mapping[str, list[str] | tuple[str, ...]]) -> None:
        self._records = {
            kind: tuple(str(value) for value in records.get(kind, ()))
            for kind in _KINDS
        }
        self._render_current()

    def set_loaded(self, loaded: bool) -> None:
        self._loaded = loaded
        self.add_button.setEnabled(loaded)
        if not loaded:
            self.browser.tree.clearSelection()
            self.remove_button.setEnabled(False)
            self.inspector.show_empty(tr(
                'ui.exclusions.select',
                'Select an exclusion to view its identifier.'))
        self._apply_empty_copy()

    def set_loading(self) -> None:
        self.entity_browser.set_collection_state(
            'loading', tr('ui.exclusions.loading', 'Loading exclusions…'))

    def set_error(self, message: str = '') -> None:
        self.entity_browser.set_collection_state('error', message)

    def switch_view(self, kind: str) -> None:
        if kind not in _KINDS:
            raise KeyError(kind)
        if kind == self._current_kind:
            return
        self._view_states[self._current_kind] = self.browser.capture_view_state()
        self._current_kind = kind
        if self.segmented.current() != kind:
            self.segmented.set_current(kind)
        self.browser.search_input.clear()
        self.browser.tree.clearSelection()
        self._render_current()
        state = self._view_states.get(kind)
        if state is not None:
            self.browser.restore_view_state(state)

    def capture_view_state(self) -> dict[str, object]:
        states = dict(self._view_states)
        states[self._current_kind] = self.browser.capture_view_state()
        return {'kind': self._current_kind, 'views': states}

    def restore_view_state(self, state: Mapping[str, object]) -> None:
        views = state.get('views')
        if isinstance(views, dict):
            self._view_states = {
                str(key): dict(value)
                for key, value in views.items() if isinstance(value, dict)
            }
        kind = str(state.get('kind', 'players'))
        if kind in _KINDS:
            self.switch_view(kind)
        view_state = self._view_states.get(self._current_kind)
        if view_state is not None:
            self.browser.restore_view_state(view_state)

    def refresh_labels(self) -> None:
        self.browser.refresh_labels()
        self.entity_browser.update_collection_state_copy(
            empty_title=tr(
                'ui.exclusions.empty_title', 'No exclusions configured'),
            empty_message=self.entity_browser.empty_state.message_label.text(),
            no_result_title=tr(
                'ui.exclusions.no_result_title', 'No matching exclusions'),
            no_result_message=tr(
                'ui.exclusions.no_result_message',
                'No exclusions match the active search or filters.'),
            loading_message=tr(
                'ui.exclusions.loading', 'Loading exclusions…'),
            empty_action_text=tr(
                'deletion.exclusions.add', '+ Add Exclusion'),
        )
        self.add_button.setText(tr(
            'deletion.exclusions.add', '+ Add Exclusion'))
        self.remove_button.setText(tr('ui.exclusions.remove', 'Remove'))
        self._apply_empty_copy()

    def _render_current(self) -> None:
        self.browser.clear()
        for value in self._records[self._current_kind]:
            self.browser.add_item((value,), data=value)
        self._apply_empty_copy()
        if not self.browser.tree.selectedItems():
            self.inspector.show_empty(tr(
                'ui.exclusions.select',
                'Select an exclusion to view its identifier.'))
            self.remove_button.setEnabled(False)

    def _apply_empty_copy(self) -> None:
        label = tr(f'ui.exclusions.{self._current_kind}',
                   self._current_kind.title())
        message = tr(
            'ui.exclusions.empty',
            'No {type} exclusions configured. Use Add Exclusion to create one.',
            type=label.lower())
        self.browser.set_empty_state(message)
        self.entity_browser.set_empty_copy(
            tr('ui.exclusions.empty_title', 'No exclusions configured'),
            message)
        self.entity_browser.set_collection_state(
            'ready' if self._loaded else 'no_save')

    def _detail_for_values(self, values: list[str]) -> tuple[str, dict[int, str]]:
        value = values[0] if values else ''
        label = tr(f'ui.exclusions.{self._current_kind}',
                   self._current_kind.title())
        return value, {0: label, 1: value}

    def _request_remove_selected(self) -> None:
        item = self.browser.get_selected_item()
        if item is not None:
            self.removeRequested.emit(self._current_kind, item.text(0))

    def _on_state_action(self, action: str) -> None:
        if action == 'empty':
            self.addRequested.emit(self._current_kind)
            return
        self.stateActionRequested.emit(action)

    def resizeEvent(self, a0) -> None:
        compact = a0.size().width() < 900
        if compact != self._compact:
            self._compact = compact
            self.entity_browser.set_compact(compact)
            if compact and self.browser.get_selected_item() is not None:
                self.entity_browser.open_inspector()
        super().resizeEvent(a0)


__all__ = ['ExclusionsPage']
