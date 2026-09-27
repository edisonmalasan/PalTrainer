from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from tests.dynamic_importer import import_from


def test_toggle_check_has_keyboard_focus_and_shared_checked_style():
    app = QApplication.instance() or QApplication([])
    widget = import_from('palworld_aio.widgets.toggle_check').ToggleCheckBtn(
        'Include item')
    widget.show()
    app.processEvents()
    button = widget._icon_btn
    assert button.objectName() == 'toggleCheckButton'
    assert button.styleSheet() == ''
    assert button.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert button.accessibleName() == 'Include item'

    toggles = []
    widget.toggled.connect(toggles.append)
    button.setFocus()
    QTest.keyClick(button, Qt.Key.Key_Space)
    assert widget.isChecked()
    assert button.isChecked()
    assert toggles == [True]

    widget.setText('Include Pal')
    assert button.accessibleName() == 'Include Pal'
    widget.setChecked(False)
    assert not button.isChecked()
    assert toggles == [True]
