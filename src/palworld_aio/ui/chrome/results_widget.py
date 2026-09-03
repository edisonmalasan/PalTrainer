from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from i18n import t
from palworld_aio.widgets import StatsPanel
class ResultsWidget(QWidget):
    hide_requested = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('resultsWidget')
        self.is_dark_mode = True
        self._setup_ui()
    def refresh_labels(self):
        if hasattr(self, 'results_title'):
            self.results_title.setText(t('deletion.results_panel') if t else 'Selection & Stats')
        if hasattr(self, 'stats_title'):
            self.stats_title.setText(t('deletion.stats_panel') if t else 'Statistics')
        if hasattr(self, 'player_label'):
            self.player_label.setText(t('deletion.selected_player_label') if t else 'Selected Player:')
        if hasattr(self, 'guild_label'):
            self.guild_label.setText(t('deletion.selected_guild_label') if t else 'Selected Guild:')
        if hasattr(self, 'base_label'):
            self.base_label.setText(t('deletion.selected_base_label') if t else 'Selected Base:')
        if hasattr(self, 'stats_panel'):
            self.stats_panel.refresh_labels()
    def _setup_ui(self):
        self.setMinimumWidth(320)
        self.setMaximumWidth(480)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        self.results_title = QLabel(t('deletion.results_panel') if t else 'Selection & Stats')
        self.results_title.setObjectName('sectionHeader')
        self.results_title.setAlignment(Qt.AlignCenter)
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.results_title)
        self.close_btn = QPushButton('\u2715')
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setToolTip(t('sidebar.close') if t else 'Hide Results')
        self.close_btn.setObjectName('resultsCloseBtn')
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.hide_requested.emit)
        title_layout.addWidget(self.close_btn)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        separator = self._create_gradient_separator()
        layout.addWidget(separator)
        selection_frame = QFrame()
        selection_frame.setObjectName('glassPanel')
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setSpacing(8)
        selection_layout.addStretch()
        player_card = self._create_value_card(t('deletion.selected_player_label') if t else 'Selected Player:', 'player')
        self.player_value = player_card['value_label']
        self.player_label = player_card['label']
        selection_layout.addWidget(player_card['container'])
        guild_card = self._create_value_card(t('deletion.selected_guild_label') if t else 'Selected Guild:', 'guild')
        self.guild_value = guild_card['value_label']
        self.guild_label = guild_card['label']
        selection_layout.addWidget(guild_card['container'])
        base_card = self._create_value_card(t('deletion.selected_base_label') if t else 'Selected Base:', 'base')
        self.base_value = base_card['value_label']
        self.base_label = base_card['label']
        selection_layout.addWidget(base_card['container'])
        selection_layout.addStretch()
        layout.addWidget(selection_frame, stretch=1)
        separator2 = self._create_gradient_separator()
        layout.addWidget(separator2)
        self.stats_title = QLabel(t('deletion.stats_panel') if t else 'Statistics')
        self.stats_title.setObjectName('sectionHeader')
        self.stats_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_title)
        stats_frame = QFrame()
        stats_frame.setObjectName('glassPanel')
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.addStretch()
        self.stats_panel = StatsPanel()
        self.stats_panel.setObjectName('statsGrid')
        stats_layout.addWidget(self.stats_panel)
        stats_layout.addStretch()
        layout.addWidget(stats_frame, stretch=1)
    def _create_gradient_separator(self):
        separator = QFrame()
        separator.setObjectName('gradientSeparator')
        separator.setFrameShape(QFrame.HLine)
        separator.setMaximumHeight(2)
        return separator
    def _create_value_card(self, label_text, card_type):
        container = QFrame()
        container.setObjectName('valueCard')
        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName('statsField')
        card_layout.addWidget(label)
        value_label = QLabel('—')
        value_label.setObjectName('statsValue')
        value_label.setProperty('placeholder', 'true')
        value_label.setWordWrap(True)
        card_layout.addWidget(value_label)
        return {'container': container, 'value_label': value_label, 'label': label}
    def _set_value(self, label, name):
        if name:
            label.setText(str(name))
            label.setProperty('placeholder', 'false')
        else:
            label.setText('—')
            label.setProperty('placeholder', 'true')
        label.style().unpolish(label)
        label.style().polish(label)
    def set_player(self, name):
        self._set_value(self.player_value, name)
    def set_guild(self, name):
        self._set_value(self.guild_value, name)
    def set_base(self, base_id):
        self._set_value(self.base_value, base_id)
    def clear_selection(self):
        self.set_player(None)
        self.set_guild(None)
        self.set_base(None)
    def update_stats(self, stats):
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.update_stats(stats)
    def refresh_stats_before(self):
        from ...managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.refresh_stats_before(stats)
    def refresh_stats_after(self):
        from ...managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.refresh_stats_after(stats)