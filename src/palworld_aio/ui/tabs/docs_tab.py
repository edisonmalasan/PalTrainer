from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from palworld_aio import constants
from i18n import t
from palworld_aio.ui.tabs.docs.wiki_tab import WikiTab

class DocsTab(QWidget):
    """Reference shelf (plan 015-r02, top-nav-shell 4.5): ribbon + reader
    stack. The single-item sub-tab bar is dropped."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._setup_ui()

    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import create_page_ribbon
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # top-nav-shell 4.5: the single-item sub-tab bar is dropped; the
        # ribbon carries the page identity. WikiTab fills the page.
        layout.addWidget(create_page_ribbon(t('docs.tab') if t else 'Docs', (t('sidebar.section.reference') if t else 'Reference').upper(), self))

        self._sub_stack = QStackedWidget()
        self.wiki_tab = WikiTab(self)
        self._sub_stack.addWidget(self.wiki_tab)
        layout.addWidget(self._sub_stack, 1)

    def _switch_sub_tab(self, tab_id):
        idx = {'wiki': 0}.get(tab_id, 0)
        self._sub_stack.setCurrentIndex(idx)

    def refresh(self):
        self.wiki_tab.refresh()

    def refresh_labels(self):
        self.wiki_tab.refresh_labels()
