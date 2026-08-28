//! Reference index harvested from the parsed Level.sav GVAS tree.
//!
//! Orphan sweeps compare recorded map keys (instance/container/dynamic-item
//! GUIDs) against cross-references. Only references the parser can verify count
//! toward deletion candidates. Entries inside `RawData` blobs whose decoders
//! are not implemented yet stay opaque and suppress deletions — per the
//! save-pipeline skill's roundtrip rule we never guess at unencoded bytes.

use std::path::Path;

use serde::Serialize;

use crate::domain::save_session::SaveSession;
use crate::error::AppError;
use crate::pal_save::compression::decompress_sav;
use crate::pal_save::gvas::model::{MapPropValue, PropertyEntry, PropertyValue, StructValue};
use crate::pal_save::gvas::reader::FArchiveReader;
use crate::pal_save::properties::dispatch::get_type_hints;

/// A real scan of world map keys and player save files for one save session.
#[derive(Debug, Clone, Default, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WorldIndex {
    /// Instance IDs from `CharacterSaveParameterMap` keys.
    pub character_ids: Vec<String>,
    /// Keys of `ItemContainerSaveData`.
    pub container_ids: Vec<String>,
    /// Keys of `CharacterContainerSaveData` (palbox / party containers).
    pub character_container_ids: Vec<String>,
    /// Keys of `DynamicItemSaveData` (singleton items).
    pub dynamic_item_ids: Vec<String>,
    /// Keys of `FoliageGridSaveDataMap`.
    pub foliage_grid_ids: Vec<String>,
    /// Keys of `WorkSaveData`.
    pub work_ids: Vec<String>,
    /// Number of `MapObjectSaveData` entries (world placement array).
    pub map_object_count: usize,
    /// Player UIDs from the `Players/` directory (`<uid>.sav`).
    pub player_uids: Vec<String>,
    /// Character references verifiable from parsed data (currently only player
    /// ownership — container slots and work assignments live in RawData blobs).
    pub referenced_character_ids: Vec<String>,
    pub referenced_dynamic_ids: Vec<String>,
    /// Number of `RawData` blobs whose decoders are not implemented yet.
    pub opaque_blob_count: usize,
    /// True when every reference source feeding the sweeps has been decoded.
    /// Harvest marks this false while RawData decoders are stubs, so sweeps
    /// suppress deletion candidates instead of guessing.
    pub references_complete: bool,
}

/// Decompresses and parses `Level.sav` from the session, harvesting the index.
pub fn harvest_world_index(session: &SaveSession) -> Result<WorldIndex, AppError> {
    let level_path = session.save_root().join("Level.sav");
    let bytes = std::fs::read(&level_path).map_err(|error| {
        AppError::io(
            "diagnostics_read_failed",
            "Could not read Level.sav for diagnostics.",
            error,
        )
    })?;
    let (gvas, _save_type) = decompress_sav(&bytes).map_err(|error| {
        AppError::new(
            "decompress_error",
            format!("Could not decompress Level.sav: {error}"),
        )
    })?;

    let mut reader = FArchiveReader::with_type_hints(&gvas, get_type_hints().clone());
    let properties = parse_gvas_properties(&mut reader)?;

    Ok(harvest_from_properties(
        &properties,
        list_player_uids(session.save_root())?,
    ))
}

/// Consumes the GVAS header and returns the root properties block.
/// Mirrors the field order used by `domain::tools::conversion`.
fn parse_gvas_properties(reader: &mut FArchiveReader<'_>) -> Result<Vec<PropertyEntry>, AppError> {
    let parse_err = |error: crate::error::SaveError| {
        AppError::new(
            "parse_error",
            format!("Level.sav GVAS parse failed: {error}"),
        )
    };
    let _magic = reader.u32().map_err(parse_err)?;
    let _save_game_version = reader.i32().map_err(parse_err)?;
    let _package_version = reader.i32().map_err(parse_err)?;
    let _major = reader.u16().map_err(parse_err)?;
    let _minor = reader.u16().map_err(parse_err)?;
    let _patch = reader.u16().map_err(parse_err)?;
    let _build = reader.u32().map_err(parse_err)?;
    let _branch = reader.fstring().map_err(parse_err)?;
    let _custom_version_format = reader.i32().map_err(parse_err)?;
    let custom_versions = reader.i32().map_err(parse_err)?;
    for _ in 0..custom_versions.max(0) {
        reader.take(16).map_err(parse_err)?;
        reader.i32().map_err(parse_err)?;
    }
    let _class_name = reader.fstring().map_err(parse_err)?;
    reader.properties_until_end("root").map_err(parse_err)
}

/// Lists player UIDs from the `Players/` directory (normalized, lowercase).
fn list_player_uids(save_root: &Path) -> Result<Vec<String>, AppError> {
    let players_dir = save_root.join("Players");
    let mut uids = Vec::new();
    let entries = match std::fs::read_dir(&players_dir) {
        Ok(entries) => entries,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(uids),
        Err(error) => {
            return Err(AppError::io(
                "diagnostics_read_failed",
                "Could not list the Players directory.",
                error,
            ))
        }
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) == Some("sav") {
            if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                uids.push(stem.to_lowercase().replace('-', ""));
            }
        }
    }
    Ok(uids)
}

/// Pure harvest from a parsed root properties block (unit-testable).
pub fn harvest_from_properties(entries: &[PropertyEntry], player_uids: Vec<String>) -> WorldIndex {
    let mut index = WorldIndex {
        player_uids,
        ..WorldIndex::default()
    };

    let world = match find_world_save_data(entries) {
        Some(world) => world,
        None => return index,
    };

    for entry in world {
        match entry.name.as_str() {
            "CharacterSaveParameterMap" => {
                index.character_ids =
                    map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "ItemContainerSaveData" => {
                index.container_ids =
                    map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "CharacterContainerSaveData" => {
                index.character_container_ids =
                    map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "DynamicItemSaveData" => {
                index.dynamic_item_ids =
                    map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "WorkSaveData" => {
                index.work_ids = map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "FoliageGridSaveDataMap" => {
                index.foliage_grid_ids =
                    map_key_ids(&entry.property.value, &mut index.opaque_blob_count);
            }
            "MapObjectSaveData" => {
                index.map_object_count = map_object_entry_count(&entry.property.value);
            }
            _ => {}
        }
    }

    // Player-owned characters are the only references verifiable today: the
    // player UID doubles as the character instance id in CharacterSaveParameterMap.
    index.referenced_character_ids = index.player_uids.clone();
    // RawData decoders (characters, container slots, works) are stubs, so the
    // reference graph is incomplete and deletion candidates must be suppressed.
    index.references_complete = false;
    index
}

fn find_world_save_data(entries: &[PropertyEntry]) -> Option<&[PropertyEntry]> {
    entries.iter().find_map(|entry| {
        if entry.name != "WorldSaveData" {
            return None;
        }
        match &entry.property.value {
            PropertyValue::Struct { value, .. } => match value.as_ref() {
                StructValue::Properties(props) => Some(props.as_slice()),
                _ => None,
            },
            _ => None,
        }
    })
}

/// Extracts normalized GUID strings from a map property's keys. Struct keys
/// that are plain GUIDs (16 bytes) are read directly; properties-style keys
/// (the Palworld container key layout) contribute their `InstanceId` property.
fn map_key_ids(value: &PropertyValue, opaque_blob_count: &mut usize) -> Vec<String> {
    let map = match value {
        PropertyValue::Map(map) => map,
        _ => return Vec::new(),
    };
    let mut ids = Vec::with_capacity(map.entries.len());
    for (key, map_value) in &map.entries {
        if let Some(id) = key_id(key) {
            ids.push(id);
        }
        *opaque_blob_count += count_raw_data_blobs(map_value);
    }
    ids
}

fn key_id(key: &MapPropValue) -> Option<String> {
    match key {
        MapPropValue::Struct(boxed) => match boxed.as_ref() {
            StructValue::Guid(guid) => Some(guid.normalized()),
            StructValue::Properties(props) => props.iter().find_map(|prop| {
                if prop.name != "InstanceId" {
                    return None;
                }
                match &prop.property.value {
                    PropertyValue::Struct { value, .. } => match value.as_ref() {
                        StructValue::Guid(guid) => Some(guid.normalized()),
                        _ => None,
                    },
                    _ => None,
                }
            }),
            _ => None,
        },
        _ => None,
    }
}

fn count_raw_data_blobs(value: &MapPropValue) -> usize {
    match value {
        MapPropValue::Struct(boxed) => match boxed.as_ref() {
            StructValue::Properties(props) => props
                .iter()
                .filter(|prop| {
                    prop.name == "RawData"
                        && matches!(
                            &prop.property.value,
                            PropertyValue::Array {
                                value: crate::pal_save::gvas::model::ArrayValue::Bytes(_),
                                ..
                            }
                        )
                })
                .count(),
            _ => 0,
        },
        _ => 0,
    }
}

fn map_object_entry_count(value: &PropertyValue) -> usize {
    match value {
        PropertyValue::Array {
            value: crate::pal_save::gvas::model::ArrayValue::Struct { values, .. },
            ..
        } => values.len(),
        _ => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::save_session::SaveSession;
    use crate::pal_save::archive::SaveType;
    use crate::pal_save::compression::compress_gvas_to_sav;
    use crate::pal_save::gvas::model::{ArrayValue, MapValue, Property};
    use crate::pal_save::gvas::uuid::PalUuid;
    use crate::pal_save::gvas::writer::FArchiveWriter;
    use std::fs;

    fn guid(hex: &str) -> PalUuid {
        PalUuid::parse(hex).unwrap()
    }

    /// Builds one `<Name>: MapProperty` entry with Guid keys and values whose
    /// struct properties carry a RawData byte blob (as real saves do).
    fn map_entry(name: &str, keys: &[PalUuid]) -> PropertyEntry {
        let entries = keys
            .iter()
            .map(|k| {
                let value_props = vec![PropertyEntry {
                    name: "RawData".to_string(),
                    property: Property::new(
                        "ArrayProperty",
                        PropertyValue::Array {
                            id: None,
                            array_type: "ByteProperty".into(),
                            value: ArrayValue::Bytes(vec![1, 2, 3]),
                        },
                    ),
                }];
                (
                    MapPropValue::Struct(Box::new(StructValue::Guid(*k))),
                    MapPropValue::Struct(Box::new(StructValue::Properties(value_props))),
                )
            })
            .collect();
        PropertyEntry {
            name: name.to_string(),
            property: Property::new(
                "MapProperty",
                PropertyValue::Map(Box::new(MapValue {
                    key_type: "StructProperty".into(),
                    value_type: "StructProperty".into(),
                    key_struct_type: Some("Guid".into()),
                    value_struct_type: None,
                    id: None,
                    entries,
                })),
            ),
        }
    }

    fn world_fixture(
        character_keys: &[PalUuid],
        container_keys: &[PalUuid],
        dynamic_keys: &[PalUuid],
    ) -> Vec<PropertyEntry> {
        vec![PropertyEntry {
            name: "WorldSaveData".to_string(),
            property: Property::new(
                "StructProperty",
                PropertyValue::Struct {
                    struct_type: "Pal.WorldSaveData".into(),
                    struct_id: PalUuid::from_raw([0u8; 16]),
                    id: None,
                    value: Box::new(StructValue::Properties(vec![
                        map_entry("CharacterSaveParameterMap", character_keys),
                        map_entry("ItemContainerSaveData", container_keys),
                        map_entry("DynamicItemSaveData", dynamic_keys),
                        map_entry("WorkSaveData", &[]),
                        map_entry("FoliageGridSaveDataMap", &[]),
                    ])),
                },
            ),
        }]
    }

    #[test]
    fn harvest_extracts_map_keys_and_flags_opaque_blobs() {
        let a = guid("00000000-0000-0000-0000-00000000000a");
        let b = guid("00000000-0000-0000-0000-00000000000b");
        let c = guid("00000000-0000-0000-0000-00000000000c");
        let props = world_fixture(&[a, b], &[c], &[a]);

        let index = harvest_from_properties(&props, vec!["aaa".into()]);

        assert_eq!(index.character_ids, vec![a.normalized(), b.normalized()]);
        assert_eq!(index.container_ids, vec![c.normalized()]);
        assert_eq!(index.dynamic_item_ids, vec![a.normalized()]);
        assert_eq!(index.player_uids, vec!["aaa"]);
        // Two character entries + one container + one dynamic entry, each value
        // carrying a RawData blob.
        assert_eq!(index.opaque_blob_count, 4);
        assert!(!index.references_complete);
        // Player UID doubles as the only verified character reference.
        assert_eq!(index.referenced_character_ids, vec!["aaa"]);
    }

    #[test]
    fn harvest_survives_missing_world_save_data() {
        let index = harvest_from_properties(&[], vec![]);
        assert!(index.character_ids.is_empty());
        assert_eq!(index.map_object_count, 0);
        assert!(!index.references_complete);
    }

    #[test]
    fn properties_style_keys_contribute_their_instance_id() {
        let instance = guid("00000000-0000-0000-0000-0000000000aa");
        let key_props = vec![
            guid_entry("PlayerUId", &guid("00000000-0000-0000-0000-000000000001")),
            guid_entry("InstanceId", &instance),
            guid_entry("Guid", &guid("00000000-0000-0000-0000-000000000002")),
        ];
        let entry = PropertyEntry {
            name: "CharacterSaveParameterMap".to_string(),
            property: Property::new(
                "MapProperty",
                PropertyValue::Map(Box::new(MapValue {
                    key_type: "StructProperty".into(),
                    value_type: "StructProperty".into(),
                    key_struct_type: Some("PalContainerKey".into()),
                    value_struct_type: None,
                    id: None,
                    entries: vec![(
                        MapPropValue::Struct(Box::new(StructValue::Properties(key_props))),
                        MapPropValue::Struct(Box::new(StructValue::Properties(vec![]))),
                    )],
                })),
            ),
        };
        let props = vec![PropertyEntry {
            name: "WorldSaveData".to_string(),
            property: Property::new(
                "StructProperty",
                PropertyValue::Struct {
                    struct_type: "Pal.WorldSaveData".into(),
                    struct_id: PalUuid::from_raw([0u8; 16]),
                    id: None,
                    value: Box::new(StructValue::Properties(vec![entry])),
                },
            ),
        }];

        let index = harvest_from_properties(&props, vec![]);
        assert_eq!(index.character_ids, vec![instance.normalized()]);
    }

    /// Full real path: fixture tree -> GVAS bytes -> compressed Level.sav ->
    /// SaveSession -> harvest. Exercises the actual decompress+parse pipeline.
    #[test]
    fn harvest_world_index_reads_a_real_compressed_level_sav() {
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path().join("World");
        fs::create_dir_all(root.join("Players")).unwrap();

        let a = guid("00000000-0000-0000-0000-00000000000a");
        let props = world_fixture(&[a], &[], &[]);

        let mut writer = FArchiveWriter::new();
        writer.u32(0x5341_5647); // GVAS magic
        writer.i32(3);
        writer.i32(522);
        writer.u16(5);
        writer.u16(1);
        writer.u16(1);
        writer.u32(0);
        writer.fstring("Palworld");
        writer.i32(3);
        writer.i32(0);
        writer.fstring("/Script/Pal.PalWorldSaveGame");
        writer.write_properties(&props); // appends the None terminator
        let gvas = writer.into_bytes();

        let sav = compress_gvas_to_sav(&gvas, SaveType::Plz).unwrap();
        fs::write(root.join("Level.sav"), &sav).unwrap();
        fs::write(
            root.join("Players")
                .join("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.sav"),
            b"p",
        )
        .unwrap();

        let session = SaveSession::open(&root).unwrap();
        let index = harvest_world_index(&session).unwrap();

        assert_eq!(index.character_ids, vec![a.normalized()]);
        assert_eq!(index.player_uids, vec!["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]);
        assert_eq!(index.opaque_blob_count, 1);
    }

    fn guid_entry(name: &str, g: &PalUuid) -> PropertyEntry {
        PropertyEntry {
            name: name.to_string(),
            property: Property::new(
                "StructProperty",
                PropertyValue::Struct {
                    struct_type: "Guid".into(),
                    struct_id: PalUuid::from_raw([0u8; 16]),
                    id: None,
                    value: Box::new(StructValue::Guid(*g)),
                },
            ),
        }
    }
}
