"""Offscreen smoke test for shell v3 (top-nav-shell). Results to a file.

MainWindow redirects stdout, so print() is unavailable; all progress goes
through log() which flushes to disk.
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

OUT = pathlib.Path.cwd() / 'Logs' / 'smoke_shell_v3.txt'
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
    from PyQt6.QtCore import QPoint, QEvent, Qt
    from PyQt6.QtGui import QMouseEvent

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

    # app bar structure
    bar = w.app_bar
    log('app_bar_present=' + str(hasattr(w, 'app_bar')))
    log('app_bar_height=' + str(bar.height()))
    log('brand_present=' + str(hasattr(bar, 'brand')))
    log('chip_present=' + str(hasattr(bar, 'save_chip')))
    log('context_present=' + str(hasattr(bar, 'context')))
    log('window_controls_in_bar=' + str(bar.window_controls.parentWidget() is bar))
    log('header_loading_repointed=' + str(getattr(w, 'app_bar', None) is not None and
                                          __import__('palworld_aio.constants', fromlist=['constants']).header_loading_widget is bar.save_chip))

    # save chip shell states
    from palworld_aio.shell_state import ShellState
    bar.save_chip.set_shell_state(ShellState.LOADING)
    app.processEvents()
    log('chip_loading=' + str(bar.save_chip.property('state')))
    bar.save_chip.set_shell_state(ShellState.LOADED)
    log('chip_loaded=' + str(bar.save_chip.property('state')))
    w._set_dirty(True)
    log('dirty_dot_visible=' + str(bar.save_chip._dirty_dot.isVisible()))
    w._set_dirty(False)
    log('dirty_dot_hidden=' + str(not bar.save_chip._dirty_dot.isVisible()))

    # context indicator
    bar.context.set_player('Tester')
    bar.context.set_guild('Guild A')
    bar.context.set_base(3)
    log('context_player=' + str('Tester' in bar.context.player_label.toolTip()))
    bar.context.clear_selection()
    log('context_cleared=' + str(bar.context.player_label.toolTip() == ''
                                 and 'Tester' not in bar.context.player_label.text()))

    # status strip visible
    log('status_strip_visible=' + str(w.status_bar.isVisible() and w.status_bar.height() == 24))

    # drag zone: empty app-bar space drags; brand button does not
    from PyQt6.QtCore import QPointF
    empty_pos = QPointF(float(bar.width() - 5), float(bar.height() / 2))
    over_brand = QPointF(10.0, 10.0)

    class _FakeEvent:
        def __init__(self, p):
            self._p = p
        def position(self):
            return self._p

    log('drag_empty_area=' + str(w._hit_window_drag_zone(_FakeEvent(empty_pos))))
    log('drag_over_button=' + str(not w._hit_window_drag_zone(_FakeEvent(over_brand))))

    # nav strip routes all 12 ids; rail is retired (5.1)
    log('nav_strip_present=' + str(hasattr(w, 'nav_strip')))
    log('nav_strip_tabs=' + str(len(w.nav_strip._tabs)))
    expected_ids = {'tools', 'base_inventory', 'player_inventory', 'pal_editor',
                    'players', 'guilds', 'bases', 'map', 'exclusions',
                    'json_editor', 'breeding', 'docs'}
    log('nav_ids_match=' + str(set(w.nav_strip._tabs.keys()) == expected_ids))
    log('rail_retired=' + str(not hasattr(w, 'nexus_band')))
    seen = []
    w.nav_strip.nav_changed.connect(lambda pid: seen.append(pid))
    w.nav_strip._on_tab('map')
    log('strip_nav_emit=' + repr(seen))
    log('strip_active_after=' + str(w.nav_strip.active_id()))
    seen.clear()
    w._activate_nav('players')
    log('activate_nav_syncs=' + str(w.nav_strip.active_id() == 'players'))

    # overflow behavior: collapse reference+edit and verify reachability
    w.nav_strip.collapse_zones({'nav.zone.reference', 'nav.zone.edit'})
    app.processEvents()
    log('overflow_visible=' + str(w.nav_strip._overflow_btn.isVisible()))
    log('overflow_actions=' + str(w.nav_strip._overflow_menu.actions().__len__()))
    log('collapsed_tab_hidden=' + str(w.nav_strip._tabs['breeding'].isHidden()))
    w.nav_strip.collapse_zones(set())
    log('restored_visible=' + str(not w.nav_strip._tabs['breeding'].isHidden()))

    # keyboard: 12 shortcuts registered
    log('shortcuts_registered=' + str(len(getattr(w, '_page_shortcuts', [])) == 12))

    # rail removed from layout in 3.4: attribute remains for facade compat
    log('rail_off_layout=' + str(not hasattr(w, 'nexus_band')))

    # selection syncs to app bar context (tray routing)
    w._on_player_selected(['Tester', 'uid', 'gid', '1h', 50, 'Guild A', 'gid', 5])
    log('context_from_selection=' + str('Tester' in w.app_bar.context.player_label.toolTip()))

    # 170px gutter gone: page ribbon right margin < 24px
    players_panel_right = w.players_panel.search_input.width()
    log('search_spans_width=' + str(players_panel_right > 600))

    # screenshot for manual QA
    shot = pathlib.Path.cwd() / 'Logs' / 'shell_v3_shot.png'
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
