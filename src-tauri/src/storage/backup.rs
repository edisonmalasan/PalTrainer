//! Backup creation, cataloging, and restoration for Palworld saves.

use serde::{Deserialize, Serialize};
use std::fs::{self, File};
use std::io;
use std::path::{Path, PathBuf};

use super::atomic::StorageError;
use super::audit::AuditLog;
use crate::security::path_policy::{canonicalize_safe, validate_save_root};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BackupMeta {
    pub id: String,
    pub original_save_path: PathBuf,
    pub world_name: String,
    pub created_at: u64,
    pub note: Option<String>,
    pub tag: String,
    pub file_count: usize,
    pub total_bytes: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BackupInfo {
    pub backup_path: PathBuf,
    pub meta: BackupMeta,
}

pub struct BackupManager {
    backup_root: PathBuf,
}

impl BackupManager {
    pub fn new(backup_root: impl Into<PathBuf>) -> Self {
        Self {
            backup_root: backup_root.into(),
        }
    }

    pub fn backup_root(&self) -> &Path {
        &self.backup_root
    }

    /// Creates a full snapshot backup of a Palworld save directory before modification.
    pub fn create_backup(
        &self,
        save_root: impl AsRef<Path>,
        tag: Option<&str>,
        note: Option<&str>,
    ) -> Result<BackupInfo, StorageError> {
        let canon_save_root = validate_save_root(save_root)?;
        fs::create_dir_all(&self.backup_root)?;

        let world_name = canon_save_root
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("WorldSave")
            .to_string();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let tag_str = tag.unwrap_or("auto");
        let backup_id = format!("{}_{}_{}", world_name, now, tag_str);
        let dest_dir = self.backup_root.join(&backup_id);
        fs::create_dir_all(&dest_dir)?;

        let mut file_count = 0;
        let mut total_bytes = 0;

        copy_dir_recursive(
            &canon_save_root,
            &dest_dir,
            &mut file_count,
            &mut total_bytes,
        )?;

        let meta = BackupMeta {
            id: backup_id,
            original_save_path: canon_save_root,
            world_name,
            created_at: now,
            note: note.map(str::to_string),
            tag: tag_str.to_string(),
            file_count,
            total_bytes,
        };

        let meta_file = dest_dir.join("backup_meta.json");
        let meta_json = serde_json::to_string_pretty(&meta)?;
        fs::write(meta_file, meta_json)?;

        Ok(BackupInfo {
            backup_path: dest_dir,
            meta,
        })
    }

    /// Lists all valid backups in the backup root, optionally filtered by original save root.
    pub fn list_backups(
        &self,
        filter_save_root: Option<&Path>,
    ) -> Result<Vec<BackupInfo>, StorageError> {
        if !self.backup_root.exists() {
            return Ok(Vec::new());
        }

        let filter_canon = filter_save_root.and_then(|p| canonicalize_safe(p).ok());
        let mut backups = Vec::new();

        for entry in fs::read_dir(&self.backup_root)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                let meta_path = path.join("backup_meta.json");
                if meta_path.is_file() {
                    if let Ok(file) = File::open(&meta_path) {
                        if let Ok(meta) = serde_json::from_reader::<_, BackupMeta>(file) {
                            if let Some(ref target) = filter_canon {
                                if meta.original_save_path != *target {
                                    continue;
                                }
                            }
                            backups.push(BackupInfo {
                                backup_path: path,
                                meta,
                            });
                        }
                    }
                }
            }
        }

        // Sort latest backups first
        backups.sort_by_key(|a| std::cmp::Reverse(a.meta.created_at));
        Ok(backups)
    }

    /// Restores a backup folder to the target save root. Takes a safety snapshot first.
    pub fn restore_backup(
        &self,
        backup_dir: impl AsRef<Path>,
        target_save_root: impl AsRef<Path>,
    ) -> Result<AuditLog, StorageError> {
        let canon_backup = canonicalize_safe(backup_dir)?;
        let meta_path = canon_backup.join("backup_meta.json");
        if !meta_path.is_file() || !canon_backup.join("Level.sav").is_file() {
            return Err(StorageError::InvalidBackup(canon_backup));
        }

        let target_root = target_save_root.as_ref();
        fs::create_dir_all(target_root)?;
        let canon_target = canonicalize_safe(target_root)?;

        // 1. Safety snapshot of current target if it contains Level.sav
        let pre_restore_backup = if canon_target.join("Level.sav").is_file() {
            let snapshot = self.create_backup(
                &canon_target,
                Some("pre-restore"),
                Some("Snapshot before backup restoration"),
            )?;
            Some(snapshot.backup_path)
        } else {
            None
        };

        let mut audit = AuditLog::new("restore_backup");
        if let Some(ref snapshot_path) = pre_restore_backup {
            audit = audit.with_backup(snapshot_path.clone());
        }

        // 2. Copy all files from backup (skipping backup_meta.json) into target
        let mut file_count = 0;
        let mut total_bytes = 0;
        for entry in fs::read_dir(&canon_backup)? {
            let entry = entry?;
            let file_name = entry.file_name();
            if file_name == "backup_meta.json" {
                continue;
            }
            let src = entry.path();
            let dest = canon_target.join(&file_name);
            if src.is_dir() {
                copy_dir_recursive(&src, &dest, &mut file_count, &mut total_bytes)?;
            } else {
                fs::copy(&src, &dest)?;
                audit.add_modified_file(&dest);
            }
        }

        audit.add_entity(format!(
            "Restored {} files ({} bytes) from {:?}",
            file_count, total_bytes, canon_backup
        ));
        Ok(audit)
    }
}

fn copy_dir_recursive(
    src: &Path,
    dst: &Path,
    file_count: &mut usize,
    total_bytes: &mut u64,
) -> io::Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let src_path = entry.path();
        let file_name = entry.file_name();
        let file_str = file_name.to_string_lossy();

        // Ignore temporary or lock files
        if file_str.ends_with(".tmp") || file_str.ends_with(".lock") {
            continue;
        }

        let dst_path = dst.join(&file_name);
        if src_path.is_dir() {
            copy_dir_recursive(&src_path, &dst_path, file_count, total_bytes)?;
        } else {
            let bytes = fs::copy(&src_path, &dst_path)?;
            *file_count += 1;
            *total_bytes += bytes;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_backup_create_list_restore() {
        let temp = tempdir().unwrap();
        let save_root = temp.path().join("SaveWorld1");
        fs::create_dir_all(save_root.join("Players")).unwrap();
        fs::write(save_root.join("Level.sav"), b"level_data_v1").unwrap();
        fs::write(
            save_root.join("Players").join("player1.sav"),
            b"player1_data",
        )
        .unwrap();

        let backup_root = temp.path().join("Backups");
        let manager = BackupManager::new(&backup_root);

        // 1. Create backup
        let backup = manager
            .create_backup(&save_root, Some("manual"), Some("Initial test backup"))
            .unwrap();
        assert!(backup.backup_path.exists());
        assert_eq!(backup.meta.file_count, 2);

        // 2. List backups
        let list = manager.list_backups(Some(&save_root)).unwrap();
        assert_eq!(list.len(), 1);
        assert_eq!(list[0].meta.id, backup.meta.id);

        // 3. Mutate save
        fs::write(save_root.join("Level.sav"), b"corrupted_or_modified_data").unwrap();

        // 4. Restore backup
        let audit = manager
            .restore_backup(&backup.backup_path, &save_root)
            .unwrap();
        assert!(audit.backup_path.is_some());
        assert_eq!(
            fs::read(save_root.join("Level.sav")).unwrap(),
            b"level_data_v1"
        );
    }
}
