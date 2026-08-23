//! Audit logging for save modifications and recovery operations.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct AuditLog {
    pub id: String,
    pub operation: String,
    pub timestamp: String,
    pub backup_path: Option<PathBuf>,
    pub modified_files: Vec<PathBuf>,
    pub deleted_files: Vec<PathBuf>,
    pub entities_affected: Vec<String>,
    pub warnings: Vec<String>,
}

impl AuditLog {
    pub fn new(operation: impl Into<String>) -> Self {
        Self {
            id: format!("audit-{}", fastrand::u64(..)),
            operation: operation.into(),
            timestamp: chrono_now_iso(),
            backup_path: None,
            modified_files: Vec::new(),
            deleted_files: Vec::new(),
            entities_affected: Vec::new(),
            warnings: Vec::new(),
        }
    }

    pub fn with_backup(mut self, backup_path: impl Into<PathBuf>) -> Self {
        self.backup_path = Some(backup_path.into());
        self
    }

    pub fn add_modified_file(&mut self, path: impl Into<PathBuf>) {
        self.modified_files.push(path.into());
    }

    pub fn add_deleted_file(&mut self, path: impl Into<PathBuf>) {
        self.deleted_files.push(path.into());
    }

    pub fn add_entity(&mut self, entity: impl Into<String>) {
        self.entities_affected.push(entity.into());
    }

    pub fn add_warning(&mut self, warning: impl Into<String>) {
        self.warnings.push(warning.into());
    }
}

pub fn chrono_now_iso() -> String {
    // Generate ISO8601-like timestamp from system time without external timezone dependency
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    format!("unix-{}", now)
}
