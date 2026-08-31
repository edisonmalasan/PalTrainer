import os

from boot_paths import (
    ROOT_DIR,
    SRC_DIR,
    RESOURCES_DIR,
    CONFIG_DIR,
    is_frozen as _is_frozen,
    get_user_config_dir as _get_user_config_dir,
    get_data_base as _get_data_base,
)


def get_base_dir() -> str:
    return str(ROOT_DIR)


def get_src_dir() -> str:
    return str(SRC_DIR)


def get_resources_dir() -> str:
    return str(RESOURCES_DIR)


def _frozen() -> bool:
    return _is_frozen()


def get_data_base() -> str:
    return str(_get_data_base())


def get_user_config_dir() -> str:
    return str(_get_user_config_dir())


_RESOURCE_MAP = {
    'assets/branding/background.png': 'assets/branding/background.png',
    'assets/branding/logo.png': 'assets/branding/logo.png',
    'assets/branding/PalTrainer.png': 'assets/branding/PalTrainer.png',
    'assets/branding/PalTrainer_Black.png': 'assets/branding/PalTrainer_Black.png',
    'assets/branding/PalTrainer_Blue.png': 'assets/branding/PalTrainer_Blue.png',
    'assets/branding/PalTrainer_readme_divider.png': 'assets/branding/PalTrainer_readme_divider.png',
    'assets/fonts/HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'assets/icons/app/icon.ico': 'assets/icons/app/icon.ico',
    'assets/icons/app/icon.png': 'assets/icons/app/icon.png',
    'assets/icons/app/icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'assets/icons/app/pal.ico': 'assets/icons/app/pal.ico',
    'assets/icons/game/baseicon.webp': 'assets/icons/game/baseicon.webp',
    'assets/icons/game/boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'assets/icons/game/boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'assets/icons/game/calibrate.webp': 'assets/icons/game/calibrate.webp',
    'assets/icons/game/lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'assets/icons/game/marker.webp': 'assets/icons/game/marker.webp',
    'assets/icons/game/outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'assets/icons/game/playericon.webp': 'assets/icons/game/playericon.webp',
    'assets/icons/game/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'assets/icons/game/ring.webp': 'assets/icons/game/ring.webp',
    'assets/icons/game/Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'assets/icons/game/zones.webp': 'assets/icons/game/zones.webp',
    'assets/maps/T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'assets/maps/T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
    'background.png': 'assets/branding/background.png',
    'logo.png': 'assets/branding/logo.png',
    'PalTrainer.png': 'assets/branding/PalTrainer.png',
    'PalTrainer_Black.png': 'assets/branding/PalTrainer_Black.png',
    'PalTrainer_Blue.png': 'assets/branding/PalTrainer_Blue.png',
    'PalTrainer_readme_divider.png': 'assets/branding/PalTrainer_readme_divider.png',
    'HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'icon.ico': 'assets/icons/app/icon.ico',
    'icon.png': 'assets/icons/app/icon.png',
    'icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'pal.ico': 'assets/icons/app/pal.ico',
    'baseicon.webp': 'assets/icons/game/baseicon.webp',
    'boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'calibrate.webp': 'assets/icons/game/calibrate.webp',
    'lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'marker.webp': 'assets/icons/game/marker.webp',
    'outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'playericon.webp': 'assets/icons/game/playericon.webp',
    'pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'UI/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'ring.webp': 'assets/icons/game/ring.webp',
    'Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'zones.webp': 'assets/icons/game/zones.webp',
    'T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
}


def resource_path(base_dir: str, *parts: str) -> str:
    rel = os.path.join(*parts).replace('\\', '/')
    mapped: str = _RESOURCE_MAP.get(rel, rel)
    return os.path.join(base_dir, 'resources', mapped)
