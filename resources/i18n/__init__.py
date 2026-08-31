from __future__ import annotations
import json
import os
from typing import Dict, Any
_LANG: str = 'zh_CN'
_RES: Dict[str, Dict[str, str]] = {}
_loaded_langs: set = set()
import sys as _sys
import os as _os
def _compute_user_config_dir():
    if getattr(_sys, 'frozen', False):
        if _sys.platform == 'win32':
            _base = _os.environ.get('APPDATA', _os.path.expanduser('~'))
        elif _sys.platform == 'darwin':
            _base = _os.path.join(_os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            _base = _os.path.join(_os.path.expanduser('~'), '.config')
        return _os.path.join(_base, 'PalTrainer', 'configs')
    return _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), 'src', 'data', 'configs')
_BASE: str = _os.path.dirname(__file__)
_CFG: str = _os.path.join(_compute_user_config_dir(), 'config.json')
_SUPPORTED_LANGS = ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR', 'pt_BR', 'pt_PT']
def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
def _ensure_lang(lang: str) -> None:
    if lang not in _loaded_langs:
        _RES[lang] = _load_json(os.path.join(_BASE, f'{lang}.json'))
        _loaded_langs.add(lang)
def load_resources(lang: str | None=None) -> None:
    global _RES, _LANG, _loaded_langs
    _loaded_langs.clear()
    for l in _SUPPORTED_LANGS:
        _RES[l] = _load_json(os.path.join(_BASE, f'{l}.json'))
        _loaded_langs.add(l)
    if lang:
        _LANG = lang
def get_language() -> str:
    return _LANG
def set_language(lang: str) -> None:
    global _LANG
    if lang not in _SUPPORTED_LANGS:
        lang = 'zh_CN'
    _ensure_lang(lang)
    _LANG = lang
    try:
        os.makedirs(os.path.dirname(_CFG), exist_ok=True)
        cfg = _load_json(_CFG) if os.path.exists(_CFG) else {}
        cfg['lang'] = lang
        with open(_CFG, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
def get_config_value(key: str, default: Any=None) -> Any:
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        return cfg.get(key, default)
    return default

def set_config_value(key: str, value: Any) -> None:
    cfg = _load_json(_CFG) if os.path.exists(_CFG) else {}
    cfg[key] = value
    try:
        os.makedirs(os.path.dirname(_CFG), exist_ok=True)
        with open(_CFG, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
def init_language(default_lang: str='zh_CN') -> None:
    global _LANG, _loaded_langs
    lang = default_lang
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        lang = cfg.get('lang', default_lang)
    _ensure_lang(lang)
    _ensure_lang('en_US')
    _LANG = lang
_DEF = object()
def get_native_lang_name(code: str) -> str:
    _ensure_lang('en_US')
    _en = _RES.get('en_US', {})
    return _en.get(f'lang.{code}', code)
def t(key: str, default: str | object=_DEF, **fmt) -> str:
    src = _RES.get(_LANG, {})
    fallback = _RES.get('en_US', {})
    text = src.get(key) or fallback.get(key)
    if text is None:
        text = key if default is _DEF else default
    try:
        return text.format(**fmt) if fmt else text
    except Exception:
        return text