import os as _os
import re as _re
from boot_paths import GUI_DIR
try:
    from palworld_aio import constants as _c
    from palworld_aio.ui.chrome import tokens as _t
except ImportError:
    _c = None
    _t = None
if _c is not None:
    ACCENT_HEX = _c.ACCENT
    MUTED_HEX = _c.MUTED
    FONT_PX_BODY = _c.FONT_SIZE_PX_BODY
    FONT_PX_SECONDARY = _c.FONT_SIZE_PX_SECONDARY
    SURFACE = _t.SURFACE
    ACCENT_BORDER_SUBTLE = _t.ACCENT_BORDER_SUBTLE
    ACCENT_BG_FAINT = _t.ACCENT_BG_FAINT
    ACCENT_BG = _t.ACCENT_BG
    ACCENT_BG_STRONG = _t.ACCENT_BG_STRONG
else:
    ACCENT_HEX = '#F59E0B'
    MUTED_HEX = '#A69F94'
    FONT_PX_BODY = 12
    FONT_PX_SECONDARY = 11
    SURFACE = 'rgba(27,25,23,0.65)'
    ACCENT_BORDER_SUBTLE = 'rgba(245,158,11,0.15)'
    ACCENT_BG_FAINT = 'rgba(245,158,11,0.08)'
    ACCENT_BG = 'rgba(245,158,11,0.12)'
    ACCENT_BG_STRONG = 'rgba(245,158,11,0.2)'
class ThemeManager:
    _darkmode_content = None
    _theme = None
    @classmethod
    def theme(cls):
        return cls._theme or 'dark'
    @classmethod
    def set_theme(cls, name):
        """Apply a named theme from the token system (falls back to file QSS)."""
        cls._theme = name
        try:
            from palworld_aio.ui.chrome.qss_builder import build_qss
            qss = build_qss(name)
        except Exception:
            return cls.apply_global()
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
        except Exception:
            pass
        return True
    @classmethod
    def load_qss_content(cls):
        if cls._darkmode_content is None:
            qss_path = _os.path.join(str(GUI_DIR), 'darkmode.qss')
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    cls._darkmode_content = f.read()
            except FileNotFoundError:
                cls._darkmode_content = ''
        return cls._darkmode_content
    @classmethod
    def apply_global(cls):
        # Applies the deployed theme file (generated global QSS + transitional
        # extras). Runtime re-generation is not used here so un-migrated
        # screens keep their objectName rules until their plan lands.
        qss = cls.load_qss_content()
        if not qss:
            return cls._apply_fallback_global()
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
        except Exception:
            pass
        return True
    @classmethod
    def apply_to_widget(cls, widget):
        qss = cls.load_qss_content()
        if not qss:
            return cls._apply_fallback_widget(widget)
        try:
            widget.setStyleSheet(qss)
        except Exception:
            pass
        return True
    @classmethod
    def _apply_fallback_global(cls):
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(_GLOBAL_FALLBACK_STYLE)
        except Exception:
            pass
        return False
    @classmethod
    def _apply_fallback_widget(cls, widget):
        try:
            widget.setStyleSheet(_GLOBAL_FALLBACK_STYLE)
        except Exception:
            pass
        return False
    @classmethod
    def load_styles(cls, widget):
        return cls.apply_to_widget(widget)
_GLOBAL_FALLBACK_STYLE = '\nQWidget {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n        stop:0 rgba(27,25,23,0.98), stop:0.5 rgba(20,19,18,0.98), stop:1 rgba(13,12,11,0.98));\n    color: #ECE7E0;\n}\nQLabel { color: #ECE7E0; }\nQLineEdit {\n    background: rgba(236,231,224,0.06); color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2); border-radius: 6px; padding: 6px 10px;\n}\nQPushButton {\n    background: rgba(245,158,11,0.12); color: #F59E0B;\n    border: 1px solid rgba(245,158,11,0.2); border-radius: 6px; padding: 8px 16px; font-weight: 600;\n}\nQPushButton:hover { background: rgba(245,158,11,0.2); color: #FFFFFF; }\nQTreeWidget {\n    background: rgba(236,231,224,0.03); color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.15); border-radius: 6px;\n}\nQHeaderView::section {\n    background: rgba(245,158,11,0.1); color: #F59E0B;\n    border: none; border-right: 1px solid rgba(245,158,11,0.12); padding: 4px 8px;\n}\nQMessageBox {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 #141312, stop:0.5 #1B1917, stop:1 #141312);\n    color: #ECE7E0;\n}\nQMessageBox QLabel { color: #ECE7E0; }\nQMessageBox QPushButton {\n    background: rgba(245,158,11,0.12); color: #F59E0B;\n    border: 1px solid rgba(245,158,11,0.2); border-radius: 4px;\n    padding: 6px 16px; min-width: 70px;\n}\nQMessageBox QPushButton:hover { background: rgba(245,158,11,0.2); color: #FFFFFF; }\nQInputDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 #141312, stop:0.5 #1B1917, stop:1 #141312);\n    color: #ECE7E0;\n}\nQInputDialog QLabel { color: #ECE7E0; }\nQInputDialog QPushButton {\n    background: rgba(245,158,11,0.12); color: #F59E0B;\n    border: 1px solid rgba(245,158,11,0.2); border-radius: 4px;\n    padding: 6px 16px;\n}\nQInputDialog QPushButton:hover { background: rgba(245,158,11,0.2); color: #FFFFFF; }\n'
DIALOG_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(27,25,23,0.98), stop:0.5 rgba(20,19,18,0.98), stop:1 rgba(13,12,11,0.98));\n    color: #ECE7E0;\n}\nQLabel {\n    color: #ECE7E0;\n}\nQLineEdit {\n    background: rgba(236,231,224,0.06);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(245,158,11,0.4);\n}\nQSpinBox {\n    background: rgba(236,231,224,0.06);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 6px;\n    padding: 4px 8px;\n}\nQSpinBox:focus {\n    border-color: rgba(245,158,11,0.4);\n}\nQComboBox {\n    background: rgba(236,231,224,0.06);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQComboBox:hover {\n    border-color: rgba(245,158,11,0.3);\n}\nQComboBox QAbstractItemView {\n    background-color: rgba(27,25,23,0.98);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2);\n    selection-background-color: rgba(245,158,11,0.3);\n    border-radius: 4px;\n}\nQPushButton {\n    background: rgba(245,158,11,0.12);\n    color: #F59E0B;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(245,158,11,0.2);\n    border-color: rgba(245,158,11,0.4);\n    color: #FFFFFF;\n}\nQPushButton:pressed {\n    background: rgba(245,158,11,0.3);\n}\nQCheckBox {\n    color: #ECE7E0;\n    spacing: 6px;\n}\nQCheckBox::indicator {\n    width: 16px;\n    height: 16px;\n    border: 1px solid rgba(245,158,11,0.3);\n    border-radius: 3px;\n    background: rgba(236,231,224,0.05);\n}\nQCheckBox::indicator:checked {\n    background: rgba(245,158,11,0.25);\n    border-color: rgba(245,158,11,0.6);\n}\nQCheckBox::indicator:hover {\n    border-color: rgba(245,158,11,0.5);\n    background: rgba(236,231,224,0.1);\n}\nQCheckBox::indicator:checked:hover {\n    background: rgba(245,158,11,0.35);\n}\nQListWidget {\n    background: rgba(236,231,224,0.03);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 4px;\n    border: 1px solid rgba(245,158,11,0.12);\n    border-radius: 4px;\n    margin: 2px;\n}\nQListWidget::item:hover {\n    border: 1px solid rgba(245,158,11,0.3);\n    background: rgba(245,158,11,0.05);\n}\nQListWidget::item:selected {\n    border: 1px solid rgba(245,158,11,0.4);\n    background: rgba(245,158,11,0.2);\n}\n'
MENU_STYLE = '\nQMenu {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(20,19,18,0.98), stop:0.5 rgba(20,19,18,0.98), stop:1 rgba(13,12,11,0.98));\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 6px;\n    color: #ECE7E0;\n    padding: 4px;\n}\nQMenu::item {\n    padding: 6px 16px;\n    border-radius: 3px;\n    color: #ECE7E0;\n}\nQMenu::item:selected {\n    background: rgba(245,158,11,0.15);\n    color: #ffffff;\n}\nQMenu::separator {\n    height: 1px;\n    background: rgba(236,231,224,0.1);\n    margin: 4px 8px;\n}\n'
STATS_PANEL_STYLE = '\nStatsPanelWidget {\n    background: rgba(27,25,23,0.95);\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 8px;\n}\nStatsPanelWidget QLabel {\n    color: #ECE7E0;\n}\nStatsPanelWidget QLineEdit {\n    background: rgba(236,231,224,0.06);\n    color: #ECE7E0;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 4px;\n    padding: 2px 4px;\n}\nStatsPanelWidget QLineEdit:focus {\n    border-color: rgba(245,158,11,0.4);\n}\nStatsPanelWidget QPushButton {\n    background: rgba(245,158,11,0.1);\n    color: #F59E0B;\n    border: 1px solid rgba(245,158,11,0.2);\n    border-radius: 3px;\n    font-weight: bold;\n}\nStatsPanelWidget QPushButton:hover {\n    background: rgba(245,158,11,0.2);\n}\nStatsPanelWidget QProgressBar {\n    background: rgba(236,231,224,0.05);\n    border: 1px solid rgba(245,158,11,0.15);\n    border-radius: 3px;\n}\nStatsPanelWidget QProgressBar::chunk {\n    background: rgba(45,212,191,0.6);\n    border-radius: 2px;\n}\n'
PICKER_BG_STYLE = 'QWidget { background: rgba(27,25,23,0.98); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px; }'
PICKER_SEARCH_STYLE = 'QLineEdit { background: rgba(236,231,224,0.06); color: #ECE7E0; border: 1px solid rgba(245,158,11,0.2); border-radius: 4px; padding: 4px 8px; font-size: 12px; } QLineEdit:focus { border-color: rgba(245,158,11,0.4); }'
PICKER_LIST_STYLE = 'QListWidget { background: transparent; color: #ECE7E0; border: none; font-size: 12px; } QListWidget::item { padding: 3px 8px; border-radius: 3px; } QListWidget::item:hover { background: rgba(245,158,11,0.08); } QListWidget::item:selected { background: rgba(245,158,11,0.15); color: #F59E0B; }'
INPUT_DIALOG_STYLE = 'QInputDialog{background:rgba(27,25,23,0.98);color:#ECE7E0}QLabel{color:#ECE7E0}QLineEdit{background:rgba(236,231,224,0.06);color:#ECE7E0;border:1px solid rgba(245,158,11,0.2);border-radius:4px;padding:4px 8px}QSpinBox{background:rgba(236,231,224,0.06);color:#ECE7E0;border:1px solid rgba(245,158,11,0.2);border-radius:4px;padding:4px}QPushButton{background:rgba(245,158,11,0.12);color:#F59E0B;border:1px solid rgba(245,158,11,0.2);border-radius:4px;padding:4px 12px}QPushButton:hover{background:rgba(245,158,11,0.2)}'
TOOLTIP_STYLE = '\nQToolTip { background: rgba(27,25,23,0.98); color: #ECE7E0; border: 1px solid rgba(245,158,11,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }'
CONTENT_PANEL_STYLE = 'background: rgba(27,25,23,0.65); border: 1px solid rgba(245,158,11,0.15); border-radius: 10px;'
SLOT_EMPTY_STYLE = 'background: rgba(236,231,224,0.03); border: 1px solid rgba(236,231,224,0.08); border-radius: 8px;'
SLOT_HOVER_STYLE = 'background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.2);'
SLOT_SELECTED_STYLE = 'background: rgba(245,158,11,0.1); border: 1px solid #F59E0B; border-radius: 8px;'
SLOT_MULTI_SELECTED_STYLE = 'background: rgba(245,158,11,0.2); border: 1px solid #F59E0B; border-radius: 8px;'
TREE_WIDGET_QSS = f'''
    QTreeWidget {{
        background: {SURFACE};
        border: 1px solid {ACCENT_BORDER_SUBTLE};
        border-radius: 8px;
        color: {MUTED_HEX};
        font-size: {FONT_PX_BODY}px;
        outline: none;
        alternate-background-color: rgba(236,231,224,0.02);
    }}
    QTreeWidget::item {{
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QTreeWidget::item:hover {{
        background: {ACCENT_BG_FAINT};
        color: {ACCENT_HEX};
    }}
    QTreeWidget::item:selected {{
        background: {ACCENT_BG_STRONG};
        color: {ACCENT_HEX};
        border-left: 3px solid {ACCENT_HEX};
    }}
    QTreeWidget::item:selected:!active {{
        background: {ACCENT_BG};
        color: {ACCENT_HEX};
    }}
    QHeaderView::section {{
        background: rgba(13,12,11,0.9);
        color: {ACCENT_HEX};
        padding: 6px 8px;
        border: none;
        border-bottom: 1px solid {ACCENT_BORDER_SUBTLE};
        font-weight: 600;
        font-size: {FONT_PX_SECONDARY}px;
        text-align: center;
    }}
    QHeaderView::section:hover {{
        background: {ACCENT_BG_FAINT};
    }}
'''
def slot_default(slot_class: str='') -> str:
    sel = f'{slot_class} {{ {SLOT_EMPTY_STYLE} }}' if slot_class else SLOT_EMPTY_STYLE
    return sel
def slot_full(slot_class: str='') -> str:
    s = slot_class or ''
    return f'{s} {{ {SLOT_EMPTY_STYLE} }} {s}:hover {{ {SLOT_HOVER_STYLE} }}'
def slot_rarity(slot_class: str, color: str) -> str:
    return f'{slot_class} {{ {SLOT_EMPTY_STYLE} border: 1px solid {color}; }} {slot_class}:hover {{ {SLOT_HOVER_STYLE} border: 1px solid {color}; }}'
def slot_selected(slot_class: str='') -> str:
    s = slot_class or ''
    return f'{s} {{ {SLOT_SELECTED_STYLE} }}'
def slot_multi_selected(slot_class: str='') -> str:
    s = slot_class or ''
    return f'{s} {{ {SLOT_MULTI_SELECTED_STYLE} }}'
def wrap_tooltip_text(text: str, width: int=80) -> str:
    if not text:
        return text
    lines = []
    for paragraph in text.replace('\r\n', '\n').split('\n'):
        words = paragraph.split(' ')
        current = ''
        for word in words:
            if len(current) + len(word) + 1 <= width or not current:
                current = current + ' ' + word if current else word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return '<br>'.join(lines)