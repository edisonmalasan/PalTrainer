import os
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from i18n import t, get_language
from palworld_aio import constants
from palworld_aio.ui.chrome.components import BaseDialog
from palworld_aio.ui.chrome import tokens as ui_tokens
from resource_resolver import resource_path

_GUIDE_TOKENS = ui_tokens.resolve()

# Page-body HTML wrapper. Body files under resources/tab_guide/ carry their
# own authored <style> blocks (content debt, not dialog chrome); the wrapper
# only sets the base text/accent so unstyled text matches the theme.
SECTION_HTML = '''<div style="color: {text_color}; font-family: '{font_family}'; font-size: 12px;">
<h3 style="color: {header_color}; margin: 0 0 4px 0;">{title}</h3>
{body}
</div>'''

PAGE_HTML = '''<div style="color: {text_color}; font-family: '{font_family}'; font-size: 12px;">
{body}
</div>'''

SECTION_KEYS = [
    ('intro', 'tab_guide.intro_page'),
    ('map', 'tab_guide.section.map'),
    ('tools', 'tab_guide.section.tools'),
    ('base_inventory', 'tab_guide.section.base_inventory'),
    ('player_inventory', 'tab_guide.section.player_inventory'),
    ('pal_editor', 'tab_guide.section.pal_editor'),
    ('players', 'tab_guide.section.players'),
    ('guilds', 'tab_guide.section.guilds'),
    ('bases', 'tab_guide.section.bases'),
    ('exclusions', 'tab_guide.section.exclusions'),
    ('docs', 'tab_guide.section.docs'),
]

FMT = dict(
    text_color=_GUIDE_TOKENS['text'], header_color=_GUIDE_TOKENS['accent'],
    font_family=constants.FONT_FAMILY
)


class _TocBtn(QPushButton):
    """TOC entry using the shared pageSwitchBtn grammar (checked = active)."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName('pageSwitchBtn')
        self.setCheckable(True)
        self.setFont(QFont(constants.FONT_FAMILY, 11))


class TabGuideDialog(BaseDialog):
    """Tab usage guide on the shared dialog scaffold (Phase 4).

    TOC uses pageSwitchBtn checked-state; page bodies are authored HTML
    content (their inner <style> blocks are content debt, untouched).
    """

    def __init__(self, parent=None):
        title = t('tab_guide.title') if t else 'Tab Usage Guide'
        super().__init__(title, parent, min_size=(720, 580))
        self.setWindowTitle(title)
        self.resize(780, 660)
        self._page_label = None
        self._current_anchor = 'intro'
        self._toc_btns = {}
        self._setup_ui()

    def _build_page_html(self, anchor, body):
        if anchor == 'intro':
            html = PAGE_HTML.format(body=body, **FMT)
        else:
            prefix = dict(SECTION_KEYS).get(anchor)
            title = t(f'{prefix}.title') if t and t(f'{prefix}.title') else anchor.title()
            html = SECTION_HTML.format(title=title, body=body, **FMT)
        return html

    def _load_section_body(self, anchor):
        lang = get_language()
        lang_dir = lang.split('_')[0]
        base = constants.get_base_path()
        path = resource_path(base, 'tab_guide', lang_dir, f'{anchor}.html')
        if not os.path.exists(path):
            path = resource_path(base, 'tab_guide', 'en', f'{anchor}.html')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except (OSError, IOError):
            return ''

    def _switch_page(self, anchor):
        self._current_anchor = anchor
        body = self._load_section_body(anchor)
        if self._page_label:
            self._page_label.setText(self._build_page_html(anchor, body))
            self._scroll_area.verticalScrollBar().setValue(0)
        for key, btn in self._toc_btns.items():
            is_active = key == anchor
            if btn.isChecked() != is_active:
                btn.setChecked(is_active)

    def refresh_labels(self):
        title = t('tab_guide.title') if t else 'Tab Usage Guide'
        self.setWindowTitle(title)
        self.title_label.setText(title)
        if hasattr(self, '_subtitle_label'):
            self._subtitle_label.setText(t('tab_guide.subtitle') if t else 'Click behaviors, shortcuts, and tips for every section')
        if hasattr(self, '_toc_title_label'):
            self._toc_title_label.setText(t('tab_guide.toc_title') if t else 'Table of Contents — click a page to open:')
        self.cancel_btn.setText(t('button.close') if t else 'Close')
        if hasattr(self, '_footer_label'):
            self._footer_label.setText(t('tab_guide.footer') if t else 'Tip: Right-click menus are your friend — always check them for deeper options in every tab.')
        for anchor, prefix in SECTION_KEYS:
            label_text = t(f'{prefix}.toc')
            btn = self._toc_btns.get(anchor)
            if btn and label_text:
                btn.setText(label_text)
        if self._page_label:
            body = self._load_section_body(self._current_anchor)
            self._page_label.setText(self._build_page_html(self._current_anchor, body))

    def _setup_ui(self):
        layout = self.content_layout

        # --- Subtitle (the scaffold owns the title row) ---
        self._subtitle_label = QLabel(t('tab_guide.subtitle') if t else 'Click behaviors, shortcuts, and tips for every section')
        self._subtitle_label.setProperty('role', 'secondary')
        self._subtitle_label.setWordWrap(True)
        layout.addWidget(self._subtitle_label)

        # --- Scroll area: TOC + Stacked pages ---
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 8, 0, 8)
        scroll_layout.setSpacing(0)

        # -- TOC --
        toc_frame = QFrame()
        toc_frame.setProperty('class', 'panel')
        toc_layout = QVBoxLayout(toc_frame)
        toc_layout.setContentsMargins(14, 10, 14, 10)
        toc_layout.setSpacing(6)
        self._toc_title_label = QLabel(t('tab_guide.toc_title') if t else 'Table of Contents — click a page to open:')
        self._toc_title_label.setObjectName('sectionHeader')
        toc_layout.addWidget(self._toc_title_label)
        grid = QGridLayout()
        grid.setSpacing(4)
        cols = 3
        for i, (anchor, prefix) in enumerate(SECTION_KEYS):
            label_text = t(f'{prefix}.toc')
            btn = _TocBtn(label_text if label_text else anchor.title())
            btn.clicked.connect(lambda checked, a=anchor: self._switch_page(a))
            self._toc_btns[anchor] = btn
            grid.addWidget(btn, i // cols, i % cols)
        toc_layout.addLayout(grid)
        scroll_layout.addWidget(toc_frame)

        scroll_layout.addSpacing(4)

        # -- Single page label (content swapped on navigation) --
        self._page_label = QLabel()
        self._page_label.setWordWrap(True)
        self._page_label.setTextFormat(Qt.RichText)
        self._page_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        scroll_layout.addWidget(self._page_label)
        scroll_layout.addStretch()

        self._scroll_area.setWidget(scroll_content)
        layout.addWidget(self._scroll_area, 1)

        # Start on intro page
        self._switch_page('intro')

        # --- Footer tip (the scaffold owns Close) ---
        self._footer_label = QLabel(t('tab_guide.footer') if t else 'Tip: Right-click menus are your friend — always check them for deeper options in every tab.')
        self._footer_label.setProperty('role', 'secondary')
        self._footer_label.setWordWrap(True)
        self.footer.insertWidget(1, self._footer_label, stretch=1)
        self.cancel_btn.setText(t('button.close') if t else 'Close')
