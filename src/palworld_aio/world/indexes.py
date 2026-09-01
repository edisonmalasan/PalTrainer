"""Derived indexes for a decoded worldSaveData document."""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from typing import Any

from palworld_aio.inventory.container_ownership import ContainerOwnership
from palworld_aio.utils import canonical_player_entries, extract_value


@dataclass
class PlayerIndex:
    """Canonical player bodies and lookup data derived from a world save."""

    levels: dict[str, int]
    entries: dict[str, dict]
    duplicates: dict[str, list[dict]]


def build_player_index(
    world_save_data: dict,
    players_dir: str | PathLike[str] | None = None,
) -> PlayerIndex:
    """Build player lookups from the save's canonical player bodies."""
    canonical, duplicates = canonical_player_entries(world_save_data, players_dir)
    levels: dict[str, int] = {}
    for uid, entry in canonical.items():
        save_parameter = entry['value']['RawData']['value']['object']['SaveParameter']['value']
        level = extract_value(save_parameter, 'Level', 1)
        levels[uid] = int(level) if level is not None else 1
    return PlayerIndex(levels=levels, entries=canonical, duplicates=duplicates)


def count_owned_pals(world_save_data: dict[str, Any]) -> dict[str, int]:
    """Count character entries by their effective owning player UID."""
    owned_count: dict[str, int] = {}
    try:
        character_map = world_save_data['CharacterSaveParameterMap']['value']
        character_containers = world_save_data.get('CharacterContainerSaveData', {}).get('value', [])
        ownership = ContainerOwnership.build(character_map, character_containers)
        for item in character_map:
            try:
                save_parameter = item['value']['RawData']['value']['object']['SaveParameter']['value']
                owner_uid = save_parameter.get('OwnerPlayerUId', {}).get('value')
                effective_owner = ownership.get_effective_owner(
                    item.get('key', {}).get('InstanceId', {}).get('value'),
                    owner_uid,
                )
                if effective_owner:
                    owned_count[effective_owner] = owned_count.get(effective_owner, 0) + 1
            except Exception:
                continue
    except Exception:
        pass
    return owned_count
