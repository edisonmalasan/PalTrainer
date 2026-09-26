"""Reusable entity list, filter, selection, and inspector composition."""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QVBoxLayout, QWidget

from palworld_aio.ui.chrome.components import InspectorSideColumn
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.state_views import (
    ConfiguredEmptyState,
    ErrorState,
    NoResultState,
    PrerequisiteState,
    SkeletonView,
)
from palworld_aio.ui.chrome.tokens import LAYOUT, SPACING
from palworld_aio.widgets.search_panel import SearchPanel


DetailProvider = Callable[[list[str]], tuple[str, dict[int, str]]]


class EntityBrowserFrame(QWidget):
    """Common browser frame with a responsive shared inspector host."""

    entitySelected = pyqtSignal(object)
    stateActionRequested = pyqtSignal(str)

    def __init__(
        self,
        label_key: str,
        column_keys: Sequence[str],
        column_widths: Optional[Sequence[int]] = None,
        *,
        selection_mode=QAbstractItemView.SelectionMode.SingleSelection,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName('entityBrowserFrame')
        self._detail_provider: Optional[DetailProvider] = None
        self._compact = False
        self._collection_state = 'ready'

        root = QVBoxLayout(self)
        self._root_layout = root
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['sm'])
        self.body = QWidget(self)
        body_layout = QHBoxLayout(self.body)
        self._body_layout = body_layout
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(SPACING['md'])
        self.browser = SearchPanel(
            label_key,
            list(column_keys),
            list(column_widths or []),
            selection_mode=selection_mode,
            parent=self.body,
        )
        body_layout.addWidget(self.browser, 1)
        self.inspector_host = InspectorSideColumn(LAYOUT['inspector_width'], self.body)
        self.inspector_host.setProperty('layoutMode', 'side')
        body_layout.addWidget(self.inspector_host)
        root.addWidget(self.body, 1)

        self.browser.item_selected.connect(self._on_selected)

    @property
    def collection_state(self) -> str:
        return self._collection_state

    def configure_collection_states(
        self,
        *,
        empty_title: str,
        empty_message: str,
        no_result_title: str,
        no_result_message: str,
        loading_message: str,
        empty_action_text: str = '',
    ) -> None:
        """Install the shared lifecycle states for an entity collection."""
        self.empty_state = ConfiguredEmptyState(
            empty_title, empty_message, empty_action_text, self.browser)
        self.no_result_state = NoResultState(
            no_result_title, no_result_message, parent=self.browser)
        self.no_save_state = PrerequisiteState(
            tr('ui.world.no_save_title', 'Load a save first'),
            tr('ui.world.no_save_message',
               'Open a Palworld save to view this World workspace.'),
            tr('ui.world.open_save', 'Open save'),
            self.browser,
        )
        self.loading_state = SkeletonView(loading_message, parent=self.browser)
        self.error_state = ErrorState(
            tr('ui.world.error_title', 'Could not load this workspace'),
            tr('ui.world.error_message',
               'The current save data could not be read. Try again.'),
            parent=self.browser,
        )
        self.empty_state.actionTriggered.connect(
            lambda: self.stateActionRequested.emit('empty'))
        self.no_result_state.actionTriggered.connect(
            self.browser.clear_filters)
        self.no_save_state.actionTriggered.connect(
            lambda: self.stateActionRequested.emit('load_save'))
        self.error_state.actionTriggered.connect(
            lambda: self.stateActionRequested.emit('retry'))
        self.browser.set_empty_state_widget(self.empty_state)
        self.browser.set_no_result_state_widget(self.no_result_state)
        self.update_collection_state_copy(
            empty_title=empty_title,
            empty_message=empty_message,
            no_result_title=no_result_title,
            no_result_message=no_result_message,
            loading_message=loading_message,
            empty_action_text=empty_action_text,
        )
        self.set_collection_state('no_save')

    def update_collection_state_copy(
        self,
        *,
        empty_title: str,
        empty_message: str,
        no_result_title: str,
        no_result_message: str,
        loading_message: str,
        empty_action_text: str = '',
    ) -> None:
        self._set_state_copy(self.empty_state, empty_title, empty_message)
        self._set_state_copy(
            self.no_result_state, no_result_title, no_result_message)
        self._set_state_copy(
            self.no_save_state,
            tr('ui.world.no_save_title', 'Load a save first'),
            tr('ui.world.no_save_message',
               'Open a Palworld save to view this World workspace.'),
        )
        self._set_state_copy(
            self.error_state,
            tr('ui.world.error_title', 'Could not load this workspace'),
            tr('ui.world.error_message',
               'The current save data could not be read. Try again.'),
        )
        self.loading_state.status_label.setText(loading_message)
        self.loading_state.setAccessibleName(loading_message)
        if self.empty_state.action_button is not None and empty_action_text:
            self.empty_state.action_button.setText(empty_action_text)
        self.no_result_state.action_button.setText(tr(
            'ui.state.clear_filters', 'Clear filters'))
        self.no_save_state.action_button.setText(tr(
            'ui.world.open_save', 'Open save'))
        self.error_state.action_button.setText(tr('ui.state.retry', 'Retry'))

    @staticmethod
    def _set_state_copy(state, title: str, message: str) -> None:
        state.title_label.setText(title)
        state.message_label.setText(message)
        state.setAccessibleName(title)
        state.setAccessibleDescription(message)

    def set_collection_state(self, state: str, message: str = '') -> None:
        if state not in {'ready', 'no_save', 'loading', 'error'}:
            raise ValueError(f'unknown collection state {state!r}')
        self._collection_state = state
        if state == 'ready':
            widget = None
        elif state == 'no_save':
            widget = self.no_save_state
        elif state == 'loading':
            if message:
                self.loading_state.status_label.setText(message)
                self.loading_state.setAccessibleName(message)
            widget = self.loading_state
        else:
            if message:
                self.error_state.message_label.setText(message)
                self.error_state.setAccessibleDescription(message)
            widget = self.error_state
        self.browser.set_forced_state_widget(widget)

    def set_empty_copy(self, title: str, message: str) -> None:
        self.empty_state.title_label.setText(title)
        self.empty_state.message_label.setText(message)
        self.empty_state.setAccessibleName(title)
        self.empty_state.setAccessibleDescription(message)
        self.browser._refresh_empty_state()

    @property
    def inspector(self):
        return self.inspector_host.panel

    def set_detail_provider(self, provider: Optional[DetailProvider]) -> None:
        self._detail_provider = provider

    def add_inspector_row(self, label: str, *, monospace: bool = False) -> None:
        self.inspector.add_row(label, monospace=monospace)

    def set_compact(self, compact: bool) -> None:
        if compact == self._compact:
            return
        self._compact = compact
        self.inspector_host.setProperty('layoutMode', 'drawer' if compact else 'side')
        if compact:
            self._body_layout.removeWidget(self.inspector_host)
            self._root_layout.addWidget(self.inspector_host)
            self.inspector_host.setMinimumWidth(0)
            self.inspector_host.setMaximumWidth(16777215)
            self.inspector_host.setMaximumHeight(310)
            self.inspector_host.hide()
        else:
            self._root_layout.removeWidget(self.inspector_host)
            self._body_layout.addWidget(self.inspector_host)
            self.inspector_host.setFixedWidth(LAYOUT['inspector_width'])
            self.inspector_host.setMaximumHeight(16777215)
            self.inspector_host.show()
        self.inspector_host.style().unpolish(self.inspector_host)
        self.inspector_host.style().polish(self.inspector_host)

    def open_inspector(self) -> None:
        self.inspector_host.show()

    def close_inspector(self) -> None:
        if self._compact:
            self.inspector_host.hide()

    def capture_view_state(self) -> dict[str, object]:
        state = self.browser.capture_view_state()
        state['inspector_open'] = self.inspector_host.isVisibleTo(self)
        return state

    def restore_view_state(self, state: dict[str, object]) -> None:
        self.browser.restore_view_state(state)
        if self._compact:
            self.inspector_host.setVisible(bool(state.get('inspector_open', False)))

    def _on_selected(self, values: list[str]) -> None:
        if self._detail_provider is not None:
            title, fields = self._detail_provider(values)
            self.inspector.show_details(title, fields)
        if self._compact:
            self.open_inspector()
        self.entitySelected.emit(values)
