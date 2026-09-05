"""Offscreen screenshot capture for top-nav-shell phase gates. Results to a file.

MainWindow redirects stdout, so print() is unavailable during capture; all
progress goes through log() which flushes to disk.
"""
import sys
import os
import pathlib
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
for entry in [SRC, SRC / 'i18n', ROOT / 'resources', SRC / 'palworld_coord', SRC / 'palsav',
              SRC / 'palworld_xgp_import', SRC / 'palworld_aio']:
    if entry.is_dir() and str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

OUT = pathlib.Path.cwd() / 'Logs' / 'shots_topnav.txt'
OUT.parent.mkdir(exist_ok=True)
lines = []


def log(msg):
    lines.append(str(msg))
    try:
        OUT.with_suffix('.progress').write_text('\n'.join(lines), encoding='utf-8')
    except OSError:
        pass


PAGES = {
    'tools': 0, 'base_inventory': 1, 'player_inventory': 2, 'pal_editor': 3,
    'players': 4, 'guilds': 5, 'bases': 6, 'map': 7, 'exclusions': 8,
    'json_editor': 9, 'docs': 10, 'breeding': 11,
}

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    app = QApplication(sys.argv)

    from i18n import init_language
    init_language('en_US')

    from palworld_aio.ui.chrome.fonts import load_app_fonts
    load_app_fonts()
    from palworld_aio.ui.chrome.styles import ThemeManager
    ThemeManager.apply_global()
    log('theme_applied=True')

    from palworld_aio.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    app.processEvents()

    which = os.environ.get('SHOT_PAGES', ','.join(PAGES))
    wanted = [p for p in which.split(',') if p]

    for page_id in wanted:
        idx = PAGES[page_id]
        w.nexus_band.set_active(page_id)
        w._on_nav_changed(page_id)
        app.processEvents()
        shot = pathlib.Path.cwd() / 'Logs' / f'shot_{page_id}.png'
        w.grab().save(str(shot))
        log(f'captured {page_id} -> {shot.name}')

    log('RESULT=PASS')
except Exception:
    log('RESULT=FAIL')
    log(traceback.format_exc())

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT)
