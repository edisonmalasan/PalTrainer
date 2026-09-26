from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QPixmap
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


cards = import_from('palworld_aio.ui.chrome.content_cards')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def item_models(app):
    portrait = QPixmap(24, 24)
    portrait.fill(Qt.GlobalColor.red)
    return [
        cards.InventorySlotModel('0', 'Pal Sphere', 12, 2, portrait, 'equipped', 'ItemId::PalSphere'),
        cards.InventorySlotModel('1'),
    ]


@pytest.fixture
def pal_model(app):
    portrait = QPixmap(24, 24)
    portrait.fill(Qt.GlobalColor.blue)
    return cards.PalCardModel('pal-1', 'Lamball', 42, 'female', 'working', 3, portrait, 'PAL-TECH-1')


def test_inventory_slot_preserves_content_semantics(item_models):
    slot = cards.InventorySlot(item_models[0])
    assert slot.name_label.text() == 'Pal Sphere'
    assert slot.quantity_label.text() == '×12'
    assert slot.property('rarity') == 2
    assert slot.property('status') == 'equipped'
    assert slot.toolTip() == 'ItemId::PalSphere'
    assert not slot.portrait_label.pixmap().isNull()
    assert 'quantity 12' in slot.accessibleName()


def test_empty_inventory_slot_is_useful(item_models):
    slot = cards.InventorySlot(item_models[1])
    assert slot.property('empty') is True
    assert slot.name_label.text() == 'Empty slot'
    assert slot.accessibleName() == 'Empty inventory slot'


def test_inventory_slot_keyboard_activation_and_selection(item_models):
    slot = cards.InventorySlot(item_models[0])
    activated, selected = [], []
    slot.activated.connect(activated.append)
    slot.selectionChanged.connect(lambda slot_id, value: selected.append((slot_id, value)))
    slot.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier))
    assert slot.selected
    assert slot.property('selected') is True
    assert activated == ['0']
    assert selected == [('0', True)]


def test_inventory_grid_tracks_multi_selection(item_models):
    grid = cards.InventoryGrid(columns=2)
    grid.set_models(item_models)
    seen = []
    grid.selectionChanged.connect(seen.append)
    grid.slots[0].set_selected(True)
    grid.slots[1].set_selected(True)
    assert grid.selected_ids() == ('0', '1')
    grid.clear_selection()
    assert grid.selected_ids() == ()
    assert seen[-1] == ()
    with pytest.raises(ValueError):
        cards.InventoryGrid(columns=0)


def test_pal_card_preserves_identity_level_gender_status_and_portrait(pal_model):
    card = cards.PalCard(pal_model)
    assert card.name_label.text() == 'Lamball'
    assert card.level_label.text() == 'Lv. 42'
    assert card.property('gender') == 'female'
    assert card.property('status') == 'working'
    assert card.property('rarity') == 3
    assert card.toolTip() == 'PAL-TECH-1'
    assert not card.portrait_label.pixmap().isNull()


def test_pal_card_keyboard_selection_emits(pal_model):
    card = cards.PalCard(pal_model)
    seen = []
    card.selectionChanged.connect(lambda pal_id, selected: seen.append((pal_id, selected)))
    card.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
    assert card.selected
    assert card.property('selected') is True
    assert seen == [('pal-1', True)]


def test_content_models_reject_invalid_numbers(app):
    with pytest.raises(ValueError):
        cards.InventorySlot(cards.InventorySlotModel('bad', 'Bad', -1))
    with pytest.raises(ValueError):
        cards.PalCard(cards.PalCardModel('bad', 'Bad', -1))
