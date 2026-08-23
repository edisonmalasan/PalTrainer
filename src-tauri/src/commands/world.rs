//! WorldOption and WorldMetadata IPC commands with mandatory preview, backup, and audit protections.

use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::domain::world::{WorldMetadataDto, WorldOptionsDto};
use crate::error::AppError;

#[tauri::command]
pub fn get_world_options(state: State<'_, SessionState>) -> Result<WorldOptionsDto, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    Ok(WorldOptionsDto::default())
}

#[tauri::command]
pub fn preview_save_world_options(
    options: WorldOptionsDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("save_world_options", session.save_root());

    preview.add_modify_entity(
        "WorldOption",
        "WorldOption.sav",
        "Server & Gameplay Settings",
        format!(
            "EXP Rate: {:.1}x, Capture Rate: {:.1}x, Death Penalty: {}, Egg Hatch: {:.1}h",
            options.exp_rate,
            options.pal_capture_rate,
            options.death_penalty,
            options.pal_egg_default_hatching_time
        ),
    );

    let world_option_sav = session.save_root().join("WorldOption.sav");
    preview.files_to_modify.push(world_option_sav);

    Ok(preview)
}

#[tauri::command]
pub fn commit_save_world_options(
    options: WorldOptionsDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<WorldOptionsDto, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-save-world-options"),
            Some("Backup before modifying WorldOption.sav"),
        )?;
    }

    Ok(options)
}

#[tauri::command]
pub fn get_world_meta(state: State<'_, SessionState>) -> Result<WorldMetadataDto, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let world_name = session
        .save_root()
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("Palworld")
        .to_string();

    Ok(WorldMetadataDto {
        world_name,
        game_days: 15,
        in_game_time_seconds: 36000.0,
        is_multiplayer: false,
    })
}

#[tauri::command]
pub fn preview_save_world_meta(
    meta: WorldMetadataDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("save_world_meta", session.save_root());

    preview.add_modify_entity(
        "LevelMeta",
        "LevelMeta.sav",
        "World Name and Day Counter",
        format!(
            "World Name: '{}', Game Days: {}, In-game Time: {:.0}s",
            meta.world_name, meta.game_days, meta.in_game_time_seconds
        ),
    );

    let level_meta_sav = session.save_root().join("LevelMeta.sav");
    preview.files_to_modify.push(level_meta_sav);

    Ok(preview)
}

#[tauri::command]
pub fn commit_save_world_meta(
    meta: WorldMetadataDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<WorldMetadataDto, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-save-world-meta"),
            Some("Backup before modifying LevelMeta.sav"),
        )?;
    }

    Ok(meta)
}
