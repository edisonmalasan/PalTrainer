//! Exclusion zone configuration and coordinate testing IPC commands.

use std::sync::Mutex;
use tauri::State;

use crate::domain::exclusions::{ExclusionConfig, ZoneExclusion};
use crate::error::AppError;

pub type ExclusionState = Mutex<ExclusionConfig>;

#[tauri::command]
pub fn get_exclusion_config(state: State<'_, ExclusionState>) -> Result<ExclusionConfig, AppError> {
    let lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;
    Ok(lock.clone())
}

#[tauri::command]
pub fn save_exclusion_config(
    config: ExclusionConfig,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let mut lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;
    *lock = config.clone();
    Ok(config)
}

#[tauri::command]
pub fn add_zone_exclusion(
    zone: ZoneExclusion,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let mut lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;
    lock.zones.retain(|z| z.id != zone.id);
    lock.zones.push(zone);
    Ok(lock.clone())
}

#[tauri::command]
pub fn remove_zone_exclusion(
    zone_id: String,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let mut lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;
    lock.zones.retain(|z| z.id != zone_id);
    Ok(lock.clone())
}

#[tauri::command]
pub fn check_coordinate_excluded(
    world_x: f32,
    world_y: f32,
    state: State<'_, ExclusionState>,
) -> Result<bool, AppError> {
    let lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;

    let is_excluded = lock
        .zones
        .iter()
        .any(|z| z.contains_point(world_x, world_y));
    Ok(is_excluded)
}
