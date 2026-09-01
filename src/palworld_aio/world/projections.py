from __future__ import annotations

from typing import Any

from palsav.archive import UUID
from palworld_aio.utils import as_uuid, extract_value, normalize_uid


def _normalize(uid: Any) -> str:
    return normalize_uid(uid)


def _guild_filter(g: dict) -> bool:
    return g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'


def _raw(entry: dict) -> dict:
    return entry['value']['RawData']['value']


def _sp(entry: dict) -> dict:
    return entry['value']['RawData']['value']['object']['SaveParameter']['value']


class SaveProjections:
    """Typed projections over a loaded save document (worldSaveData).

    All methods are pure reads — they accept the ``worldSaveData`` dict
    (``loaded_level_json['properties']['worldSaveData']['value']``) and
    return structured data.  No mutations, no UI imports, no access to
    module-level constants.
    """

    __slots__ = ()

    # ------------------------------------------------------------------
    # World metadata
    # ------------------------------------------------------------------

    @staticmethod
    def get_tick(wsd: dict) -> int:
        return wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']

    @staticmethod
    def get_world_name(wsd: dict) -> str:
        wsd_meta = wsd.get('WorldSaveParameter', {}).get('value', {})
        return wsd_meta.get('WorldName', {}).get('value', 'World')

    # ------------------------------------------------------------------
    # Guilds
    # ------------------------------------------------------------------

    @staticmethod
    def get_guilds(wsd: dict) -> list[dict]:
        out: list[dict] = []
        for g in wsd['GroupSaveDataMap']['value']:
            if not _guild_filter(g):
                continue
            r = _raw(g)
            gid = str(g['key'])
            out.append({
                'id': gid,
                'name': r.get('guild_name', 'Unknown'),
                'level': r.get('base_camp_level', 1),
                'member_count': len(r.get('players', [])),
                'admin_player_uid': str(r.get('admin_player_uid', '')),
                'base_ids': [str(b) for b in r.get('base_ids', [])],
                'group_id': str(r.get('group_id', '')),
            })
        return out

    @staticmethod
    def get_guild_members(wsd: dict, guild_id: str) -> list[dict]:
        gid_clean = _normalize(guild_id)
        for g in wsd['GroupSaveDataMap']['value']:
            if not _guild_filter(g):
                continue
            if _normalize(g['key']) == gid_clean:
                r = _raw(g)
                tick = SaveProjections.get_tick(wsd)
                out: list[dict] = []
                for p in r.get('players', []):
                    uid = str(p.get('player_uid', ''))
                    last = p.get('player_info', {}).get('last_online_real_time')
                    elapsed = None if last is None else (tick - last) / 10000000.0
                    out.append({
                        'uid': uid,
                        'name': p.get('player_info', {}).get('player_name', 'Unknown'),
                        'role': p.get('role', 3),
                        'last_online_real_time': last,
                        'elapsed': elapsed,
                    })
                return out
        return []

    @staticmethod
    def get_guild_id_for_player(wsd: dict, player_uid: str) -> str | None:
        uid_clean = _normalize(player_uid)
        for g in wsd['GroupSaveDataMap']['value']:
            if not _guild_filter(g):
                continue
            r = _raw(g)
            for p in r.get('players', []):
                if _normalize(p.get('player_uid', '')) == uid_clean:
                    return str(g['key'])
        return None

    @staticmethod
    def get_guild_name(wsd: dict, guild_id: str) -> str:
        gid_clean = _normalize(guild_id)
        for g in wsd['GroupSaveDataMap']['value']:
            if not _guild_filter(g):
                continue
            if _normalize(g['key']) == gid_clean:
                return _raw(g).get('guild_name', 'Unknown Guild')
        return 'Unknown Guild'

    # ------------------------------------------------------------------
    # Players
    # ------------------------------------------------------------------

    @staticmethod
    def get_player_info(wsd: dict, player_uid: str,
                        player_levels: dict | None = None,
                        pal_counts: dict | None = None) -> dict | None:
        uid_clean = _normalize(player_uid)
        tick = SaveProjections.get_tick(wsd)
        for g in wsd['GroupSaveDataMap']['value']:
            if not _guild_filter(g):
                continue
            gid = str(g['key'])
            gname = _raw(g).get('guild_name', 'Unknown Guild')
            for p in _raw(g).get('players', []):
                if _normalize(p.get('player_uid', '')) == uid_clean:
                    last = p.get('player_info', {}).get('last_online_real_time')
                    elapsed = None if last is None else (tick - last) / 10000000.0
                    return {
                        'uid': player_uid,
                        'name': p.get('player_info', {}).get('player_name', 'Unknown'),
                        'level': (player_levels or {}).get(uid_clean, 1),
                        'pals': (pal_counts or {}).get(uid_clean, 0),
                        'lastseen': elapsed,
                        'guild_id': gid,
                        'guild_name': gname,
                    }
        return None

    @staticmethod
    def get_player_char_entries(wsd: dict) -> list[dict]:
        """Return all ``IsPlayer`` entries from CharacterSaveParameterMap."""
        cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        out: list[dict] = []
        for entry in cmap:
            try:
                sv = _sp(entry)
                if sv.get('IsPlayer', {}).get('value'):
                    out.append(entry)
            except Exception:
                continue
        return out

    @staticmethod
    def get_pal_char_entries(wsd: dict) -> list[dict]:
        """Return non-player CharacterSaveParameterMap entries."""
        cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        out: list[dict] = []
        for entry in cmap:
            try:
                sv = _sp(entry)
                if not sv.get('IsPlayer', {}).get('value'):
                    out.append(entry)
            except Exception:
                continue
        return out

    @staticmethod
    def get_player_save_param(wsd: dict, player_uid: str) -> dict | None:
        uid_clean = _normalize(player_uid)
        for entry in SaveProjections.get_player_char_entries(wsd):
            key_uid = entry.get('key', {}).get('PlayerUId', {}).get('value')
            if key_uid and _normalize(key_uid) == uid_clean:
                return _sp(entry)
        return None

    # ------------------------------------------------------------------
    # Bases
    # ------------------------------------------------------------------

    @staticmethod
    def get_bases(wsd: dict) -> list[dict]:
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        out: list[dict] = []
        for b in base_list:
            try:
                r = _raw(b)
                trans = r.get('transform', {}).get('translation', {})
                out.append({
                    'id': str(b['key']),
                    'guild_id': str(r.get('group_id_belong_to', '')),
                    'x': trans.get('x', 0),
                    'y': trans.get('y', 0),
                    'z': trans.get('z', 0),
                    'level': r.get('base_camp_level', 1),
                    'area_radius': r.get('base_camp_area_radius', 0),
                })
            except Exception:
                continue
        return out

    @staticmethod
    def get_base_by_id(wsd: dict, base_id: str) -> dict | None:
        bid_clean = _normalize(base_id)
        for b in SaveProjections.get_bases(wsd):
            if _normalize(b['id']) == bid_clean:
                return b
        return None

    @staticmethod
    def get_base_coords(wsd: dict, base_id: str) -> tuple[float, float, float] | None:
        bid_clean = _normalize(base_id)
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        for b in base_list:
            if _normalize(b['key']) == bid_clean:
                try:
                    trans = _raw(b).get('transform', {}).get('translation', {})
                    return (trans.get('x', 0), trans.get('y', 0), trans.get('z', 0))
                except Exception:
                    return None
        return None

    # ------------------------------------------------------------------
    # Containers
    # ------------------------------------------------------------------

    @staticmethod
    def get_container_entries(wsd: dict) -> list[dict]:
        return wsd.get('ItemContainerSaveData', {}).get('value', [])

    @staticmethod
    def get_container_by_id(wsd: dict, container_id: str) -> dict | None:
        cid_clean = _normalize(container_id)
        for cont in SaveProjections.get_container_entries(wsd):
            key_id = cont.get('key', {}).get('ID', {}).get('value')
            if key_id and _normalize(key_id) == cid_clean:
                return cont
        return None

    @staticmethod
    def get_container_slot_count(wsd: dict, container_id: str) -> int:
        cont = SaveProjections.get_container_by_id(wsd, container_id)
        if cont is None:
            return 0
        try:
            return len(cont['value']['Slots']['value']['values'])
        except Exception:
            return 0

    @staticmethod
    def get_container_contents(wsd: dict, container_id: str) -> list[dict]:
        cont = SaveProjections.get_container_by_id(wsd, container_id)
        if cont is None:
            return []
        try:
            return list(cont['value']['Slots']['value']['values'])
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Map objects
    # ------------------------------------------------------------------

    @staticmethod
    def get_map_objects(wsd: dict) -> list[dict]:
        return wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])

    @staticmethod
    def get_map_object_save_data(wsd: dict) -> list[dict]:
        return wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])

    # ------------------------------------------------------------------
    # Character containers
    # ------------------------------------------------------------------

    @staticmethod
    def get_character_containers(wsd: dict) -> list[dict]:
        return wsd.get('CharacterContainerSaveData', {}).get('value', [])

    @staticmethod
    def get_group_save_data_map(wsd: dict) -> list[dict]:
        return wsd['GroupSaveDataMap']['value']

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_raw_data(entry: dict) -> dict:
        return _raw(entry)

    @staticmethod
    def get_save_param(entry: dict) -> dict:
        return _sp(entry)
