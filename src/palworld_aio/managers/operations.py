"""Compatibility facade for world-save mutation operations."""

from palworld_aio.world.operations import (
    OperationResult,
    clean_character_save_parameter_map,
    cleanup_player_references,
    collect_death_bag_ids,
    delete_player_pals,
    is_death_bag,
    is_death_penalty_chest_obj,
    is_dropped_character,
)

__all__ = [
    'OperationResult',
    'clean_character_save_parameter_map',
    'cleanup_player_references',
    'collect_death_bag_ids',
    'delete_player_pals',
    'is_death_bag',
    'is_death_penalty_chest_obj',
    'is_dropped_character',
]
