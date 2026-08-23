//! Tauri IPC commands for backup creation, listing, and safe restoration.

use std::path::PathBuf;
use std::sync::Mutex;
use tauri::State;

use crate::error::AppError;
use crate::storage::audit::AuditLog;
use crate::storage::backup::{BackupInfo, BackupManager};

pub type BackupState = Mutex<BackupManager>;

#[tauri::command]
pub fn list_backups(
    save_path: Option<String>,
    state: State<'_, BackupState>,
) -> Result<Vec<BackupInfo>, AppError> {
    let manager = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock backup state: {}", e)))?;

    let filter_path = save_path.map(PathBuf::from);
    let backups = manager.list_backups(filter_path.as_deref())?;
    Ok(backups)
}

#[tauri::command]
pub fn create_manual_backup(
    save_path: String,
    note: Option<String>,
    state: State<'_, BackupState>,
) -> Result<BackupInfo, AppError> {
    let manager = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock backup state: {}", e)))?;

    let backup = manager.create_backup(&save_path, Some("manual"), note.as_deref())?;
    Ok(backup)
}

#[tauri::command]
pub fn restore_backup(
    backup_path: String,
    target_save_root: String,
    state: State<'_, BackupState>,
) -> Result<AuditLog, AppError> {
    let manager = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock backup state: {}", e)))?;

    let audit = manager.restore_backup(&backup_path, &target_save_root)?;
    Ok(audit)
}
