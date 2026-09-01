"""In-memory player mutations for decoded world-save documents."""
from __future__ import annotations

from typing import Any


def _player_save_parameter(wsd: dict[str, Any], player_uid: Any) -> tuple[dict[str, Any] | None, str]:
    player_uid_clean = str(player_uid).replace('-', '')
    character_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for entry in character_map:
        raw_data = entry.get('value', {}).get('RawData', {}).get('value', {})
        save_parameter = raw_data.get('object', {}).get('SaveParameter', {})
        if save_parameter.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        save_value = save_parameter.get('value', {})
        if not save_value.get('IsPlayer', {}).get('value'):
            continue
        uid_object = entry.get('key', {}).get('PlayerUId', {})
        uid = str(uid_object.get('value', '')).replace('-', '') if isinstance(uid_object, dict) else ''
        if uid == player_uid_clean:
            return save_value, uid
    return None, ''


def rename_player(wsd: dict[str, Any], player_uid: Any, new_name: str) -> bool:
    """Rename a player in the guild roster and their character body.

    This mirrors the legacy manager's successful no-op behavior when the
    loaded document has no matching player.
    """
    player_uid_clean = str(player_uid).replace('-', '')
    for guild in wsd['GroupSaveDataMap']['value']:
        raw_guild = guild['value']['RawData']['value']
        for player in raw_guild.get('players', []):
            uid = str(player.get('player_uid', '')).replace('-', '')
            if uid == player_uid_clean:
                player.setdefault('player_info', {})['player_name'] = new_name
                break
        else:
            continue
        break

    save_value, _ = _player_save_parameter(wsd, player_uid)
    if save_value is not None:
        save_value['NickName'] = {
            'id': None,
            'type': 'StrProperty',
            'value': new_name,
        }
    return True


def set_player_level(
    wsd: dict[str, Any],
    player_uid: Any,
    new_level: int,
    exp_data: dict[str, Any],
) -> tuple[bool, str]:
    """Set a player's level and EXP, returning the matched normalized UID."""
    if new_level < 1 or new_level > 80:
        return False, ''

    save_value, uid = _player_save_parameter(wsd, player_uid)
    if save_value is None:
        return False, ''
    if 'Level' not in save_value or not save_value['Level']:
        save_value['Level'] = {
            'id': None,
            'type': 'ByteProperty',
            'value': {'type': 'None'},
        }
    if 'value' not in save_value['Level']:
        save_value['Level']['value'] = {'type': 'None'}
    save_value['Level']['value']['value'] = new_level

    exp_value = exp_data[str(new_level)]['TotalEXP']
    if 'Exp' not in save_value:
        save_value['Exp'] = {
            'id': None,
            'type': 'IntProperty',
            'value': exp_value,
        }
    else:
        save_value['Exp']['value'] = exp_value
    return True, uid


def set_player_stats(
    wsd: dict[str, Any],
    player_uid: Any,
    stat_changes: dict[str, Any],
    unused_stat_points: Any = None,
) -> bool:
    """Apply supported player status-point changes to an in-memory save."""
    save_value, _ = _player_save_parameter(wsd, player_uid)
    if save_value is None:
        return False

    for property_name in ('GotStatusPointList', 'GotExStatusPointList'):
        status_list = save_value.get(property_name)
        if not isinstance(status_list, dict):
            continue
        status_values = status_list.get('value')
        if not isinstance(status_values, dict):
            continue
        for status_item in status_values.get('values', []):
            if 'StatusName' not in status_item or 'StatusPoint' not in status_item:
                continue
            status_point = status_item['StatusPoint']
            status_name = status_item['StatusName']
            if not isinstance(status_point, dict) or 'value' not in status_point:
                continue
            if not isinstance(status_name, dict) or 'value' not in status_name:
                continue
            if status_name['value'] in stat_changes:
                status_point['value'] = stat_changes[status_name['value']]

    if 'UnusedStatusPoint' in save_value:
        unused_points = save_value['UnusedStatusPoint']
        if isinstance(unused_points, dict) and 'value' in unused_points:
            unused_points['value'] = 0 if unused_stat_points is None else unused_stat_points
    return True
