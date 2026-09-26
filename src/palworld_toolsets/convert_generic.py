"""SAV/JSON file conversion with explicit source, target, and result state."""
from __future__ import annotations

import gc
import os
import sys

from PyQt6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLineEdit

from i18n import t
from loading_manager import run_with_loading
from palsav.commands.convert import main as convert_main
from palworld_aio.ui.chrome.components import BaseDialog, BulkWorkflowReview, make_button


def convert_sav_to_json(input_file: str, output_file: str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = ['convert', input_file, '--output', output_file, '--force']
        convert_main()
    finally:
        sys.argv = old_argv


def convert_json_to_sav(input_file: str, output_file: str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = ['convert', input_file, '--output', output_file, '--force']
        convert_main()
    finally:
        sys.argv = old_argv


def default_output_path(input_file: str, target_extension: str) -> str:
    root, _extension = os.path.splitext(input_file)
    return root + ('.sav' if target_extension == 'sav' else '.json')


def file_picker(ext: str, parent=None) -> str:
    if ext == 'sav':
        path, _ = QFileDialog.getOpenFileName(
            parent, t('tool.convert.select_json', default='Select JSON File'),
            '', 'JSON Files (*.json)')
    else:
        path, _ = QFileDialog.getOpenFileName(
            parent, t('tool.convert.select_sav', default='Select SAV File'),
            '', 'SAV Files (*.sav)')
    return path


class SaveConversionDialog(BaseDialog):
    def __init__(self, target_extension: str, parent=None):
        if target_extension not in {'sav', 'json'}:
            raise ValueError('target extension must be sav or json')
        self.target_extension = target_extension
        self.source_extension = 'json' if target_extension == 'sav' else 'sav'
        self.success = False
        super().__init__(
            t('tool.convert.saves'), parent, min_size=(720, 390),
            kicker=t('tools.section.converting', default='Conversion'))
        self.workflow_review = BulkWorkflowReview(
            source=t('tool.convert.source_missing', default='Choose a source file'),
            target=t('tool.convert.target_missing', default='Target is derived from the source'),
            review=t(
                'tool.convert.review_safe',
                default='The source remains unchanged; output is written to a separate file.'),
            parent=self,
        )
        self.workflow_review.set_risk('', t(
            'tool.convert.backup_note',
            default='The converter does not overwrite the selected source file.'))
        self.content_layout.addWidget(self.workflow_review)

        self.source_entry = QLineEdit(self)
        self.source_entry.setReadOnly(True)
        self.source_entry.setPlaceholderText(t(
            'tool.convert.source_missing', default='Choose a source file'))
        source_row = QHBoxLayout()
        source_row.addWidget(self.source_entry, 1)
        self.source_button = make_button(
            t('tool.convert.choose_source', default='Choose source'),
            'secondary', parent=self)
        self.source_button.clicked.connect(self.choose_source)
        source_row.addWidget(self.source_button)
        self.content_layout.addLayout(source_row)

        self.target_entry = QLineEdit(self)
        self.target_entry.setReadOnly(True)
        self.target_entry.setPlaceholderText(t(
            'tool.convert.target_missing', default='Target is derived from the source'))
        target_row = QHBoxLayout()
        target_row.addWidget(self.target_entry, 1)
        self.target_button = make_button(
            t('tool.convert.choose_target', default='Choose target'),
            'tertiary', parent=self)
        self.target_button.clicked.connect(self.choose_target)
        target_row.addWidget(self.target_button)
        self.content_layout.addLayout(target_row)

        self.convert_button = make_button(
            t('steamid.btn.convert', default='Convert'), 'primary', parent=self)
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self.start_conversion)
        self.footer.insertWidget(self.footer.count() - 1, self.convert_button)
        self._primary_button = self.source_button

    def set_source(self, path: str) -> bool:
        normalized = os.path.abspath(path) if path else ''
        if not normalized:
            return False
        if os.path.splitext(normalized)[1].casefold() != f'.{self.source_extension}':
            self.workflow_review.set_result(t(
                'tool.convert.invalid_source',
                default='Choose a {extension} source file.',
                extension=self.source_extension.upper()), success=False)
            return False
        if not os.path.isfile(normalized):
            self.workflow_review.set_result(t(
                'tool.convert.source_not_found',
                default='The selected source file does not exist.'),
                success=False)
            return False
        self.source_entry.setText(normalized)
        self.target_entry.setText(default_output_path(
            normalized, self.target_extension))
        self._sync_review()
        self.convert_button.setEnabled(True)
        self._primary_button = self.convert_button
        return True

    def choose_source(self) -> None:
        selected = file_picker(self.target_extension, self)
        if not selected:
            self.workflow_review.set_result(t(
                'tool.convert.cancelled', default='Cancelled. No files were changed.'),
                success=True)
            return
        self.set_source(selected)

    def choose_target(self) -> None:
        source = self.source_entry.text()
        initial = self.target_entry.text() or default_output_path(
            source, self.target_extension)
        selected, _ = QFileDialog.getSaveFileName(
            self,
            t('tool.convert.choose_target', default='Choose target'),
            initial,
            ('SAV Files (*.sav)' if self.target_extension == 'sav'
             else 'JSON Files (*.json)'),
        )
        if not selected:
            return
        self.target_entry.setText(selected)
        self._sync_review()

    def _sync_review(self) -> None:
        self.workflow_review.set_context(
            source=self.source_entry.text(),
            target=self.target_entry.text(),
            review=t(
                'tool.convert.review_safe',
                default='The source remains unchanged; output is written to a separate file.'),
        )

    def _convert(self) -> str:
        source = self.source_entry.text()
        target = self.target_entry.text()
        if self.target_extension == 'sav':
            convert_json_to_sav(source, target)
        else:
            convert_sav_to_json(source, target)
        gc.collect()
        return target

    def start_conversion(self) -> bool:
        source = self.source_entry.text()
        target = self.target_entry.text()
        if not source or not target:
            self.workflow_review.set_result(t(
                'tool.convert.source_missing', default='Choose a source file'),
                success=False)
            return False
        self.convert_button.setEnabled(False)
        self.workflow_review.set_progress(
            0, 1, t('tool.convert.running', default='Converting…'))

        def on_done(output_path):
            self.success = True
            self.convert_button.setEnabled(True)
            self.workflow_review.set_progress(
                1, 1, t('tool.convert.complete', default='Conversion complete'))
            self.workflow_review.set_result(t(
                'tool.convert.level_done', source=source, target=output_path),
                success=True)

        def on_error(error):
            self.success = False
            self.convert_button.setEnabled(True)
            self.workflow_review.set_result(t(
                'tool.convert.failed',
                default='Conversion failed. The source file was not changed. {detail}',
                detail=str(error)), success=False)

        run_with_loading(
            on_done, self._convert, parent=self, on_error=on_error,
            local_state=True)
        return True


def convert_generic(ext: str) -> bool:
    dialog = SaveConversionDialog(ext, QApplication.activeWindow())
    dialog.exec()
    return dialog.success


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {'sav', 'json'}:
        raise SystemExit('Usage: script.py <sav|json>')
    convert_generic(sys.argv[1])


if __name__ == '__main__':
    main()
