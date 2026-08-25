//! IPC command handlers for Character Transfer and Host Save / UID Swap.

use std::sync::Mutex;
use tauri::State;

use crate::commands::save_session::SessionState;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::domain::tools::host_swap::{
    commit_host_swap as domain_commit_host_swap, inspect_host_swap as domain_inspect_host_swap,
    preview_host_swap as domain_preview_host_swap, HostSwapAuditResult, HostSwapInspectionDto,
    HostSwapOptions,
};
use crate::domain::tools::transfer::{
    commit_character_transfer as domain_commit_character_transfer,
    inspect_transfer_source as domain_inspect_transfer_source,
    preview_character_transfer as domain_preview_character_transfer, CharacterTransferAuditResult,
    CharacterTransferOptions, TransferPlayerSummaryDto,
};
use crate::error::AppError;
use crate::storage::backup::BackupManager;

#[tauri::command]
pub fn inspect_transfer_source(
    source_path: String,
) -> Result<Vec<TransferPlayerSummaryDto>, AppError> {
    domain_inspect_transfer_source(&source_path)
}

#[tauri::command]
pub fn preview_character_transfer(
    options: CharacterTransferOptions,
) -> Result<MutationPreview, AppError> {
    domain_preview_character_transfer(&options)
}

#[tauri::command]
pub fn commit_character_transfer(
    options: CharacterTransferOptions,
    backup_state: State<'_, Mutex<BackupManager>>,
) -> Result<CharacterTransferAuditResult, AppError> {
    let backup_mgr = backup_state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock backup manager: {}", e),
        )
    })?;

    domain_commit_character_transfer(&options, &backup_mgr)
}

#[tauri::command]
pub fn inspect_host_swap(
    source_uid: String,
    target_uid: String,
    state: State<'_, SessionState>,
) -> Result<HostSwapInspectionDto, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let active = guard.as_ref().ok_or(SessionError::NoActiveSession)?;

    domain_inspect_host_swap(active, &source_uid, &target_uid)
}

#[tauri::command]
pub fn preview_host_swap(
    options: HostSwapOptions,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let active = guard.as_ref().ok_or(SessionError::NoActiveSession)?;

    domain_preview_host_swap(active, &options)
}

#[tauri::command]
pub fn commit_host_swap(
    options: HostSwapOptions,
    state: State<'_, SessionState>,
    backup_state: State<'_, Mutex<BackupManager>>,
) -> Result<HostSwapAuditResult, AppError> {
    let mut guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let backup_mgr = backup_state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock backup manager: {}", e),
        )
    })?;
    let active = guard.as_mut().ok_or(SessionError::NoActiveSession)?;

    domain_commit_host_swap(active, &backup_mgr, &options)
}
