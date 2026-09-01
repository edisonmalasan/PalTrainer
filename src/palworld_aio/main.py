import sys
import os

_found_root = None
if os.path.isfile(sys.executable):
    _exe_dir = os.path.dirname(os.path.realpath(sys.executable))
    if os.path.isdir(os.path.join(_exe_dir, 'resources')):
        _found_root = _exe_dir
    else:
        _parent = os.path.dirname(_exe_dir)
        if os.path.isdir(os.path.join(_parent, 'resources')):
            _found_root = _parent
if not _found_root:
    _probe = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.isdir(os.path.join(_probe, 'resources')):
            _found_root = _probe
            break
        _probe = os.path.dirname(_probe)
    if not _found_root:
        _found_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys._PALTRAINER_BINARY_ROOT = _found_root

import traceback
import multiprocessing
_is_frozen = getattr(sys, 'frozen', False)
if _is_frozen:
    multiprocessing.set_executable(sys.executable)
if __name__ == '__main__':
    multiprocessing.freeze_support()
os.environ['QT_LOGGING_RULES'] = '*=false'
os.environ['QT_DEBUG_PLUGINS'] = '0'
if _is_frozen:
    import io
    class MockStdin:
        def read(self, size=-1):
            return ''
        def readline(self, size=-1):
            return '\n'
        def readlines(self, hint=-1):
            return []
        def __iter__(self):
            return iter([])
        def __next__(self):
            raise StopIteration
    if '--spawn-loader' not in sys.argv:
        sys.stdin = MockStdin()
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
if _is_frozen:
    base_dir = sys._PALTRAINER_BINARY_ROOT
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _is_frozen:
    src_dir = os.path.join(base_dir, 'src')
else:
    src_dir = base_dir if os.path.basename(base_dir) == 'src' else os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
for sub in ['palworld_coord', 'palsav', 'palworld_xgp_import', 'resources', 'palworld_aio']:
    p = os.path.join(src_dir, sub)
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
    elif sub == 'resources':
        p = os.path.join(base_dir, 'resources')
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
try:
    from bootup import _migrate_configs
    _migrate_configs()
except Exception:
    pass
import io
from contextlib import redirect_stderr
stderr_capture = io.StringIO()
try:
    with redirect_stderr(stderr_capture):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import Qt, qInstallMessageHandler, QtMsgType
        from i18n import init_language
        from import_libs import center_window
        from palworld_aio import constants
        from palworld_aio.ui import MainWindow
        from palworld_aio.managers.save_manager import save_manager
        from loading_manager import show_error_screen
except Exception:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt, qInstallMessageHandler, QtMsgType
    from i18n import init_language
    from import_libs import center_window
    from palworld_aio import constants
    from palworld_aio.ui import MainWindow
    from palworld_aio.managers.save_manager import save_manager
    from loading_manager import show_error_screen
def qt_message_handler(mode, context, message):
    if 'QThreadStorage' in str(message) and 'destroyed before end of thread' in str(message):
        return
qInstallMessageHandler(qt_message_handler)
def run_aio():
    try:
        with redirect_stderr(stderr_capture):
            init_language('en_US')
    except Exception:
        init_language('en_US')
    from cli import parse_app_options
    opts = parse_app_options(sys.argv[1:])
    if opts.save_path:
        path_arg = opts.save_path
        options = {'logs': opts.logs, 'fix': opts.fix}
        print(f'Processing save file: {path_arg}')
        mode_desc = []
        if options['logs']:
            mode_desc.append('logs')
        if options['fix']:
            mode_desc.append('fix')
        print(f"Mode: {', '.join(mode_desc)}")
        from palworld_aio.application.save_session import save_session, SavePathError
        if constants.loaded_level_json is not None:
            save_session.reset()
        p = path_arg
        try:
            p = save_session.approve_save_path(p)
        except SavePathError as e:
            print(f'Error: {e}')
            sys.exit(1)
        d = os.path.dirname(p)
        playerdir = os.path.join(d, 'Players')
        print('Loading save...')
        from common import set_last_save_path
        set_last_save_path(d)
        save_session.current_save_path = d
        save_session.backup_save_path = d
        save_session.make_backup('AllinOneTools')
        if not save_session.load(p):
            print('Error: Failed to load save')
            sys.exit(1)
        print(f'Save loaded')
        data_source = constants.loaded_level_json['properties']['worldSaveData']['value']
        guild_name_map = {}
        if constants.srcGuildMapping:
            for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                gid = str(gid_uuid)
                guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                guild_name_map[gid.lower()] = guild_name
        print('Loading done')
        if options['logs']:
            from resource_resolver import get_data_base
            base_path = get_data_base()
            log_folder = os.path.join(base_path, 'Logs', 'Scan Save Logger')
            import shutil
            if os.path.exists(log_folder):
                try:
                    shutil.rmtree(log_folder)
                except:
                    pass
            os.makedirs(log_folder, exist_ok=True)
            print('Generating logs...')
            player_pals_count = {}
            save_manager._count_pals_found(data_source, player_pals_count, log_folder, constants.current_save_path, guild_name_map)
            constants.PLAYER_PAL_COUNTS = player_pals_count
            save_manager._process_scan_log(data_source, playerdir, log_folder, guild_name_map, base_path)
            print('Logs generated successfully')
        if options['fix']:
            from palworld_aio.managers.func_manager import remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, delete_invalid_structure_map_objects, delete_unreferenced_data, delete_non_base_map_objects, fix_illegal_pals_in_save
            print('Running cleanup operations...')
            remove_invalid_items_from_save()
            remove_invalid_pals_from_save()
            remove_invalid_passives_from_save()
            delete_invalid_structure_map_objects()
            delete_unreferenced_data()
            delete_non_base_map_objects()
            fixed_count = fix_illegal_pals_in_save(parent=None)
            print('Saving changes...')
            if constants.current_save_path and constants.loaded_level_json:
                save_session.save()
                print('Changes saved successfully')
            else:
                print('Error: No save file loaded')
        sys.exit(0)
    if opts.test_loading_popup:
        from palworld_aio.widgets import LoadingPopup
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        popup = LoadingPopup()
        popup.show_with_fade()
        def hide_popup():
            popup.hide_with_fade(lambda: app.quit())
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(5000, hide_popup)
        sys.exit(app.exec())
    if sys.platform == 'darwin':
        os.environ.setdefault('QT_SCALE_FACTOR_ROUNDING_POLICY', 'PassThrough')
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(
        'QToolTip { color: #e2e8f0; background: #1e2128; border: 1px solid #3B8ED0; '
        'padding: 6px 10px; font-size: 11px; border-radius: 4px; }')
    if os.path.exists(constants.ICON_PATH):
        app.setWindowIcon(QIcon(constants.ICON_PATH))
    window = MainWindow()
    center_window(window)
    window.show()
    sys.exit(app.exec())
if __name__ == '__main__':
    run_aio()
