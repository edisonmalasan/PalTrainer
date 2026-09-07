"""Focused tests for Player Inventory picker chip parity (uiux-audit-
remediation 6.4): the player selector matches Base Inventory's selectorChip
treatment, and the page ribbon caption reads EDITING.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

inventory_mod = import_from('palworld_aio.ui.tabs.inventory_tab')
qss_mod = import_from('palworld_aio.ui.chrome.qss_builder')
i18n_mod = import_from('i18n')

_app = None


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture(scope='session')
def app():
    return _app_instance()


@pytest.fixture
def tab(app):
    return inventory_mod.PlayerInventoryTab(None)


def test_player_picker_uses_selector_chip(tab):
    assert tab.player_select_btn.objectName() == 'selectorChip'
    assert tab.player_select_btn.objectName() != 'ghostBtn'


def test_player_picker_has_chevron_icon(tab):
    chevron = inventory_mod.app_icons.get_qicon('chevron_down',
                                                role='text_secondary')
    assert chevron is not None
    assert not chevron.pixmap(32, 32).isNull()
    assert not tab.player_select_btn.icon().pixmap(32, 32).isNull()
    assert (tab.player_select_btn.icon().pixmap(32, 32).toImage()
            == chevron.pixmap(32, 32).toImage())


def test_picker_selected_rule_covers_selector_chip(app):
    """set_picker_selected stays effective: the QSS builder ships the
    selectorChip[pickerSelected="true"] accent rule."""
    qss = qss_mod.build_qss('dark')
    assert 'QPushButton#selectorChip[pickerSelected="true"]' in qss
    components_mod = import_from('palworld_aio.ui.chrome.components')
    tab = inventory_mod.PlayerInventoryTab(None)
    components_mod.set_picker_selected(tab.player_select_btn, True)
    assert tab.player_select_btn.property('pickerSelected') == 'true'
    components_mod.set_picker_selected(tab.player_select_btn, False)
    assert tab.player_select_btn.property('pickerSelected') is None


def test_ribbon_caption_reads_editing(tab):
    from PyQt6.QtWidgets import QLabel
    texts = [lbl.text() for lbl in tab.findChildren(QLabel)]
    assert 'EDITING' in texts
    assert 'WORLD DATA' not in texts


def test_popup_handler_unchanged(tab, app):
    """The picker still opens through the existing popup flow."""
    assert callable(tab._open_player_popup)
    meta = tab.player_select_btn.metaObject()
    clicked = meta.method(meta.indexOfMethod('clicked()'))
    assert tab.player_select_btn.isSignalConnected(clicked)
