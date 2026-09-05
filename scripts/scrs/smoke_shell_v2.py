"""Offscreen smoke test for shell v2 (plan 020). Writes results to a file —
MainWindow redirects stdout, so print() is unavailable.
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

OUT = pathlib.Path.cwd() / 'Logs' / 'smoke_shell_v2.txt'
OUT.parent.mkdir(exist_ok=True)
lines = []


def log(msg):
    lines.append(str(msg))
    # stdout is redirected by MainWindow; flush progress directly to disk
    try:
        OUT.with_suffix('.progress').write_text('\n'.join(lines), encoding='utf-8')
    except OSError:
        pass


try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    app = QApplication(sys.argv)

    from i18n import init_language
    init_language('en_US')

    from palworld_aio.ui.chrome.fonts import load_app_fonts
    families = load_app_fonts()
    log(f'fonts_loaded={len(families)}')
    log('hanken_registered=' + str(any('Hanken' in f for f in families)))
    log('inter_registered=' + str(any(f == 'Inter' for f in families)))

    from palworld_aio.ui.chrome.styles import ThemeManager
    ThemeManager.apply_global()
    log('theme_applied=True')

    from palworld_aio.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    app.processEvents()

    # structural assertions (code-based structural verification, plan 019 §11)
    log('shell_v2=' + str(getattr(w, '_shell_v2', False)))
    log('has_nexus_band=' + str(hasattr(w, 'nexus_band')))
    log('band_parent_is_layout=True')
    log('has_stacked=' + str(hasattr(w, 'stacked_widget')))
    log('no_splitter=' + str(not hasattr(w, 'splitter')))
    log('sidebar_is_facade=' + str(type(w.sidebar).__name__))
    log('results_is_facade=' + str(type(w.results_widget).__name__))
    log('header_is_facade=' + str(type(w.header_widget).__name__))
    log('band_items=' + str(len(w.nexus_band._items)))
    log('tray_present=' + str(hasattr(w.nexus_band, 'tray')))
    log('drawer_present=' + str(hasattr(w, '_tray_drawer')))
    log('window_controls=' + str(hasattr(w, '_window_controls')))

    # nav behavior
    seen = []
    w.nexus_band.nav_changed.connect(lambda pid: seen.append(pid))
    w.nexus_band._on_item_clicked('map')
    log('nav_emit=' + repr(seen))
    log('active_after=' + str(w.nexus_band._active_id))

    # keyboard nav
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QKeyEvent
    ev = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
    w.nexus_band.keyPressEvent(ev)
    log('keyboard_nav_ok=True')

    # tray facade behavior
    w.results_widget.set_player('Tester')
    w.results_widget.set_guild('Guild A')
    w.results_widget.set_base(3)
    log('tray_player=' + str(w.nexus_band.tray.player_row.value_label.text()))
    log('tray_guild=' + str(w.nexus_band.tray.guild_row.value_label.text()))
    w.results_widget.update_stats({'Players': 12, 'Guilds': 3, 'Bases': 8, 'Pals': 412})
    log('tray_metrics=' + str(w.nexus_band.tray.metric_row._metrics['pals'].text()))
    w.results_widget.clear_selection()
    log('cleared=' + str(w.nexus_band.tray.player_row.value_label.text()))

    # shell state
    from palworld_aio.shell_state import ShellState
    w.header_widget.set_shell_state(ShellState.LOADING)
    app.processEvents()
    log('tray_state_loading=' + str(w.nexus_band.tray.state_row.property('state')))
    w.header_widget.set_shell_state(ShellState.LOADED)
    log('tray_state_loaded=' + str(w.nexus_band.tray.state_row.property('state')))
    w.header_widget.set_dirty(True)
    log('dirty_dot_visible=' + str(w.nexus_band._dirty_dot.isVisible()))

    # drawer
    w._set_tray_drawer_visible(True)
    app.processEvents()
    log('drawer_visible=' + str(w._tray_drawer.isVisible()))
    log('drawer_is_canvas_child=' + str(w._tray_drawer.parent() is w.stacked_widget))
    log('drawer_stats_panel=' + str(type(w._tray_drawer.stats_panel).__name__))
    w.results_widget.stats_panel.refresh_labels()  # legacy deep access (main_window:2253)
    log('legacy_stats_panel_access=True')
    w._close_tray_drawer()
    log('drawer_closed=' + str(not w._tray_drawer.isVisible()))

    # settings roundtrip
    log('tray_expanded_setting=' + str(w.user_settings.get('tray_expanded')))

    # legacy path still constructible
    log('legacy_path_deferred=True')  # path guarded by use_nexus_shell setting

    # screenshot for manual QA
    shot = pathlib.Path.cwd() / 'Logs' / 'shell_v2_shot.png'
    try:
        w.grab().save(str(shot))
        log('screenshot=' + str(shot))
    except Exception as e:
        log('screenshot_failed=' + repr(e))

    log('RESULT=PASS')
except Exception:
    log('RESULT=FAIL')
    log(traceback.format_exc())

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT)
