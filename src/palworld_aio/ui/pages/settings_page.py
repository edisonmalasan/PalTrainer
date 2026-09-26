"""Application preferences workspace."""
from __future__ import annotations

from typing import Mapping, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QScrollArea, QVBoxLayout, QWidget,
)

from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING
from palworld_aio.ui.user_preferences import LANGUAGES, UserPreferences


_LANGUAGE_LABELS = {
    'en_US': 'English', 'zh_CN': '中文', 'ru_RU': 'Русский',
    'fr_FR': 'Français', 'es_ES': 'Español', 'de_DE': 'Deutsch',
    'ja_JP': '日本語', 'ko_KR': '한국어', 'pt_BR': 'Português (Brasil)',
    'pt_PT': 'Português (Portugal)',
}


class SettingsPage(QWidget):
    preferencesChanged = pyqtSignal(object)

    def __init__(
        self,
        settings: object = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName('settingsPage')
        self.setAccessibleName(tr('ui.settings.title', 'Settings'))
        self._restoring = False
        self._preserved = UserPreferences()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setObjectName('settingsScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        body.setObjectName('settingsBody')
        self.sections = QGridLayout(body)
        self.sections.setContentsMargins(0, 0, 0, 0)
        self.sections.setHorizontalSpacing(SPACING['lg'])
        self.sections.setVerticalSpacing(SPACING['lg'])

        general = self._section(
            'general', tr('ui.settings.general', 'General'),
            tr('ui.settings.general_help',
               'Language and what PalTrainer does when this workspace closes.'))
        self.language_combo = self._combo(
            general, tr('ui.settings.language', 'Language'),
            [(_LANGUAGE_LABELS[code], code) for code in LANGUAGES])
        self.boot_combo = self._combo(
            general, tr('ui.settings.startup', 'After closing this workspace'),
            [(tr('ui.settings.return_menu', 'Return to launcher'), 'menu'),
             (tr('ui.settings.exit_app', 'Exit PalTrainer'), 'palworld_aio')])

        appearance = self._section(
            'appearance', tr('ui.settings.appearance', 'Appearance'),
            tr('ui.settings.appearance_help',
               'Choose how progress and interface motion are presented.'))
        self.loading_combo = self._combo(
            appearance, tr('ui.settings.loading', 'Loading progress'),
            [(tr('ui.settings.loading_overlay', 'Full loading overlay'), 'overlay'),
             (tr('ui.settings.loading_header', 'Compact header status'), 'header')])
        self.reduced_motion_check = self._check(
            appearance, tr('ui.settings.reduced_motion', 'Reduce interface motion'))

        safety = self._section(
            'saveSafety', tr('ui.settings.save_safety', 'Save Safety'),
            tr('ui.settings.save_safety_help',
               'Keep recovery points and warnings around save-changing work.'))
        self.backup_check = self._check(
            safety, tr('ui.settings.backup_on_load',
                       'Create a full backup before loading a save'))
        self.unsaved_check = self._check(
            safety, tr('ui.settings.warn_unsaved',
                       'Warn before closing with unsaved changes'))

        advanced = self._section(
            'advanced', tr('ui.settings.advanced', 'Advanced'),
            tr('ui.settings.advanced_help',
               'Diagnostics and naming behavior used by editing workflows.'))
        self.name_mode_combo = self._combo(
            advanced, tr('ui.settings.pal_names', 'New Pal nickname'),
            [(tr('edit_pals.name_mode_new', 'New'), 'new'),
             (tr('edit_pals.name_mode_copy', '© Copy'), 'copy'),
             (tr('edit_pals.name_mode_none', 'No nickname'), 'none')])
        self.sync_nickname_check = self._check(
            advanced, tr('ui.settings.sync_nickname',
                         'Apply nickname during Bulk Sync'))
        self.console_check = self._check(
            advanced, tr('ui.settings.detach_console',
                         'Open diagnostics console in a separate window'))

        self._section_widgets = (general, appearance, safety, advanced)
        self._section_columns = 0
        self.sections.setColumnStretch(0, 1)
        self.sections.setColumnStretch(1, 1)
        self._reflow_sections(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

        self.status_label = QLabel(
            tr('ui.settings.saved_automatically', 'Changes are saved automatically.'),
            self)
        self.status_label.setObjectName('settingsStatus')
        self.status_label.setProperty('class', 'secondary')
        root.addWidget(self.status_label)

        for combo in (self.language_combo, self.boot_combo, self.loading_combo,
                      self.name_mode_combo):
            combo.currentIndexChanged.connect(self._emit_preferences)
        for check in (self.reduced_motion_check, self.backup_check,
                      self.unsaved_check, self.sync_nickname_check,
                      self.console_check):
            check.toggled.connect(self._emit_preferences)
        self.set_preferences(settings)

    def _section(self, role: str, title: str, description: str) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName('settingsSection')
        frame.setProperty('settingsRole', role)
        frame.setAccessibleName(title)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        layout.setSpacing(SPACING['md'])
        heading = QLabel(title, frame)
        heading.setObjectName('settingsSectionTitle')
        layout.addWidget(heading)
        help_label = QLabel(description, frame)
        help_label.setObjectName('settingsSectionHelp')
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        return frame

    def _combo(
        self,
        section: QFrame,
        label: str,
        options: list[tuple[str, str]],
    ) -> QComboBox:
        field = QWidget(section)
        row = QHBoxLayout(field)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING['md'])
        field_label = QLabel(label, field)
        field_label.setWordWrap(True)
        row.addWidget(field_label, 1)
        combo = QComboBox(field)
        combo.setMinimumWidth(170)
        combo.setAccessibleName(label)
        for text, value in options:
            combo.addItem(text, value)
        field_label.setBuddy(combo)
        row.addWidget(combo)
        section.layout().addWidget(field)
        return combo

    def _check(self, section: QFrame, label: str) -> QCheckBox:
        check = QCheckBox(label, section)
        check.setAccessibleName(label)
        section.layout().addWidget(check)
        return check

    def set_preferences(self, settings: object) -> None:
        preferences = UserPreferences.from_mapping(settings)
        self._preserved = preferences
        self._restoring = True
        try:
            self._select(self.language_combo, preferences.language)
            self._select(self.boot_combo, preferences.boot_preference)
            self._select(self.loading_combo, preferences.loading_screen_mode)
            self._select(
                self.name_mode_combo, preferences.pal_creation_name_mode)
            self.reduced_motion_check.setChecked(preferences.reduced_motion)
            self.backup_check.setChecked(preferences.automatic_backup_on_load)
            self.unsaved_check.setChecked(preferences.warn_unsaved_exit)
            self.sync_nickname_check.setChecked(
                preferences.bulk_sync_apply_nickname)
            self.console_check.setChecked(preferences.console_detached)
        finally:
            self._restoring = False

    @staticmethod
    def _select(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(max(0, index))

    def preferences(self) -> UserPreferences:
        return UserPreferences(
            language=str(self.language_combo.currentData()),
            boot_preference=str(self.boot_combo.currentData()),
            loading_screen_mode=str(self.loading_combo.currentData()),
            reduced_motion=self.reduced_motion_check.isChecked(),
            automatic_backup_on_load=self.backup_check.isChecked(),
            warn_unsaved_exit=self.unsaved_check.isChecked(),
            pal_creation_name_mode=str(self.name_mode_combo.currentData()),
            bulk_sync_apply_nickname=self.sync_nickname_check.isChecked(),
            console_detached=self.console_check.isChecked(),
            show_icons=self._preserved.show_icons,
            tray_expanded=self._preserved.tray_expanded,
            console_window_geometry=self._preserved.console_window_geometry,
        )

    def _emit_preferences(self, _value: object = None) -> None:
        if not self._restoring:
            self.preferencesChanged.emit(self.preferences().to_mapping())

    def _reflow_sections(self, columns: int) -> None:
        if columns == self._section_columns:
            return
        self._section_columns = columns
        for section in self._section_widgets:
            self.sections.removeWidget(section)
        for index, section in enumerate(self._section_widgets):
            self.sections.addWidget(section, index // columns, index % columns)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self._reflow_sections(2 if self.width() >= 1100 else 1)
        super().resizeEvent(a0)


__all__ = ['SettingsPage']
