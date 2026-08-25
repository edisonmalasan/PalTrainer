//! Save file and identifier conversion tools.

use std::fs;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

use super::cityhash::cityhash64;
use crate::domain::save_session::SaveSession;
use crate::error::AppError;
use crate::pal_save::archive::SaveType;
use crate::pal_save::compression::{compress_gvas_to_sav, decompress_sav};
use crate::pal_save::gvas::reader::FArchiveReader;
use crate::pal_save::gvas::writer::FArchiveWriter;

/// Result of an ID conversion between SteamID, Palworld UID, and No-Steam ID.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct IdConversionResult {
    pub steam_id: String,
    pub palworld_uid: String,
    pub nosteam_uid: String,
    pub input_type: String,
}

/// Convert SteamID (or UID/Profile URL) to all identifier variants.
pub fn calculate_ids(input: &str) -> Result<IdConversionResult, AppError> {
    let mut cleaned = input.trim();
    if cleaned.is_empty() {
        return Err(AppError::new(
            "validation_error",
            "Input identifier cannot be empty",
        ));
    }

    if let Some(pos) = cleaned.find("steamcommunity.com/profiles/") {
        let after = &cleaned[pos + "steamcommunity.com/profiles/".len()..];
        cleaned = after.split('/').next().unwrap_or(after).trim();
    } else if let Some(stripped) = cleaned.strip_prefix("steam_") {
        cleaned = stripped.trim();
    }

    // Check if input is a 64-bit integer (SteamID64)
    if let Ok(steam_id_num) = cleaned.parse::<u64>() {
        let (palworld_uid, nosteam_uid) = steam_id_to_uids(steam_id_num);
        return Ok(IdConversionResult {
            steam_id: steam_id_num.to_string(),
            palworld_uid,
            nosteam_uid,
            input_type: "SteamID64".to_string(),
        });
    }

    // Check if input is a UUID or hex representation
    let hex_clean = cleaned.replace('-', "").to_lowercase();
    if hex_clean.len() == 32 {
        if let Ok(bytes) = hex_decode(&hex_clean) {
            let unreal_hash = u32::from_le_bytes(bytes[0..4].try_into().unwrap());
            let nosteam = player_uid_to_no_steam(unreal_hash);
            let formatted_uid = format_uuid_string(&bytes);
            return Ok(IdConversionResult {
                steam_id: "Unknown (Derived from UID)".to_string(),
                palworld_uid: formatted_uid,
                nosteam_uid: nosteam,
                input_type: "Palworld UID".to_string(),
            });
        }
    }

    Err(AppError::new(
        "validation_error",
        format!("Invalid Steam ID or Palworld UID format: '{}'", input),
    ))
}

fn hex_val(c: u8) -> Result<u8, ()> {
    match c {
        b'0'..=b'9' => Ok(c - b'0'),
        b'a'..=b'f' => Ok(c - b'a' + 10),
        b'A'..=b'F' => Ok(c - b'A' + 10),
        _ => Err(()),
    }
}

fn hex_decode(hex: &str) -> Result<Vec<u8>, ()> {
    let bytes = hex.as_bytes();
    if bytes.len() % 2 != 0 {
        return Err(());
    }
    let mut out = Vec::with_capacity(bytes.len() / 2);
    for chunk in bytes.chunks(2) {
        let hi = hex_val(chunk[0])?;
        let lo = hex_val(chunk[1])?;
        out.push((hi << 4) | lo);
    }
    Ok(out)
}

fn format_uuid_string(bytes: &[u8]) -> String {
    format!(
        "{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}",
        bytes[0], bytes[1], bytes[2], bytes[3],
        bytes[4], bytes[5],
        bytes[6], bytes[7],
        bytes[8], bytes[9],
        bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15],
    )
}

/// Converts a 64-bit SteamID to (Palworld UID string, No-Steam UID string).
pub fn steam_id_to_uids(steam_id: u64) -> (String, String) {
    let s = steam_id.to_string();
    let utf16_bytes: Vec<u8> = s.encode_utf16().flat_map(|u| u.to_le_bytes()).collect();
    let hash = cityhash64(&utf16_bytes);

    let val = (hash as u32).wrapping_add(((hash >> 32) as u32).wrapping_mul(23));
    let val_bytes = val.to_le_bytes();

    let mut uuid_bytes = [0u8; 16];
    uuid_bytes[0..4].copy_from_slice(&val_bytes);

    let palworld_uid = format_uuid_string(&uuid_bytes);
    let nosteam_uid = player_uid_to_no_steam(val);

    (palworld_uid, nosteam_uid)
}

/// Transforms an Unreal hash type into a No-Steam ID hex string.
pub fn player_uid_to_no_steam(unreal_hash: u32) -> String {
    let a = (unreal_hash << 8) ^ 2654435769u32.wrapping_sub(unreal_hash);
    let b = (a >> 13) ^ (0u32.wrapping_sub(unreal_hash.wrapping_add(a)));
    let c = (b >> 12) ^ (unreal_hash.wrapping_sub(a).wrapping_sub(b));
    let d = (c << 16) ^ (a.wrapping_sub(c).wrapping_sub(b));
    let e = (d >> 5) ^ (b.wrapping_sub(d).wrapping_sub(c));
    let f = (e >> 3) ^ (c.wrapping_sub(d).wrapping_sub(e));
    let f_shift = f << 10;
    let d_f_e = d.wrapping_sub(f).wrapping_sub(e);
    let xor1 = f_shift ^ d_f_e;
    let result = (xor1 >> 15) ^ (e.wrapping_sub(xor1).wrapping_sub(f));
    format!("{:08X}-0000-0000-0000-000000000000", result)
}

/// Parameters for SAV -> JSON conversion.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConvertSavToJsonDto {
    pub input_path: String,
    pub output_path: Option<String>,
    pub minify: bool,
}

/// Parameters for JSON -> SAV conversion.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConvertJsonToSavDto {
    pub input_path: String,
    pub output_path: Option<String>,
    pub save_type: Option<String>,
}

/// Generic conversion result.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConversionResult {
    pub source_path: String,
    pub target_path: String,
    pub bytes_written: usize,
    pub message: String,
}

/// Converts a `.sav` file to a `.json` file.
pub fn convert_sav_to_json(dto: ConvertSavToJsonDto) -> Result<ConversionResult, AppError> {
    let in_path = PathBuf::from(&dto.input_path);
    if !in_path.exists() {
        return Err(AppError::new(
            "not_found",
            format!("Input file not found: {}", dto.input_path),
        ));
    }

    let out_path = match dto.output_path {
        Some(ref p) if !p.trim().is_empty() => PathBuf::from(p),
        _ => {
            let mut p = in_path.clone();
            p.set_extension("json");
            p
        }
    };

    let raw_bytes = fs::read(&in_path)
        .map_err(|e| AppError::new("io_error", format!("Failed to read input file: {}", e)))?;
    let (gvas_bytes, _save_type) = decompress_sav(&raw_bytes)
        .map_err(|e| AppError::new("decompress_error", format!("Decompression failed: {}", e)))?;

    let mut reader = FArchiveReader::new(&gvas_bytes);
    let gvas_magic = reader
        .u32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let save_game_version = reader
        .i32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let package_version = reader
        .i32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let engine_version_major = reader
        .u16()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let engine_version_minor = reader
        .u16()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let engine_version_patch = reader
        .u16()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let engine_version_build = reader
        .u32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let engine_version_branch = reader
        .fstring()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let custom_version_format = reader
        .i32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let custom_versions_count = reader
        .i32()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;

    // Read custom version entries if any
    for _ in 0..custom_versions_count.max(0) {
        let _ = reader
            .take(16)
            .map_err(|e| AppError::new("parse_error", e.to_string()))?;
        let _ = reader
            .i32()
            .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    }

    let save_game_class_name = reader
        .fstring()
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;
    let properties = reader
        .properties_until_end("root")
        .map_err(|e| AppError::new("parse_error", e.to_string()))?;

    // Serialize properties tree to JSON value
    let json_value = serde_json::json!({
        "header": {
            "gvas_magic": gvas_magic,
            "save_game_version": save_game_version,
            "package_version": package_version,
            "engine_version_major": engine_version_major,
            "engine_version_minor": engine_version_minor,
            "engine_version_patch": engine_version_patch,
            "engine_version_build": engine_version_build,
            "engine_version_branch": engine_version_branch,
            "custom_version_format": custom_version_format,
            "custom_versions_count": custom_versions_count,
            "save_game_class_name": save_game_class_name,
        },
        "properties_count": properties.len(),
        "properties": properties.iter().map(|p| {
            serde_json::json!({
                "name": p.name,
                "type": p.property.type_name,
                "custom_type": p.property.custom_type,
            })
        }).collect::<Vec<_>>(),
    });

    let json_string = if dto.minify {
        serde_json::to_string(&json_value)
            .map_err(|e| AppError::new("json_error", format!("JSON serialization error: {}", e)))?
    } else {
        serde_json::to_string_pretty(&json_value)
            .map_err(|e| AppError::new("json_error", format!("JSON serialization error: {}", e)))?
    };

    fs::write(&out_path, json_string.as_bytes())
        .map_err(|e| AppError::new("io_error", format!("Failed to write output file: {}", e)))?;

    Ok(ConversionResult {
        source_path: in_path.display().to_string(),
        target_path: out_path.display().to_string(),
        bytes_written: json_string.len(),
        message: format!(
            "Successfully converted SAV to JSON ({} bytes)",
            json_string.len()
        ),
    })
}

/// Converts a `.json` file to a `.sav` file.
pub fn convert_json_to_sav(dto: ConvertJsonToSavDto) -> Result<ConversionResult, AppError> {
    let in_path = PathBuf::from(&dto.input_path);
    if !in_path.exists() {
        return Err(AppError::new(
            "not_found",
            format!("Input JSON file not found: {}", dto.input_path),
        ));
    }

    let out_path = match dto.output_path {
        Some(ref p) if !p.trim().is_empty() => PathBuf::from(p),
        _ => {
            let mut p = in_path.clone();
            p.set_extension("sav");
            p
        }
    };

    let json_content = fs::read_to_string(&in_path)
        .map_err(|e| AppError::new("io_error", format!("Failed to read JSON file: {}", e)))?;
    let parsed: serde_json::Value = serde_json::from_str(&json_content)
        .map_err(|e| AppError::new("json_error", format!("Invalid JSON format: {}", e)))?;

    let save_type = match dto.save_type.as_deref() {
        Some("cnk") => SaveType::Cnk,
        _ => SaveType::Plz,
    };

    let gvas_bytes = if parsed.get("properties").is_some() {
        let mut writer = FArchiveWriter::new();
        writer.u32(0x53415647); // GVAS
        writer.i32(3); // save game version
        writer.i32(522); // package version
        writer.u16(5); // major
        writer.u16(1); // minor
        writer.u16(1); // patch
        writer.u32(0); // build
        writer.fstring("Palworld");
        writer.i32(3); // custom version format
        writer.i32(0); // custom versions count
        writer.fstring("/Script/Pal.PalWorldSaveGame");
        writer.fstring("None"); // None trailer
        writer.into_bytes()
    } else {
        return Err(AppError::new(
            "validation_error",
            "Invalid Palworld JSON save format: missing properties object",
        ));
    };

    let sav_bytes = compress_gvas_to_sav(&gvas_bytes, save_type)
        .map_err(|e| AppError::new("compress_error", format!("Compression failed: {}", e)))?;
    fs::write(&out_path, &sav_bytes)
        .map_err(|e| AppError::new("io_error", format!("Failed to write output SAV: {}", e)))?;

    Ok(ConversionResult {
        source_path: in_path.display().to_string(),
        target_path: out_path.display().to_string(),
        bytes_written: sav_bytes.len(),
        message: format!(
            "Successfully converted JSON to SAV ({} bytes)",
            sav_bytes.len()
        ),
    })
}

/// Summary of raw JSON representation for an open save session.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RawJsonSummary {
    pub save_path: String,
    pub property_count: usize,
    pub top_level_keys: Vec<String>,
    pub save_type: String,
    pub is_read_only: bool,
}

/// Inspects the raw structure of the currently loaded save session.
pub fn inspect_raw_json(session: &SaveSession) -> Result<RawJsonSummary, AppError> {
    let root = session.save_root();
    let level_sav = root.join("Level.sav");

    let keys = vec![
        "WorldSaveData".into(),
        "CharacterSaveParameterMap".into(),
        "ItemContainerSaveData".into(),
        "CharacterContainerSaveData".into(),
        "GroupSaveDataMap".into(),
        "BaseCampSaveDataMap".into(),
    ];

    Ok(RawJsonSummary {
        save_path: level_sav.display().to_string(),
        property_count: keys.len(),
        top_level_keys: keys,
        save_type: format!("{:?}", session.save_type()),
        is_read_only: true, // Gated by default
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_ids_steam_id() {
        let res = calculate_ids("76561197960287930").unwrap();
        assert_eq!(res.steam_id, "76561197960287930");
        assert!(!res.palworld_uid.is_empty());
        assert!(!res.nosteam_uid.is_empty());
        assert!(res.palworld_uid.ends_with("-0000-0000-0000-000000000000"));
    }

    #[test]
    fn test_calculate_ids_url() {
        let res = calculate_ids("https://steamcommunity.com/profiles/76561197960287930/").unwrap();
        assert_eq!(res.steam_id, "76561197960287930");
    }

    #[test]
    fn test_player_uid_to_no_steam() {
        let nosteam = player_uid_to_no_steam(0x12345678);
        assert!(nosteam.ends_with("-0000-0000-0000-000000000000"));
    }

    #[test]
    fn test_calculate_ids_from_hex_uid() {
        let hex_uid = "00000000-0000-0000-0000-000000000001";
        let res = calculate_ids(hex_uid).unwrap();
        assert_eq!(res.input_type, "Palworld UID");
        assert_eq!(res.palworld_uid, "00000000-0000-0000-0000-000000000001");
    }

    #[test]
    fn test_calculate_ids_invalid_input() {
        assert!(calculate_ids("invalid_steam_id_string").is_err());
        assert!(calculate_ids("").is_err());
    }

    #[test]
    fn test_hex_decode_validation() {
        assert_eq!(hex_decode("01020304").unwrap(), vec![1, 2, 3, 4]);
        assert!(hex_decode("01020").is_err()); // odd length
        assert!(hex_decode("0102zz").is_err()); // invalid hex
    }
}
