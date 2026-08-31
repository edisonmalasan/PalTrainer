"""Domain service for Pal stat calculations.

Centralizes stat recalculation formulas used throughout the application.
All functions are pure — they accept Pal data dicts (matching the
``characters.json`` structure) and return computed values.
No PyQt6 import, no module-level constants access.
"""

from palworld_aio.utils import (
    calculate_max_hp as calculate_max_hp,
    calculate_shot_attack as calculate_shot_attack,
    calculate_attack as calculate_attack,
    calculate_defense as calculate_defense,
    calculate_work_speed as calculate_work_speed,
    get_friendship_rank as get_friendship_rank,
    get_pal_data as get_pal_data,
    _hp_breakdown as hp_breakdown,
    _atk_breakdown as atk_breakdown,
    _def_breakdown as def_breakdown,
    _ws_breakdown as ws_breakdown,
)