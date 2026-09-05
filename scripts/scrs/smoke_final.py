"""Final smoke: shell v2 + all recomposed screens (020-024). Results to file."""
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
OUT = pathlib.Path.cwd() / 'Logs' / 'smoke_final.txt'
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
    from PyQt6.QtCore import Qt, QTimer, QEventLoop
    from PyQt6.QtGui import QKeySequence
    app = QApplication(sys.argv)
    from i18n import init_language
    init_language('en_US')
    from palworld_aio.ui.chrome.fonts import load_app_fonts
    fams = load_app_fonts()
    log('fonts=' + repr(fams))
    from palworld_aio.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    app.sendPostedEvents()
    loop = QEventLoop()
    QTimer.singleShot(1500, loop.quit)
    loop.exec()
    log('shell_v2=' + str(getattr(w, '_shell_v2', False)))
    log('no_splitter=' + str(not hasattr(w, 'splitter')))
    log('band_items=' + str(len(w.nexus_band._items)))

    # all 12 pages build + switch
    page_ids = ['tools', 'base_inventory', 'player_inventory', 'pal_editor', 'players',
                'guilds', 'bases', 'map', 'exclusions', 'json_editor', 'docs', 'breeding']
    ok_pages = []
    for pid in page_ids:
        try:
            w.nexus_band.set_active(pid)
            w._on_nav_changed(pid)
            app.sendPostedEvents()
            ok_pages.append(pid)
        except Exception as e:
            log(f'page_fail {pid}: {e!r}')
    log('pages_ok=' + str(len(ok_pages)) + '/12')

    # shortcuts exist
    log('shortcuts=' + str(len(getattr(w, '_page_shortcuts', []))))

    # search panels: count labels + footer
    pp = w.players_panel
    pp.add_item(['Tester', '1h', '50', 12, 'uid-1', 'G', 'gid', '5'])
    log('search_count=' + str(pp.count_label.text()))
    pp.search_input.setText('tester')
    app.processEvents()
    log('filter_count=' + str(pp.count_label.text()))
    log('footer_present=' + str(pp.footer_slot is not None))

    # exclusions segmented switch
    w._switch_exclusion_view('guilds')
    log('excl_switch=' + str(w._excl_stack.currentIndex()))
    w._switch_exclusion_view('players')

    # tray drawer + escape
    w._set_tray_drawer_visible(True)
    app.sendPostedEvents()
    vis = w._tray_drawer.isVisible()
    w._on_global_escape()
    log('drawer_esc=' + str(vis and not w._tray_drawer.isVisible()))

    # language cycle
    ok_langs = 0
    from i18n import set_language, load_resources
    for code in ['zh_CN', 'ja_JP', 'de_DE', 'en_US']:
        try:
            set_language(code)
            load_resources()
            w.nexus_band.refresh_labels()
            w.tools_tab.refresh_labels()
            ok_langs += 1
        except Exception as e:
            log(f'lang_fail {code}: {e!r}')
    log('langs_ok=' + str(ok_langs) + '/4')

    # DPR 2.0 grab
    try:
        pm = w.grab()
        log('grab_dpr=' + str(pm.devicePixelRatio()))
    except Exception as e:
        log('grab_fail=' + repr(e))

    shots = pathlib.Path.cwd() / 'Logs'
    for pid in ['tools', 'map', 'pal_editor', 'players', 'exclusions', 'json_editor', 'breeding']:
        w.nexus_band.set_active(pid)
        w._on_nav_changed(pid)
        app.sendPostedEvents()
        loop2 = QEventLoop()
        QTimer.singleShot(350, loop2.quit)
        loop2.exec()
        w.grab().save(str(shots / f'page_{pid}.png'))
    log('screenshots_saved=True')
    log('RESULT=PASS')
except Exception:
    log('RESULT=FAIL')
    log(traceback.format_exc())

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT)
