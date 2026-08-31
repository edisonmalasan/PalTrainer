from __future__ import annotations

from dataclasses import dataclass, field

from palworld_aio.inventory.container_ownership import ContainerOwnership


@dataclass
class OperationResult:
    """Structured result for a save-domain operation.

    Tracks changed entities, warnings, deleted files, and whether the
    operation requires explicit confirmation before being committed.
    """

    changed_entities: int = 0
    warnings: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    confirmation_required: bool = False
    ok: bool = True

    def merge(self, other: 'OperationResult') -> 'OperationResult':
        self.changed_entities += other.changed_entities
        self.warnings.extend(other.warnings)
        self.deleted_files.extend(other.deleted_files)
        self.confirmation_required = self.confirmation_required or other.confirmation_required
        self.ok = self.ok and other.ok
        return self


# ---------------------------------------------------------------------------
# Death-bag protection (pure collection + predicates)
# ---------------------------------------------------------------------------

def collect_death_bag_ids(wsd: dict) -> OperationResult:
    """Scan map objects for DroppedCharacter / DeathPenaltyChest entries.

    Returns protected instance/container id sets and counts.  Pure —
    does not touch ``constants``.
    """
    protected_instance_ids: set[str] = set()
    protected_container_ids: set[str] = set()
    dropped_pals = 0
    death_penalty_chests = 0
    map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objects:
        try:
            map_object_id = obj.get('MapObjectId', {}).get('value', '')
            raw_data = obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {})
            if map_object_id == 'DroppedCharacter':
                instance_id = raw_data.get('instance_id', '')
                stored_param_id = raw_data.get('stored_parameter_id', '')
                if instance_id:
                    protected_instance_ids.add(str(instance_id).replace('-', '').lower())
                if stored_param_id:
                    protected_instance_ids.add(str(stored_param_id).replace('-', '').lower())
                dropped_pals += 1
            elif map_object_id == 'DeathPenaltyChest':
                instance_id = raw_data.get('instance_id', '')
                if instance_id:
                    protected_instance_ids.add(str(instance_id).replace('-', '').lower())
                module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
                for module in module_map:
                    if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                        module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                        target_container_id = module_raw.get('target_container_id')
                        if target_container_id:
                            protected_container_ids.add(str(target_container_id).replace('-', '').lower())
                        break
                death_penalty_chests += 1
        except Exception:
            continue
    result = OperationResult()
    result.protected_instance_ids = protected_instance_ids
    result.protected_container_ids = protected_container_ids
    result.changed_entities = dropped_pals + death_penalty_chests
    return result


def is_dropped_character(obj: dict) -> bool:
    return obj.get('MapObjectId', {}).get('value') == 'DroppedCharacter'


def is_death_penalty_chest_obj(obj: dict) -> bool:
    return obj.get('MapObjectId', {}).get('value') == 'DeathPenaltyChest'


def is_death_bag(obj: dict) -> bool:
    return is_dropped_character(obj) or is_death_penalty_chest_obj(obj)


# ---------------------------------------------------------------------------
# Character map operations (pure, over a wsd document)
# ---------------------------------------------------------------------------

def delete_player_pals(wsd: dict, to_delete_uids: list) -> OperationResult:
    """Remove all Pals owned by the given player UIDs from the save.

    Uses container-ownership resolution for Pals whose ``OwnerPlayerUId``
    is missing.  Mutates the passed ``wsd`` in place and returns how many
    Pal bodies were removed.
    """
    char_save_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    uids_set = {uid.replace('-', '').lower() for uid in to_delete_uids if uid}
    ownership = ContainerOwnership.build(char_save_map, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    new_map = []
    removed_pals = 0
    for entry in char_save_map:
        try:
            val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type = entry['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid = val.get('OwnerPlayerUId', {}).get('value')
            owner_uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else ''
            in_delete_set = owner_uid_str in uids_set
            if not in_delete_set:
                effective = ownership.get_effective_owner(entry.get('key', {}).get('InstanceId', {}).get('value'), owner_uid)
                if effective in uids_set:
                    in_delete_set = True
            if struct_type in ('PalIndividualCharacterSaveParameter', 'PlayerCharacterSaveParameter') and in_delete_set:
                removed_pals += 1
                continue
        except Exception:
            pass
        new_map.append(entry)
    wsd['CharacterSaveParameterMap']['value'] = new_map
    return OperationResult(changed_entities=removed_pals)


def clean_character_save_parameter_map(data_source: dict, valid_uids: set) -> OperationResult:
    """Drop character map entries owned by UIDs outside ``valid_uids``.

    Entries without an owner, with a zero owner, or with a PlayerUId in
    ``valid_uids`` are always kept.  Returns the number of removed
    entries.
    """
    if 'CharacterSaveParameterMap' not in data_source:
        return OperationResult()
    entries = data_source['CharacterSaveParameterMap'].get('value', [])
    keep = []
    removed = 0
    for entry in entries:
        key = entry.get('key', {})
        value = entry.get('value', {}).get('RawData', {}).get('value', {})
        saveparam = value.get('object', {}).get('SaveParameter', {}).get('value', {})
        owner_uid_obj = saveparam.get('OwnerPlayerUId')
        if owner_uid_obj is None:
            keep.append(entry)
            continue
        owner_uid = owner_uid_obj.get('value', '')
        no_owner = owner_uid in ('', '00000000-0000-0000-0000-000000000000')
        player_uid = key.get('PlayerUId', {}).get('value', '')
        if player_uid and str(player_uid).replace('-', '') in valid_uids or str(owner_uid).replace('-', '') in valid_uids or no_owner:
            keep.append(entry)
        else:
            removed += 1
    entries[:] = keep
    return OperationResult(changed_entities=removed)
