"""Loaded-save and onboarding Overview workspace."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Optional, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING


@dataclass(frozen=True, slots=True)
class OverviewActivityItem:
    label: str
    detail: str = ''
    status: str = 'info'


@dataclass(frozen=True, slots=True)
class LoadedOverviewModel:
    save_name: str
    platform: str
    modified_at: str
    backup_label: str
    pending_changes: int
    counts: Mapping[str, int]
    activity: Sequence[OverviewActivityItem] = ()


@dataclass(frozen=True, slots=True)
class RecentSaveEntry:
    save_id: str
    label: str
    path: str
    platform: str = 'Steam'
    available: bool = True


class _MetricCard(QPushButton):
    def __init__(self, key: str, label: str, route_id: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.route_id = route_id
        self.setObjectName('overviewMetric')
        self.setProperty('metricKey', key)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(82)
        self.setAccessibleDescription(tr(
            'ui.overview.metric_action', 'Open {label}', label=label))
        self.set_value(label, 0)

    def set_value(self, label: str, value: int) -> None:
        self.setText(f'{value:,}\n{label}')
        self.setAccessibleName(f'{label}: {value:,}')


class OverviewPage(QWidget):
    navigateRequested = pyqtSignal(str)
    openSaveRequested = pyqtSignal()
    openFolderRequested = pyqtSignal()
    recentSaveRequested = pyqtSignal(str)
    locateRecentRequested = pyqtSignal(str)
    removeRecentRequested = pyqtSignal(str)
    utilityRequested = pyqtSignal(str)

    METRICS = (
        ('players', 'Players', 'players'),
        ('guilds', 'Guilds', 'guilds'),
        ('bases', 'Bases', 'bases'),
        ('pals', 'Pals', 'pal_editor'),
    )
    QUICK_ACTIONS = (
        ('player_inventory', 'Player Inventory', 'player_inventory'),
        ('pal_editor', 'Pal Editor', 'pal_editor'),
        ('base_inventory', 'Base Inventory', 'base_inventory'),
        ('map', 'Map', 'map'),
    )
    STANDALONE_UTILITIES = (
        ('convert_saves', 'Convert Save Files'),
        ('convert_gamepass_steam', 'GamePass ↔ Steam'),
        ('convert_steam_id', 'Steam ID Converter'),
    )

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('overviewPage')
        self._model: LoadedOverviewModel | None = None
        self._metric_columns = 4
        self._utility_columns = 3
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget(self)
        root.addWidget(self.stack)
        self.no_save_view = self._build_no_save_view()
        self.stack.addWidget(self.no_save_view)
        self.loaded_view = self._build_loaded_view()
        self.stack.addWidget(self.loaded_view)
        self.set_no_save(())

    def _build_no_save_view(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setObjectName('overviewNoSaveScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        body.setObjectName('overviewNoSaveBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['xl'])

        hero = QFrame(body)
        hero.setObjectName('overviewWelcome')
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(
            SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        hero_layout.setSpacing(SPACING['md'])
        title = QLabel(tr('ui.overview.welcome', 'Welcome to PalTrainer'), hero)
        title.setObjectName('overviewWelcomeTitle')
        hero_layout.addWidget(title)
        description = QLabel(tr(
            'ui.overview.welcome_description',
            'Load a Palworld save to inspect your world, players, bases, '
            'inventory, Pals, and save data.'), hero)
        description.setObjectName('overviewWelcomeDescription')
        description.setWordWrap(True)
        hero_layout.addWidget(description)
        actions = QGridLayout()
        actions.setHorizontalSpacing(SPACING['sm'])
        self.open_save_button = make_button(
            tr('ui.overview.open_save', 'Open Save File'), 'primary', parent=hero)
        self.open_save_button.clicked.connect(self.openSaveRequested.emit)
        actions.addWidget(self.open_save_button, 0, 0)
        self.open_folder_button = make_button(
            tr('ui.overview.open_folder', 'Open Save Folder'), 'secondary', parent=hero)
        self.open_folder_button.clicked.connect(self.openFolderRequested.emit)
        actions.addWidget(self.open_folder_button, 0, 1)
        actions.setColumnStretch(2, 1)
        hero_layout.addLayout(actions)
        drop_hint = QLabel(
            tr('ui.overview.drop_hint', 'Drop a Level.sav anywhere in this window'),
            hero,
        )
        drop_hint.setObjectName('overviewDropHint')
        drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(drop_hint)
        layout.addWidget(hero)

        section = QLabel(tr('ui.overview.recent_saves', 'Recent saves'), body)
        section.setProperty('class', 'sectionTitle')
        layout.addWidget(section)
        self.recent_host = QFrame(body)
        self.recent_host.setObjectName('overviewRecentSaves')
        self.recent_layout = QVBoxLayout(self.recent_host)
        self.recent_layout.setContentsMargins(
            SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        self.recent_layout.setSpacing(SPACING['sm'])
        layout.addWidget(self.recent_host)

        section = QLabel(tr(
            'ui.overview.standalone_tools',
            "Utilities that don't require a loaded save"), body)
        section.setProperty('class', 'sectionTitle')
        layout.addWidget(section)
        self._utility_host = QWidget(body)
        self._utility_layout = QGridLayout(self._utility_host)
        self._utility_layout.setContentsMargins(0, 0, 0, 0)
        self._utility_layout.setSpacing(SPACING['sm'])
        self.utility_buttons = {}
        for tool_id, fallback in self.STANDALONE_UTILITIES:
            button = make_button(
                tr(f'ui.overview.utility.{tool_id}', fallback),
                'secondary', parent=self._utility_host)
            button.clicked.connect(
                lambda _checked=False, identifier=tool_id:
                self.utilityRequested.emit(identifier))
            self.utility_buttons[tool_id] = button
        self._layout_utilities(3)
        layout.addWidget(self._utility_host)
        layout.addStretch(1)
        scroll.setWidget(body)
        return scroll

    def _build_loaded_view(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setObjectName('overviewScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        body.setObjectName('overviewBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['xl'])

        identity = QFrame(body)
        identity.setObjectName('overviewIdentity')
        identity_layout = QVBoxLayout(identity)
        identity_layout.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        identity_layout.setSpacing(SPACING['md'])
        identity_text = QVBoxLayout()
        self.save_name_label = QLabel('', identity)
        self.save_name_label.setObjectName('overviewSaveName')
        self.save_detail_label = QLabel('', identity)
        self.save_detail_label.setObjectName('overviewSaveDetail')
        identity_text.addWidget(self.save_name_label)
        identity_text.addWidget(self.save_detail_label)
        identity_layout.addLayout(identity_text)
        safety_row = QGridLayout()
        safety_row.setContentsMargins(0, 0, 0, 0)
        safety_row.setHorizontalSpacing(SPACING['sm'])
        self.backup_label = QLabel('', identity)
        self.backup_label.setObjectName('overviewBackupState')
        safety_row.addWidget(self.backup_label, 0, 0)
        self.pending_label = QLabel('', identity)
        self.pending_label.setObjectName('overviewPendingState')
        safety_row.addWidget(self.pending_label, 0, 1)
        safety_row.setColumnStretch(2, 1)
        identity_layout.addLayout(safety_row)
        layout.addWidget(identity)

        self._metric_host = QWidget(body)
        self._metric_layout = QGridLayout(self._metric_host)
        self._metric_layout.setContentsMargins(0, 0, 0, 0)
        self._metric_layout.setSpacing(SPACING['md'])
        self.metric_cards = {}
        for key, fallback, route_id in self.METRICS:
            label = tr(f'ui.overview.metric.{key}', fallback)
            card = _MetricCard(key, label, route_id, self._metric_host)
            card.clicked.connect(
                lambda _checked=False, route=route_id: self.navigateRequested.emit(route))
            self.metric_cards[key] = card
        self._layout_metrics(4)
        layout.addWidget(self._metric_host)

        section = QLabel(tr('ui.overview.quick_actions', 'Quick actions'), body)
        section.setProperty('class', 'sectionTitle')
        layout.addWidget(section)
        quick_host = QWidget(body)
        quick = QGridLayout(quick_host)
        quick.setContentsMargins(0, 0, 0, 0)
        quick.setSpacing(SPACING['sm'])
        self.quick_buttons = {}
        for index, (action_id, fallback, route_id) in enumerate(self.QUICK_ACTIONS):
            button = make_button(
                tr(f'ui.overview.action.{action_id}', fallback), 'secondary',
                parent=quick_host)
            icon = app_icons.get_qicon(route_id, role='text_secondary')
            if icon is not None:
                button.setIcon(icon)
            button.clicked.connect(
                lambda _checked=False, route=route_id: self.navigateRequested.emit(route))
            quick.addWidget(button, index // 2, index % 2)
            self.quick_buttons[action_id] = button
        layout.addWidget(quick_host)

        section = QLabel(tr('ui.overview.recent_activity', 'Recent activity'), body)
        section.setProperty('class', 'sectionTitle')
        layout.addWidget(section)
        self.activity_host = QFrame(body)
        self.activity_host.setObjectName('overviewActivity')
        self.activity_layout = QVBoxLayout(self.activity_host)
        self.activity_layout.setContentsMargins(SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        self.activity_layout.setSpacing(SPACING['sm'])
        layout.addWidget(self.activity_host)
        layout.addStretch(1)
        scroll.setWidget(body)
        return scroll

    def set_loaded(self, model: LoadedOverviewModel) -> None:
        if model.pending_changes < 0:
            raise ValueError('pending changes cannot be negative')
        self._model = model
        self.save_name_label.setText(model.save_name)
        self.save_detail_label.setText(
            tr('ui.overview.save_detail', '{platform} • Modified {modified}',
               platform=model.platform, modified=model.modified_at))
        self.backup_label.setText(model.backup_label)
        self.backup_label.setProperty('state', 'available' if model.backup_label else 'missing')
        pending = tr(
            'ui.pending.none' if model.pending_changes == 0 else 'ui.pending.many',
            'No pending changes' if model.pending_changes == 0 else '{count} pending changes',
            count=model.pending_changes,
        )
        self.pending_label.setText(pending)
        self.pending_label.setProperty('hasChanges', model.pending_changes > 0)
        for key, fallback, _route in self.METRICS:
            self.metric_cards[key].set_value(
                tr(f'ui.overview.metric.{key}', fallback),
                max(0, int(model.counts.get(key, 0))),
            )
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        activity = tuple(model.activity)
        if not activity:
            activity = (OverviewActivityItem(
                tr('ui.overview.activity_empty', 'No recent operations yet')),
            )
        for entry in activity[:5]:
            label = QLabel(
                entry.label if not entry.detail else f'{entry.label}  ·  {entry.detail}',
                self.activity_host,
            )
            label.setProperty('activityStatus', entry.status)
            label.setAccessibleName(label.text())
            self.activity_layout.addWidget(label)
        self.stack.setCurrentWidget(self.loaded_view)

    def set_no_save(self, recent_saves: Sequence[RecentSaveEntry]) -> None:
        self._model = None
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.recent_rows: dict[str, QFrame] = {}
        if not recent_saves:
            empty = QLabel(
                tr('ui.overview.recent_empty', 'No recent saves yet'),
                self.recent_host,
            )
            empty.setObjectName('overviewRecentEmpty')
            self.recent_layout.addWidget(empty)
        for entry in recent_saves[:5]:
            row = QFrame(self.recent_host)
            row.setObjectName('overviewRecentRow')
            row.setProperty('available', entry.available)
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(
                SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
            row_layout.setHorizontalSpacing(SPACING['sm'])
            label = QLabel(entry.label, row)
            label.setObjectName('overviewRecentName')
            row_layout.addWidget(label, 0, 0)
            detail = QLabel(
                f'{entry.platform} • {entry.path}' if entry.available else
                tr('ui.overview.file_not_found', 'File not found'),
                row,
            )
            detail.setObjectName('overviewRecentDetail')
            detail.setToolTip(entry.path)
            row_layout.addWidget(detail, 1, 0)
            row_layout.setColumnStretch(0, 1)
            if entry.available:
                action = make_button(
                    tr('ui.overview.open_recent', 'Open'), 'secondary', parent=row)
                action.clicked.connect(
                    lambda _checked=False, path=entry.path:
                    self.recentSaveRequested.emit(path))
                row_layout.addWidget(action, 0, 1, 2, 1)
            else:
                locate = make_button(
                    tr('ui.overview.locate', 'Locate…'), 'secondary', parent=row)
                locate.clicked.connect(
                    lambda _checked=False, save_id=entry.save_id:
                    self.locateRecentRequested.emit(save_id))
                remove = make_button(
                    tr('ui.overview.remove_recent', 'Remove from Recent'),
                    'ghost', parent=row)
                remove.clicked.connect(
                    lambda _checked=False, save_id=entry.save_id:
                    self.removeRecentRequested.emit(save_id))
                row_layout.addWidget(locate, 0, 1, 2, 1)
                row_layout.addWidget(remove, 0, 2, 2, 1)
            self.recent_layout.addWidget(row)
            self.recent_rows[entry.save_id] = row
        self.stack.setCurrentWidget(self.no_save_view)

    def update_context_summary(
        self,
        *,
        pending_changes: int,
        backup_label: str,
    ) -> None:
        """Refresh volatile safety state without rebuilding entity metrics."""
        if self._model is None:
            return
        self.set_loaded(replace(
            self._model,
            pending_changes=pending_changes,
            backup_label=backup_label,
        ))

    def _layout_metrics(self, columns: int) -> None:
        if columns == self._metric_columns and self._metric_layout.count():
            return
        self._metric_columns = columns
        for card in self.metric_cards.values():
            self._metric_layout.removeWidget(card)
        for index, (key, _label, _route) in enumerate(self.METRICS):
            self._metric_layout.addWidget(
                self.metric_cards[key], index // columns, index % columns)

    def _layout_utilities(self, columns: int) -> None:
        if columns == self._utility_columns and self._utility_layout.count():
            return
        self._utility_columns = columns
        for button in self.utility_buttons.values():
            self._utility_layout.removeWidget(button)
        for index, (tool_id, _label) in enumerate(self.STANDALONE_UTILITIES):
            self._utility_layout.addWidget(
                self.utility_buttons[tool_id], index // columns, index % columns)

    def resizeEvent(self, a0) -> None:
        compact = a0.size().width() < 760
        self._layout_metrics(2 if compact else 4)
        self._layout_utilities(1 if compact else 3)
        super().resizeEvent(a0)


__all__ = [
    'LoadedOverviewModel', 'OverviewActivityItem', 'OverviewPage',
    'RecentSaveEntry',
]
