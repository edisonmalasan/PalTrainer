//! In-memory save session tracking file baselines, dirty states, and stale save detection.

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};
use thiserror::Error;

use crate::pal_save::archive::{SavHeader, SaveType};
use crate::security::path_policy::{resolve_save_root, SecurityError};
use crate::storage::atomic::StorageError;

#[derive(Debug, Error)]
pub enum SessionError {
    #[error("No active save session loaded")]
    NoActiveSession,

    #[error("Save file is stale: {0:?} was modified externally after loading")]
    StaleSaveFile(Vec<PathBuf>),

    #[error("Security validation failed: {0}")]
    Security(#[from] SecurityError),

    #[error("Storage error: {0}")]
    Storage(#[from] StorageError),

    #[error("Save engine error: {0}")]
    Save(#[from] crate::pal_save::SaveError),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct FileSnapshot {
    pub path: PathBuf,
    pub mtime: u64,
    pub size: u64,
    pub crc32: u32,
}

impl FileSnapshot {
    pub fn capture(path: impl AsRef<Path>) -> Result<Self, std::io::Error> {
        let p = path.as_ref();
        let meta = fs::metadata(p)?;
        let mtime = meta
            .modified()?
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let size = meta.len();

        let mut file = File::open(p)?;
        let mut buffer = Vec::with_capacity(size.min(1024 * 1024) as usize);
        file.read_to_end(&mut buffer)?;
        let crc32 = crc32fast::hash(&buffer);

        Ok(Self {
            path: p.to_path_buf(),
            mtime,
            size,
            crc32,
        })
    }

    pub fn is_stale(&self) -> bool {
        if let Ok(current) = Self::capture(&self.path) {
            current.mtime != self.mtime || current.size != self.size || current.crc32 != self.crc32
        } else {
            true // Missing or inaccessible file is considered stale/modified
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct SaveSummaryDto {
    pub save_root: PathBuf,
    pub world_name: String,
    pub save_type: String,
    pub player_count: usize,
    pub level_sav_size: u64,
    pub is_dirty: bool,
    pub loaded_at: u64,
}

pub struct SaveSession {
    save_root: PathBuf,
    save_type: SaveType,
    snapshots: HashMap<PathBuf, FileSnapshot>,
    is_dirty: bool,
    pending_deletions: HashSet<PathBuf>,
    loaded_at: u64,
}

impl SaveSession {
    /// Opens and indexes a Palworld save directory.
    pub fn open(save_root: impl AsRef<Path>) -> Result<Self, SessionError> {
        let canon_root = resolve_save_root(save_root)?;
        let level_sav_path = canon_root.join("Level.sav");

        let level_bytes = fs::read(&level_sav_path)?;
        let header = SavHeader::parse(&level_bytes)?;
        let save_type = header.save_type;

        let mut snapshots = HashMap::new();

        // Capture Level.sav snapshot
        let level_snap = FileSnapshot::capture(&level_sav_path)?;
        snapshots.insert(level_sav_path, level_snap);

        // Capture LevelMeta.sav if present
        let meta_sav = canon_root.join("LevelMeta.sav");
        if meta_sav.is_file() {
            if let Ok(snap) = FileSnapshot::capture(&meta_sav) {
                snapshots.insert(meta_sav, snap);
            }
        }

        // Capture WorldOption.sav if present
        let world_option_sav = canon_root.join("WorldOption.sav");
        if world_option_sav.is_file() {
            if let Ok(snap) = FileSnapshot::capture(&world_option_sav) {
                snapshots.insert(world_option_sav, snap);
            }
        }

        // Capture all files in Players/
        let players_dir = canon_root.join("Players");
        if players_dir.is_dir() {
            for entry in fs::read_dir(&players_dir)? {
                let entry = entry?;
                let path = entry.path();
                if path.is_file() && path.extension().and_then(|e| e.to_str()) == Some("sav") {
                    if let Ok(snap) = FileSnapshot::capture(&path) {
                        snapshots.insert(path, snap);
                    }
                }
            }
        }

        let loaded_at = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        Ok(Self {
            save_root: canon_root,
            save_type,
            snapshots,
            is_dirty: false,
            pending_deletions: HashSet::new(),
            loaded_at,
        })
    }

    pub fn save_root(&self) -> &Path {
        &self.save_root
    }

    pub fn save_type(&self) -> SaveType {
        self.save_type
    }

    pub fn is_dirty(&self) -> bool {
        self.is_dirty
    }

    pub fn mark_dirty(&mut self) {
        self.is_dirty = true;
    }

    pub fn queue_deletion(&mut self, path: PathBuf) {
        self.pending_deletions.insert(path);
        self.is_dirty = true;
    }

    pub fn pending_deletions(&self) -> &HashSet<PathBuf> {
        &self.pending_deletions
    }

    /// Checks if any file in the baseline session has changed on disk since load.
    pub fn check_stale(&self) -> Result<Vec<PathBuf>, SessionError> {
        let mut stale_files = Vec::new();
        for (path, snap) in &self.snapshots {
            if snap.is_stale() {
                stale_files.push(path.clone());
            }
        }
        Ok(stale_files)
    }

    /// Updates snapshots after a successful write operation.
    pub fn refresh_snapshots(&mut self) -> Result<(), SessionError> {
        for (path, snap) in self.snapshots.iter_mut() {
            if path.exists() {
                *snap = FileSnapshot::capture(path)?;
            }
        }
        self.is_dirty = false;
        self.pending_deletions.clear();
        Ok(())
    }

    pub fn summary(&self) -> SaveSummaryDto {
        let world_name = self
            .save_root
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("World")
            .to_string();

        let level_sav_path = self.save_root.join("Level.sav");
        let level_sav_size = self
            .snapshots
            .get(&level_sav_path)
            .map(|s| s.size)
            .unwrap_or(0);

        let player_count = self
            .snapshots
            .keys()
            .filter(|p| {
                p.parent()
                    .and_then(|par| par.file_name())
                    .map(|n| n == "Players")
                    .unwrap_or(false)
            })
            .count();

        SaveSummaryDto {
            save_root: self.save_root.clone(),
            world_name,
            save_type: format!("{:?}", self.save_type),
            player_count,
            level_sav_size,
            is_dirty: self.is_dirty,
            loaded_at: self.loaded_at,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::security::canonicalize_safe;
    use tempfile::tempdir;

    fn make_valid_sav_header() -> Vec<u8> {
        let mut buf = Vec::new();
        buf.extend_from_slice(&100u32.to_le_bytes()); // uncompressed len
        buf.extend_from_slice(&50u32.to_le_bytes()); // compressed len
        buf.extend_from_slice(b"PlZ");
        buf.push(0x32); // Plz type
        buf.extend_from_slice(&[0u8; 38]); // payload padding
        buf
    }

    #[test]
    fn test_save_session_open_and_stale_detection() {
        let temp = tempdir().unwrap();
        let save_root = temp.path().join("World1");
        fs::create_dir_all(save_root.join("Players")).unwrap();

        let level_file = save_root.join("Level.sav");
        fs::write(&level_file, make_valid_sav_header()).unwrap();

        let player_file = save_root.join("Players").join("player1.sav");
        fs::write(&player_file, b"player_data").unwrap();

        let session = SaveSession::open(&save_root).unwrap();
        assert_eq!(session.save_type(), SaveType::Plz);
        assert_eq!(session.summary().player_count, 1);
        assert!(session.check_stale().unwrap().is_empty());

        // Modify file externally to simulate stale file
        std::thread::sleep(std::time::Duration::from_millis(50));
        fs::write(&player_file, b"modified_player_data").unwrap();

        let stale = session.check_stale().unwrap();
        assert_eq!(stale.len(), 1);
        assert_eq!(stale[0], canonicalize_safe(&player_file).unwrap());
    }
}
