//! Exclusion zone configuration and coordinate testing IPC commands.

use std::sync::Mutex;
use tauri::{AppHandle, State};

use crate::domain::exclusions::store::{
    exclusions_config_path, load_exclusions_from_path, save_exclusions_to_path,
};
use crate::domain::exclusions::{
    build_zone_from_map, ExclusionConfig, ZoneExclusion, ZoneFromMapDraft,
};
use crate::error::AppError;

pub type ExclusionState = Mutex<ExclusionConfig>;

fn persist(
    app: &AppHandle,
    state: &State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let path = exclusions_config_path(app)?;
    let snapshot = {
        let lock = state.lock().map_err(|e| {
            AppError::new(
                "lock_error",
                format!("Failed to lock exclusion state: {}", e),
            )
        })?;
        lock.clone()
    };
    save_exclusions_to_path(&path, &snapshot)?;
    Ok(snapshot)
}

#[tauri::command]
pub fn get_exclusion_config(
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    load_state(app, state)
}

fn load_state(
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    load_state_from_app(&app, &state)
}

fn load_state_from_app(
    app: &AppHandle,
    state: &State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let path = exclusions_config_path(app)?;
    let loaded = load_exclusions_from_path(&path)?;
    *state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })? = loaded.clone();
    Ok(loaded)
}

#[tauri::command]
pub fn save_exclusion_config(
    config: ExclusionConfig,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    *state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })? = config.clone();
    persist(&app, &state)
}

#[tauri::command]
pub fn add_zone_exclusion(
    zone: ZoneExclusion,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    load_state_from_app(&app, &state)?;
    let mut lock = state.lock().map_err(|e| {
        AppError::new(
            "lock_error",
            format!("Failed to lock exclusion state: {}", e),
        )
    })?;
    lock.zones.retain(|z| z.id != zone.id);
    lock.zones.push(zone);
    drop(lock);
    persist(&app, &state)
}

#[tauri::command]
pub fn remove_zone_exclusion(
    zone_id: String,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    load_state_from_app(&app, &state)?;
    {
        let mut lock = state.lock().map_err(|e| {
            AppError::new(
                "lock_error",
                format!("Failed to lock exclusion state: {}", e),
            )
        })?;
        lock.zones.retain(|z| z.id != zone_id);
    }
    persist(&app, &state)
}

#[tauri::command]
pub fn check_coordinate_excluded(
    world_x: f32,
    world_y: f32,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<bool, AppError> {
    let config = load_state(app, state)?;
    Ok(config
        .zones
        .iter()
        .any(|z| z.contains_point(world_x, world_y)))
}

#[tauri::command]
pub fn is_point_in_exclusion(
    world_x: f32,
    world_y: f32,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<bool, AppError> {
    check_coordinate_excluded(world_x, world_y, app, state)
}

/// Adds a zone drawn on the map canvas. The draft arrives in post-Sakurajima
/// map-grid units and is converted to world coordinates by the domain layer so
/// the calibration stays authoritative in Rust.
#[tauri::command]
pub fn add_zone_exclusion_from_map(
    zone: ZoneFromMapDraft,
    app: AppHandle,
    state: State<'_, ExclusionState>,
) -> Result<ExclusionConfig, AppError> {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or_default();
    let new_zone = build_zone_from_map(&zone, &format!("zone_{nanos}"))?;
    load_state_from_app(&app, &state)?;
    {
        let mut lock = state.lock().map_err(|e| {
            AppError::new(
                "lock_error",
                format!("Failed to lock exclusion state: {}", e),
            )
        })?;
        lock.zones.retain(|z| z.id != new_zone.id);
        lock.zones.push(new_zone);
    }
    persist(&app, &state)
}
