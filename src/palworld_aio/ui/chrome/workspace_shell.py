"""Sidebar workspace shell used by the audit UI rehaul."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from palworld_aio.shell_state import ShellState
from palworld_aio.ui.chrome.components import Drawer, make_tool_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.sidebar import WorkspaceSidebar
from palworld_aio.ui.chrome.state_views import ConfiguredEmptyState, PrerequisiteState
from palworld_aio.ui.chrome.tokens import LAYOUT, SPACING
from palworld_aio.ui.chrome.window_controls import WindowControls
from palworld_aio.ui.chrome.workspace_header import ContextItem, WorkspaceHeader
from palworld_aio.ui.router import NavigationResult, PageStateAdapter, WorkspaceRouter
from palworld_aio.ui.routes import ContextKind, ROUTES, RouteRegistry
from palworld_aio.ui.workspace_context import WorkspaceContext, WorkspaceContextSnapshot


class WindowDragRegion(QFrame):
    """The only shell surface authorized to initiate frameless movement."""

    dragStarted = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('windowDragRegion')
        self.setProperty('dragRegion', True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self._manual_offset: QPoint | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], 0, SPACING['sm'], 0)
        self.label = QLabel(
            tr('ui.shell.drag_region', 'Drag window'), self)
        self.label.setObjectName('windowDragLabel')
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.label)
        layout.addStretch(1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self.dragStarted.emit()
        top_level = self.window()
        handle = top_level.windowHandle()
        started = bool(handle and handle.startSystemMove())
        if not started:
            self._manual_offset = (
                event.globalPosition().toPoint() - top_level.frameGeometry().topLeft())
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (self._manual_offset is not None
                and event.buttons() & Qt.MouseButton.LeftButton):
            self.window().move(event.globalPosition().toPoint() - self._manual_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._manual_offset = None
        super().mouseReleaseEvent(event)


class ShellTitleBar(QFrame):
    backRequested = pyqtSignal()
    forwardRequested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('shellTitleBar')
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], 0, SPACING['sm'], 0)
        layout.setSpacing(SPACING['xs'])
        self.back_button = make_tool_button(
            'chevron_left', tr('ui.shell.back', 'Back'), self)
        self.forward_button = make_tool_button(
            'chevron_right', tr('ui.shell.forward', 'Forward'), self)
        self.back_button.clicked.connect(self.backRequested.emit)
        self.forward_button.clicked.connect(self.forwardRequested.emit)
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        self.drag_region = WindowDragRegion(self)
        layout.addWidget(self.drag_region, 1)
        self.window_controls = WindowControls(self)
        layout.addWidget(self.window_controls)

    def set_history_available(self, back: bool, forward: bool) -> None:
        self.back_button.setEnabled(back)
        self.forward_button.setEnabled(forward)


class WorkspaceShell(QFrame):
    """Composes navigation, header, page, inspector, and notification hosts."""

    routeChanged = pyqtSignal(str)
    prerequisiteActionRequested = pyqtSignal(str)
    minimizeRequested = pyqtSignal()
    maximizeRequested = pyqtSignal()
    closeRequested = pyqtSignal()

    COMPACT_INSPECTOR_WIDTH = 1200

    def __init__(
        self,
        context: WorkspaceContext,
        router: WorkspaceRouter | None = None,
        registry: RouteRegistry = ROUTES,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('workspaceShell')
        self._context = context
        self._registry = registry
        self.router = router or WorkspaceRouter(context, registry)
        self._route_pages: dict[str, QWidget] = {}
        self._inspector: QWidget | None = None
        self._inspector_compact = False
        self.setProperty('inspectorMode', 'side')

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = WorkspaceSidebar(registry, self)
        root.addWidget(self.sidebar)

        workspace = QFrame(self)
        workspace.setObjectName('workspaceArea')
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        self.title_bar = ShellTitleBar(workspace)
        workspace_layout.addWidget(self.title_bar)
        initial = registry.resolve(self.router.current_route_id)
        self.header = WorkspaceHeader(initial.label, initial.help_text, workspace)
        workspace_layout.addWidget(self.header)

        self.content_frame = QFrame(workspace)
        self.content_frame.setObjectName('workspaceContent')
        content_layout = QHBoxLayout(self.content_frame)
        content_layout.setContentsMargins(
            LAYOUT['content_padding'],
            LAYOUT['content_padding_medium'],
            LAYOUT['content_padding'],
            LAYOUT['content_padding'],
        )
        content_layout.setSpacing(SPACING['lg'])
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.content_frame)
        self.splitter.setObjectName('workspaceSplitter')
        self.page_host = QStackedWidget(self.content_frame)
        self.page_host.setObjectName('workspacePageHost')
        self.splitter.addWidget(self.page_host)

        self._prerequisite_state = PrerequisiteState(
            tr('ui.shell.prerequisite_title', 'More context needed'),
            tr('ui.shell.prerequisite_message',
               'Load a save or choose the required context to continue.'),
            tr('ui.shell.prerequisite_action', 'Resolve context'),
            self.page_host,
        )
        self._prerequisite_state.actionTriggered.connect(
            lambda: self.prerequisiteActionRequested.emit(self.router.current_route_id))
        self.page_host.addWidget(self._prerequisite_state)
        self._unavailable_state = ConfiguredEmptyState(
            tr('ui.shell.unavailable_title', 'Workspace coming next'),
            tr('ui.shell.unavailable_message',
               'This destination is registered and will be connected during its migration phase.'),
            parent=self.page_host,
        )
        self.page_host.addWidget(self._unavailable_state)

        self.inspector_side = QFrame(self.content_frame)
        self.inspector_side.setObjectName('workspaceInspectorSide')
        self.inspector_side.setFixedWidth(LAYOUT['inspector_width'])
        self._inspector_side_layout = QVBoxLayout(self.inspector_side)
        self._inspector_side_layout.setContentsMargins(0, 0, 0, 0)
        self.inspector_side.hide()
        self.splitter.addWidget(self.inspector_side)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        content_layout.addWidget(self.splitter, 1)
        self.inspector_drawer = Drawer(
            tr('ui.shell.inspector', 'Details'),
            self.content_frame,
            min_width=min(320, LAYOUT['inspector_width']),
        )
        self.inspector_drawer.closeRequested.connect(
            lambda: self.inspector_side.setProperty('drawerOpen', False))
        workspace_layout.addWidget(self.content_frame, 1)
        root.addWidget(workspace, 1)

        self.sidebar.routeActivated.connect(self.navigate)
        self.title_bar.backRequested.connect(self.go_back)
        self.title_bar.forwardRequested.connect(self.go_forward)
        controls = self.title_bar.window_controls
        controls.minimize_clicked.connect(self.minimizeRequested.emit)
        controls.maximize_clicked.connect(self.maximizeRequested.emit)
        controls.close_clicked.connect(self.closeRequested.emit)
        self._unsubscribe_router = self.router.subscribe(self._apply_navigation)
        self._unsubscribe_context = context.subscribe(self._apply_context)
        self._apply_context(context.snapshot)
        self.router.navigate(self.router.current_route_id)

    def register_page(
        self,
        route_id: str,
        page: QWidget,
        adapter: PageStateAdapter | None = None,
    ) -> None:
        self._registry.resolve(route_id)
        previous = self._route_pages.get(route_id)
        if previous is not None and previous is not page:
            shared_elsewhere = any(
                registered is previous
                for existing_route, registered in self._route_pages.items()
                if existing_route != route_id
            )
            if not shared_elsewhere:
                self.page_host.removeWidget(previous)
        self._route_pages[route_id] = page
        if self.page_host.indexOf(page) < 0:
            self.page_host.addWidget(page)
        state_adapter = adapter
        if state_adapter is None and all(
            hasattr(page, method)
            for method in ('capture_view_state', 'restore_view_state')
        ):
            state_adapter = page  # type: ignore[assignment]
        if state_adapter is not None:
            self.router.register_page(route_id, state_adapter)
        if route_id == self.router.current_route_id:
            self.page_host.setCurrentWidget(page)

    def navigate(self, route_id: str) -> NavigationResult:
        return self.router.navigate(route_id)

    def go_back(self) -> NavigationResult | None:
        return self.router.back()

    def go_forward(self) -> NavigationResult | None:
        return self.router.forward()

    def _apply_navigation(self, result: NavigationResult) -> None:
        route = result.route
        self.sidebar.set_active(route.route_id)
        self.header.title_label.setText(tr(route.label_key, route.label))
        self.header.description_label.setText(tr(route.help_key, route.help_text))
        self.header.description_label.setVisible(not self.header.compact)
        self.title_bar.set_history_available(
            self.router.can_go_back, self.router.can_go_forward)
        if result.missing_prerequisites:
            names = ', '.join(
                kind.value.replace('_', ' ').title()
                for kind in sorted(result.missing_prerequisites,
                                   key=tuple(ContextKind).index)
            )
            self._prerequisite_state.message_label.setText(tr(
                'ui.shell.route_requires',
                'This workspace requires: {context}.', context=names))
            self.page_host.setCurrentWidget(self._prerequisite_state)
        else:
            page = self._route_pages.get(route.route_id)
            self.page_host.setCurrentWidget(page or self._unavailable_state)
        self.routeChanged.emit(route.route_id)

    def _apply_context(self, snapshot: WorkspaceContextSnapshot) -> None:
        if snapshot.save is None:
            load_failed = snapshot.save_state.value == 'error'
            self.header.save_context.set_context(
                snapshot.save_state.value,
                (tr('ui.save.state.load_failed', 'Save load failed')
                 if load_failed else tr('ui.save.no_save_title',
                                        'No save loaded')),
                (tr('ui.save.state.load_failed_detail',
                    'Choose a save to try again')
                 if load_failed else tr('ui.save.no_save_detail',
                                        'Open or drop a save to begin')),
            )
        else:
            state_labels = {
                'loaded': ('ui.save.state.saved', 'Saved'),
                'dirty': ('ui.save.state.unsaved', 'Unsaved'),
                'saving': ('ui.save.state.saving', 'Saving'),
                'error': ('ui.save.state.failed', 'Save failed'),
                'read_only': ('ui.save.state.read_only', 'Read only'),
                'backup_recommended': (
                    'ui.save.state.backup_recommended', 'Backup recommended'),
            }
            state_key, state_fallback = state_labels.get(
                snapshot.save_state.value,
                ('ui.save.state.loading', 'Loading'))
            self.header.save_context.set_context(
                snapshot.save_state.value,
                snapshot.save.display_name,
                f'{snapshot.save.platform.value.title()} · '
                f'{tr(state_key, state_fallback)}',
            )
        self.header.pending_changes.set_count(snapshot.pending_changes.count)
        items = [ContextItem(snapshot.current_route, snapshot.current_route.replace('_', ' ').title(), 'route')]
        for kind in ('player', 'guild', 'base', 'container'):
            selected = getattr(snapshot, kind)
            if selected is not None:
                items.append(ContextItem(selected.identifier, selected.label, kind))
        self.header.set_context_items(items)
        missing = {
            route.route_id: self._context.missing_prerequisites(route)
            for route in self._registry
        }
        self.sidebar.set_route_availability(missing)

    def set_inspector(
        self,
        widget: QWidget | None,
        *,
        title: str = '',
    ) -> None:
        if self._inspector is not None:
            self._inspector_side_layout.removeWidget(self._inspector)
            self.inspector_drawer.content_layout.removeWidget(self._inspector)
            self._inspector.hide()
            self._inspector.setParent(None)
        self._inspector = widget
        if title:
            self.inspector_drawer.title_label.setText(title)
            self.inspector_drawer.setAccessibleName(title)
        self._place_inspector()

    def _place_inspector(self) -> None:
        if self._inspector is None:
            self.inspector_side.hide()
            self.inspector_drawer.hide()
            return
        if self._inspector_compact:
            self._inspector_side_layout.removeWidget(self._inspector)
            self._inspector.setParent(self.inspector_drawer)
            self.inspector_drawer.content_layout.addWidget(self._inspector)
            self.inspector_side.hide()
            self.inspector_drawer.hide()
        else:
            self.inspector_drawer.content_layout.removeWidget(self._inspector)
            self._inspector.setParent(self.inspector_side)
            self._inspector_side_layout.addWidget(self._inspector)
            self.inspector_drawer.hide()
            self.inspector_side.show()
            self._inspector.show()

    def open_inspector(self, invoker: QWidget | None = None) -> None:
        if self._inspector is None:
            return
        if self._inspector_compact:
            self.inspector_drawer.setGeometry(
                max(0, self.content_frame.width() - LAYOUT['inspector_width']),
                0,
                min(LAYOUT['inspector_width'], self.content_frame.width()),
                self.content_frame.height(),
            )
            self.inspector_drawer.open(invoker)
        else:
            self.inspector_side.show()

    def splitter_sizes(self) -> tuple[int, ...]:
        return tuple(self.splitter.sizes())

    def restore_splitter_sizes(self, sizes) -> None:
        if (isinstance(sizes, (list, tuple)) and len(sizes) == 2
                and all(isinstance(value, int) and value >= 0 for value in sizes)
                and sum(sizes) > 0):
            self.splitter.setSizes(list(sizes))

    def resizeEvent(self, event) -> None:
        compact = event.size().width() <= self.COMPACT_INSPECTOR_WIDTH
        if compact != self._inspector_compact:
            self._inspector_compact = compact
            self.setProperty('inspectorMode', 'drawer' if compact else 'side')
            self._place_inspector()
        if self.inspector_drawer.isVisible():
            self.inspector_drawer.setGeometry(
                max(0, self.content_frame.width() - LAYOUT['inspector_width']),
                0,
                min(LAYOUT['inspector_width'], self.content_frame.width()),
                self.content_frame.height(),
            )
        super().resizeEvent(event)


__all__ = ['ShellTitleBar', 'WindowDragRegion', 'WorkspaceShell']
