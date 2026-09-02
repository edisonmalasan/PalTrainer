"""UI stability diagnostics.

Activated by PALTRAINER_UI_DEBUG=1 (or PALTRAINER_DEBUG). Writes a
timestamped, thread-tagged event log to Logs/ui_debug.log so the exact
sequence before a crash can be reconstructed. Never changes behavior.
"""
from __future__ import annotations

import os
import threading
import time

_ENABLED = None
_LOG_PATH = None
_lock = threading.Lock()
_t0 = time.perf_counter()


def _enabled() -> bool:
    global _ENABLED
    if _ENABLED is None:
        _ENABLED = (
            os.environ.get('PALTRAINER_UI_DEBUG', '') in ('1', 'true', 'True')
            or os.environ.get('PALTRAINER_DEBUG', '') in ('1', 'true', 'True')
        )
    return _ENABLED


def _resolve_log_path():
    global _LOG_PATH
    if _LOG_PATH is not None:
        return _LOG_PATH
    try:
        base = os.environ.get('PALTRAINER_UI_DEBUG_DIR', '')
        if not base:
            try:
                from palworld_aio import constants
                base = constants.get_base_path()
            except Exception:
                base = os.getcwd()
        log_dir = os.path.join(str(base), 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        _LOG_PATH = os.path.join(log_dir, 'ui_debug.log')
    except Exception:
        _LOG_PATH = os.path.join(os.environ.get('TEMP', '.'), 'ui_debug.log')
    print(f'[ui_debug] logging to {_LOG_PATH}', flush=True)
    return _LOG_PATH


def log(event: str, **fields) -> None:
    """Record one UI pipeline event. Safe from any thread; never raises."""
    if not _enabled():
        return
    try:
        t = time.perf_counter() - _t0
        thread = threading.current_thread()
        tname = 'GUI' if thread.name == 'MainThread' else thread.name
        parts = [f'[UI {t:10.3f}] [{tname}:{thread.ident}] {event}']
        for k, v in fields.items():
            parts.append(f'{k}={v}')
        line = ' '.join(parts)
        with _lock:
            try:
                with open(_resolve_log_path(), 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
            except Exception as inner:
                # fall back so events are never silently lost
                with open(os.path.join(os.environ.get('TEMP', '.'), 'ui_debug_fallback.log'), 'a', encoding='utf-8') as f:
                    f.write(f'[FALLBACK {_LOG_PATH!r} {inner!r}] {line}\n')
    except Exception:
        pass


def log_exception(event: str) -> None:
    if not _enabled():
        return
    import traceback
    try:
        tb = traceback.format_exc()
        with _lock:
            with open(_resolve_log_path(), 'a', encoding='utf-8') as f:
                f.write(f'{event} EXCEPTION:\n{tb}\n')
    except Exception:
        pass
