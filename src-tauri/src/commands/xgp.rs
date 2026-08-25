//! IPC command handlers for Xbox GamePass (XGP) save tools.

use std::sync::Mutex;
use tauri::State;

use crate::domain::save_session::preview::MutationPreview;
use crate::domain::tools::xgp::{
    commit_import_steam_to_xgp as domain_commit_import_steam_to_xgp,
    discover_xgp_saves as domain_discover_xgp_saves, extract_xgp_save as domain_extract_xgp_save,
    preview_import_steam_to_xgp as domain_preview_import_steam_to_xgp, XgpExtractOptions,
    XgpExtractResult, XgpImportAuditResult, XgpImportOptions, XgpSaveEntry,
};
use crate::error::AppError;
use crate::storage::backup::BackupManager;

#[tauri::command]
pub fn discover_xgp_saves() -> Result<Vec<XgpSaveEntry>, AppError> {
    domain_discover_xgp_saves()
}

#[tauri::command]
pub fn extract_xgp_save(options: XgpExtractOptions) -> Result<XgpExtractResult, AppError> {
    domain_extract_xgp_save(&options)
}

#[tauri::command]
pub fn preview_import_steam_to_xgp(options: XgpImportOptions) -> Result<MutationPreview, AppError> {
    domain_preview_import_steam_to_xgp(&options)
}

#[tauri::command]
pub fn commit_import_steam_to_xgp(
    options: XgpImportOptions,
    backup_state: State<'_, Mutex<BackupManager>>,
) -> Result<XgpImportAuditResult, AppError> {
    let backup_mgr = backup_state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock backup manager: {}", e),
        )
    })?;

    domain_commit_import_steam_to_xgp(&options, &backup_mgr)
}
