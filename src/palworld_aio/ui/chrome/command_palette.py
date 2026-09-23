"""Keyboard-first command palette for routes and safe application actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QWidget

from palworld_aio.ui.chrome.components import BaseDialog
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.routes import ROUTES, RouteRegistry


@dataclass(frozen=True, slots=True)
class CommandDescriptor:
    command_id: str
    label: str
    category: str
    callback: Callable[[], None]
    keywords: tuple[str, ...] = ()
    shortcut: str | None = None

    @property
    def search_text(self) -> str:
        return ' '.join((self.label, self.category, *self.keywords)).casefold()


def _fuzzy_score(query: str, text: str) -> int | None:
    query = ' '.join(query.casefold().split())
    if not query:
        return 0
    if query in text:
        return text.index(query)
    position = -1
    gap_score = 0
    for char in query:
        found = text.find(char, position + 1)
        if found < 0:
            return None
        gap_score += found - position - 1
        position = found
    return 100 + gap_score


def route_commands(
    callback: Callable[[str], None],
    registry: RouteRegistry = ROUTES,
) -> tuple[CommandDescriptor, ...]:
    return tuple(CommandDescriptor(
        command_id=f'route:{route.route_id}',
        label=tr(route.label_key, route.label),
        category=tr('ui.command.category.navigate', 'Navigate'),
        callback=lambda route_id=route.route_id: callback(route_id),
        keywords=(route.group.value, route.help_text, route.route_id.replace('_', ' ')),
        shortcut=route.shortcut,
    ) for route in registry)


class CommandPalette(BaseDialog):
    commandExecuted = pyqtSignal(str)

    def __init__(
        self,
        commands: Iterable[CommandDescriptor],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            tr('ui.command.title', 'Command palette'),
            parent,
            min_size=(620, 420),
        )
        self.setObjectName('commandPalette')
        self._commands = tuple(commands)
        ids = [command.command_id for command in self._commands]
        if len(ids) != len(set(ids)):
            raise ValueError('command IDs must be unique')
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName('commandSearch')
        self.search_input.setPlaceholderText(
            tr('ui.command.search', 'Search destinations and commands…'))
        self.search_input.setAccessibleName(
            tr('ui.command.search_accessible', 'Search commands'))
        self.search_input.installEventFilter(self)
        self.content_layout.addWidget(self.search_input)
        self.result_list = QListWidget(self)
        self.result_list.setObjectName('commandResults')
        self.result_list.setAccessibleName(
            tr('ui.command.results', 'Command results'))
        self.result_list.itemActivated.connect(self._execute_item)
        self.result_list.itemDoubleClicked.connect(self._execute_item)
        self.content_layout.addWidget(self.result_list, 1)
        self.empty_label = QLabel(
            tr('ui.command.no_results', 'No matching commands'), self)
        self.empty_label.setObjectName('commandEmpty')
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.empty_label)
        self.cancel_btn.setText(tr('ui.action.close', 'Close'))
        self.search_input.textChanged.connect(self.set_query)
        self.set_query('')

    @property
    def visible_command_ids(self) -> tuple[str, ...]:
        return tuple(
            str(self.result_list.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(self.result_list.count())
        )

    def set_query(self, query: str) -> None:
        matches = []
        for order, command in enumerate(self._commands):
            score = _fuzzy_score(query, command.search_text)
            if score is not None:
                matches.append((score, order, command))
        matches.sort(key=lambda value: (value[0], value[1]))
        self.result_list.clear()
        for _score, _order, command in matches:
            shortcut = f'    {command.shortcut}' if command.shortcut else ''
            item = QListWidgetItem(
                f'{command.label}  ·  {command.category}{shortcut}')
            item.setData(Qt.ItemDataRole.UserRole, command.command_id)
            item.setData(
                Qt.ItemDataRole.AccessibleTextRole,
                f'{command.label}, {command.category}',
            )
            self.result_list.addItem(item)
        self.empty_label.setVisible(not matches)
        if matches:
            self.result_list.setCurrentRow(0)

    def open_palette(self) -> None:
        self.search_input.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _execute_item(self, item: QListWidgetItem) -> None:
        command_id = str(item.data(Qt.ItemDataRole.UserRole))
        command = next(
            command for command in self._commands
            if command.command_id == command_id)
        self.accept()
        command.callback()
        self.commandExecuted.emit(command_id)

    def execute_current(self) -> None:
        item = self.result_list.currentItem()
        if item is not None:
            self._execute_item(item)

    def eventFilter(self, watched: Optional[QObject], event: Optional[QEvent]) -> bool:
        if watched is self.search_input and event is not None \
                and event.type() == QEvent.Type.KeyPress:
            key = event.key()  # type: ignore[attr-defined]
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                count = self.result_list.count()
                if count:
                    delta = 1 if key == Qt.Key.Key_Down else -1
                    row = (self.result_list.currentRow() + delta) % count
                    self.result_list.setCurrentRow(row)
                event.accept()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.execute_current()
                event.accept()
                return True
        return super().eventFilter(watched, event)


__all__ = [
    'CommandDescriptor',
    'CommandPalette',
    'route_commands',
]
