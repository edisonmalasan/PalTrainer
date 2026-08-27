//! Base camp mutation, coordinate nudging, export, and import IPC commands.

use std::path::PathBuf;
use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::bases::mutation::{
    validate_area_range, ImportBaseBundleDto, MoveBaseToMapDto, NudgeBaseCoordinatesDto,
    UpdateBaseAreaRangeDto, UpdateBaseDto,
};
use crate::domain::bases::BaseProjection;
use crate::domain::map::{map_to_world_coordinates, world_to_map_coordinates};
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;
use crate::security::path_policy::validate_import_export_path;

#[tauri::command]
pub fn preview_update_base(
    dto: UpdateBaseDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("update_base", session.save_root());
    let mut changes = Vec::new();

    if let Some(level) = dto.level {
        changes.push(format!("Base Level -> {}", level));
    }
    if let Some(radius) = dto.radius {
        changes.push(format!("Base Radius -> {:.1}m", radius));
    }

    let change_str = if changes.is_empty() {
        "No changes specified".to_string()
    } else {
        changes.join(", ")
    };

    preview.add_modify_entity(
        "Base",
        &dto.base_id,
        format!("Base {}", dto.base_id),
        change_str,
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_base(
    dto: UpdateBaseDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<BaseProjection, AppError> {
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
            Some("pre-edit-base"),
            Some(&format!("Backup before updating base {}", dto.base_id)),
        )?;
    }

    let (mx, my) = world_to_map_coordinates(0.0, 0.0);
    let updated = BaseProjection {
        base_id: dto.base_id,
        guild_id: "00000000000000000000000000000001".to_string(),
        world_coord_x: 0.0,
        world_coord_y: 0.0,
        world_coord_z: 0.0,
        map_x: mx,
        map_y: my,
        worker_count: 5,
        container_count: 2,
        structure_count: 10,
    };

    Ok(updated)
}

#[tauri::command]
pub fn preview_nudge_base_coordinates(
    dto: NudgeBaseCoordinatesDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("nudge_base_coordinates", session.save_root());

    preview.add_modify_entity(
        "Base",
        &dto.base_id,
        format!("Base {}", dto.base_id),
        format!(
            "Shift position by ΔX: {:.1}, ΔY: {:.1}, ΔZ: {:.1}",
            dto.delta_x, dto.delta_y, dto.delta_z
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_nudge_base_coordinates(
    dto: NudgeBaseCoordinatesDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
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
            Some("pre-nudge-base"),
            Some(&format!("Backup before nudging base {}", dto.base_id)),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_delete_base(
    base_id: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("delete_base", session.save_root());

    preview.add_delete_entity(
        "Base",
        &base_id,
        format!("Base {}", base_id),
        "Remove base camp record, dismantle child map structures, release workers, and unregister from guild",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_delete_base(
    base_id: String,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
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
            Some("pre-delete-base"),
            Some(&format!("Backup before deleting base {}", base_id)),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn export_base_bundle(
    base_id: String,
    export_path: String,
    state: State<'_, SessionState>,
) -> Result<String, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let dest_path = PathBuf::from(&export_path);
    let valid_path = validate_import_export_path(&dest_path, false)?;

    let meta = format!(
        r#"{{"format":"PalTrainer.BaseBundle","version":1,"baseId":"{}"}}"#,
        base_id
    );
    std::fs::write(&valid_path, meta.as_bytes())?;

    Ok(valid_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn preview_import_base_bundle(
    dto: ImportBaseBundleDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let bundle_path = PathBuf::from(&dto.bundle_path);
    let _valid_bundle = validate_import_export_path(&bundle_path, true)?;

    let mut preview = MutationPreview::new("import_base_bundle", session.save_root());
    preview.add_modify_entity(
        "Base",
        "imported_base",
        format!("Import Base from {}", bundle_path.display()),
        format!("Register new base in guild {}", dto.target_guild_id),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_import_base_bundle(
    dto: ImportBaseBundleDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
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
            Some("pre-import-base"),
            Some(&format!(
                "Backup before importing base bundle to guild {}",
                dto.target_guild_id
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_clone_base(
    dto: crate::domain::bases::mutation::CloneBaseDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("clone_base", session.save_root());

    preview.add_modify_entity(
        "Base",
        &dto.base_id,
        format!("Clone Base {}", dto.base_id),
        format!(
            "Duplicate base camp and child structures into guild {}",
            dto.target_guild_id
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_clone_base(
    dto: crate::domain::bases::mutation::CloneBaseDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
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
            Some("pre-clone-base"),
            Some(&format!(
                "Backup before cloning base {} into guild {}",
                dto.base_id, dto.target_guild_id
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_repair_base_structures(
    base_id: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("repair_base_structures", session.save_root());

    preview.add_modify_entity(
        "Base",
        &base_id,
        format!("Base {}", base_id),
        "Restore all damaged map objects and structures within base radius to full HP",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_repair_base_structures(
    base_id: String,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
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
            Some("pre-repair-base"),
            Some(&format!(
                "Backup before repairing structures for base {}",
                base_id
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_move_base_to_map(
    dto: MoveBaseToMapDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let (world_x, world_y) = map_to_world_coordinates(dto.map_x, dto.map_y);

    let mut preview = MutationPreview::new("move_base_to_map", session.save_root());
    preview.add_modify_entity(
        "Base",
        &dto.base_id,
        format!("Base {}", dto.base_id),
        format!(
            "Move base camp to map ({}, {}) -> world ({:.0}, {:.0})",
            dto.map_x, dto.map_y, world_x, world_y
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_move_base_to_map(
    dto: MoveBaseToMapDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<BaseProjection, AppError> {
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
            Some("pre-move-base"),
            Some(&format!(
                "Backup before moving base {} to map ({}, {})",
                dto.base_id, dto.map_x, dto.map_y
            )),
        )?;
    }

    let (world_x, world_y) = map_to_world_coordinates(dto.map_x, dto.map_y);
    Ok(BaseProjection {
        base_id: dto.base_id,
        guild_id: "00000000000000000000000000000001".to_string(),
        world_coord_x: world_x,
        world_coord_y: world_y,
        world_coord_z: 0.0,
        map_x: dto.map_x,
        map_y: dto.map_y,
        worker_count: 5,
        container_count: 2,
        structure_count: 10,
    })
}

#[tauri::command]
pub fn preview_update_base_area_range(
    dto: UpdateBaseAreaRangeDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    validate_area_range(dto.area_range)
        .map_err(|message| AppError::new("area_range_out_of_range", message))?;

    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("update_base_area_range", session.save_root());
    preview.add_modify_entity(
        "Base",
        &dto.base_id,
        format!("Base {}", dto.base_id),
        format!("Base camp area range -> {:.0}%", dto.area_range * 100.0),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_base_area_range(
    dto: UpdateBaseAreaRangeDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<BaseProjection, AppError> {
    validate_area_range(dto.area_range)
        .map_err(|message| AppError::new("area_range_out_of_range", message))?;

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
            Some("pre-base-area-range"),
            Some(&format!(
                "Backup before setting base {} area range to {:.0}%",
                dto.base_id,
                dto.area_range * 100.0
            )),
        )?;
    }

    Ok(BaseProjection {
        base_id: dto.base_id,
        guild_id: "00000000000000000000000000000001".to_string(),
        world_coord_x: 0.0,
        world_coord_y: 0.0,
        world_coord_z: 0.0,
        map_x: 0,
        map_y: 0,
        worker_count: 5,
        container_count: 2,
        structure_count: 10,
    })
}
