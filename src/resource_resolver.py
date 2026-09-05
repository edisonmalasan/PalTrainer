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
    'assets/fonts/HankenGrotesk-Medium.ttf': 'assets/fonts/HankenGrotesk-Medium.ttf',
    'assets/fonts/HankenGrotesk-Regular.ttf': 'assets/fonts/HankenGrotesk-Regular.ttf',
    'assets/fonts/HankenGrotesk-SemiBold.ttf': 'assets/fonts/HankenGrotesk-SemiBold.ttf',
    'assets/fonts/Inter_28pt-Medium.ttf': 'assets/fonts/Inter_28pt-Medium.ttf',
    'assets/fonts/Inter_28pt-Regular.ttf': 'assets/fonts/Inter_28pt-Regular.ttf',
    'assets/fonts/Inter_28pt-SemiBold.ttf': 'assets/fonts/Inter_28pt-SemiBold.ttf',
    'assets/fonts/LICENSE.txt': 'assets/fonts/LICENSE.txt',
    'assets/icons/svg/tools.svg': 'assets/icons/svg/tools.svg',
    'assets/icons/svg/map.svg': 'assets/icons/svg/map.svg',
    'assets/icons/svg/base_inventory.svg': 'assets/icons/svg/base_inventory.svg',
    'assets/icons/svg/player_inventory.svg': 'assets/icons/svg/player_inventory.svg',
    'assets/icons/svg/pal_editor.svg': 'assets/icons/svg/pal_editor.svg',
    'assets/icons/svg/players.svg': 'assets/icons/svg/players.svg',
    'assets/icons/svg/guilds.svg': 'assets/icons/svg/guilds.svg',
    'assets/icons/svg/bases.svg': 'assets/icons/svg/bases.svg',
    'assets/icons/svg/exclusions.svg': 'assets/icons/svg/exclusions.svg',
    'assets/icons/svg/json_editor.svg': 'assets/icons/svg/json_editor.svg',
    'assets/icons/svg/breeding.svg': 'assets/icons/svg/breeding.svg',
    'assets/icons/svg/docs.svg': 'assets/icons/svg/docs.svg',
    'assets/icons/svg/save.svg': 'assets/icons/svg/save.svg',
    'assets/icons/svg/console.svg': 'assets/icons/svg/console.svg',
    'assets/icons/svg/toolbox.svg': 'assets/icons/svg/toolbox.svg',
    'assets/icons/svg/warning.svg': 'assets/icons/svg/warning.svg',
    'assets/icons/svg/info.svg': 'assets/icons/svg/info.svg',
    'assets/icons/svg/menu.svg': 'assets/icons/svg/menu.svg',
    'assets/icons/svg/minimize.svg': 'assets/icons/svg/minimize.svg',
    'assets/icons/svg/maximize.svg': 'assets/icons/svg/maximize.svg',
    'assets/icons/svg/restore.svg': 'assets/icons/svg/restore.svg',
    'assets/icons/svg/close.svg': 'assets/icons/svg/close.svg',
    'assets/icons/svg/search.svg': 'assets/icons/svg/search.svg',
    'assets/icons/svg/chevron_down.svg': 'assets/icons/svg/chevron_down.svg',
    'assets/icons/svg/chevron_up.svg': 'assets/icons/svg/chevron_up.svg',
    'assets/icons/svg/chevron_right.svg': 'assets/icons/svg/chevron_right.svg',
    'assets/icons/svg/chevron_left.svg': 'assets/icons/svg/chevron_left.svg',
    'assets/icons/svg/edit.svg': 'assets/icons/svg/edit.svg',
    'assets/icons/svg/player_select.svg': 'assets/icons/svg/player_select.svg',
    'assets/icons/svg/external_link.svg': 'assets/icons/svg/external_link.svg',
    'assets/icons/svg/copy.svg': 'assets/icons/svg/copy.svg',
    'assets/icons/svg/check.svg': 'assets/icons/svg/check.svg',
    'assets/icons/svg/trash.svg': 'assets/icons/svg/trash.svg',
    'assets/icons/svg/download.svg': 'assets/icons/svg/download.svg',
    'assets/icons/svg/upload.svg': 'assets/icons/svg/upload.svg',
    'assets/icons/svg/refresh.svg': 'assets/icons/svg/refresh.svg',
    'assets/icons/svg/import.svg': 'assets/icons/svg/import.svg',
    'assets/icons/svg/export.svg': 'assets/icons/svg/export.svg',
    'assets/icons/svg/video.svg': 'assets/icons/svg/video.svg',
    'assets/icons/svg/steam.svg': 'assets/icons/svg/steam.svg',
    'assets/icons/svg/gamepass.svg': 'assets/icons/svg/gamepass.svg',
    'assets/icons/svg/gamepass_alt.svg': 'assets/icons/svg/gamepass_alt.svg',
    'assets/icons/svg/cloud.svg': 'assets/icons/svg/cloud.svg',
    'assets/icons/svg/check_circle.svg': 'assets/icons/svg/check_circle.svg',
    'assets/icons/svg/save_state.svg': 'assets/icons/svg/save_state.svg',
    'assets/icons/svg/spinner.svg': 'assets/icons/svg/spinner.svg',
    'assets/icons/svg/crosshair.svg': 'assets/icons/svg/crosshair.svg',
    'assets/icons/svg/container.svg': 'assets/icons/svg/container.svg',
    'assets/icons/svg/grid.svg': 'assets/icons/svg/grid.svg',
    'assets/icons/svg/languages.svg': 'assets/icons/svg/languages.svg',
    'assets/icons/svg/cog.svg': 'assets/icons/svg/cog.svg',
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
