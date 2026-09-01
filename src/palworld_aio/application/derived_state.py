"""Derived application state refreshed as part of the save-session lifecycle."""

from __future__ import annotations

import os
from typing import Any, cast

from palworld_aio import constants
from palworld_aio.utils import canonical_player_entries, extract_value
from palworld_aio.world.operations import collect_death_bag_ids


def _loaded_world_save_data() -> dict[str, Any]:
    level_json = cast(dict[str, Any], constants.loaded_level_json)
    return cast(dict[str, Any], level_json['properties']['worldSaveData']['value'])


def refresh_death_bag_protection() -> dict[str, int]:
    """Refresh the protection sets derived from a loaded world save."""
    if not constants.loaded_level_json:
        return {'dropped_pals': 0, 'death_penalty_chests': 0}

    constants.death_bag_protected_instance_ids.clear()
    constants.death_bag_protected_container_ids.clear()
    world_save_data = _loaded_world_save_data()
    result = collect_death_bag_ids(world_save_data)
    constants.death_bag_protected_instance_ids.update(result.protected_instance_ids)
    constants.death_bag_protected_container_ids.update(result.protected_container_ids)

    dropped_pals_count = 0
    death_penalty_chests_count = 0
    for obj in world_save_data.get('MapObjectSaveData', {}).get('value', {}).get('values', []):
        try:
            map_object_id = obj.get('MapObjectId', {}).get('value', '')
            if map_object_id == 'DroppedCharacter':
                dropped_pals_count += 1
            elif map_object_id == 'DeathPenaltyChest':
                death_penalty_chests_count += 1
        except Exception:
            continue

    return {
        'dropped_pals': dropped_pals_count,
        'death_penalty_chests': death_penalty_chests_count,
    }


def build_player_levels() -> None:
    """Refresh player level and character caches for the loaded world save."""
    if not constants.loaded_level_json:
        return

    world_save_data = _loaded_world_save_data()
    players_dir = (
        os.path.join(constants.current_save_path, 'Players')
        if constants.current_save_path
        else None
    )
    canonical, duplicates = canonical_player_entries(world_save_data, players_dir)
    uid_level_map: dict = {}
    uid_entry_map: dict = {}
    for uid, entry in canonical.items():
        save_parameter = entry['value']['RawData']['value']['object']['SaveParameter']['value']
        level = extract_value(save_parameter, 'Level', 1)
        uid_level_map[uid] = int(level) if level is not None else 1
        uid_entry_map[uid] = entry
    constants.player_levels = dict(uid_level_map)
    constants.player_character_cache = uid_entry_map
    constants.player_duplicate_bodies = duplicates
