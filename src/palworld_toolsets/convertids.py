"""Steam/Palworld identifier conversion on the shared dialog scaffold."""
from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLineEdit

from i18n import t
from palobject import PlayerUid2NoSteam, steamIdToPlayerUid, toUUID
from palworld_aio.ui.chrome.components import BaseDialog, BulkWorkflowReview, make_button


def normalize_steam_id(value: str) -> int:
    """Accept a raw ID, ``steam_`` value, or Steam community profile URL."""
    cleaned = value.strip()
    marker = 'steamcommunity.com/profiles/'
    if marker in cleaned:
        cleaned = cleaned.split(marker, 1)[1].split('/', 1)[0]
    elif cleaned.casefold().startswith('steam_'):
        cleaned = cleaned[6:]
    if not cleaned or not cleaned.isdecimal():
        raise ValueError('invalid Steam ID')
    return int(cleaned)


def convert_identifier(value: str) -> tuple[str, str]:
    steam_id = normalize_steam_id(value)
    palworld_uid = steamIdToPlayerUid(steam_id)
    nosteam_uid = (
        PlayerUid2NoSteam(int.from_bytes(
            toUUID(palworld_uid).raw_bytes[0:4], byteorder='little'))
        + '-0000-0000-0000-000000000000'
    )
    return str(palworld_uid).upper(), nosteam_uid.upper()


class SteamIdConversionDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(
            t('steamid.title'), parent, min_size=(600, 340),
            kicker=t('tools.section.converting', default='Conversion'))
        self.result_text = ''
        self.workflow_review = BulkWorkflowReview(
            source=t('steamid.source_prompt', default='Steam ID or profile URL'),
            target=t('steamid.target_summary', default='Palworld UID and non-Steam UID'),
            review=t('steamid.review', default='This calculation does not modify save files.'),
            parent=self,
        )
        self.workflow_review.set_risk('', t(
            'steamid.safe', default='Read-only conversion; no backup is required.'))
        self.content_layout.addWidget(self.workflow_review)

        row = QHBoxLayout()
        self.steam_entry = QLineEdit(self)
        self.steam_entry.setPlaceholderText(t(
            'steamid.placeholder', default='Enter Steam ID or profile URL'))
        self.steam_entry.setAccessibleName(t(
            'steamid.input_accessible', default='Steam identifier'))
        self.steam_entry.returnPressed.connect(self.convert_input)
        row.addWidget(self.steam_entry, 1)
        self.convert_button = make_button(
            t('steamid.btn.convert'), 'primary', parent=self)
        self.convert_button.clicked.connect(self.convert_input)
        row.addWidget(self.convert_button)
        self.content_layout.addLayout(row)

        self.copy_button = make_button(
            t('steamid.copy', default='Copy result'), 'secondary',
            icon='copy', parent=self)
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_result)
        self.footer.insertWidget(self.footer.count() - 1, self.copy_button)
        self._primary_button = self.convert_button

    def convert_input(self) -> bool:
        value = self.steam_entry.text()
        if not value.strip():
            self.workflow_review.set_result(t(
                'steamid.warn.enter_id'), success=False)
            self.copy_button.setEnabled(False)
            return False
        try:
            palworld_uid, nosteam_uid = convert_identifier(value)
        except (TypeError, ValueError, OverflowError):
            self.workflow_review.set_result(t('steamid.err.invalid'), success=False)
            self.copy_button.setEnabled(False)
            return False
        self.result_text = t(
            'steamid.result', pal=palworld_uid, nosteam=nosteam_uid)
        self.workflow_review.set_context(
            source=str(normalize_steam_id(value)),
            target=f'{palworld_uid} / {nosteam_uid}',
            review=t('steamid.review', default='This calculation does not modify save files.'),
        )
        self.workflow_review.set_progress(1, 1, t(
            'steamid.complete', default='Conversion complete'))
        self.workflow_review.set_result(self.result_text, success=True)
        self.copy_button.setEnabled(True)
        return True

    def copy_result(self) -> None:
        if not self.result_text:
            return
        QApplication.clipboard().setText(self.result_text)
        self.copy_button.setText(t('steamid.copied', default='Copied'))
        QTimer.singleShot(
            2000,
            lambda: self.copy_button.setText(t('steamid.copy', default='Copy result')),
        )


def convert_steam_id(parent=None):
    return SteamIdConversionDialog(parent or QApplication.activeWindow())


def main():
    app = QApplication.instance() or QApplication([])
    dialog = convert_steam_id()
    dialog.show()
    app.exec()


if __name__ == '__main__':
    main()
