from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from palworld_aio.ui.tabs.docs.wiki_tab import WikiTab

class DocsTab(QWidget):
    """Reference shelf (plan 015-r02, top-nav-shell 4.5): ribbon + reader
    stack. The single-item sub-tab bar is dropped."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

    def open_reference(self, category: str, identifier: str) -> bool:
        """Open one bundled-data record while preserving shell history."""
        self._switch_sub_tab('wiki')
        return self.wiki_tab.open_reference(category, identifier)
