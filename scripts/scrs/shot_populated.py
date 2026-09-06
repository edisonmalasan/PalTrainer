"""Populated-state review captures: load the backup Level.sav through the real
save_session path, emit load_finished (real refresh path), then capture pages.

Read-only for the backup save. Results to Logs/shots_populated.txt.
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

OUT = pathlib.Path.cwd() / 'Logs' / 'shots_populated.txt'
OUT.parent.mkdir(exist_ok=True)
lines = []

SAVE = ROOT / 'Backups' / 'AllinOneTools' / 'PalworldSave_backup_20260906_144431' / 'Level.sav'

PAGES = {
    'tools': 0, 'base_inventory': 1, 'player_inventory': 2, 'pal_editor': 3,
    'players': 4, 'guilds': 5, 'bases': 6, 'map': 7, 'exclusions': 8,
    'json_editor': 9, 'docs': 10, 'breeding': 11,
}


def drive_base_inventory(w, app):
    """Select the first guild (auto-selects first base) to show the populated workspace."""
    tab = w.base_inventory_tab
    if not tab._guilds_data:
        return 'no guilds'
    tab._on_guild_changed(tab._guilds_data[0]['id'])
    loop = QEventLoop()
    QTimer.singleShot(4000, loop.quit)
    loop.exec()
    app.processEvents()
    return f"guild={getattr(tab, '_current_guild_name', '')} base={'set' if tab._current_base_id else 'none'}"


def drive_player_inventory(w, app):
    """Select the first player to show the populated inventory workspace."""
    tab = w.inventory_tab
    if not tab._player_list:
        tab.refresh_players()
    if not tab._player_list:
        return 'no players'
    p = tab._player_list[0]
    tab.select_player(p['uid'], p['name'], p.get('display') or p['name'])
    loop = QEventLoop()
    QTimer.singleShot(4000, loop.quit)
    loop.exec()
    app.processEvents()
    return f"player={tab.current_player_name} loaded={tab.inventory is not None}"


def drive_pal_editor(w, app):
    """Select the first player, then the first box pal, to show the populated
    Pal Editor workspace including the right-side inspector."""
    tab = w.pal_editor_tab
    if not tab._player_list:
        tab.refresh()
    if not tab._player_list:
        return 'no players'
    p = tab._player_list[0]
    tab.select_player(p['uid'], p['name'], p.get('display') or p['name'])
    loop = QEventLoop()
    QTimer.singleShot(4000, loop.quit)
    loop.exec()
    app.processEvents()
    widget = tab.pal_editor_widget if hasattr(tab, 'pal_editor_widget') else getattr(tab, 'pal_widget', None)
    if widget is None:
        for attr in vars(tab).values():
            if hasattr(attr, '_on_palbox_slot_clicked'):
                widget = attr
                break
    if widget is None:
        return 'player selected; pal widget not found'
    widget._on_palbox_slot_clicked(0)
    app.processEvents()
    return f"player={tab.current_player_name} pal_clicked={widget._clicked_pal is not None}"


DRIVERS = {
    'base_inventory': drive_base_inventory,
    'player_inventory': drive_player_inventory,
    'pal_editor': drive_pal_editor,
}


def log(msg):
    lines.append(str(msg))
    try:
        OUT.with_suffix('.progress').write_text('\n'.join(lines), encoding='utf-8')
    except OSError:
        pass


try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer, QEventLoop

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

    # Real load path (parse + scan), no backup copy, no settings writes.
    from palworld_aio.managers.save_manager import save_manager
    ok = save_manager._load_from_path(str(SAVE))
    log(f'loaded={ok}')
    if not ok:
        raise RuntimeError('backup Level.sav failed to load')
    save_manager.load_finished.emit(True)
    app.processEvents()

    which = os.environ.get('SHOT_PAGES', ','.join(PAGES))
    wanted = [p for p in which.split(',') if p]
    settle_ms = int(os.environ.get('SHOT_SETTLE_MS', '0') or 0)

    for page_id in wanted:
        idx = PAGES[page_id]
        w._activate_nav(page_id)
        w._on_nav_changed(page_id)
        if settle_ms:
            loop = QEventLoop()
            QTimer.singleShot(settle_ms, loop.quit)
            loop.exec()
        driver = DRIVERS.get(page_id)
        if driver:
            log(f"drive {page_id}: {driver(w, app)}")
        app.processEvents()
        shot = pathlib.Path.cwd() / 'Logs' / f'shot_pop_{page_id}.png'
        w.grab().save(str(shot))
        log(f'captured {page_id} -> {shot.name}')

    log('RESULT=PASS')
except Exception:
    log('RESULT=FAIL')
    log(traceback.format_exc())

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT)
