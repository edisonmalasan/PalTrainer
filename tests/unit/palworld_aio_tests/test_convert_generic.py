"""SAV/JSON conversion workflow success, cancel, and failure paths."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

module = import_from('palworld_toolsets.convert_generic')
components = import_from('palworld_aio.ui.chrome.components')
i18n = import_from('i18n')

_app = None


@pytest.fixture(scope='session', autouse=True)
def _locale():
    i18n.load_resources('en_US')


@pytest.fixture(scope='session')
def app():
    global _app
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    return _app


def _run_synchronously(callback, function, *args, on_error=None, **_kwargs):
    try:
        callback(function(*args))
    except Exception as error:
        if on_error is not None:
            on_error(error)


def test_dialog_derives_separate_target_and_uses_shared_review(app, tmp_path):
    source = tmp_path / 'Level.sav'
    source.write_bytes(b'fixture')
    dialog = module.SaveConversionDialog('json')

    assert isinstance(dialog, components.BaseDialog)
    assert dialog.set_source(str(source))
    assert dialog.target_entry.text() == str(tmp_path / 'Level.json')
    assert dialog.source_entry.text() != dialog.target_entry.text()
    assert dialog.convert_button.isEnabled()


def test_cancelled_picker_reports_no_change(app, monkeypatch):
    dialog = module.SaveConversionDialog('json')
    monkeypatch.setattr(module, 'file_picker', lambda *_args, **_kwargs: '')
    dialog.choose_source()
    assert dialog.source_entry.text() == ''
    assert 'No files were changed' in dialog.workflow_review.result_label.text()


def test_success_path_reports_output(app, monkeypatch, tmp_path):
    source = tmp_path / 'Level.sav'
    source.write_bytes(b'fixture')
    dialog = module.SaveConversionDialog('json')
    assert dialog.set_source(str(source))
    monkeypatch.setattr(module, 'run_with_loading', _run_synchronously)
    monkeypatch.setattr(
        module, 'convert_sav_to_json',
        lambda _source, target: Path(target).write_text('{}', encoding='utf-8'),
    )

    assert dialog.start_conversion()
    assert dialog.success
    assert os.path.isfile(dialog.target_entry.text())
    assert dialog.workflow_review.result_label.property('resultState') == 'success'


def test_failure_keeps_source_and_reports_unchanged(app, monkeypatch, tmp_path):
    source = tmp_path / 'Level.sav'
    source.write_bytes(b'original')
    dialog = module.SaveConversionDialog('json')
    assert dialog.set_source(str(source))
    monkeypatch.setattr(module, 'run_with_loading', _run_synchronously)

    def fail(_source, _target):
        raise RuntimeError('fixture failure')

    monkeypatch.setattr(module, 'convert_sav_to_json', fail)
    assert dialog.start_conversion()
    assert not dialog.success
    assert source.read_bytes() == b'original'
    assert 'source file was not changed' in dialog.workflow_review.result_label.text()
    assert dialog.workflow_review.result_label.property('resultState') == 'error'


def test_invalid_or_missing_source_is_rejected(app, tmp_path):
    dialog = module.SaveConversionDialog('json')
    assert not dialog.set_source(str(tmp_path / 'Level.json'))
    assert not dialog.set_source(str(tmp_path / 'Missing.sav'))
    assert not dialog.convert_button.isEnabled()


def test_existing_converter_callback_contract_restores_argv(monkeypatch):
    original = list(sys.argv)
    observed = []

    def converter():
        observed.append(tuple(sys.argv))

    monkeypatch.setattr(module, 'convert_main', converter)
    module.convert_sav_to_json('Level.sav', 'Level.json')
    assert observed == [(
        'convert', 'Level.sav', '--output', 'Level.json', '--force')]
    assert sys.argv == original
