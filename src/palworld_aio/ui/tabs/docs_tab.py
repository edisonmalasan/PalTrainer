from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from palworld_aio import constants
from i18n import t
from palworld_aio.ui.tabs.docs.wiki_tab import WikiTab

class DocsTab(QWidget):
    """Reference shelf (plan 015-r02): ribbon + tokenized sub-tab switch +
    reader stack. The old inline _SUB_TAB_STYLE (cyan hardcodes) is retired —
    presentation comes from the shared pageSwitchBtn grammar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._setup_ui()

    def _setup_ui(self):
        from palworld_aio.ui.chrome.components import create_page_ribbon
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(create_page_ribbon(t('docs.tab') if t else 'Docs', (t('sidebar.section.reference') if t else 'Reference').upper(), self))

        sub_tab_bar = QHBoxLayout()
        sub_tab_bar.setContentsMargins(16, 6, 170, 6)
        sub_tab_bar.setSpacing(6)

        self._sub_btns = {}
        for sid, skey in [('wiki', 'docs.wiki')]:
            btn = QPushButton(t(skey) if t else skey)
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setObjectName('pageSwitchBtn')
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, s=sid: self._switch_sub_tab(s))
            self._sub_btns[sid] = btn
            sub_tab_bar.addWidget(btn)

        sub_tab_bar.addStretch()
        layout.addLayout(sub_tab_bar)

        self._sub_stack = QStackedWidget()
        self.wiki_tab = WikiTab(self)
        self._sub_stack.addWidget(self.wiki_tab)
        layout.addWidget(self._sub_stack, 1)

        self._switch_sub_tab('wiki')

    def _switch_sub_tab(self, tab_id):
        idx = {'wiki': 0}.get(tab_id, 0)
        self._sub_stack.setCurrentIndex(idx)
        for sid, btn in self._sub_btns.items():
            btn.setChecked(sid == tab_id)

    def refresh(self):
        self.wiki_tab.refresh()

    def refresh_labels(self):
        for sid, skey in [('wiki', 'docs.wiki')]:
            if sid in self._sub_btns:
                self._sub_btns[sid].setText(t(skey) if t else skey)
        self.wiki_tab.refresh_labels()
