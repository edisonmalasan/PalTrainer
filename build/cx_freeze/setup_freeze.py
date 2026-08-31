import sys, os
# Keep src/palsav ahead of src: src/palsav is a namespace dir (no __init__.py)
# that would otherwise shadow the installed palsav package and break
# palsav.core resolution in cx_Freeze's module finder.
sys.path.insert(0, os.path.abspath('src/palsav'))
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('resources'))
from cx_Freeze import setup, Executable
def find_pyqt6_assets():
    result = []
    try:
        import PyQt6
        p = os.path.dirname(PyQt6.__file__)
        plugins_dir = os.path.join(p, 'plugins')
        if os.path.exists(plugins_dir):
            result.append((plugins_dir, 'lib/PyQt6/plugins'))
        translations_dir = os.path.join(p, 'translations')
        if os.path.exists(translations_dir):
            for name in os.listdir(translations_dir):
                if name.startswith('qtbase_en') or name.startswith('qt_en'):
                    src = os.path.join(translations_dir, name)
                    result.append((src, f'lib/PyQt6/translations/{name}'))
        return result if result else None
    except:
        pass
    return None
_PYQT6_EXCLUDES = ['PyQt6.QtQuick', 'PyQt6.QtQml', 'PyQt6.QtDesigner', 'PyQt6.QtHelp', 'PyQt6.QtTest', 'PyQt6.QtDBus', 'PyQt6.QtPrintSupport', 'PyQt6.QtSql', 'PyQt6.QtUiTools', 'PyQt6.QtSvgWidgets', 'PyQt6.QtXml', 'PyQt6.QtQuickWidgets', 'PyQt6.QtQuickControls2', 'PyQt6.QtQuickTemplates2', 'PyQt6.QtQuickDialogs2', 'PyQt6.QtQuickDialogs2QuickImpl', 'PyQt6.QtQuickDialogs2Utils', 'PyQt6.QtQuickLayouts', 'PyQt6.QtQuickParticles', 'PyQt6.QtQuickEffects', 'PyQt6.QtQuickShapes', 'PyQt6.QtQuickTest', 'PyQt6.QtQuickTimeline', 'PyQt6.QtQuickVectorImage', 'PyQt6.QtQuickVectorImageGenerator', 'PyQt6.QtQuickVectorImageHelpers', 'PyQt6.QtLabsAnimation', 'PyQt6.QtLabsFolderListModel', 'PyQt6.QtLabsPlatform', 'PyQt6.QtLabsQmlModels', 'PyQt6.QtLabsSettings', 'PyQt6.QtLabsSharedImage', 'PyQt6.QtLabsStyleKit', 'PyQt6.QtLabsStyleKitImpl', 'PyQt6.QtLabsSynchronizer', 'PyQt6.QtLabsWavefrontMesh', 'PyQt6.QtLottie', 'PyQt6.QtLottieVectorImageGenerator', 'PyQt6.QtQmlCore', 'PyQt6.QtQmlLocalStorage', 'PyQt6.QtQmlMeta', 'PyQt6.QtQmlModels', 'PyQt6.QtQmlNetwork', 'PyQt6.QtQmlWorkerScript', 'PyQt6.QtQmlXmlListModel', 'PyQt6.QtQmlCompiler']
_BUILD_PACKAGES = ['subprocess', 'pathlib', 'shutil', 'json', 'uuid', 'time', 'datetime', 'struct', 'enum', 'collections', 'itertools', 'math', 'zlib', 'gzip', 'zipfile', 'threading', 'multiprocessing', 'io', 'base64', 'binascii', 'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'urllib', 'http', 'mimetypes', 'tempfile', 'glob', 'fnmatch', 'argparse', 'configparser', 'logging', 'traceback', 'string', 'random', 're', 'copy', 'ctypes', 'gc', 'importlib', 'palooz', 'pickle', 'platform', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'nerdfont', 'concurrent.futures', 'palworld_toolsets', 'palworld_xgp_import', 'palsav.core']
_BUILD_EXCLUDES = ['pandas', 'numpy', 'email', 'unittest', 'unittest.mock', 'test', 'pdb', 'tkinter.test', 'lib2to3', 'distutils', 'setuptools', 'pip', 'wheel', 'venv', 'ensurepip', 'msgpack', 'palsav.pyooz'] + _PYQT6_EXCLUDES
build_exe_options = {'packages': _BUILD_PACKAGES, 'excludes': _BUILD_EXCLUDES, 'include_files': [('resources/', 'resources/'), ('src/data/', 'src/data/'), ('src/games.json', 'games.json')], 'zip_include_packages': [], 'zip_exclude_packages': ['*'], 'build_exe': 'PalTrainer_standalone', 'optimize': 2}
ps6_a = find_pyqt6_assets()
if ps6_a:
    build_exe_options['include_files'].extend(ps6_a)
setup(name='PalTrainer', version="2.4.0", options={'build_exe': build_exe_options}, executables=[Executable('src/palworld_aio/main.py', base='gui', target_name='PalTrainer.exe', icon='resources/assets/icons/app/icon.ico')])