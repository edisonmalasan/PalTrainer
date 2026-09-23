"""Guided source/target/review workflow for guild assignment."""
from __future__ import annotations

import os
from typing import Any, Iterable, cast

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QAbstractItemView, QFrame, QHBoxLayout, QLabel, QMenu,
    QProgressBar, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from i18n import t
from palworld_aio import constants
from palworld_aio.managers.guild_manager import move_player_to_guild, set_member_role
from palworld_aio.ui.chrome.components import BaseDialog, make_button
from palworld_aio.widgets.search_panel import SearchPanel


_ROLE_LABELS = {
    1: 'guild.role.guild_master', 2: 'guild.role.submaster',
    3: 'guild.role.member', 4: 'guild.role.guest',
}
_SOURCE_GUILD_ROLE = Qt.UserRole + 4


class _SortableItem(QTreeWidgetItem):
    _SORT_ROLE = Qt.UserRole + 1

    def __lt__(self, other):
        col = self.treeWidget().sortColumn() if self.treeWidget() else 0
        left = self.data(col, self._SORT_ROLE)
        right = other.data(col, self._SORT_ROLE)
        if left is not None and right is not None:
            return left < right
        return self.text(col).lower() < other.text(col).lower()


class GuildAssignDialog(BaseDialog):
    """Move players through explicit source, target, and review steps."""

    def __init__(
        self, parent=None, *, selected_player_uids: Iterable[str] = (),
    ) -> None:
        title = t('guild.assign.title') if t else 'Guild Assignment'
        super().__init__(title, parent, min_size=(760, 560))
        self.setWindowTitle(title)
        self.resize(920, 640)
        self._requested_uids = {
            str(uid).replace('-', '').lower() for uid in selected_player_uids
        }
        self._completed = False
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self._setup_ui()
        self._load_data()
        self._show_step(0)

    def _setup_ui(self) -> None:
        description = QLabel(t(
            'guild.assign.workflow_desc',
            default='Choose players, select a target guild, then review the move.'))
        description.setProperty('role', 'secondary')
        description.setWordWrap(True)
        self.content_layout.addWidget(description)

        step_row = QHBoxLayout()
        step_row.setSpacing(8)
        self.step_labels = []
        for number, key, fallback in (
            (1, 'guild.assign.step.source', 'Source'),
            (2, 'guild.assign.step.target', 'Target'),
            (3, 'guild.assign.step.review', 'Review'),
        ):
            label = QLabel(f'{number}  {t(key, default=fallback)}')
            label.setObjectName('workflowStep')
            label.setProperty('stepState', 'upcoming')
            step_row.addWidget(label)
            self.step_labels.append(label)
        step_row.addStretch(1)
        self.content_layout.addLayout(step_row)

        self.workflow = QStackedWidget(self)
        self.workflow.setObjectName('guildAssignWorkflow')
        self.workflow.addWidget(self._build_source_page())
        self.workflow.addWidget(self._build_target_page())
        self.workflow.addWidget(self._build_review_page())
        self.content_layout.addWidget(self.workflow, 1)
        self._build_bottom_bar()

    def _section(self, title: str, hint: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget(self.workflow)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName('sectionHeader')
        layout.addWidget(heading)
        copy = QLabel(hint)
        copy.setProperty('role', 'secondary')
        copy.setWordWrap(True)
        layout.addWidget(copy)
        return page, layout

    def _build_source_page(self) -> QWidget:
        page, layout = self._section(
            t('guild.assign.source_title', default='Choose players'),
            t('guild.assign.source_hint', default=(
                'Select one or more players. Their current guild is shown for '
                'context; no changes occur until the final review is confirmed.')),
        )
        self.player_panel = SearchPanel(
            'guild.assign.players_label',
            (
                'deletion.col.player_name', 'deletion.col.level',
                'deletion.col.guild_name', 'guild.assign.role',
            ),
            (200, 55, 190, 110),
            selection_mode=QAbstractItemView.ExtendedSelection,
            parent=page,
        )
        self.player_panel.tree.itemSelectionChanged.connect(self._update_status)
        layout.addWidget(self.player_panel, 1)
        self.source_count = QLabel('')
        self.source_count.setProperty('role', 'secondary')
        layout.addWidget(self.source_count)
        return page

    def _build_target_page(self) -> QWidget:
        page, layout = self._section(
            t('guild.assign.target_title', default='Choose a target guild'),
            t('guild.assign.target_hint', default=(
                'Review the current membership before choosing the destination.')),
        )
        splitter = QSplitter(Qt.Orientation.Vertical, page)
        splitter.setHandleWidth(6)
        self.guild_panel = SearchPanel(
            'guild.assign.guild_label',
            (
                'deletion.col.guild_name', 'deletion.col.member',
                'deletion.col.guild_level',
            ),
            (240, 80, 70),
            parent=splitter,
        )
        self.guild_panel.tree.itemSelectionChanged.connect(self._update_status)
        self.guild_panel.tree.itemSelectionChanged.connect(
            self._update_members_panel)
        splitter.addWidget(self.guild_panel)
        splitter.addWidget(self._build_members_pane())
        splitter.setSizes([270, 210])
        layout.addWidget(splitter, 1)
        return page

    def _build_members_pane(self) -> QFrame:
        pane = QFrame()
        pane.setObjectName('guildMembersPane')
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        heading = QLabel(t(
            'guild.assign.members_label', default='Current Members'))
        heading.setObjectName('sectionHeader')
        layout.addWidget(heading)
        self.members_tree = QTreeWidget()
        self.members_tree.setHeaderLabels([
            t('deletion.col.player_name', default='Name'),
            t('deletion.col.level', default='Lv'),
            t('guild.assign.role', default='Role'),
        ])
        self.members_tree.setColumnWidth(0, 220)
        self.members_tree.setColumnWidth(1, 50)
        self.members_tree.header().setStretchLastSection(True)
        self.members_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self.members_tree.setRootIsDecorated(False)
        self.members_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.members_tree.customContextMenuRequested.connect(
            self._show_member_context_menu)
        self.members_tree.setSortingEnabled(True)
        layout.addWidget(self.members_tree, 1)
        self.members_lbl = QLabel(t(
            'guild.assign.members_empty',
            default='Select a guild to see its members.'))
        self.members_lbl.setObjectName('bulkHintLabel')
        layout.addWidget(self.members_lbl)
        return pane

    def _build_review_page(self) -> QWidget:
        page, layout = self._section(
            t('guild.assign.review_title', default='Review assignment'),
            t('guild.assign.review_hint', default=(
                'Confirm the affected players and destination before applying.')),
        )
        self.review_summary = QLabel('')
        self.review_summary.setObjectName('operationSummary')
        self.review_summary.setWordWrap(True)
        layout.addWidget(self.review_summary)
        self.review_players = QLabel('')
        self.review_players.setProperty('role', 'secondary')
        self.review_players.setWordWrap(True)
        layout.addWidget(self.review_players)
        self.progress = QProgressBar(page)
        self.progress.setTextVisible(True)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.result_label = QLabel('')
        self.result_label.setObjectName('operationResult')
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        layout.addWidget(self.result_label)
        layout.addStretch(1)
        return page

    def _build_bottom_bar(self) -> None:
        self.status_lbl = QLabel(t(
            'guild.assign.status_no_players',
            default='Select one or more players to move.'))
        self.status_lbl.setProperty('role', 'secondary')
        self.status_lbl.setWordWrap(True)
        self.footer.insertWidget(1, self.status_lbl, stretch=1)
        self.back_btn = make_button(t(
            'guild.assign.back', default='Back'), 'secondary')
        self.back_btn.clicked.connect(self._go_back)
        self.next_btn = make_button(t(
            'guild.assign.next', default='Next'), 'primary')
        self.next_btn.clicked.connect(self._go_next)
        self.assign_btn = make_button(t(
            'guild.assign.btn', default='Assign to Guild'), 'primary')
        self.assign_btn.clicked.connect(self._assign)
        for button in (self.back_btn, self.next_btn, self.assign_btn):
            self.footer.insertWidget(self.footer.count() - 1, button)
        self._primary_button = self.next_btn

    def _load_data(self) -> None:
        self._load_players()
        self._load_guilds()
        self._update_members_panel()
        self._apply_requested_selection()
        self._update_status()

    def _load_players(self) -> None:
        self.player_panel.clear()
        if not constants.loaded_level_json:
            return
        world = cast(dict[str, Any], constants.loaded_level_json)[
            'properties']['worldSaveData']['value']
        for group in world['GroupSaveDataMap']['value']:
            raw = group['value']['RawData']['value']
            group_type = group['value']['GroupType']['value']['value']
            guild_name = (
                raw.get('guild_name', '')
                if group_type == 'EPalGroupType::Guild' else '')
            source_guild_id = str(group['key']) if guild_name else ''
            for player in raw.get('players', []):
                raw_uid = player.get('player_uid')
                if raw_uid is None:
                    continue
                uid = str(raw_uid)
                uid_norm = uid.replace('-', '').lower()
                name = player.get('player_info', {}).get(
                    'player_name', 'Unknown')
                level = constants.player_levels.get(uid_norm, 1)
                role = player.get('role', 3)
                role_key = _ROLE_LABELS.get(role)
                role_label = t(role_key) if role_key else f'?{role}'
                item = self.player_panel.add_item(
                    [name, str(level), guild_name, role_label],
                    data=uid,
                    sort_keys={1: int(level), 3: int(role)},
                )
                item.setData(0, _SOURCE_GUILD_ROLE, source_guild_id)

    def _load_guilds(self) -> None:
        self.guild_panel.clear()
        if not constants.loaded_level_json:
            return
        world = cast(dict[str, Any], constants.loaded_level_json)[
            'properties']['worldSaveData']['value']
        for group in world['GroupSaveDataMap']['value']:
            if (group['value']['GroupType']['value']['value']
                    != 'EPalGroupType::Guild'):
                continue
            raw = group['value']['RawData']['value']
            guild_id = str(group['key'])
            guild_name = raw.get('guild_name', 'Unknown')
            guild_level = raw.get('base_camp_level', 1)
            members = len(raw.get('players', []))
            self.guild_panel.add_item(
                [guild_name, str(members), str(guild_level)],
                data=guild_id,
                sort_keys={1: members, 2: int(guild_level)},
            )

    def _apply_requested_selection(self) -> None:
        if not self._requested_uids:
            return
        for item in self.player_panel._all_items:
            uid = str(item.data(0, Qt.ItemDataRole.UserRole) or '')
            item.setSelected(uid.replace('-', '').lower() in self._requested_uids)

    def _update_members_panel(self) -> None:
        self.members_tree.setSortingEnabled(False)
        self.members_tree.clear()
        _, guild_id = self._selected_guild()
        if guild_id is None or not constants.loaded_level_json:
            self.members_lbl.setText(t(
                'guild.assign.members_empty',
                default='Select a guild to see its members.'))
            return
        world = cast(dict[str, Any], constants.loaded_level_json)[
            'properties']['worldSaveData']['value']
        for group in world['GroupSaveDataMap']['value']:
            if str(group['key']) != guild_id:
                continue
            raw = group['value']['RawData']['value']
            for player in raw.get('players', []):
                raw_uid = player.get('player_uid')
                if raw_uid is None:
                    continue
                uid_norm = str(raw_uid).replace('-', '').lower()
                name = player.get('player_info', {}).get(
                    'player_name', 'Unknown')
                level = constants.player_levels.get(uid_norm, 1)
                role = player.get('role', 3)
                role_key = _ROLE_LABELS.get(role)
                role_label = t(role_key) if role_key else f'?{role}'
                item = _SortableItem([name, str(level), role_label])
                item.setData(0, Qt.ItemDataRole.UserRole, str(raw_uid))
                item.setData(1, _SortableItem._SORT_ROLE, int(level))
                item.setData(2, _SortableItem._SORT_ROLE, role)
                self.members_tree.addTopLevelItem(item)
            break
        self.members_tree.setSortingEnabled(True)
        self.members_tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        count = self.members_tree.topLevelItemCount()
        self.members_lbl.setText(t(
            'guild.assign.members_count', default='{count} current member(s)',
            count=count))

    def _show_member_context_menu(self, pos) -> None:
        item = self.members_tree.itemAt(pos)
        if item is None:
            return
        uid = item.data(0, Qt.ItemDataRole.UserRole)
        _, guild_id = self._selected_guild()
        if not uid or not guild_id:
            return
        current_role = item.data(2, _SortableItem._SORT_ROLE) or 3
        menu = QMenu(self)
        menu.setObjectName('appContextMenu')
        menu.setAccessibleName(t(
            'ui.menu.context_actions', default='Context actions'))
        for role_value, role_name in (
            (1, 'guild_master'), (2, 'submaster'),
            (3, 'member'), (4, 'guest'),
        ):
            label = t(f'guild.role.{role_name}')
            prefix = '✓ ' if role_value == current_role else '  '
            action = menu.addAction(f'{prefix}{label}')
            action.setData(role_value)
        action = menu.exec(self.members_tree.viewport().mapToGlobal(pos))
        if action is not None:
            new_role = action.data()
            if new_role and new_role != current_role:
                set_member_role(guild_id, uid, new_role)
                self._update_members_panel()

    def _selected_players(self) -> list[tuple[str, str]]:
        return [
            (item.text(0), str(item.data(0, Qt.ItemDataRole.UserRole)))
            for item in self.player_panel.get_selected_items()
        ]

    def _selected_guild(self) -> tuple[str | None, str | None]:
        item = self.guild_panel.get_selected_item()
        if item is None:
            return None, None
        return item.text(0), str(item.data(0, Qt.ItemDataRole.UserRole))

    def _assignment_plan(self) -> tuple[list[tuple[str, str]], int]:
        _, guild_id = self._selected_guild()
        if guild_id is None:
            return [], 0
        eligible = []
        unchanged = 0
        for item in self.player_panel.get_selected_items():
            player = (
                item.text(0), str(item.data(0, Qt.ItemDataRole.UserRole)))
            if str(item.data(0, _SOURCE_GUILD_ROLE) or '') == guild_id:
                unchanged += 1
            else:
                eligible.append(player)
        return eligible, unchanged

    def _update_status(self) -> None:
        players = self._selected_players()
        guild_name, guild_id = self._selected_guild()
        step = self.workflow.currentIndex() if hasattr(self, 'workflow') else 0
        self.source_count.setText(t(
            'guild.assign.selected_count', default='{count} selected',
            count=len(players)))
        if not players:
            message = t(
                'guild.assign.status_no_players',
                default='Select one or more players to move.')
        elif guild_id is None and step > 0:
            message = t(
                'guild.assign.status_no_guild',
                default='Select a target guild.')
        elif step == 0:
            message = t(
                'guild.assign.source_ready',
                default='{count} player(s) selected.', count=len(players))
        else:
            message = t(
                'guild.assign.target_ready',
                default='{count} player(s) → {guild}',
                count=len(players), guild=guild_name or '')
        self.status_lbl.setText(message)
        self._sync_footer()

    def _sync_footer(self) -> None:
        step = self.workflow.currentIndex()
        has_players = bool(self._selected_players())
        _, guild_id = self._selected_guild()
        eligible, _unchanged = self._assignment_plan()
        self.back_btn.setVisible(step > 0 and not self._completed)
        self.next_btn.setVisible(step < 2 and not self._completed)
        self.assign_btn.setVisible(step == 2 and not self._completed)
        self.next_btn.setEnabled(has_players if step == 0 else guild_id is not None)
        self.assign_btn.setEnabled(bool(eligible))
        self.cancel_btn.setText(t(
            'button.close' if self._completed else 'button.cancel',
            default='Close' if self._completed else 'Cancel'))

    def _show_step(self, step: int) -> None:
        step = max(0, min(step, 2))
        self.workflow.setCurrentIndex(step)
        for index, label in enumerate(self.step_labels):
            state = 'complete' if index < step else (
                'active' if index == step else 'upcoming')
            label.setProperty('stepState', state)
            label.style().unpolish(label)
            label.style().polish(label)
        if step == 2:
            self._update_review()
        self._update_status()

    def _go_next(self) -> None:
        step = self.workflow.currentIndex()
        if step == 0 and not self._selected_players():
            return
        if step == 1 and self._selected_guild()[1] is None:
            return
        self._show_step(step + 1)

    def _go_back(self) -> None:
        if not self._completed:
            self._show_step(self.workflow.currentIndex() - 1)

    def _update_review(self) -> None:
        players = self._selected_players()
        eligible, unchanged = self._assignment_plan()
        guild_name, _guild_id = self._selected_guild()
        self.review_summary.setText(t(
            'guild.assign.review_summary',
            default='{affected} of {selected} selected player(s) will move to {guild}.',
            affected=len(eligible), selected=len(players), guild=guild_name or ''))
        names = ', '.join(name for name, _uid in players[:8])
        if len(players) > 8:
            names += f' +{len(players) - 8} more'
        if unchanged:
            names += '\n' + t(
                'guild.assign.already_members',
                default='{count} already in the target guild; no change.',
                count=unchanged)
        self.review_players.setText(names)
        self.progress.hide()
        self.result_label.hide()

    def _assign(self) -> None:
        eligible, unchanged = self._assignment_plan()
        guild_name, guild_id = self._selected_guild()
        if not eligible or guild_id is None:
            return
        self.back_btn.setEnabled(False)
        self.assign_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress.setRange(0, len(eligible))
        self.progress.setValue(0)
        self.progress.show()
        successes = 0
        failures = 0
        for index, (_player_name, uid) in enumerate(eligible, start=1):
            if move_player_to_guild(uid, guild_id):
                successes += 1
            else:
                failures += 1
            self.progress.setValue(index)
            QApplication.processEvents()
        constants.invalidate_container_lookup()
        self._completed = True
        self.cancel_btn.setEnabled(True)
        self.result_label.setProperty(
            'resultState', 'success' if failures == 0 else 'warning')
        self.result_label.setText(t(
            'guild.assign.result',
            default=(
                'Moved {successes} player(s) to {guild}. '
                '{failures} failed; {unchanged} already there.'),
            successes=successes, failures=failures,
            unchanged=unchanged, guild=guild_name or ''))
        self.result_label.show()
        self.status_lbl.setProperty(
            'role', 'success' if failures == 0 else 'warning')
        self.status_lbl.setText(t(
            'guild.assign.result_status',
            default='Assignment complete: {successes} moved, {failures} failed.',
            successes=successes, failures=failures))
        for widget in (self.result_label, self.status_lbl):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._sync_footer()


__all__ = ['GuildAssignDialog']
