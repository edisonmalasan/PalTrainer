from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from tests.dynamic_importer import import_from


def test_styled_combo_uses_shared_style_and_keyboard_selection():
    app = QApplication.instance() or QApplication([])
    combo = import_from('palworld_aio.ui.chrome.styled_combo').StyledCombo()
    combo.addItem('First', 'one')
    combo.addItem('Second', 'two')
    combo.show()
    app.processEvents()

    assert combo._button.objectName() == 'styledComboButton'
    assert combo._list.objectName() == 'styledComboList'
    assert combo._button.styleSheet() == ''
    assert combo._list.styleSheet() == ''
    assert combo._button.accessibleName() == 'First'

    combo._button.setFocus()
    QTest.keyClick(combo._button, Qt.Key.Key_Down)
    app.processEvents()
    assert combo._popup.isVisible()
    assert combo._list.hasFocus()
    QTest.keyClick(combo._list, Qt.Key.Key_Down)
    QTest.keyClick(combo._list, Qt.Key.Key_Return)
    app.processEvents()
    assert combo.currentData() == 'two'
    assert combo._button.accessibleName() == 'Second'
    assert not combo._popup.isVisible()
    assert combo._button.hasFocus()

    QTest.keyClick(combo._button, Qt.Key.Key_Down)
    app.processEvents()
    QTest.keyClick(combo._list, Qt.Key.Key_Escape)
    app.processEvents()
    assert combo.currentData() == 'two'
    assert not combo._popup.isVisible()
