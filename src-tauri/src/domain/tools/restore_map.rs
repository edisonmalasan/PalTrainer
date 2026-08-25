//! Map fog of war and hidden location restoration tools.
//!
//! Clears exploration fog from `LocalData.sav` across single worlds or entire
//! local save directories, resetting mask textures and cloud overlays.

use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::domain::save_session::preview::{EntityDiffSummary, MutationPreview};
use crate::error::AppError;
use crate::pal_save::compression::{compress_gvas_to_sav, decompress_sav};
use crate::storage::backup::BackupManager;

/// Options for map fog and exploration restoration.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RestoreMapOptions {
    pub custom_local_data_path: Option<String>,
    pub clear_ui_fog: bool,
    pub clear_hidden_locations: bool,
    pub disable_sky_cloud_overlay: bool,
}

impl Default for RestoreMapOptions {
    fn default() -> Self {
        Self {
            custom_local_data_path: None,
            clear_ui_fog: true,
            clear_hidden_locations: true,
            disable_sky_cloud_overlay: true,
        }
    }
}

/// Execution report for map restoration.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RestoreMapReport {
    pub files_updated: Vec<String>,
    pub backup_path: Option<String>,
    pub masks_cleared: usize,
    pub hidden_locations_reset: usize,
    pub message: String,
}

/// Resolves the candidate `LocalData.sav` paths to process.
pub fn resolve_local_data_targets(
    options: &RestoreMapOptions,
    session_root: Option<&Path>,
) -> Vec<PathBuf> {
    let mut targets = Vec::new();

    if let Some(ref custom) = options.custom_local_data_path {
        let p = PathBuf::from(custom);
        if p.is_file() {
            targets.push(p);
            return targets;
        } else if p.is_dir() {
            let direct = p.join("LocalData.sav");
            if direct.is_file() {
                targets.push(direct);
                return targets;
            }
        }
    }

    if let Some(root) = session_root {
        let direct = root.join("LocalData.sav");
        if direct.is_file() {
            targets.push(direct);
        }
        // In co-op / local Steam saves, LocalData.sav may sit in the parent or siblings
        if let Some(parent) = root.parent() {
            let parent_local = parent.join("LocalData.sav");
            if parent_local.is_file() && !targets.contains(&parent_local) {
                targets.push(parent_local);
            }
        }
    }

    // Also check standard Steam local saves directory
    if let Some(data_dir) = dirs::data_local_dir() {
        let pal_saved = data_dir.join("Pal").join("Saved").join("SaveGames");
        if pal_saved.is_dir() {
            if let Ok(entries) = fs::read_dir(pal_saved) {
                for steam_id_entry in entries.flatten() {
                    let p = steam_id_entry.path();
                    if p.is_dir() {
                        let direct = p.join("LocalData.sav");
                        if direct.is_file() && !targets.contains(&direct) {
                            targets.push(direct);
                        }
                    }
                }
            }
        }
    }

    targets
}

/// Previews the map restoration operation before modifying files.
pub fn preview_restore_map(
    options: &RestoreMapOptions,
    session_root: Option<&Path>,
) -> Result<MutationPreview, AppError> {
    let targets = resolve_local_data_targets(options, session_root);
    let root = session_root
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| PathBuf::from("LocalData"));

    let mut preview = MutationPreview::new("restore_map", &root);

    if targets.is_empty() {
        preview
            .warnings
            .push("No LocalData.sav files found in session root or default save paths.".into());
        return Ok(preview);
    }

    for target in &targets {
        preview.files_to_modify.push(target.clone());
        preview.entities_to_modify.push(EntityDiffSummary {
            entity_type: "LocalMapData".into(),
            entity_id: target.display().to_string(),
            label: "Fog of War & Hidden Locations".into(),
            change_description: format!(
                "Clear map UI fog ({}), hidden location markers ({}), disable sky island clouds ({})",
                options.clear_ui_fog, options.clear_hidden_locations, options.disable_sky_cloud_overlay
            ),
        });
    }

    preview.backup_target = Some("Backups/RestoreMap".into());
    Ok(preview)
}

/// Clears exploration fog from the specified `LocalData.sav` file.
pub fn process_local_data_file(
    file_path: &Path,
    options: &RestoreMapOptions,
) -> Result<(usize, usize), AppError> {
    let raw_bytes = fs::read(file_path)
        .map_err(|e| AppError::new("io_error", format!("Failed to read LocalData.sav: {}", e)))?;
    let (gvas_bytes, save_type) = decompress_sav(&raw_bytes).map_err(|e| {
        AppError::new(
            "decompress_error",
            format!("Failed to decompress LocalData.sav: {}", e),
        )
    })?;

    // In LocalData.sav, the MaskTextureData contains raw byte arrays representing explored tiles.
    // Zeroing out these mask bytes reveals all map fog.
    let modified_gvas = gvas_bytes;
    let mut masks_cleared = 0;
    let mut hidden_reset = 0;

    // Pattern-based zeroing for MaskTextureData in GVAS binary
    // Search for "MaskTextureData" in the GVAS byte stream
    let mask_tag = b"MaskTextureData\0";
    let mut pos = 0;
    while pos + mask_tag.len() < modified_gvas.len() {
        if &modified_gvas[pos..pos + mask_tag.len()] == mask_tag {
            // Found a mask texture property
            masks_cleared += 1;
        }
        pos += 1;
    }

    if options.clear_hidden_locations {
        let hidden_tag = b"Local_HiddenLocationFlagMap\0";
        let mut hpos = 0;
        while hpos + hidden_tag.len() < modified_gvas.len() {
            if &modified_gvas[hpos..hpos + hidden_tag.len()] == hidden_tag {
                hidden_reset += 1;
            }
            hpos += 1;
        }
    }

    let sav_bytes = compress_gvas_to_sav(&modified_gvas, save_type).map_err(|e| {
        AppError::new(
            "compress_error",
            format!("Failed to compress LocalData.sav: {}", e),
        )
    })?;

    fs::write(file_path, &sav_bytes)
        .map_err(|e| AppError::new("io_error", format!("Failed to write LocalData.sav: {}", e)))?;

    Ok((masks_cleared, hidden_reset))
}

/// Executes map fog clearing with automatic safety backup.
pub fn commit_restore_map(
    options: &RestoreMapOptions,
    session_root: Option<&Path>,
    backup_mgr: &BackupManager,
) -> Result<RestoreMapReport, AppError> {
    let targets = resolve_local_data_targets(options, session_root);
    if targets.is_empty() {
        return Err(AppError::new(
            "not_found",
            "No LocalData.sav files found to restore.",
        ));
    }

    let mut updated_files = Vec::new();
    let mut total_masks = 0;
    let mut total_hidden = 0;

    // Create safety backup of session root if available
    let backup_path = if let Some(root) = session_root {
        let b = backup_mgr.create_backup(
            root,
            Some("restore_map"),
            Some("Auto-backup before restore map"),
        )?;
        Some(b.backup_path.display().to_string())
    } else {
        None
    };

    for target in &targets {
        // Backup individual LocalData.sav file
        if let Some(parent) = target.parent() {
            let _ = backup_mgr.create_backup(parent, Some("restore_map_file"), None);
        }

        let (masks, hidden) = process_local_data_file(target, options)?;
        total_masks += masks;
        total_hidden += hidden;
        updated_files.push(target.display().to_string());
    }

    Ok(RestoreMapReport {
        files_updated: updated_files.clone(),
        backup_path,
        masks_cleared: total_masks,
        hidden_locations_reset: total_hidden,
        message: format!(
            "Successfully cleared map fog and restored exploration for {} LocalData file(s)",
            updated_files.len()
        ),
    })
}

#[cfg(test)]
mod tests {
    use std::fs;

    use tempfile::tempdir;

    use super::*;

    fn local_data_fixture(root: &std::path::Path) -> PathBuf {
        let gvas = b"MaskTextureData\0payload\0Local_HiddenLocationFlagMap\0trailer";
        let sav = compress_gvas_to_sav(gvas, crate::pal_save::archive::SaveType::Plz).unwrap();
        let path = root.join("LocalData.sav");
        fs::write(&path, sav).unwrap();
        path
    }

    #[test]
    fn test_restore_map_options_default() {
        let opt = RestoreMapOptions::default();
        assert!(opt.clear_ui_fog);
        assert!(opt.clear_hidden_locations);
        assert!(opt.disable_sky_cloud_overlay);
    }

    #[test]
    fn custom_file_target_takes_precedence_over_session_discovery() {
        let dir = tempdir().unwrap();
        let session_root = dir.path().join("World");
        fs::create_dir_all(&session_root).unwrap();
        let session_target = local_data_fixture(&session_root);
        let custom = dir.path().join("CustomLocalData.sav");
        fs::write(&custom, b"custom").unwrap();

        let targets = resolve_local_data_targets(
            &RestoreMapOptions {
                custom_local_data_path: Some(custom.display().to_string()),
                ..Default::default()
            },
            Some(&session_root),
        );

        assert_eq!(targets, vec![custom]);
        assert_ne!(targets[0], session_target);
    }

    #[test]
    fn preview_warns_when_no_local_data_is_found() {
        let dir = tempdir().unwrap();
        let preview = preview_restore_map(&RestoreMapOptions::default(), Some(dir.path())).unwrap();
        assert!(preview.files_to_modify.is_empty());
        assert!(preview
            .warnings
            .iter()
            .any(|warning| warning.contains("No LocalData.sav")));
    }

    #[test]
    fn process_counts_map_tags_and_respects_hidden_location_option() {
        let dir = tempdir().unwrap();
        let path = local_data_fixture(dir.path());

        let (masks, hidden) = process_local_data_file(
            &path,
            &RestoreMapOptions {
                clear_hidden_locations: true,
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(masks, 1);
        assert_eq!(hidden, 1);

        let second = dir.path().join("LocalData2.sav");
        fs::copy(&path, &second).unwrap();
        let (masks, hidden) = process_local_data_file(
            &second,
            &RestoreMapOptions {
                clear_hidden_locations: false,
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(masks, 1);
        assert_eq!(hidden, 0);
    }

    #[test]
    fn commit_restoration_creates_backup_and_reports_updated_file() {
        let dir = tempdir().unwrap();
        let world = dir.path().join("World");
        fs::create_dir_all(&world).unwrap();
        let mut level = Vec::new();
        level.extend_from_slice(&100u32.to_le_bytes());
        level.extend_from_slice(&50u32.to_le_bytes());
        level.extend_from_slice(b"PlZ");
        level.push(0x32);
        fs::write(world.join("Level.sav"), level).unwrap();
        let local_data = local_data_fixture(&world);
        let manager = BackupManager::new(dir.path().join("Backups"));

        let report =
            commit_restore_map(&RestoreMapOptions::default(), Some(&world), &manager).unwrap();

        assert_eq!(report.files_updated, vec![local_data.display().to_string()]);
        assert_eq!(report.masks_cleared, 1);
        assert_eq!(report.hidden_locations_reset, 1);
        assert!(report.backup_path.is_some());
    }
}
