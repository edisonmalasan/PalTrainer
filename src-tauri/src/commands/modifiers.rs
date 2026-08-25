//! IPC commands for save modifiers: Map Fog Restoration and Palbox Slot Injection.

use std::sync::Mutex;
use tauri::State;

use crate::commands::save_session::SessionState;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::domain::tools::restore_map::{
    commit_restore_map as domain_commit_restore_map,
    preview_restore_map as domain_preview_restore_map, RestoreMapOptions, RestoreMapReport,
};
use crate::domain::tools::slot_injector::{
    commit_inject_palbox_slots as domain_commit_inject_palbox_slots,
    get_player_palbox_capacity as domain_get_player_palbox_capacity,
    preview_inject_palbox_slots as domain_preview_inject_palbox_slots, PalboxCapacityDto,
    SlotInjectionAuditResult, SlotInjectionParams,
};
use crate::error::AppError;
use crate::storage::backup::BackupManager;

#[tauri::command]
pub fn preview_restore_map(
    options: RestoreMapOptions,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let root = guard.as_ref().map(|s| s.save_root());
    domain_preview_restore_map(&options, root)
}

#[tauri::command]
pub fn commit_restore_map(
    options: RestoreMapOptions,
    state: State<'_, SessionState>,
    backup_state: State<'_, Mutex<BackupManager>>,
) -> Result<RestoreMapReport, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let backup_mgr = backup_state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock backup manager: {}", e),
        )
    })?;

    let root = guard.as_ref().map(|s| s.save_root());
    domain_commit_restore_map(&options, root, &backup_mgr)
}

#[tauri::command]
pub fn get_palbox_capacity(
    player_uid: String,
    state: State<'_, SessionState>,
) -> Result<PalboxCapacityDto, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let active = guard.as_ref().ok_or(SessionError::NoActiveSession)?;

    domain_get_player_palbox_capacity(active, &player_uid)
}

#[tauri::command]
pub fn preview_inject_palbox_slots(
    params: SlotInjectionParams,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let active = guard.as_ref().ok_or(SessionError::NoActiveSession)?;

    domain_preview_inject_palbox_slots(active, &params)
}

#[tauri::command]
pub fn commit_inject_palbox_slots(
    params: SlotInjectionParams,
    state: State<'_, SessionState>,
    backup_state: State<'_, Mutex<BackupManager>>,
) -> Result<SlotInjectionAuditResult, AppError> {
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

    domain_commit_inject_palbox_slots(active, &backup_mgr, &params)
}
