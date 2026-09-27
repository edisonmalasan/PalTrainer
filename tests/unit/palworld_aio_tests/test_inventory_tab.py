from __future__ import annotations

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


def test_capture_indicator_uses_bundled_icon_for_caught_pals():
    from PyQt6.QtWidgets import QApplication, QLabel

    app = QApplication.instance() or QApplication(sys.argv)
    panel = import_from('palworld_aio.ui.tabs.inventory_tab').PalpediaPanelWidget
    label = QLabel()

    panel._set_capture_indicator(label, 1)
    assert label.pixmap() is not None
    assert not label.pixmap().isNull()
    assert label.text() == ''

    panel._set_capture_indicator(label, 5)
    assert label.pixmap() is not None
    assert not label.pixmap().isNull()

    panel._set_capture_indicator(label, 0)
    assert label.pixmap() is None or label.pixmap().isNull()
    assert label.text() == ''
    label.deleteLater()
    assert app is not None
