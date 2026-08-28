//! Persistent storage for exclusion zone configuration.
//!
//! Zone exclusions live in `zone_exclusions.json` under the app config dir so
//! they survive restarts and are not tied to any loaded save. Writes go through
//! the atomic write helper (temp file + rename) mirroring the settings store.

use std::path::{Path, PathBuf};

use serde_json;
use tauri::{AppHandle, Manager};

use crate::domain::exclusions::ExclusionConfig;
use crate::error::AppError;
use crate::storage::atomic_write;

pub const EXCLUSIONS_CONF_FILE: &str = "zone_exclusions.json";

/// Resolves the persistent config path under the app config directory.
pub fn exclusions_config_path(app: &AppHandle) -> Result<PathBuf, AppError> {
    let config_dir = app.path().app_config_dir().map_err(|error| {
        AppError::io(
            "exclusions_dir_unavailable",
            "Could not locate the PalTrainer config directory.",
            error,
        )
    })?;
    Ok(config_dir.join(EXCLUSIONS_CONF_FILE))
}

/// Loads the config from `path`. A missing or empty file yields defaults.
/// Parse errors are returned so the UI can surface a corrupt config.
pub fn load_exclusions_from_path(path: &Path) -> Result<ExclusionConfig, AppError> {
    if !path.exists() {
        return Ok(ExclusionConfig::default());
    }
    let text = std::fs::read_to_string(path).map_err(|error| {
        AppError::io(
            "exclusions_read_failed",
            "Could not read the exclusion zone config.",
            error,
        )
    })?;
    if text.trim().is_empty() {
        return Ok(ExclusionConfig::default());
    }
    serde_json::from_str(&text).map_err(|error| {
        AppError::io(
            "exclusions_parse_failed",
            "The exclusion zone config file is corrupt.",
            error,
        )
    })
}

/// Persists `config` to `path` atomically.
pub fn save_exclusions_to_path(path: &Path, config: &ExclusionConfig) -> Result<(), AppError> {
    let text = serde_json::to_string_pretty(config).map_err(|error| {
        AppError::io(
            "exclusions_serialize_failed",
            "Could not serialize the exclusion zone config.",
            error,
        )
    })?;
    atomic_write(path, text.as_bytes()).map_err(|error| {
        AppError::io(
            "exclusions_write_failed",
            "Could not write the exclusion zone config.",
            error,
        )
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::exclusions::{Point2D, ZoneExclusion};

    #[test]
    fn missing_file_loads_default_config() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("zone_exclusions.json");
        assert_eq!(
            load_exclusions_from_path(&path).unwrap(),
            ExclusionConfig::default()
        );
    }

    #[test]
    fn empty_file_loads_default_config() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("zone_exclusions.json");
        std::fs::write(&path, "  ").unwrap();
        assert_eq!(
            load_exclusions_from_path(&path).unwrap(),
            ExclusionConfig::default()
        );
    }

    #[test]
    fn roundtrips_a_config_with_zones() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("nested").join("zone_exclusions.json");
        let config = ExclusionConfig {
            excluded_player_uids: vec!["aaaa".into()],
            excluded_guild_ids: vec![],
            excluded_base_ids: vec![],
            zones: vec![ZoneExclusion {
                id: "zone_1".into(),
                name: "Spawn Sanctuary".into(),
                zone_type: "rectangle".into(),
                points: vec![Point2D { x: 0.0, y: 0.0 }, Point2D { x: 500.0, y: 500.0 }],
                protect_bases: true,
                protect_players: false,
                protect_structures: true,
            }],
        };

        save_exclusions_to_path(&path, &config).unwrap();
        assert_eq!(load_exclusions_from_path(&path).unwrap(), config);
    }

    #[test]
    fn corrupt_file_returns_parse_error() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("zone_exclusions.json");
        std::fs::write(&path, "{ not json ").unwrap();
        let err = load_exclusions_from_path(&path).unwrap_err();
        assert_eq!(err.code, "exclusions_parse_failed");
    }
}
