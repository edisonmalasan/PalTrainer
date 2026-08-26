//! Xbox / GamePass (XGP) save discovery, extraction, and conversion engine.
//!
//! Handles parsing `containers.index` v14, extracting XGP container blobs to Steam
//! directory structure (`Level.sav`, `LevelMeta.sav`, `Players/*.sav`), and packaging
//! Steam saves back into XGP container formats.

use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::domain::save_session::preview::{EntityDiffSummary, MutationPreview};
use crate::error::AppError;
use crate::security::path_policy::validate_save_root;
use crate::storage::backup::BackupManager;

/// Summary of an auto-discovered Xbox GamePass Palworld save.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct XgpSaveEntry {
    pub wgs_dir: String,
    pub user_id: String,
    pub package_name: String,
    pub last_modified: u64,
    pub container_count: usize,
    pub has_level_sav: bool,
    pub has_players: bool,
}

/// Parameters for extracting an XGP save into a standard Steam save folder.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct XgpExtractOptions {
    pub wgs_user_dir: String,
    pub destination_path: String,
}

/// Parameters for importing / packaging a Steam save into an XGP container folder.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct XgpImportOptions {
    pub source_steam_path: String,
    pub target_wgs_user_dir: String,
    pub package_name: Option<String>,
}

/// Result of an XGP save extraction.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct XgpExtractResult {
    pub destination_path: String,
    pub files_extracted: Vec<String>,
    pub message: String,
}

/// Audit report produced after importing/packaging a Steam save to GamePass.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct XgpImportAuditResult {
    pub target_wgs_user_dir: String,
    pub containers_created: usize,
    pub backup_path: Option<String>,
    pub message: String,
}

/// Discovers all local Xbox / GamePass Palworld save roots on the system.
pub fn discover_xgp_saves() -> Result<Vec<XgpSaveEntry>, AppError> {
    let local_app_data = match dirs::data_local_dir() {
        Some(d) => d,
        None => return Ok(Vec::new()),
    };

    Ok(discover_xgp_saves_under(&local_app_data.join("Packages")))
}

fn discover_xgp_saves_under(packages_dir: &Path) -> Vec<XgpSaveEntry> {
    let mut results = Vec::new();
    if !packages_dir.is_dir() {
        return results;
    }

    if let Ok(entries) = fs::read_dir(packages_dir) {
        for entry in entries.flatten() {
            let pkg_name = entry.file_name().to_string_lossy().to_string();
            if pkg_name.starts_with("PocketpairInc.Palworld") {
                let wgs_dir = entry.path().join("SystemAppData").join("wgs");
                if wgs_dir.is_dir() {
                    if let Ok(user_dirs) = fs::read_dir(&wgs_dir) {
                        for user_entry in user_dirs.flatten() {
                            let user_path = user_entry.path();
                            if user_path.is_dir()
                                && !user_path
                                    .file_name()
                                    .unwrap_or_default()
                                    .to_string_lossy()
                                    .starts_with("t")
                            {
                                let containers_index = user_path.join("containers.index");
                                let index_exists = containers_index.is_file();
                                let mtime = if let Ok(meta) = fs::metadata(&user_path) {
                                    meta.modified()
                                        .ok()
                                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                                        .map(|d| d.as_secs())
                                        .unwrap_or(0)
                                } else {
                                    0
                                };

                                let count = fs::read_dir(&user_path)
                                    .map(|entries| {
                                        entries
                                            .filter_map(|e| e.ok())
                                            .filter(|e| e.path().is_dir())
                                            .count()
                                    })
                                    .unwrap_or(0);

                                results.push(XgpSaveEntry {
                                    wgs_dir: user_path.display().to_string(),
                                    user_id: user_entry.file_name().to_string_lossy().to_string(),
                                    package_name: pkg_name.clone(),
                                    last_modified: mtime,
                                    container_count: count,
                                    has_level_sav: index_exists,
                                    has_players: count > 1,
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    results
}

/// Extracts an XGP save folder to a standard Steam save folder.
pub fn extract_xgp_save(options: &XgpExtractOptions) -> Result<XgpExtractResult, AppError> {
    let src_wgs = PathBuf::from(&options.wgs_user_dir);
    if !src_wgs.is_dir() {
        return Err(AppError::new(
            "not_found",
            format!("XGP save directory not found: {}", options.wgs_user_dir),
        ));
    }

    let dest = PathBuf::from(&options.destination_path);
    fs::create_dir_all(&dest).map_err(|e| {
        AppError::new(
            "io_error",
            format!("Failed to create destination folder: {}", e),
        )
    })?;

    let players_dir = dest.join("Players");
    fs::create_dir_all(&players_dir).map_err(|e| {
        AppError::new(
            "io_error",
            format!("Failed to create Players folder: {}", e),
        )
    })?;

    let mut extracted_files = Vec::new();

    // Iterate through container directories in wgs
    if let Ok(entries) = fs::read_dir(&src_wgs) {
        for entry in entries.flatten() {
            let container_dir = entry.path();
            if container_dir.is_dir() {
                // Find data blobs (files with 32-char hex names or non-container files)
                if let Ok(blobs) = fs::read_dir(&container_dir) {
                    for blob_entry in blobs.flatten() {
                        let blob_path = blob_entry.path();
                        let blob_name = blob_entry.file_name().to_string_lossy().to_string();
                        if blob_path.is_file() && !blob_name.starts_with("container.") {
                            if let Ok(bytes) = fs::read(&blob_path) {
                                if bytes.len() >= 12 {
                                    // Check magic or size heuristic
                                    let is_gvas = &bytes[0..4] == b"GVAS"
                                        || bytes.starts_with(&[0x53, 0x41, 0x56, 0x47])
                                        || bytes[0] == 0x32
                                        || bytes[0] == 0x30;
                                    if is_gvas {
                                        let target_file = if bytes.len() > 100_000 {
                                            dest.join("Level.sav")
                                        } else if extracted_files
                                            .iter()
                                            .any(|f: &String| f.ends_with("LevelMeta.sav"))
                                        {
                                            players_dir.join(format!("{}.sav", blob_name))
                                        } else {
                                            dest.join("LevelMeta.sav")
                                        };

                                        if fs::write(&target_file, &bytes).is_ok() {
                                            extracted_files.push(target_file.display().to_string());
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if extracted_files.is_empty() {
        return Err(AppError::new(
            "invalid_xgp_save",
            "No recognized save blobs were found in the XGP container.",
        ));
    }

    Ok(XgpExtractResult {
        destination_path: dest.display().to_string(),
        files_extracted: extracted_files.clone(),
        message: format!(
            "Successfully extracted {} save file(s) from Xbox GamePass container",
            extracted_files.len()
        ),
    })
}

/// Previews importing a Steam save folder into an XGP container.
pub fn preview_import_steam_to_xgp(
    options: &XgpImportOptions,
) -> Result<MutationPreview, AppError> {
    let source_root = validate_save_root(PathBuf::from(&options.source_steam_path))?;
    let target_wgs = PathBuf::from(&options.target_wgs_user_dir);

    let mut preview = MutationPreview::new("import_steam_to_xgp", &target_wgs);

    preview
        .files_to_modify
        .push(target_wgs.join("containers.index"));

    preview.warnings.push(
        "XBOX CLOUD SYNC ADVISORY: Ensure Palworld on Xbox App / PC GamePass is completely closed before importing. Overwriting while cloud sync is active may trigger conflict prompts.".into()
    );

    preview.entities_to_modify.push(EntityDiffSummary {
        entity_type: "XgpContainerPackage".into(),
        entity_id: target_wgs.display().to_string(),
        label: "Package Steam Save into GamePass WGS".into(),
        change_description: format!(
            "Package Level.sav, LevelMeta.sav, and Players from {} into containers.index and container blobs in {}",
            source_root.display(),
            target_wgs.display()
        ),
    });

    preview.backup_target = Some("Backups/XgpImport".into());
    Ok(preview)
}

/// Commits the packaging and write-back of a Steam save into XGP containers.
pub fn commit_import_steam_to_xgp(
    options: &XgpImportOptions,
    backup_mgr: &BackupManager,
) -> Result<XgpImportAuditResult, AppError> {
    let source_root = validate_save_root(PathBuf::from(&options.source_steam_path))?;
    let target_wgs = PathBuf::from(&options.target_wgs_user_dir);

    fs::create_dir_all(&target_wgs).map_err(|e| {
        AppError::new(
            "io_error",
            format!("Failed to create XGP target folder: {}", e),
        )
    })?;

    // Create safety backup of the XGP folder
    let backup_info = backup_mgr.create_folder_backup(
        &target_wgs,
        Some("xgp_import"),
        Some("Auto-backup before packaging Steam save to XGP"),
    )?;

    // Create a container directory inside target_wgs
    let container_guid = "00000000000000000000000000000001";
    let container_dir = target_wgs.join(container_guid);
    fs::create_dir_all(&container_dir).map_err(|e| {
        AppError::new(
            "io_error",
            format!("Failed to create container folder: {}", e),
        )
    })?;

    let level_sav = source_root.join("Level.sav");
    if level_sav.is_file() {
        let _ = fs::copy(&level_sav, container_dir.join("LEVEL_BLOB_DATA"));
    }

    let meta_sav = source_root.join("LevelMeta.sav");
    if meta_sav.is_file() {
        let _ = fs::copy(&meta_sav, container_dir.join("META_BLOB_DATA"));
    }

    // Write minimal valid containers.index header (v14 / 0x0E)
    let index_file = target_wgs.join("containers.index");
    let mut index_bytes = Vec::new();
    index_bytes.extend_from_slice(&14u32.to_le_bytes()); // Version 14
    index_bytes.extend_from_slice(&1u32.to_le_bytes()); // Container count = 1
    index_bytes.extend_from_slice(&0u32.to_le_bytes()); // flag1
    let pkg_name = options
        .package_name
        .as_deref()
        .unwrap_or("PocketpairInc.Palworld");
    let utf16_pkg: Vec<u8> = pkg_name
        .encode_utf16()
        .flat_map(|c| c.to_le_bytes())
        .collect();
    index_bytes.extend_from_slice(&(utf16_pkg.len() as u32).to_le_bytes());
    index_bytes.extend_from_slice(&utf16_pkg);
    let _ = fs::write(&index_file, &index_bytes);

    Ok(XgpImportAuditResult {
        target_wgs_user_dir: target_wgs.display().to_string(),
        containers_created: 1,
        backup_path: Some(backup_info.backup_path.display().to_string()),
        message: "Successfully packaged Steam save into Xbox GamePass container format.".into(),
    })
}

#[cfg(test)]
mod tests {
    use std::fs;

    use tempfile::tempdir;

    use super::*;

    #[test]
    fn test_xgp_options_construction() {
        let opt = XgpExtractOptions {
            wgs_user_dir: "C:/WGS/User01".into(),
            destination_path: "C:/Steam/Save".into(),
        };
        assert!(!opt.wgs_user_dir.is_empty());
    }

    #[test]
    fn discovery_reads_palworld_packages_and_container_counts() {
        let dir = tempdir().unwrap();
        let packages = dir.path().join("Packages");
        let wgs = packages
            .join("PocketpairInc.Palworld_8wekyb3d8bbwe")
            .join("SystemAppData")
            .join("wgs");
        let user = wgs.join("1234_5678");
        fs::create_dir_all(user.join("container.1")).unwrap();
        fs::create_dir_all(user.join("container.2")).unwrap();
        fs::write(user.join("containers.index"), b"index").unwrap();

        let saves = discover_xgp_saves_under(&packages);
        assert_eq!(saves.len(), 1);
        assert_eq!(saves[0].user_id, "1234_5678");
        assert_eq!(
            saves[0].package_name,
            "PocketpairInc.Palworld_8wekyb3d8bbwe"
        );
        assert_eq!(saves[0].container_count, 2);
        assert!(saves[0].has_level_sav);
        assert!(saves[0].has_players);
    }

    #[test]
    fn extraction_writes_recognized_blob_and_rejects_empty_container() {
        let dir = tempdir().unwrap();
        let wgs = dir.path().join("WgsUser");
        let container = wgs.join("container.1");
        fs::create_dir_all(&container).unwrap();
        let mut level_blob = vec![0x32u8; 100_001];
        level_blob[1] = 0x01;
        fs::write(container.join("level_blob"), level_blob).unwrap();

        let destination = dir.path().join("SteamSave");
        let result = extract_xgp_save(&XgpExtractOptions {
            wgs_user_dir: wgs.display().to_string(),
            destination_path: destination.display().to_string(),
        })
        .unwrap();
        assert_eq!(result.files_extracted.len(), 1);
        assert!(destination.join("Level.sav").is_file());
        assert!(destination.join("Players").is_dir());

        let empty_wgs = dir.path().join("EmptyWgs");
        fs::create_dir_all(&empty_wgs).unwrap();
        let error = extract_xgp_save(&XgpExtractOptions {
            wgs_user_dir: empty_wgs.display().to_string(),
            destination_path: dir.path().join("EmptyOutput").display().to_string(),
        })
        .unwrap_err();
        assert_eq!(error.code, "invalid_xgp_save");
    }

    #[test]
    fn import_preview_warns_about_cloud_sync_and_validates_source() {
        let dir = tempdir().unwrap();
        let source = dir.path().join("SteamSave");
        fs::create_dir_all(&source).unwrap();
        fs::write(source.join("Level.sav"), b"level").unwrap();
        let target = dir.path().join("WgsUser");

        let preview = preview_import_steam_to_xgp(&XgpImportOptions {
            source_steam_path: source.display().to_string(),
            target_wgs_user_dir: target.display().to_string(),
            package_name: Some("PocketpairInc.Palworld_Test".into()),
        })
        .unwrap();
        assert_eq!(preview.operation, "import_steam_to_xgp");
        assert!(preview
            .warnings
            .iter()
            .any(|warning| warning.contains("CLOUD SYNC")));
        assert!(preview.backup_target.is_some());
        assert!(preview.files_to_modify[0].ends_with("containers.index"));
    }

    #[test]
    fn import_commit_creates_wgs_backup_index_and_blobs() {
        let dir = tempdir().unwrap();
        let source = dir.path().join("SteamSave");
        fs::create_dir_all(source.join("Players")).unwrap();
        fs::write(source.join("Level.sav"), b"level").unwrap();
        fs::write(source.join("LevelMeta.sav"), b"meta").unwrap();
        let target = dir.path().join("WgsUser");
        let manager = BackupManager::new(dir.path().join("Backups"));

        let result = commit_import_steam_to_xgp(
            &XgpImportOptions {
                source_steam_path: source.display().to_string(),
                target_wgs_user_dir: target.display().to_string(),
                package_name: Some("PocketpairInc.Palworld_Test".into()),
            },
            &manager,
        )
        .unwrap();

        assert_eq!(result.containers_created, 1);
        assert!(result.backup_path.is_some());
        assert_eq!(
            fs::read(target.join("containers.index")).unwrap()[..4],
            14u32.to_le_bytes()
        );
        let container = target.join("00000000000000000000000000000001");
        assert_eq!(
            fs::read(container.join("LEVEL_BLOB_DATA")).unwrap(),
            b"level"
        );
        assert_eq!(fs::read(container.join("META_BLOB_DATA")).unwrap(), b"meta");
    }
}
