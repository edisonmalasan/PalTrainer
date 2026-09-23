from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication, QPushButton

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


page_mod = import_from('palworld_aio.ui.pages.diagnostics_page')
system_info = import_from('palworld_aio.application.system_info')
_APP = None


@pytest.fixture(scope='module')
def app():
    global _APP
    _APP = QApplication.instance() or QApplication([])
    return _APP


def _page():
    return page_mod.DiagnosticsPage(system_info.DiagnosticsInfo(
        app_version='2.4.0', game_version='1.0.3', python_version='3.13.0',
        qt_version='6.9.0', pyqt_version='6.9.0', operating_system='Fixture OS',
        architecture='x86_64', packaged=False,
        paths={'application': 'C:/PalTrainer', 'configuration': 'C:/Config'},
    ))


def test_report_excludes_console_until_explicit_opt_in(app):
    page = _page()
    secret = 'SAVE_CONTENT_MARKER_9157'
    page.set_console_text(f'Raw parser output {secret}')
    assert secret not in page.report_text()
    assert 'console output are excluded' in page.report_text()
    page.include_console_check.setChecked(True)
    assert secret in page.report_text()
    assert 'user included' in page.report_text()


def test_copy_export_reveal_detach_and_update_actions_emit(app):
    page = _page()
    copied, exported, revealed = [], [], []
    detached, updates = [], []
    page.copyRequested.connect(copied.append)
    page.exportRequested.connect(exported.append)
    page.revealPathRequested.connect(revealed.append)
    page.detachConsoleRequested.connect(lambda: detached.append(True))
    page.updateCheckRequested.connect(lambda: updates.append(True))

    page.copy_button.click()
    page.export_button.click()
    open_buttons = [
        button for button in page.findChildren(QPushButton)
        if button.text() == 'Open'
    ]
    open_buttons[0].click()
    page.detach_button.click()
    page.update_button.click()
    assert copied and copied[0] == page.report_text()
    assert exported and exported[0] == page.report_text()
    assert revealed == ['C:/PalTrainer']
    assert detached == [True]
    assert updates == [True]


def test_console_and_result_states_are_bounded_and_explicit(app):
    page = _page()
    page.set_console_text('x' * (page.MAX_CONSOLE_CHARS + 10))
    assert len(page.console_output.toPlainText()) == page.MAX_CONSOLE_CHARS
    page.set_console_detached(True)
    assert page.detach_button.text() == 'Reattach'
    page.set_result('Copied', 'success')
    assert page.result_label.text() == 'Copied'
    assert page.result_label.property('status') == 'success'
    page.set_update_warning('Update check failed')
    assert page.result_label.property('status') == 'warning'
