"""Pure validation checks for decoded world-save entities."""
from __future__ import annotations

from typing import Any

from palworld_aio.utils import extract_value


def check_is_illegal_pal(raw: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return whether a Pal entry exceeds the editor's supported limits.

    The checker accepts both a CharacterSaveParameterMap entry and the direct
    SaveParameter wrapper used by player-side storage scans.
    """
    try:
        try:
            save_parameter = raw['value']['RawData']['value']['object']['SaveParameter']['value']
        except Exception:
            save_parameter = raw.get('SaveParameter', {}).get('value', {})
            if not save_parameter:
                return (False, [])

        illegal_markers = []
        level = extract_value(save_parameter, 'Level', 1)
        if level > 80:
            illegal_markers.append('Level')
        talent_hp = extract_value(save_parameter, 'Talent_HP', 0)
        talent_shot = extract_value(save_parameter, 'Talent_Shot', 0)
        talent_defense = extract_value(save_parameter, 'Talent_Defense', 0)
        if talent_hp > 100:
            illegal_markers.append('HP IV')
        if talent_shot > 100:
            illegal_markers.append('ATK IV')
        if talent_defense > 100:
            illegal_markers.append('DEF IV')
        rank_hp = extract_value(save_parameter, 'Rank_HP', 0)
        rank_attack = extract_value(save_parameter, 'Rank_Attack', 0)
        rank_defense = extract_value(save_parameter, 'Rank_Defence', 0)
        rank_craftspeed = extract_value(save_parameter, 'Rank_CraftSpeed', 0)
        if rank_hp > 20:
            illegal_markers.append('HP Soul')
        if rank_attack > 20:
            illegal_markers.append('ATK Soul')
        if rank_defense > 20:
            illegal_markers.append('DEF Soul')
        if rank_craftspeed > 20:
            illegal_markers.append('Craft Soul')
        passive_skills = save_parameter.get('PassiveSkillList')
        if isinstance(passive_skills, dict):
            passive_values = passive_skills.get('value')
            if isinstance(passive_values, dict):
                passive_values = passive_values.get('values', [])
            if isinstance(passive_values, list):
                if len(passive_values) > 4:
                    illegal_markers.append('>4 Passives')
                if len(passive_values) != len(set(passive_values)):
                    illegal_markers.append('Duplicate Passives')
        equipped_skills = save_parameter.get('EquipWaza')
        if isinstance(equipped_skills, dict):
            equipped_values = equipped_skills.get('value')
            if isinstance(equipped_values, dict):
                equipped_values = equipped_values.get('values', [])
            if isinstance(equipped_values, list):
                active_count = sum(1 for skill in equipped_values if skill and skill.strip())
                if active_count > 3:
                    illegal_markers.append('>3 Active Skills')
        rank = extract_value(save_parameter, 'Rank', 1)
        if rank > 5:
            illegal_markers.append('>4 Stars')
        return (len(illegal_markers) > 0, illegal_markers)
    except Exception:
        return (False, [])
