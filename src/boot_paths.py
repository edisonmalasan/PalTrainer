import os
import sys
from pathlib import Path


def _compute_root() -> Path:
    if hasattr(sys, '_PALTRAINER_BINARY_ROOT'):
        return Path(sys._PALTRAINER_BINARY_ROOT)
    _found_root: Path | None = None
    if os.path.isfile(sys.executable):
        _exe_dir = Path(os.path.realpath(sys.executable)).parent
        if (_exe_dir / 'resources').is_dir():
            _found_root = _exe_dir
        else:
            _parent = _exe_dir.parent
            if (_parent / 'resources').is_dir():
                _found_root = _parent
    if _found_root is None:
        _probe = Path(__file__).resolve().parent
        for _ in range(5):
            if (_probe / 'resources').is_dir():
                _found_root = _probe
                break
            _probe = _probe.parent
        if _found_root is None:
            _found_root = Path(__file__).resolve().parent.parent
    return _found_root


_RO = _compute_root()
if not hasattr(sys, '_PALTRAINER_BINARY_ROOT'):
    sys._PALTRAINER_BINARY_ROOT = str(_RO)

ROOT_DIR: Path = _RO
SRC_DIR: Path = ROOT_DIR / 'src'
RESOURCES_DIR: Path = ROOT_DIR / 'resources'
DATA_DIR: Path = SRC_DIR / 'data'
CONFIG_DIR: Path = DATA_DIR / 'configs'
GUI_DIR: Path = RESOURCES_DIR / 'ui' / 'themes'
ASSETS_DIR: Path = RESOURCES_DIR / 'assets'


def is_frozen() -> bool:
    if getattr(sys, 'frozen', False):
        return True
    _exe = getattr(sys, 'executable', '') or ''
    return not os.path.basename(_exe).lower().startswith('python')


def get_user_config_dir() -> Path:
    """Return the per-user configuration directory.

    Frozen/standalone builds store user configuration under the platform
    application-data directory; development builds store it under the
    repository's ``src/data/configs``.
    """
    if is_frozen():
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.path.join(os.path.expanduser('~'), '.config')
        return Path(base) / 'PalTrainer' / 'configs'
    return CONFIG_DIR


USER_CONFIG_DIR: Path = get_user_config_dir()


def get_data_base() -> Path:
    """Return the writable data base directory for the current launch mode."""
    if is_frozen():
        return get_user_config_dir().parent
    return ROOT_DIR


def ensure_src_on_path() -> None:
    """Insert the repository ``src`` directory at the front of ``sys.path``.

    Development launches run scripts that live in ``src`` (for example
    ``bootup.py``), so this is normally already true.  The function exists so
    entry points have one predictable place to guarantee it.
    """
    _src = str(SRC_DIR)
    if _src not in sys.path:
        sys.path.insert(0, _src)
