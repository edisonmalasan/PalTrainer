"""Render deterministic World workspace states without reading save files."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / 'src'
for entry in (
    SRC_ROOT,
    SRC_ROOT / 'i18n',
    PROJECT_ROOT / 'resources',
    SRC_ROOT / 'palworld_coord',
    SRC_ROOT / 'palsav',
    SRC_ROOT / 'palworld_xgp_import',
    SRC_ROOT / 'palworld_aio',
):
    if entry.is_dir() and str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def _capture(app, widget, path: Path, width: int, height: int) -> dict[str, int | str]:
    widget.resize(width, height)
    widget.show()
    app.processEvents()
    pixmap = widget.grab()
    if pixmap.isNull() or not pixmap.save(str(path), 'PNG'):
        raise RuntimeError(f'Could not render {path.name}')
    result: dict[str, int | str] = {
        'file': path.name,
        'width': pixmap.width(),
        'height': pixmap.height(),
        'bytes': path.stat().st_size,
    }
    widget.hide()
    widget.deleteLater()
    app.processEvents()
    return result


def _world_shell(
    route_id: str,
    page,
    *,
    player: tuple[str, str] | None = None,
    guild: tuple[str, str] | None = None,
    base: tuple[str, str] | None = None,
):
    from palworld_aio.ui.chrome.workspace_shell import WorkspaceShell
    from palworld_aio.ui.workspace_context import (
        ContextSelection, SaveIdentity, SavePlatform, WorkspaceContext,
    )

    context = WorkspaceContext()
    context.finish_load(SaveIdentity(
        'synthetic-world', 'Synthetic World', 'C:/Synthetic/Level.sav',
        SavePlatform.STEAM,
    ))
    if player is not None:
        context.set_player(ContextSelection(*player))
    if guild is not None:
        context.set_guild(ContextSelection(*guild))
    if base is not None:
        context.set_base(ContextSelection(*base))
    shell = WorkspaceShell(context)
    page.setParent(shell.page_host)
    shell.register_page(route_id, page)
    shell.navigate(route_id)
    return shell


def _players_sample():
    from palworld_aio.ui.pages.players_page import PlayerRow, PlayersPage

    page = PlayersPage()
    page.set_loaded(True)
    page.set_players((
        PlayerRow(
            '0E656D544A2B4C3D8E9F0A1B2C3D4E5F', 'Hathaway',
            'Today, 09:42', 55, 220, 'Wayfarers',
            'A7CA8B1447324FB593FA8DA90ED36A11', 19, True, 1.0,
        ),
        PlayerRow(
            '2F867E655B3C4D5E9F0A1B2C3D4E5F60', 'Juniper',
            'Yesterday', 47, 136, 'Wayfarers',
            'A7CA8B1447324FB593FA8DA90ED36A11', 19, False, 2.0,
        ),
    ))
    page.browser.tree.setCurrentItem(page.browser.tree.topLevelItem(0))
    return _world_shell('players', page)


def _bases_sample(no_result: bool = False):
    from palworld_aio.ui.pages.bases_page import BaseRow, BasesPage

    page = BasesPage()
    page.set_loaded(True)
    page.set_bases((
        BaseRow(
            '9D2B9D77-8324-4D42-8F1B-0F4D5A9E85D1', 'Clifftop Foundry',
            'A7CA8B1447324FB593FA8DA90ED36A11', 'Wayfarers', 19,
            'X: 324, Y: -118', 'Active',
        ),
        BaseRow(
            '1F6C26B1-9684-4B72-A2D8-28FCF12B7210', 'Marsh Outpost',
            'A7CA8B1447324FB593FA8DA90ED36A11', 'Wayfarers', 19,
            'X: -92, Y: 441', 'Active',
        ),
    ))
    if no_result:
        page.browser.search_input.setText('missing synthetic base')
    else:
        page.browser.tree.setCurrentItem(page.browser.tree.topLevelItem(0))
    return _world_shell('bases', page)


def _guilds_sample():
    from palworld_aio.ui.pages.guilds_page import (
        GuildMemberRow, GuildRow, GuildsPage,
    )

    page = GuildsPage()
    guild_id = 'A7CA8B1447324FB593FA8DA90ED36A11'
    page.set_loaded(True)
    page.set_guilds((GuildRow(guild_id, 'Wayfarers', 19, 2, 2),))
    page.browser.tree.setCurrentItem(page.browser.tree.topLevelItem(0))
    page.set_members(guild_id, (
        GuildMemberRow(
            '0E656D544A2B4C3D8E9F0A1B2C3D4E5F', 'Hathaway',
            'Guild Master', 55, 220, 'Today, 09:42', True, 0, 1.0,
        ),
        GuildMemberRow(
            '2F867E655B3C4D5E9F0A1B2C3D4E5F60', 'Juniper',
            'Member', 47, 136, 'Yesterday', False, 3, 2.0,
        ),
    ))
    return _world_shell('guilds', page)


def _exclusions_sample(empty: bool = False):
    from palworld_aio.ui.pages.exclusions_page import ExclusionsPage

    page = ExclusionsPage()
    page.set_loaded(True)
    if not empty:
        page.set_exclusions({
            'players': ('0E656D544A2B4C3D8E9F0A1B2C3D4E5F',),
            'guilds': ('A7CA8B1447324FB593FA8DA90ED36A11',),
            'bases': (),
        })
        page.browser.tree.setCurrentItem(page.browser.tree.topLevelItem(0))
    return _world_shell('exclusions', page)


def _map_sample():
    from palworld_aio.ui.tabs.map_tab import MapTab

    page = MapTab()
    guild_id = 'A7CA8B1447324FB593FA8DA90ED36A11'
    base = {
        'base_id': '9D2B9D77-8324-4D42-8F1B-0F4D5A9E85D1',
        'base_position': 1,
        'guild_id': guild_id,
        'guild_name': 'Wayfarers',
        'leader_name': 'Hathaway',
        'coords': (324.0, -118.0),
        'img_coords': (1260.0, 880.0),
        'pal_count': 15,
        'map_type': 'world',
    }
    player = {
        'player_uid': '0E656D544A2B4C3D8E9F0A1B2C3D4E5F',
        'player_name': 'Hathaway',
        'guild_id': guild_id,
        'guild_name': 'Wayfarers',
        'level': 55,
        'last_seen': 'Today, 09:42',
        'last_seen_sort': 1.0,
        'pal_count': 220,
        'coords': (318.0, -112.0),
        'img_coords': (1246.0, 868.0),
        'map_type': 'world',
    }
    page.guilds_data = {
        guild_id: {
            'guild_name': 'Wayfarers',
            'leader_name': 'Hathaway',
            'last_seen': 'Today, 09:42',
            'last_seen_sort': 1.0,
            'bases': [base],
        },
    }
    page.filtered_guilds = page.guilds_data
    page.players_data = [player]
    page.filtered_players_data = page.players_data
    page.set_loaded(True)
    page._update_tree()
    page._update_markers()
    page._update_info(base)
    return _world_shell('map', page)


def _player_inventory_sample(*, equipment: bool = False):
    from palworld_aio.ui.tabs.inventory_tab import PlayerInventoryTab

    page = PlayerInventoryTab()
    page.current_player_uid = '0E656D544A2B4C3D8E9F0A1B2C3D4E5F'
    page.current_player_name = 'Hathaway'
    page.player_select_btn.setText('Hathaway (Lv.55)')
    page.placeholder_label.hide()
    page.inv_tabs.show()
    page.main_grid.load_items((
        {
            'slot_index': 0, 'item_id': 'Wood', 'item_name': 'Wood',
            'stack_count': 824, 'rarity': 0,
            'description': 'Material gathered from trees.',
        },
        {
            'slot_index': 1, 'item_id': 'PalSphereMega',
            'item_name': 'Mega Sphere', 'stack_count': 48, 'rarity': 2,
            'description': 'A stronger Pal capture sphere.',
        },
        {
            'slot_index': 6, 'item_id': 'LegendaryLaserRifle',
            'item_name': 'Legendary Laser Rifle With Extended Optics',
            'stack_count': 1, 'rarity': 4,
            'description': 'High-output weapon with advanced optics.',
        },
        {
            'slot_index': 8, 'item_id': 'AncientTechnologyPoint',
            'item_name': 'Ancient Technology Point', 'stack_count': 12,
            'rarity': 3,
        },
    ), max_slots=43)
    page.main_grid.slots[6].set_selected(True, emit=False)
    page.main_grid._show_slot_preview(page.main_grid.slots[6])
    if equipment:
        equipped = {
            'weapon1': ('LaserRifle', 'Legendary Laser Rifle', 4),
            'weapon2': ('Sword', 'Refined Metal Sword', 2),
            'head': ('Helmet', 'Pal Metal Helm', 3),
            'body': ('Armor', 'Heat Resistant Pal Metal Armor', 3),
            'shield': ('Shield', 'Hyper Shield', 2),
            'glider': ('Glider', 'Giga Glider', 1),
        }
        for slot_name, (item_id, name, rarity) in equipped.items():
            page.equip_slots[slot_name].set_item({
                'item_id': item_id,
                'item_name': name,
                'stack_count': 1,
                'rarity': rarity,
            })
        page.inv_tabs.setCurrentIndex(1)
        page._on_equipment_preview(page.equip_slots['weapon1'])
    else:
        page.inv_tabs.setCurrentIndex(0)
    return _world_shell(
        'player_inventory', page,
        player=(page.current_player_uid, page.current_player_name),
    )


def _base_inventory_sample(*, base_pals: bool = False):
    from palworld_aio.ui.tabs.base_inventory_tab import BaseInventoryTab
    from palworld_aio.ui.chrome.components import set_picker_selected

    page = BaseInventoryTab()
    guild_id = 'A7CA8B1447324FB593FA8DA90ED36A11'
    base_id = '9D2B9D77-8324-4D42-8F1B-0F4D5A9E85D1'
    page._guilds_data = [{
        'id': guild_id, 'name': 'Wayfarers', 'level': 19,
    }]
    page._bases_data = [{'id': base_id, 'guild_id': guild_id}]
    page._current_guild_id = guild_id
    page._current_guild_name = 'Wayfarers (Level 19)'
    page._current_base_id = base_id
    page._current_base_name = 'Base 1'
    page.guild_button.setText(page._current_guild_name)
    page.guild_button.setToolTip(guild_id)
    page.base_button.setText(page._current_base_name)
    page.base_button.setToolTip(base_id)
    page.base_button.setEnabled(True)
    set_picker_selected(page.guild_button, True)
    set_picker_selected(page.base_button, True)
    containers = [
        {
            'id': 'guild-chest', 'name': 'Guild Chest', 'slot_count': 54,
            'is_guild_chest': True, 'map_object_id': 'StorageChest',
            'type': 'StorageChest', 'location': 'Guild Storage',
        },
        {
            'id': 'wood-box', 'name': 'Wooden Storage Box', 'slot_count': 24,
            'is_guild_chest': False, 'map_object_id': 'WoodChest',
            'type': 'WoodChest', 'location': 'Clifftop Foundry',
        },
        {
            'id': 'drop-1', 'name': 'Dropped Items', 'slot_count': 1,
            'is_guild_chest': False, 'map_object_id': '3D/CommonDropItem',
            'type': '3D/CommonDropItem', 'location': 'Clifftop Foundry',
        },
    ]
    page.manager.containers = containers
    page._load_containers_for_base(base_id, containers=containers)
    page.inventory_grid.load_items((
        {
            'slot_index': 0, 'item_id': 'Wood', 'item_name': 'Wood',
            'stack_count': 824, 'rarity': 0,
        },
        {
            'slot_index': 1, 'item_id': 'Ingot', 'item_name': 'Refined Ingot',
            'stack_count': 220, 'rarity': 1,
        },
        {
            'slot_index': 6, 'item_id': 'AncientCore',
            'item_name': 'Ancient Civilization Core',
            'stack_count': 8, 'rarity': 3,
        },
    ), max_slots=54)
    page.manager.current_container = containers[0]
    page.manager.inventory_container = object()
    page.container_info.items_count_label.setText('Items: 3')
    page.container_info.empty_slots_label.setText('Empty: 51')
    page._set_container_actions_enabled(True)
    if base_pals:
        page._current_tab = 1
        page.content_stack.setCurrentIndex(1)
        page.inv_tab_btn.setChecked(False)
        page.pals_tab_btn.setChecked(True)
        for control in (
            page.item_button, page.clear_item_button,
            page.structure_button, page.clear_structure_button,
            page.replace_button,
        ):
            control.hide()
        page.base_pals_widget.set_pals([], base_id)
    return _world_shell(
        'base_inventory', page,
        guild=(guild_id, 'Wayfarers'),
        base=(base_id, 'Base 1'),
    )


def render_world_workspaces(output_dir: Path) -> dict[str, object]:
    from PyQt6.QtWidgets import QApplication
    from i18n import init_language
    from palworld_aio.ui.chrome.fonts import load_app_fonts
    from palworld_aio.ui.chrome.styles import ThemeManager

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    init_language('en_US')
    load_app_fonts()
    ThemeManager.apply_global()

    sizes = {'default': (1450, 800), 'minimum': (1024, 700)}
    builders = {
        'players_selected': _players_sample,
        'bases_no_result': lambda: _bases_sample(no_result=True),
        'guilds_selected': _guilds_sample,
        'exclusions_empty': lambda: _exclusions_sample(empty=True),
        'map_selected': _map_sample,
        'player_inventory_selected': _player_inventory_sample,
        'player_equipment_selected': lambda: _player_inventory_sample(
            equipment=True),
        'base_inventory_context': _base_inventory_sample,
        'base_pals_context': lambda: _base_inventory_sample(base_pals=True),
    }
    rendered: dict[str, dict[str, int | str]] = {}
    for state_name, builder in builders.items():
        for size_name, (width, height) in sizes.items():
            name = f'{state_name}_{size_name}_{width}x{height}'
            rendered[name] = _capture(
                app, builder(), output_dir / f'{name}.png', width, height,
            )

    manifest: dict[str, object] = {
        'synthetic_data_only': True,
        'real_save_files_read': False,
        'states': rendered,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2), encoding='utf-8',
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render_world_workspaces(args.output_dir), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
