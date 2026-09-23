"""Searchable, requirement-aware Tool Center workspace."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome.components import (
    make_badge, make_button, make_chip, make_search_field,
)
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING
from palworld_aio.ui.routes import ContextKind
from palworld_aio.ui.tool_registry import (
    TOOLS, DataRequirement, ToolCategory, ToolDescriptor, ToolRegistry,
    ToolRisk,
)
from palworld_aio.ui.workspace_context import (
    WorkspaceContext, WorkspaceContextSnapshot,
)


_CATEGORY_LABELS = {
    ToolCategory.SAVE_FORMAT: ('ui.tools.category.save_format', 'Save & Format'),
    ToolCategory.REPAIR_RECOVERY: (
        'ui.tools.category.repair_recovery', 'Repair & Recovery'),
    ToolCategory.TRANSFER_INJECTION: (
        'ui.tools.category.transfer_injection', 'Transfer & Injection'),
    ToolCategory.ADDITIONAL: ('ui.tools.category.additional', 'Additional'),
}

_REQUIREMENT_LABELS = {
    DataRequirement.NONE: 'None',
    DataRequirement.IDENTIFIER: 'Identifier',
    DataRequirement.SAVE_FILE: 'Save file',
    DataRequirement.SAVE_FOLDER: 'Save folder',
    DataRequirement.PLAYER_SAVE: 'Player save',
    DataRequirement.WORLD_SAVE: 'World save',
    DataRequirement.OUTPUT_FILE: 'Output file',
}


class ToolCard(QFrame):
    launchRequested = pyqtSignal(str)
    prerequisiteRequested = pyqtSignal(str)

    def __init__(self, tool: ToolDescriptor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tool = tool
        self._missing: tuple[ContextKind, ...] = ()
        self.setObjectName('toolCenterCard')
        self.setProperty('risk', tool.risk.value)
        self.setMinimumHeight(188)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        layout.setSpacing(SPACING['sm'])

        heading = QHBoxLayout()
        title = QLabel(tr(tool.title_key, tool.tool_id.replace('_', ' ').title()), self)
        title.setObjectName('toolCenterTitle')
        heading.addWidget(title, 1)
        if tool.risk is not ToolRisk.SAFE:
            risk_key = f'ui.tools.risk.{tool.risk.value}'
            self.risk_badge = make_badge(
                tr(risk_key, 'High risk' if tool.risk is ToolRisk.HIGH else 'Caution'),
                'danger' if tool.risk is ToolRisk.HIGH else 'warning', self)
            heading.addWidget(self.risk_badge)
        layout.addLayout(heading)
        description = QLabel(tr(tool.description_key, ''), self)
        description.setObjectName('toolCenterDescription')
        description.setWordWrap(True)
        layout.addWidget(description)
        requirements = []
        if tool.source_requirement is not DataRequirement.NONE:
            requirements.append(
                f"Source: {_REQUIREMENT_LABELS[tool.source_requirement]}")
        if tool.target_requirement is not DataRequirement.NONE:
            requirements.append(
                f"Target: {_REQUIREMENT_LABELS[tool.target_requirement]}")
        self.io_label = QLabel(' • '.join(requirements), self)
        self.io_label.setObjectName('toolCenterIo')
        self.io_label.setWordWrap(True)
        layout.addWidget(self.io_label)
        layout.addStretch(1)
        self.requirement_label = QLabel('', self)
        self.requirement_label.setObjectName('toolCenterRequirement')
        self.requirement_label.setWordWrap(True)
        layout.addWidget(self.requirement_label)
        self.action_button = make_button(
            tr('ui.tools.open', 'Open'), 'secondary', parent=self)
        self.action_button.clicked.connect(self._activate)
        layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignRight)

    def update_context(self, snapshot: WorkspaceContextSnapshot) -> None:
        missing = []
        if self.tool.requires_save and snapshot.save is None:
            missing.append(ContextKind.SAVE)
        for kind in self.tool.required_context:
            if getattr(snapshot, kind.value, None) is None:
                missing.append(kind)
        self._missing = tuple(dict.fromkeys(missing))
        ready = not self._missing
        self.setProperty('ready', ready)
        if ready:
            self.requirement_label.setText(tr('ui.tools.ready', 'Ready'))
            self.action_button.setText(tr('ui.tools.open', 'Open'))
            self.action_button.setProperty('controlRole', 'secondary')
        else:
            names = ', '.join(kind.value.replace('_', ' ').title()
                              for kind in self._missing)
            self.requirement_label.setText(tr(
                'ui.tools.requires', 'Requires: {requirements}',
                requirements=names))
            first = self._missing[0]
            self.action_button.setText(
                tr('ui.tools.load_save', 'Load a Save')
                if first is ContextKind.SAVE else
                tr('ui.tools.select_context', 'Select {context}',
                   context=first.value.title()))
            self.action_button.setProperty('controlRole', 'primary')
        self.action_button.setAccessibleName(self.action_button.text())
        self.action_button.setAccessibleDescription(self.requirement_label.text())
        self.action_button.style().unpolish(self.action_button)
        self.action_button.style().polish(self.action_button)
        self.style().unpolish(self)
        self.style().polish(self)

    def _activate(self) -> None:
        if self._missing:
            self.prerequisiteRequested.emit(self._missing[0].value)
        else:
            self.launchRequested.emit(self.tool.tool_id)


class ToolCenterPage(QWidget):
    launchRequested = pyqtSignal(str)
    prerequisiteRequested = pyqtSignal(str)

    def __init__(
        self,
        context: WorkspaceContext,
        registry: ToolRegistry = TOOLS,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('toolCenterPage')
        self._context = context
        self._registry = registry
        self._category: ToolCategory | None = None
        self._columns = 2
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING['md'])

        search_frame, self.search_input = make_search_field(
            tr('ui.tools.search', 'Search tools…'), self._apply_filters, self)
        root.addWidget(search_frame)
        filters = QHBoxLayout()
        filters.setSpacing(SPACING['xs'])
        self.category_buttons = {}
        all_button = make_chip(tr('ui.tools.category.all', 'All'), checked=True)
        all_button.clicked.connect(
            lambda _checked=False: self.set_category(None))
        filters.addWidget(all_button)
        self.category_buttons[None] = all_button
        for category in ToolCategory:
            if not registry.in_category(category):
                continue
            key, fallback = _CATEGORY_LABELS[category]
            label = tr(key, fallback)
            button = make_chip(label.replace('&', '&&'))
            button.setAccessibleName(label)
            button.clicked.connect(
                lambda _checked=False, value=category: self.set_category(value))
            filters.addWidget(button)
            self.category_buttons[category] = button
        filters.addStretch(1)
        root.addLayout(filters)

        scroll = QScrollArea(self)
        scroll.setObjectName('toolCenterScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.card_host = QWidget(scroll)
        self.card_host.setObjectName('toolCenterBody')
        self.card_layout = QGridLayout(self.card_host)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(SPACING['md'])
        self.cards = {}
        for tool in registry:
            card = ToolCard(tool, self.card_host)
            card.launchRequested.connect(self.launchRequested.emit)
            card.prerequisiteRequested.connect(self.prerequisiteRequested.emit)
            self.cards[tool.tool_id] = card
        self.empty_label = QLabel(
            tr('ui.tools.no_results', 'No tools match your search.'), self.card_host)
        self.empty_label.setObjectName('toolCenterEmpty')
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout_cards()
        scroll.setWidget(self.card_host)
        root.addWidget(scroll, 1)
        self._unsubscribe = context.subscribe(self._on_context_changed)
        self._on_context_changed(context.snapshot)

    def set_category(self, category: ToolCategory | None) -> None:
        self._category = category
        for value, button in self.category_buttons.items():
            button.setChecked(value is category)
        self._apply_filters()

    def _matching_tools(self) -> tuple[ToolDescriptor, ...]:
        matches = self._registry.search(self.search_input.text())
        if self._category is None:
            return matches
        return tuple(tool for tool in matches if tool.category is self._category)

    def _apply_filters(self, _text: str = '') -> None:
        visible = {tool.tool_id for tool in self._matching_tools()}
        for tool_id, card in self.cards.items():
            card.setVisible(tool_id in visible)
        self._layout_cards()

    def _layout_cards(self) -> None:
        while self.card_layout.count():
            self.card_layout.takeAt(0)
        cards = [card for card in self.cards.values() if not card.isHidden()]
        for index, card in enumerate(cards):
            self.card_layout.addWidget(
                card, index // self._columns, index % self._columns)
        self.empty_label.setVisible(not cards)
        if not cards:
            self.card_layout.addWidget(self.empty_label, 0, 0)
        self.card_layout.setRowStretch(
            (len(cards) + self._columns - 1) // self._columns, 1)

    def _on_context_changed(self, snapshot: WorkspaceContextSnapshot) -> None:
        for card in self.cards.values():
            card.update_context(snapshot)

    def visible_tool_ids(self) -> tuple[str, ...]:
        return tuple(
            tool.tool_id for tool in self._registry
            if not self.cards[tool.tool_id].isHidden()
        )

    def resizeEvent(self, a0) -> None:
        columns = 1 if a0.size().width() < 760 else 2
        if columns != self._columns:
            self._columns = columns
            self._layout_cards()
        super().resizeEvent(a0)


__all__ = ['ToolCard', 'ToolCenterPage']
