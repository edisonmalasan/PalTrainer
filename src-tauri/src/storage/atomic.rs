//! Atomic file writing via temporary sibling files and replacement.

use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StorageError {
    #[error("Atomic write failed: parent directory could not be resolved for '{0}'")]
    NoParentDir(PathBuf),

    #[error("Backup directory not found: '{0}'")]
    BackupNotFound(PathBuf),

    #[error("Invalid backup archive: missing metadata in '{0}'")]
    InvalidBackup(PathBuf),

    #[error("IO error: {0}")]
    Io(#[from] io::Error),

    #[error("Security error: {0}")]
    Security(#[from] crate::security::SecurityError),

    #[error("JSON serialization error: {0}")]
    Json(#[from] serde_json::Error),
}

/// Writes `data` to `target_path` atomically.
///
/// Steps:
/// 1. Creates a temporary file in the same directory as `target_path` (`{filename}.tmp.{rand}`).
/// 2. Writes all bytes and explicitly calls `sync_all()`.
/// 3. Replaces `target_path` using `fs::rename`.
pub fn atomic_write(target_path: impl AsRef<Path>, data: &[u8]) -> Result<(), StorageError> {
    let target = target_path.as_ref();
    let parent = target
        .parent()
        .ok_or_else(|| StorageError::NoParentDir(target.to_path_buf()))?;

    // Ensure parent directory exists
    fs::create_dir_all(parent)?;

    let file_stem = target
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("file");
    let temp_name = format!("{}.tmp.{}", file_stem, fastrand::u64(..));
    let temp_path = parent.join(&temp_name);

    // Write to temp file with sync
    {
        let mut file = File::create(&temp_path)?;
        file.write_all(data)?;
        file.sync_all()?;
    }

    // Atomic replacement
    if let Err(e) = fs::rename(&temp_path, target) {
        // Clean up temp file on failure
        let _ = fs::remove_file(&temp_path);
        return Err(StorageError::Io(e));
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_atomic_write_new_and_overwrite() {
        let dir = tempdir().unwrap();
        let target = dir.path().join("atomic_test.sav");

        // 1. Initial write
        atomic_write(&target, b"initial payload").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"initial payload");

        // 2. Overwrite
        atomic_write(&target, b"updated payload").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"updated payload");
    }

    #[test]
    fn test_atomic_write_creates_parent_directories() {
        let dir = tempdir().unwrap();
        let target = dir.path().join("nested").join("deep").join("save.sav");

        atomic_write(&target, b"deep content").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"deep content");
    }

    #[test]
    fn test_atomic_write_empty_payload() {
        let dir = tempdir().unwrap();
        let target = dir.path().join("empty.sav");

        atomic_write(&target, b"").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"");
    }
}
