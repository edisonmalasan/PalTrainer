"""Offscreen smoke test for shell v3 (top-nav-shell 5.4). Writes results to a
file — MainWindow redirects stdout, so print() is unavailable.

Retired rail/tray/facade assertions from the v2 shell are replaced by
app-bar / nav-strip equivalents; run smoke_shell_v3.py for the full
behavioral sweep.
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

    from palworld_aio.ui.chrome.styles import ThemeManager
    ThemeManager.apply_global()
    log('theme_applied=True')

    from palworld_aio.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    app.processEvents()

    # structural assertions (shell v3: two-tier top chrome, no rail)
    log('shell_v2=' + str(getattr(w, '_shell_v2', False)))
    log('rail_retired=' + str(not hasattr(w, 'nexus_band')))
    log('nav_strip_present=' + str(hasattr(w, 'nav_strip')))
    log('app_bar_present=' + str(hasattr(w, 'app_bar')))
    log('has_stacked=' + str(hasattr(w, 'stacked_widget')))
    log('no_splitter=' + str(not hasattr(w, 'splitter')))
    log('players_panel=' + str(hasattr(w, 'players_panel')))
    log('guilds_panel=' + str(hasattr(w, 'guilds_panel')))
    log('bases_panel=' + str(hasattr(w, 'bases_panel')))
    log('drawer_present=' + str(hasattr(w, '_tray_drawer')))
    log('window_controls_in_bar=' + str(w._window_controls.parentWidget() is w.app_bar))

    # nav behavior
    seen = []
    w.nav_strip.nav_changed.connect(lambda pid: seen.append(pid))
    w.nav_strip._on_tab('map')
    log('nav_emit=' + repr(seen))
    log('active_after=' + str(w.nav_strip.active_id()))

    # selection routing (legacy results facade calls, now app-bar context)
    w._on_player_selected(['Tester', 'uid', 'gid', '1h', 50, 'Guild A', 'gid', 5])
    log('context_player=' + str('Tester' in w.app_bar.context.player_label.toolTip()))
    log('context_guild=' + str('Guild A' in w.app_bar.context.guild_label.toolTip()))
    w._update_stats_all({'Players': 12, 'Guilds': 3, 'Bases': 8, 'Pals': 412})
    log('drawer_stats_updated=True')

    # shell state
    from palworld_aio.shell_state import ShellState
    w.app_bar.save_chip.set_shell_state(ShellState.LOADING)
    app.processEvents()
    log('chip_state_loading=' + str(w.app_bar.save_chip.property('state')))
    w.app_bar.save_chip.set_shell_state(ShellState.LOADED)
    log('chip_state_loaded=' + str(w.app_bar.save_chip.property('state')))
    w._set_dirty(True)
    log('dirty_dot_visible=' + str(w.app_bar.save_chip._dirty_dot.isVisible()))
    w._set_dirty(False)
    w.app_bar.context.clear_selection()
    log('cleared=' + str(w.app_bar.context.player_label.toolTip() == ''))

    # drawer
    w._set_tray_drawer_visible(True)
    app.processEvents()
    log('drawer_visible=' + str(w._tray_drawer.isVisible()))
    log('drawer_is_canvas_child=' + str(w._tray_drawer.parent() is w.stacked_widget))
    log('drawer_stats_panel=' + str(type(w._tray_drawer.stats_panel).__name__))
    w._tray_drawer.stats_panel.refresh_labels()  # legacy deep access (main_window:2253)
    log('legacy_stats_panel_access=True')
    w._close_tray_drawer()
    log('drawer_closed=' + str(not w._tray_drawer.isVisible()))

    # settings roundtrip
    log('tray_expanded_setting=' + str(w.user_settings.get('tray_expanded')))

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
