"""First-class About workspace."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from palworld_aio.application.system_info import ProductInfo, build_product_info
from palworld_aio.ui.chrome.components import make_badge, make_button
from palworld_aio.ui.chrome.localization import tr
from palworld_aio.ui.chrome.tokens import SPACING


class AboutPage(QWidget):
    projectRequested = pyqtSignal(str)
    updateCheckRequested = pyqtSignal()
    diagnosticsRequested = pyqtSignal()

    def __init__(
        self,
        info: ProductInfo | None = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.info = info or build_product_info()
        self.setObjectName('aboutPage')
        self.setAccessibleName(tr('about.title', 'About PalTrainer'))
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setObjectName('aboutScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        body.setObjectName('aboutBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['lg'])

        hero = QFrame(body)
        hero.setObjectName('aboutHero')
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(
            SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        hero_layout.setSpacing(SPACING['md'])
        title = QLabel(tr('about.title', 'About PalTrainer'), hero)
        title.setObjectName('aboutProductTitle')
        hero_layout.addWidget(title)
        description = QLabel(tr(
            'about.description',
            'A comprehensive toolkit for managing Palworld save files.'), hero)
        description.setObjectName('aboutDescription')
        description.setWordWrap(True)
        hero_layout.addWidget(description)
        versions = QHBoxLayout()
        versions.setSpacing(SPACING['sm'])
        self.app_badge = make_badge(
            tr('ui.about.app_version', 'PalTrainer {version}',
               version=self.info.app_version), 'accent', hero)
        self.game_badge = make_badge(
            tr('ui.about.game_version', 'Palworld {version}',
               version=self.info.game_version), 'neutral', hero)
        versions.addWidget(self.app_badge)
        versions.addWidget(self.game_badge)
        versions.addStretch(1)
        hero_layout.addLayout(versions)
        layout.addWidget(hero)

        self.details = QGridLayout()
        self.details.setSpacing(SPACING['lg'])
        self.features_card = self._card(
            tr('about.features.label', 'Features'),
            '\n'.join(f'• {tr(f"about.features.{index}", fallback)}'
                      for index, fallback in enumerate((
                          'Convert save files between different formats',
                          'Manage and modify save data',
                          'Transfer characters between saves',
                          'Fix common save issues',
                          'Restore map data',
                      ), start=1)), body)
        self.credits_card = self._card(
            tr('ui.about.credits', 'Credits'),
            tr('ui.about.credits_body',
               'Built and maintained by {developer}.\n\nPalTrainer is an '
               'independent community tool and is not affiliated with '
               'Pocketpair.', developer=self.info.developer), body)
        self._detail_columns = 0
        self._reflow_details(1)
        layout.addLayout(self.details)

        self.update_banner = QFrame(body)
        self.update_banner.setObjectName('systemUpdateBanner')
        self.update_banner.setProperty('status', 'neutral')
        update_layout = QHBoxLayout(self.update_banner)
        update_layout.setContentsMargins(
            SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        self.update_label = QLabel(
            tr('ui.about.update_ready', 'Ready to check for updates.'),
            self.update_banner)
        self.update_label.setWordWrap(True)
        update_layout.addWidget(self.update_label, 1)
        self.update_button = make_button(
            tr('base_inventory.check_updates', 'Check for Updates'),
            'secondary', parent=self.update_banner)
        self.update_button.clicked.connect(self._request_update)
        update_layout.addWidget(self.update_button)
        layout.addWidget(self.update_banner)

        actions = QHBoxLayout()
        self.project_button = make_button(
            tr('about.github', 'View on GitHub'), 'secondary',
            icon='external_link', parent=body)
        self.project_button.clicked.connect(
            lambda _checked=False: self.projectRequested.emit(self.info.project_url))
        actions.addWidget(self.project_button)
        self.diagnostics_button = make_button(
            tr('ui.about.open_diagnostics', 'Open Diagnostics'),
            'tertiary', icon='console', parent=body)
        self.diagnostics_button.clicked.connect(self.diagnosticsRequested.emit)
        actions.addWidget(self.diagnostics_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

    @staticmethod
    def _card(title: str, text: str, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName('aboutCard')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        heading = QLabel(title, card)
        heading.setObjectName('aboutCardTitle')
        card_layout.addWidget(heading)
        body = QLabel(text, card)
        body.setObjectName('aboutCardBody')
        body.setWordWrap(True)
        card_layout.addWidget(body, 1)
        return card

    def _request_update(self) -> None:
        self.set_update_state('checking')
        self.updateCheckRequested.emit()

    def set_update_state(
        self,
        status: str,
        *,
        current: str = '',
        latest: str = '',
        detail: str = '',
    ) -> None:
        copy = {
            'checking': tr('update.checking', 'Checking…'),
            'available': tr(
                'ui.about.update_available',
                'Update available: {current} → {latest}',
                current=current, latest=latest),
            'current': tr(
                'ui.about.up_to_date', 'PalTrainer {current} is up to date.',
                current=current),
            'error': detail or tr(
                'update.error.network',
                'Could not check for updates. Please try again later.'),
            'neutral': tr('ui.about.update_ready', 'Ready to check for updates.'),
        }
        resolved = status if status in copy else 'neutral'
        self.update_banner.setProperty('status', resolved)
        self.update_banner.style().unpolish(self.update_banner)
        self.update_banner.style().polish(self.update_banner)
        self.update_label.setText(copy[resolved])
        self.update_button.setEnabled(resolved != 'checking')

    def _reflow_details(self, columns: int) -> None:
        if columns == self._detail_columns:
            return
        self._detail_columns = columns
        for card in (self.features_card, self.credits_card):
            self.details.removeWidget(card)
        for index, card in enumerate((self.features_card, self.credits_card)):
            self.details.addWidget(card, index // columns, index % columns)
        self.details.setColumnStretch(0, 1)
        self.details.setColumnStretch(1, 1 if columns == 2 else 0)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self._reflow_details(2 if self.width() >= 900 else 1)
        super().resizeEvent(a0)


__all__ = ['AboutPage']
