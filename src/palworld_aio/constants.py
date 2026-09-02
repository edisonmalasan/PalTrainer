import os
import sys
from typing import TYPE_CHECKING
from resource_resolver import get_base_dir, get_src_dir, get_user_config_dir, resource_path
if TYPE_CHECKING:
    from palobject import MappingCacheObject
BG = '#0A0B0E'
GLASS = '#121418'
ACCENT = '#7DD3FC'
TEXT = '#E6EEF6'
MUTED = '#94A3B8'
EMPHASIS = '#FFFFFF'
ALERT = '#FBBF24'
SUCCESS = '#4ADE80'
ERROR = '#FB7185'
WARNING = ALERT
DANGER = ERROR
BORDER = '#1E2128'
BUTTON_FG = '#7DD3FC'
BUTTON_BG = 'transparent'
BUTTON_HOVER = '#2A2D3A'
BUTTON_PRIMARY = ACCENT
BUTTON_SECONDARY = GLASS
TEXT_DISABLED = '#475569'
TEXT_MUTED = MUTED
SURFACE_ELEVATED = '#161A20'
SURFACE_HOVER = 'rgba(125,211,252,0.08)'
BORDER_SUBTLE = 'rgba(125,211,252,0.15)'
ACCENT_BG = 'rgba(125,211,252,0.12)'
ACCENT_BG_STRONG = 'rgba(125,211,252,0.2)'
ACCENT_BORDER = 'rgba(125,211,252,0.2)'
ACCENT_BORDER_HOVER = 'rgba(125,211,252,0.35)'
ACCENT_BORDER_FOCUS = 'rgba(125,211,252,0.4)'
INFO = '#818CF8'
SPECIAL = '#A78BFA'
RARITY_1 = '#9CA3AF'
RARITY_2 = '#4ADE80'
RARITY_3 = '#60A5FA'
RARITY_4 = '#A78BFA'
RARITY_5 = '#FBBF24'
FOCUS_RING = ACCENT
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_XXL = 32
CONTROL_H_SM = 24
CONTROL_H_MD = 28
CONTROL_H_LG = 36
RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 8
RADIUS_XL = 10
FONT_SIZE_PX_BODY = 12
FONT_SIZE_PX_SECONDARY = 11
FONT_SIZE_PX_SECTION = 13
FONT_SIZE_PX_TITLE = 15
FONT_SIZE_PX_DISPLAY = 20
ICON_SM = 14
ICON_MD = 16
ICON_LG = 20
ICON_XL = 24
TREE_ROW_HEIGHT = 28
FONT_FAMILY = 'Segoe UI'
FONT_FAMILY_NERD = 'Hack Nerd Font'
FONT_FAMILY_MONO = 'Consolas'
FONT_SIZE = 10
FONT_SIZE_BOLD = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_SMALL = 9
SPACE_SMALL = SPACE_SM
SPACE_MEDIUM = SPACE_MD
SPACE_LARGE = SPACE_LG
CORNER_RADIUS = 6
FRAME_CORNER_RADIUS = 8
MAX_QUANTITY = 999_999_999
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/edisonmalasan/PalTrainer/main/src/common.py'
GIT_REPO_URL = 'https://github.com/edisonmalasan/PalTrainer.git'
STABLE_BRANCH = 'main'
STABLE_VERSION_URL = 'https://api.github.com/repos/edisonmalasan/PalTrainer/releases/latest'
RELEASE_DOWNLOAD_URL = 'https://github.com/edisonmalasan/PalTrainer/releases/download/v{version}/PalTrainer_standalone_v{version}.zip'
RELEASES_PAGE_URL = 'https://github.com/edisonmalasan/PalTrainer/releases/latest'
def get_base_path():
    return get_base_dir()
def get_src_path():
    return get_src_dir()
def get_icon_path():
    return resource_path(get_base_dir(), 'icon.ico')
ICON_PATH = get_icon_path()
EXCLUSIONS_FILE = os.path.join(get_user_config_dir(), 'deletion_exclusions.json')
ZONE_EXCLUSIONS_FILE = os.path.join(get_user_config_dir(), 'zone_exclusions.json')
current_save_path: str | None = None
loaded_level_json = None
loaded_level_mtime: float | None = None
original_loaded_level_json = None
backup_save_path = None
srcGuildMapping: "MappingCacheObject | None" = None
player_levels = {}
player_character_cache = {}
player_duplicate_bodies = {}
base_guild_lookup = {}
container_lookup = {}
files_to_delete = set()
PLAYER_PAL_COUNTS = {}
PLAYER_DETAILS_CACHE = {}
PLAYER_REMAPS = {}
exclusions = {}
death_bag_protected_instance_ids = set()
death_bag_protected_container_ids = set()
selected_source_player = None
dps_executor = None
dps_futures = []
dps_tasks = []
dirty = False
xgp_container_path: str | None = None
xgp_save_id: str | None = None
xgp_container_index = None
loading_screen_mode = 'overlay'
pal_creation_name_mode = 'new'
bulk_sync_apply_nickname = False
header_loading_widget = None
xgp_loaded: bool = False
gps_path: str | None = None
gps_gvas = None
gps_xgp_container_path: str | None = None
def get_container_lookup():
    global container_lookup
    if container_lookup and loaded_level_json:
        return container_lookup
    if not loaded_level_json:
        return {}
    container_lookup = {}
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    for cont in item_containers:
        try:
            cont_id = str(cont['key']['ID']['value']).replace('-', '').lower()
            container_lookup[cont_id] = cont
        except:
            pass
    return container_lookup
def invalidate_container_lookup():
    global container_lookup
    container_lookup = {}