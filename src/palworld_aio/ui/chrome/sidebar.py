"""Grouped, responsive workspace sidebar backed by the route registry."""
from __future__ import annotations

from typing import Iterable, Mapping, Optional

from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.ui.chrome import icons as app_icons
from palworld_aio.ui.chrome.components import make_tool_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import LAYOUT, SPACING
from palworld_aio.ui.routes import (
    ContextKind,
    GROUP_LABEL_KEYS,
    ROUTES,
    RouteDescriptor,
    RouteGroup,
    RouteRegistry,
)


_GROUP_LABELS = {
    RouteGroup.WORKSPACE: 'Workspace',
    RouteGroup.WORLD: 'World',
    RouteGroup.EDITORS: 'Editors',
    RouteGroup.TOOLS: 'Tools',
    RouteGroup.REFERENCE: 'Reference',
    RouteGroup.SYSTEM: 'System',
}


class WorkspaceSidebar(QFrame):
    """Persistent route navigation with a scrollable keyboard focus order."""

    routeActivated = pyqtSignal(str)
    collapsedChanged = pyqtSignal(bool)

    MIN_EXPANDED_WIDTH = 208
    MAX_EXPANDED_WIDTH = 320

    def __init__(
        self,
        registry: RouteRegistry = ROUTES,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('sideBar')
        self.setProperty('collapsed', False)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._registry = registry
        self._collapsed = False
        self._expanded_width = LAYOUT['sidebar_expanded']
        self._active_route: str | None = None
        self._buttons: dict[str, QPushButton] = {}
        self._group_labels: dict[RouteGroup, QLabel] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING['sm'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        root.setSpacing(SPACING['sm'])

        masthead = QHBoxLayout()
        masthead.setContentsMargins(SPACING['xs'], 0, SPACING['xs'], 0)
        self.brand_label = QLabel('PalTrainer', self)
        self.brand_label.setObjectName('sidebarBrand')
        masthead.addWidget(self.brand_label, 1)
        self.collapse_button = make_tool_button(
            'chevron_left', tr('ui.sidebar.collapse', 'Collapse sidebar'), self)
        self.collapse_button.setObjectName('sidebarCollapseButton')
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        masthead.addWidget(self.collapse_button)
        root.addLayout(masthead)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName('sidebarScroll')
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(self.scroll_area)
        content.setObjectName('sidebarContent')
        self._routes_layout = QVBoxLayout(content)
        self._routes_layout.setContentsMargins(0, 0, 0, 0)
        self._routes_layout.setSpacing(SPACING['xs'])
        for group in RouteGroup:
            self._add_group(group)
        self._routes_layout.addStretch(1)
        self.scroll_area.setWidget(content)
        root.addWidget(self.scroll_area, 1)

        self.set_expanded_width(self._expanded_width)

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    @property
    def active_route(self) -> str | None:
        return self._active_route

    @property
    def route_buttons(self) -> Mapping[str, QPushButton]:
        return self._buttons.copy()

    def _add_group(self, group: RouteGroup) -> None:
        label = QLabel(
            tr(GROUP_LABEL_KEYS[group], _GROUP_LABELS[group]), self.scroll_area)
        label.setObjectName('sidebarSection')
        label.setProperty('routeGroup', group.value)
        self._group_labels[group] = label
        self._routes_layout.addWidget(label)
        for route in self._registry.for_group(group):
            button = self._create_route_button(route)
            self._routes_layout.addWidget(button)

    def _create_route_button(self, route: RouteDescriptor) -> QPushButton:
        button = QPushButton(self.scroll_area)
        button.setCheckable(True)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(40)
        button.setProperty('sidebarItem', True)
        button.setProperty('routeId', route.route_id)
        button.setProperty('routeGroup', route.group.value)
        button.setProperty('risk', route.risk.value)
        button.setProperty('prerequisiteMissing', False)
        button.installEventFilter(self)
        button.clicked.connect(
            lambda _checked=False, route_id=route.route_id:
                self.routeActivated.emit(route_id))
        self._button_group.addButton(button)
        self._buttons[route.route_id] = button
        self._apply_button_presentation(route, button)
        return button

    def _route_label(self, route: RouteDescriptor) -> str:
        return tr(route.label_key, route.label)

    def _apply_button_presentation(
        self, route: RouteDescriptor, button: QPushButton,
    ) -> None:
        label = self._route_label(route)
        button.setText('' if self._collapsed else label)
        button.setAccessibleName(label)
        description = tr(route.help_key, route.help_text)
        shortcut = f' ({route.shortcut})' if route.shortcut else ''
        button.setToolTip(f'{label}{shortcut}\n{description}')
        icon = app_icons.get_qicon(
            route.icon,
            role='accent' if route.route_id == self._active_route else 'text_secondary',
        )
        if icon is not None:
            button.setIcon(icon)

    def set_active(self, route_id: str) -> None:
        route = self._registry.resolve(route_id)
        self._active_route = route_id
        for item_id, button in self._buttons.items():
            active = item_id == route_id
            button.setChecked(active)
            button.setProperty('active', active)
            self._apply_button_presentation(self._registry.resolve(item_id), button)
            button.style().unpolish(button)
            button.style().polish(button)
        self.scroll_area.ensureWidgetVisible(self._buttons[route_id], 0, SPACING['md'])

    def set_route_availability(
        self,
        missing: Mapping[str, Iterable[ContextKind]],
    ) -> None:
        """Explain unmet prerequisites while keeping every route reachable."""
        for route_id, button in self._buttons.items():
            kinds = tuple(missing.get(route_id, ()))
            button.setProperty('prerequisiteMissing', bool(kinds))
            route = self._registry.resolve(route_id)
            self._apply_button_presentation(route, button)
            base = tr(route.help_key, route.help_text)
            if kinds:
                ordered = sorted(kinds, key=tuple(ContextKind).index)
                names = ', '.join(
                    kind.value.replace('_', ' ').title() for kind in ordered)
                explanation = tr(
                    'ui.sidebar.requires_context',
                    'Requires: {context}', context=names)
                button.setAccessibleDescription(f'{base} {explanation}')
                button.setToolTip(f'{button.toolTip()}\n{explanation}')
            else:
                button.setAccessibleDescription(base)
            button.setEnabled(True)
            button.style().unpolish(button)
            button.style().polish(button)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        collapsed = bool(collapsed)
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.setProperty('collapsed', collapsed)
        self.brand_label.setVisible(not collapsed)
        for label in self._group_labels.values():
            label.setVisible(not collapsed)
        for route_id, button in self._buttons.items():
            self._apply_button_presentation(self._registry.resolve(route_id), button)
        icon_name = 'chevron_right' if collapsed else 'chevron_left'
        label = tr(
            'ui.sidebar.expand' if collapsed else 'ui.sidebar.collapse',
            'Expand sidebar' if collapsed else 'Collapse sidebar',
        )
        icon = app_icons.get_qicon(icon_name, role='text_secondary')
        if icon is not None:
            self.collapse_button.setIcon(icon)
        self.collapse_button.setToolTip(label)
        self.collapse_button.setAccessibleName(label)
        self.setFixedWidth(
            LAYOUT['sidebar_collapsed'] if collapsed else self._expanded_width)
        self.style().unpolish(self)
        self.style().polish(self)
        self.collapsedChanged.emit(collapsed)

    def set_expanded_width(self, width: int) -> None:
        self._expanded_width = max(
            self.MIN_EXPANDED_WIDTH, min(self.MAX_EXPANDED_WIDTH, int(width)))
        if not self._collapsed:
            self.setFixedWidth(self._expanded_width)

    def export_settings(self) -> dict[str, object]:
        return {
            'collapsed': self._collapsed,
            'expanded_width': self._expanded_width,
        }

    def restore_settings(self, settings: Mapping[str, object]) -> None:
        width = settings.get('expanded_width', LAYOUT['sidebar_expanded'])
        if not isinstance(width, int) or isinstance(width, bool):
            width = LAYOUT['sidebar_expanded']
        collapsed = settings.get('collapsed', False)
        if not isinstance(collapsed, bool):
            collapsed = False
        self.set_expanded_width(width)
        self.set_collapsed(collapsed)

    def refresh_labels(self) -> None:
        for group, label in self._group_labels.items():
            label.setText(tr(GROUP_LABEL_KEYS[group], _GROUP_LABELS[group]))
        for route_id, button in self._buttons.items():
            self._apply_button_presentation(self._registry.resolve(route_id), button)

    def eventFilter(self, watched: Optional[QObject], event: Optional[QEvent]) -> bool:
        if watched in self._buttons.values() and event is not None \
                and event.type() == QEvent.Type.KeyPress:
            key = event.key()  # type: ignore[attr-defined]
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
                buttons = tuple(self._buttons.values())
                index = buttons.index(watched)  # type: ignore[arg-type]
                if key == Qt.Key.Key_Home:
                    target = buttons[0]
                elif key == Qt.Key.Key_End:
                    target = buttons[-1]
                else:
                    delta = -1 if key == Qt.Key.Key_Up else 1
                    target = buttons[(index + delta) % len(buttons)]
                target.setFocus(Qt.FocusReason.ShortcutFocusReason)
                self.scroll_area.ensureWidgetVisible(target)
                event.accept()
                return True
        return super().eventFilter(watched, event)


__all__ = ['WorkspaceSidebar']
