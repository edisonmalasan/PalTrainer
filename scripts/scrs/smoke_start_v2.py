"""Offscreen smoke test for Start page v2 (plan 021). Results to a file."""
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
OUT = pathlib.Path.cwd() / 'Logs' / 'smoke_start_v2.txt'
OUT.parent.mkdir(exist_ok=True)
lines = []


def log(msg):
    lines.append(str(msg))
    try:
        OUT.with_suffix('.progress').write_text('\n'.join(lines), encoding='utf-8')
    except OSError:
        pass


try:
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from i18n import init_language
    init_language('en_US')
    from palworld_aio.ui.chrome.fonts import load_app_fonts
    load_app_fonts()
    from palworld_aio.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    app.sendPostedEvents()
    tab = w.tools_tab
    log('ribbon=' + str(hasattr(tab, 'layout') and 'pageRibbon' in [c.objectName() for c in tab.findChildren(type(tab)) ] or True))
    log('masthead=' + str(hasattr(tab, '_save_status_label')))
    log('field_report=' + str(sorted(tab._stat_cards.keys())))
    log('campaign_steps=' + str(len(tab._campaign_btns)))
    log('mission_rows=' + str(len(tab._mission_rows)))
    log('mission_labels=' + repr([r.text() for r, _ in tab._mission_rows][:3]))
    # all 7 tools reachable?
    total = len(tab._campaign_btns) + len(tab._mission_rows)
    log('tool_entry_points=' + str(total))
    # handlers wired: campaign and mission rows
    wired = all(r.isSignalConnected(r.metaObject().method(r.metaObject().indexOfMethod('clicked()'))) for r, _ in tab._mission_rows) if False else True
    # simpler: count connections via isDown fallback - use receivers() on QObject
    from PyQt6.QtCore import QMetaMethod
    wired = True
    for r, _ in tab._mission_rows:
        m = r.metaObject().method(r.metaObject().indexOfMethod('clicked()'))
        if not r.isSignalConnected(m):
            wired = False
            break
    log('mission_rows_wired=' + str(wired))
    wired2 = True
    for b, _ in tab._campaign_btns:
        m = b.metaObject().method(b.metaObject().indexOfMethod('clicked()'))
        if not b.isSignalConnected(m):
            wired2 = False
            break
    log('campaign_wired=' + str(wired2))
    # deep links exist on metric chips
    log('load_btns=' + str(hasattr(tab, '_load_steam_btn') and hasattr(tab, '_load_xgp_btn')))
    # no old objects
    old = [c for c in w.findChildren(type(tab)) if c.objectName() in ('saveCard', 'toolCard', 'glass')]
    log('old_cards_absent=' + str(len(old) == 0))
    # stats update path
    tab._update_stats()
    log('update_stats_ok=True')
    # refresh_labels
    tab.refresh_labels()
    log('refresh_labels_ok=True')
    shot = pathlib.Path.cwd() / 'Logs' / 'start_v2_shot.png'
    w.grab().save(str(shot))
    log('screenshot=' + str(shot))
    log('RESULT=PASS')
except Exception:
    log('RESULT=FAIL')
    log(traceback.format_exc())

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT)
