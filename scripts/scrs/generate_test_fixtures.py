#!/usr/bin/env python3
"""Generate sanitized synthetic Palworld save fixtures for test suites.

Creates minimal valid Level.sav, LocalData.sav, Player save, and Player DPS save
files under tests/save_test/ adhering to the zero-real-save security policy.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from palsav.gvas import GvasFile
from palsav.core import compress_gvas_to_sav
from palsav.paltypes import PALWORLD_CUSTOM_PROPERTIES


def create_header(class_name: str) -> dict:
    return {
        "magic": 1396790855,
        "save_game_version": 3,
        "package_file_version_ue4": 522,
        "package_file_version_ue5": 1008,
        "engine_version_major": 5,
        "engine_version_minor": 1,
        "engine_version_patch": 1,
        "engine_version_changelist": 0,
        "engine_version_branch": "++UE5+Release-5.1",
        "custom_version_format": 3,
        "custom_versions": [],
        "save_game_class_name": class_name,
    }


def generate_sanitized_fixtures(target_dir: Path | None = None) -> Path:
    if target_dir is None:
        target_dir = PROJECT_DIR / "tests" / "save_test"

    players_dir = target_dir / "Players"
    players_dir.mkdir(parents=True, exist_ok=True)

    # 1. Level.sav
    level_dict = {
        "header": create_header("/Script/Pal.PalWorldSaveGame"),
        "properties": {
            "Version": {"type": "IntProperty", "value": 100},
            "Timestamp": {"type": "Int64Property", "value": 123456789},
            "worldSaveData": {
                "type": "StructProperty",
                "struct_type": "PalWorldSaveData",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "value": {
                    "CharacterSaveParameterMap": {
                        "type": "MapProperty",
                        "key_type": "StructProperty",
                        "value_type": "StructProperty",
                        "key_struct_type": "PalInstanceId",
                        "value_struct_type": "PalIndividualCharacterSaveParameter",
                        "value": [
                            {
                                "key": {
                                    "PlayerUId": {
                                        "type": "StructProperty",
                                        "struct_type": "Guid",
                                        "struct_id": "00000000-0000-0000-0000-000000000000",
                                        "value": "00000000-0000-0000-0000-000000000001",
                                    },
                                    "InstanceId": {
                                        "type": "StructProperty",
                                        "struct_type": "Guid",
                                        "struct_id": "00000000-0000-0000-0000-000000000000",
                                        "value": "11111111-1111-1111-1111-111111111111",
                                    },
                                    "DebugName": {"type": "StrProperty", "value": "TestCharacter"},
                                },
                                "value": {
                                    "RawData": {
                                        "array_type": "ByteProperty",
                                        "type": "ArrayProperty",
                                        "custom_type": ".worldSaveData.CharacterSaveParameterMap.Value.RawData",
                                        "value": {
                                            "object": {
                                                "SaveParameter": {
                                                    "type": "StructProperty",
                                                    "struct_type": "PalIndividualCharacterSaveParameter",
                                                    "struct_id": "00000000-0000-0000-0000-000000000000",
                                                    "value": {
                                                        "IsPlayer": {"type": "BoolProperty", "value": True}
                                                    },
                                                }
                                            },
                                            "unknown_bytes": [0, 0, 0, 0],
                                            "group_id": "00000000-0000-0000-0000-000000000001",
                                            "trailing_bytes": [0, 0, 0, 0],
                                        },
                                    }
                                },
                            }
                        ],
                    },
                    "GroupSaveDataMap": {
                        "type": "MapProperty",
                        "key_type": "StructProperty",
                        "value_type": "StructProperty",
                        "key_struct_type": "Guid",
                        "value_struct_type": "PalGroupSaveData",
                        "custom_type": ".worldSaveData.GroupSaveDataMap",
                        "value": [],
                    },
                },
            },
        },
        "trailer": b"\x00\x00\x00\x00",
    }
    gvas_level = GvasFile.load(level_dict)
    level_sav_bytes = compress_gvas_to_sav(
        gvas_level.write(custom_properties=PALWORLD_CUSTOM_PROPERTIES), 0x32
    )
    (target_dir / "Level.sav").write_bytes(level_sav_bytes)

    # 2. LocalData.sav
    local_dict = {
        "header": create_header("/Script/Pal.PalLocalWorldSaveGame"),
        "properties": {
            "SaveData": {
                "type": "StructProperty",
                "struct_type": "PalLocalWorldSaveData",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "value": {
                    "WorldName": {"type": "StrProperty", "value": "SanitizedTestWorld"}
                },
            }
        },
        "trailer": b"\x00\x00\x00\x00",
    }
    gvas_local = GvasFile.load(local_dict)
    local_sav_bytes = compress_gvas_to_sav(
        gvas_local.write(custom_properties=PALWORLD_CUSTOM_PROPERTIES), 0x32
    )
    (target_dir / "LocalData.sav").write_bytes(local_sav_bytes)

    # 3. Players/00000000000000000000000000000001.sav
    player_dict = {
        "header": create_header("/Script/Pal.PalWorldPlayerSaveGame"),
        "properties": {
            "Version": {"type": "IntProperty", "value": 100},
            "SaveData": {
                "type": "StructProperty",
                "struct_type": "PalWorldPlayerSaveData",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "value": {
                    "PlayerUId": {
                        "type": "StructProperty",
                        "struct_type": "Guid",
                        "struct_id": "00000000-0000-0000-0000-000000000000",
                        "value": "00000000-0000-0000-0000-000000000001",
                    }
                },
            },
        },
        "trailer": b"\x00\x00\x00\x00",
    }
    gvas_player = GvasFile.load(player_dict)
    player_sav_bytes = compress_gvas_to_sav(
        gvas_player.write(custom_properties=PALWORLD_CUSTOM_PROPERTIES), 0x32
    )
    (players_dir / "00000000000000000000000000000001.sav").write_bytes(player_sav_bytes)

    # 4. Players/00000000000000000000000000000001_dps.sav
    player_dps_dict = {
        "header": create_header("/Script/Pal.PalWorldPlayerDynamicSaveGame"),
        "properties": {
            "Version": {"type": "IntProperty", "value": 100}
        },
        "trailer": b"\x00\x00\x00\x00",
    }
    gvas_player_dps = GvasFile.load(player_dps_dict)
    player_dps_bytes = compress_gvas_to_sav(
        gvas_player_dps.write(custom_properties=PALWORLD_CUSTOM_PROPERTIES), 0x32
    )
    (players_dir / "00000000000000000000000000000001_dps.sav").write_bytes(player_dps_bytes)

    return target_dir


if __name__ == "__main__":
    out = generate_sanitized_fixtures()
    print(f"Sanitized fixtures generated at: {out}")
