"""Shared inventory slot/grid and Pal card presentation primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from palworld_aio.ui.chrome.tokens import SPACING
from palworld_aio.ui.chrome.localization import tr


@dataclass(frozen=True)
class InventorySlotModel:
    slot_id: str
    name: str = ''
    quantity: int = 0
    rarity: int = 0
    portrait: Optional[QPixmap] = None
    status: str = ''
    technical_id: str = ''
    description: str = ''
    badge: str = ''
    slot_label: str = ''


@dataclass(frozen=True)
class PalCardModel:
    pal_id: str
    name: str
    level: int
    gender: str = 'unknown'
    status: str = ''
    rarity: int = 0
    portrait: Optional[QPixmap] = None
    technical_id: str = ''


def apply_pal_card_semantics(widget: QWidget, model: PalCardModel) -> None:
    """Apply the shared Pal-card state/accessibility contract to any Pal view.

    Editors keep their richer drag/drop and badge rendering, while this helper
    ensures cards and editable slots expose the same semantic properties.
    """
    if model.level < 0 or model.rarity < 0:
        raise ValueError('level and rarity cannot be negative')
    widget.setProperty('cardRole', 'pal')
    widget.setProperty('empty', model.status == 'empty')
    widget.setProperty('gender', model.gender)
    widget.setProperty('status', model.status or 'normal')
    widget.setProperty('rarity', min(model.rarity, 4))
    if model.status == 'empty':
        widget.setAccessibleName(model.name)
    else:
        widget.setAccessibleName(tr(
            'ui.pal.card_accessible',
            '{name}, level {level}, {gender}{status}',
            name=model.name,
            level=model.level,
            gender=model.gender,
            status=f', {model.status}' if model.status else '',
        ))
    if model.technical_id:
        widget.setToolTip(model.technical_id)


class InventorySlot(QFrame):
    activated = pyqtSignal(str)
    selectionChanged = pyqtSignal(str, bool)

    def __init__(self, model: InventorySlotModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('auditInventorySlot')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._selected = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        layout.setSpacing(SPACING['xs'])
        self.portrait_label = QLabel(self)
        self.portrait_label.setObjectName('slotPortrait')
        self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.portrait_label.setMinimumSize(40, 40)
        self.name_label = QLabel(self)
        self.name_label.setObjectName('slotName')
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.quantity_label = QLabel(self)
        self.quantity_label.setObjectName('slotQuantity')
        self.quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label = QLabel(self)
        self.badge_label.setObjectName('slotBadge')
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.portrait_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(SPACING['xs'])
        meta_row.addWidget(self.badge_label)
        meta_row.addStretch(1)
        meta_row.addWidget(self.quantity_label)
        layout.addLayout(meta_row)
        self.set_model(model)

    @property
    def model(self) -> InventorySlotModel:
        return self._model

    @property
    def selected(self) -> bool:
        return self._selected

    def set_model(self, model: InventorySlotModel) -> None:
        if model.quantity < 0 or model.rarity < 0:
            raise ValueError('quantity and rarity cannot be negative')
        self._model = model
        occupied = bool(model.name)
        self.setProperty('empty', not occupied)
        self.setProperty('rarity', min(model.rarity, 4))
        self.quantity_label.setProperty('rarity', min(model.rarity, 4))
        self.setProperty('status', model.status or 'normal')
        empty_slot = model.slot_label or tr('ui.inventory.empty_slot', 'Empty slot')
        self._full_name = model.name or empty_slot
        self._update_elided_name()
        self.name_label.setToolTip(model.name or empty_slot)
        self.quantity_label.setText(f'×{model.quantity}' if occupied else '')
        self.badge_label.setText(model.badge)
        self.badge_label.setVisible(bool(model.badge))
        self.portrait_label.clear()
        if model.portrait is not None and not model.portrait.isNull():
            self.portrait_label.setPixmap(model.portrait)
        detail = model.technical_id or model.name or empty_slot
        if model.description:
            detail = (
                f'<b>{model.name or empty_slot}</b><br>'
                f'{model.technical_id}<br><br>{model.description}')
        self.setToolTip(detail)
        empty_accessible = (
            tr(
                'ui.inventory.named_empty_slot_accessible',
                '{slot} is empty',
                slot=empty_slot,
            ) if model.slot_label else tr(
                'ui.inventory.empty_slot_accessible',
                'Empty inventory slot',
            )
        )
        self.setAccessibleName(
            empty_accessible if not occupied else tr(
                'ui.inventory.slot_accessible',
                '{name}, quantity {quantity}, rarity {rarity}',
                name=model.name, quantity=model.quantity, rarity=model.rarity,
            )
        )
        self._polish()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_elided_name()

    def _update_elided_name(self) -> None:
        if not hasattr(self, '_full_name'):
            return
        width = max(32, self.width() - (SPACING['sm'] * 2))
        self.name_label.setText(self.name_label.fontMetrics().elidedText(
            self._full_name, Qt.TextElideMode.ElideRight, width))

    def set_selected(self, selected: bool, *, emit: bool = True) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self.setProperty('selected', selected)
        self._polish()
        if emit:
            self.selectionChanged.emit(self._model.slot_id, selected)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(not self._selected)
            self.activated.emit(self._model.slot_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.set_selected(not self._selected)
            self.activated.emit(self._model.slot_id)
            event.accept()
            return
        super().keyPressEvent(event)

    def _polish(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class InventoryGrid(QWidget):
    slotActivated = pyqtSignal(str)
    selectionChanged = pyqtSignal(object)

    def __init__(self, columns: int = 6, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if columns < 1:
            raise ValueError('inventory grid columns must be positive')
        self.setObjectName('auditInventoryGrid')
        self.columns = columns
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(SPACING['sm'])
        self._layout.setVerticalSpacing(SPACING['sm'])
        for column in range(columns):
            self._layout.setColumnStretch(column, 1)
        self.slots: list[InventorySlot] = []

    @property
    def grid_layout(self) -> QGridLayout:
        return self._layout

    def place_slot(self, slot: InventorySlot, position: int) -> None:
        self._layout.addWidget(
            slot, position // self.columns, position % self.columns)

    def set_models(self, models: Sequence[InventorySlotModel]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.slots = []
        for index, model in enumerate(models):
            slot = InventorySlot(model, self)
            slot.activated.connect(self.slotActivated.emit)
            slot.selectionChanged.connect(self._on_selection_changed)
            self.slots.append(slot)
            self.place_slot(slot, index)

    def selected_ids(self) -> tuple[str, ...]:
        return tuple(slot.model.slot_id for slot in self.slots if slot.selected)

    def clear_selection(self) -> None:
        for slot in self.slots:
            slot.set_selected(False, emit=False)
        self.selectionChanged.emit(self.selected_ids())

    def _on_selection_changed(self, _slot_id: str, _selected: bool) -> None:
        self.selectionChanged.emit(self.selected_ids())


class PalCard(QFrame):
    activated = pyqtSignal(str)
    selectionChanged = pyqtSignal(str, bool)

    def __init__(self, model: PalCardModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('auditPalCard')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._selected = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        layout.setSpacing(SPACING['sm'])
        self.portrait_label = QLabel(self)
        self.portrait_label.setObjectName('palCardPortrait')
        self.portrait_label.setFixedSize(48, 48)
        self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.portrait_label)
        detail = QVBoxLayout()
        detail.setSpacing(SPACING['xs'])
        title_row = QHBoxLayout()
        self.name_label = QLabel(self)
        self.name_label.setObjectName('palCardName')
        self.level_label = QLabel(self)
        self.level_label.setObjectName('palCardLevel')
        title_row.addWidget(self.name_label, 1)
        title_row.addWidget(self.level_label)
        detail.addLayout(title_row)
        self.meta_label = QLabel(self)
        self.meta_label.setObjectName('palCardMeta')
        detail.addWidget(self.meta_label)
        layout.addLayout(detail, 1)
        self.set_model(model)

    @property
    def model(self) -> PalCardModel:
        return self._model

    @property
    def selected(self) -> bool:
        return self._selected

    def set_model(self, model: PalCardModel) -> None:
        self._model = model
        apply_pal_card_semantics(self, model)
        self.level_label.setProperty('rarity', min(model.rarity, 4))
        self.name_label.setText(model.name)
        self.level_label.setText(f'Lv. {model.level}')
        self.meta_label.setText(' · '.join(part for part in (model.gender.title(), model.status) if part))
        self.portrait_label.clear()
        if model.portrait is not None and not model.portrait.isNull():
            self.portrait_label.setPixmap(model.portrait)
        self.setToolTip(model.technical_id or model.pal_id)
        self._polish()

    def set_selected(self, selected: bool, *, emit: bool = True) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self.setProperty('selected', selected)
        self._polish()
        if emit:
            self.selectionChanged.emit(self._model.pal_id, selected)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(not self._selected)
            self.activated.emit(self._model.pal_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.set_selected(not self._selected)
            self.activated.emit(self._model.pal_id)
            event.accept()
            return
        super().keyPressEvent(event)

    def _polish(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
