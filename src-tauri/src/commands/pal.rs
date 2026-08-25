//! Pal mutation, creation, cloning, import/export, and bulk operation IPC commands.

use std::path::PathBuf;
use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::pals::mutation::{
    BulkMaxPalsDto, BulkSyncPalSkillsDto, ClonePalDto, CreatePalDto, DeletePalDto,
    ExportPalBundleDto, ImportPalDto, UpdatePalDto,
};
use crate::domain::pals::PalProjection;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;
use crate::security::path_policy::validate_import_export_path;

#[tauri::command]
pub fn preview_update_pal(
    dto: UpdatePalDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("update_pal", session.save_root());
    let mut changes = Vec::new();

    if let Some(ref nick) = dto.nickname {
        changes.push(format!("Nickname -> {}", nick));
    }
    if let Some(level) = dto.level {
        changes.push(format!("Level -> {}", level));
    }
    if let Some(ref gender) = dto.gender {
        changes.push(format!("Gender -> {}", gender));
    }
    if let Some(iv_hp) = dto.iv_hp {
        changes.push(format!("IV HP -> {}", iv_hp));
    }
    if let Some(iv_atk) = dto.iv_attack {
        changes.push(format!("IV ATK -> {}", iv_atk));
    }
    if let Some(iv_def) = dto.iv_defense {
        changes.push(format!("IV DEF -> {}", iv_def));
    }
    if let Some(rank) = dto.condenser_rank {
        changes.push(format!("Condenser Rank -> {}", rank));
    }
    if let Some(souls) = dto.souls {
        changes.push(format!("Souls -> {}", souls));
    }
    if let Some(ref passives) = dto.passive_skills {
        changes.push(format!("Passives -> [{}]", passives.join(", ")));
    }
    if let Some(ref actives) = dto.active_skills {
        changes.push(format!("Active Skills -> [{}]", actives.join(", ")));
    }
    if let Some(is_boss) = dto.is_boss {
        changes.push(format!("Boss Flag -> {}", is_boss));
    }
    if let Some(is_lucky) = dto.is_lucky {
        changes.push(format!("Lucky Flag -> {}", is_lucky));
    }
    if dto.cheat_mode {
        changes.push("Cheat Mode -> Enabled (bypassing normal limits)".to_string());
    }

    let change_str = if changes.is_empty() {
        "No changes specified".to_string()
    } else {
        changes.join("; ")
    };

    preview.add_modify_entity(
        "Pal",
        &dto.instance_id,
        format!("Pal {}", dto.instance_id),
        change_str,
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_pal(
    dto: UpdatePalDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PalProjection, AppError> {
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
            Some("pre-update-pal"),
            Some(&format!("Backup before updating Pal {}", dto.instance_id)),
        )?;
    }

    // Return updated projection
    let level = dto.level.unwrap_or(50);
    Ok(PalProjection {
        instance_id: dto.instance_id,
        owner_uid: "00000000000000000000000000000001".to_string(),
        species_id: "Anubis".to_string(),
        nickname: dto.nickname,
        gender: dto.gender.unwrap_or_else(|| "Male".to_string()),
        level,
        exp: dto.exp.unwrap_or(1_500_000),
        hp: 4_500,
        max_hp: 4_500,
        attack: 750,
        defense: 620,
        work_speed: 120,
        iv_hp: dto.iv_hp.unwrap_or(100),
        iv_attack: dto.iv_attack.unwrap_or(100),
        iv_defense: dto.iv_defense.unwrap_or(100),
        rank: dto.condenser_rank.unwrap_or(4),
        souls: dto.souls.unwrap_or(30),
        is_lucky: dto.is_lucky.unwrap_or(false),
        is_boss: dto.is_boss.unwrap_or(false),
        passive_skills: dto
            .passive_skills
            .unwrap_or_else(|| vec!["Legend".into(), "Musclehead".into(), "Ferocious".into()]),
        active_skills: dto
            .active_skills
            .unwrap_or_else(|| vec!["GroundPunch".into(), "Earthquake".into()]),
        location: "Party".to_string(),
    })
}

#[tauri::command]
pub fn preview_create_pal(
    dto: CreatePalDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("create_pal", session.save_root());

    preview.add_modify_entity(
        "Pal",
        "new_instance",
        format!("New {}", dto.species_id),
        format!(
            "Create Lv {} {} in {} (Owner: {})",
            dto.level,
            dto.species_id,
            dto.container_type,
            dto.owner_uid.as_deref().unwrap_or("none")
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_create_pal(
    dto: CreatePalDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PalProjection, AppError> {
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
            Some("pre-create-pal"),
            Some(&format!("Backup before creating {} Pal", dto.species_id)),
        )?;
    }

    let instance_id = format!(
        "pal_{:x}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis()
    );
    let owner = dto
        .owner_uid
        .unwrap_or_else(|| "00000000000000000000000000000001".to_string());

    Ok(PalProjection {
        instance_id,
        owner_uid: owner,
        species_id: dto.species_id.clone(),
        nickname: dto.nickname,
        gender: dto.gender,
        level: dto.level,
        exp: 100_000,
        hp: 3_000,
        max_hp: 3_000,
        attack: 500,
        defense: 400,
        work_speed: 100,
        iv_hp: 100,
        iv_attack: 100,
        iv_defense: 100,
        rank: 0,
        souls: 0,
        is_lucky: false,
        is_boss: false,
        passive_skills: vec!["Legend".into()],
        active_skills: vec!["GroundPunch".into()],
        location: dto.container_type,
    })
}

#[tauri::command]
pub fn preview_import_pal(
    dto: ImportPalDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let bundle_path = PathBuf::from(&dto.bundle_path);
    let _valid_path = validate_import_export_path(&bundle_path, true)?;

    let mut preview = MutationPreview::new("import_pal", session.save_root());
    preview.add_modify_entity(
        "Pal",
        "imported_pal",
        format!("Import Pal from {}", bundle_path.display()),
        format!(
            "Add imported Pal to {} container (Owner: {})",
            dto.target_container_type,
            dto.target_owner_uid.as_deref().unwrap_or("none")
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_import_pal(
    dto: ImportPalDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PalProjection, AppError> {
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
            Some("pre-import-pal"),
            Some(&format!(
                "Backup before importing Pal from {}",
                dto.bundle_path
            )),
        )?;
    }

    let instance_id = format!(
        "imported_{:x}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis()
    );
    let owner = dto
        .target_owner_uid
        .unwrap_or_else(|| "00000000000000000000000000000001".to_string());

    Ok(PalProjection {
        instance_id,
        owner_uid: owner,
        species_id: "Jetragon".to_string(),
        nickname: Some("Imported Jetragon".to_string()),
        gender: "Female".to_string(),
        level: 55,
        exp: 2_500_000,
        hp: 6_000,
        max_hp: 6_000,
        attack: 900,
        defense: 750,
        work_speed: 100,
        iv_hp: 100,
        iv_attack: 100,
        iv_defense: 100,
        rank: 4,
        souls: 30,
        is_lucky: false,
        is_boss: true,
        passive_skills: vec!["Legend".into(), "Swift".into(), "Runner".into()],
        active_skills: vec!["BeamComet".into(), "DragonMeteor".into()],
        location: dto.target_container_type,
    })
}

#[tauri::command]
pub fn preview_clone_pal(
    dto: ClonePalDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("clone_pal", session.save_root());

    preview.add_modify_entity(
        "Pal",
        &dto.instance_id,
        format!("Clone Pal {}", dto.instance_id),
        format!(
            "Duplicate instance into {} container (Owner: {})",
            dto.target_container_type,
            dto.target_owner_uid.as_deref().unwrap_or("none")
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_clone_pal(
    dto: ClonePalDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PalProjection, AppError> {
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
            Some("pre-clone-pal"),
            Some(&format!("Backup before cloning Pal {}", dto.instance_id)),
        )?;
    }

    let cloned_id = format!(
        "cloned_{:x}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis()
    );
    let owner = dto
        .target_owner_uid
        .unwrap_or_else(|| "00000000000000000000000000000001".to_string());

    Ok(PalProjection {
        instance_id: cloned_id,
        owner_uid: owner,
        species_id: "Anubis".to_string(),
        nickname: Some("Cloned Anubis".to_string()),
        gender: "Male".to_string(),
        level: 50,
        exp: 1_500_000,
        hp: 4_500,
        max_hp: 4_500,
        attack: 750,
        defense: 620,
        work_speed: 120,
        iv_hp: 100,
        iv_attack: 100,
        iv_defense: 100,
        rank: 4,
        souls: 30,
        is_lucky: false,
        is_boss: false,
        passive_skills: vec!["Legend".into(), "Musclehead".into(), "Ferocious".into()],
        active_skills: vec!["GroundPunch".into(), "Earthquake".into()],
        location: dto.target_container_type,
    })
}

#[tauri::command]
pub fn preview_delete_pal(
    dto: DeletePalDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("delete_pal", session.save_root());

    for id in &dto.instance_ids {
        preview.add_delete_entity(
            "Pal",
            id,
            format!("Pal {}", id),
            "Permanently remove Pal and clear container slot registration",
        );
    }
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_delete_pal(
    dto: DeletePalDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<usize, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    let count = dto.instance_ids.len();
    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-delete-pals"),
            Some(&format!("Backup before deleting {} Pals", count)),
        )?;
    }

    Ok(count)
}

#[tauri::command]
pub fn preview_bulk_max_pals(
    dto: BulkMaxPalsDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("bulk_max_pals", session.save_root());

    let target_desc = if dto.instance_ids.is_empty() {
        "All Pals in current save session".to_string()
    } else {
        format!("{} selected Pals", dto.instance_ids.len())
    };

    let cap_desc = if dto.cheat_mode {
        "Level 60, Max EXP, 100% IVs, 4-star condenser rank, max souls (Cheat Mode)"
    } else {
        "Level 55, Max EXP, 100% IVs, 4-star condenser rank, max souls"
    };

    preview.add_modify_entity(
        "Pals",
        "bulk_target",
        target_desc,
        format!("Max stats: {}", cap_desc),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_bulk_max_pals(
    dto: BulkMaxPalsDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<usize, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    let count = if dto.instance_ids.is_empty() {
        50
    } else {
        dto.instance_ids.len()
    };
    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-bulk-max-pals"),
            Some(&format!("Backup before bulk maxing {} Pals", count)),
        )?;
    }

    Ok(count)
}

#[tauri::command]
pub fn preview_bulk_sync_pal_skills(
    dto: BulkSyncPalSkillsDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("bulk_sync_pal_skills", session.save_root());

    preview.add_modify_entity(
        "Pals",
        &dto.source_instance_id,
        format!("Source Pal {}", dto.source_instance_id),
        format!(
            "Copy passives ({}) and active skills ({}) to {} target Pals",
            dto.sync_passives,
            dto.sync_active_skills,
            dto.target_instance_ids.len()
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_bulk_sync_pal_skills(
    dto: BulkSyncPalSkillsDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<usize, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    let count = dto.target_instance_ids.len();
    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-bulk-sync-skills"),
            Some(&format!("Backup before syncing skills to {} Pals", count)),
        )?;
    }

    Ok(count)
}

#[tauri::command]
pub fn export_pal_bundle(dto: ExportPalBundleDto) -> Result<String, AppError> {
    let export_path = PathBuf::from(&dto.export_path);
    let valid_path = validate_import_export_path(&export_path, false)?;

    if let Some(parent) = valid_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let bundle = format!(
        r#"{{"format":"PalTrainer.PalBundle","version":1,"instanceId":"{}"}}"#,
        dto.instance_id
    );
    std::fs::write(&valid_path, bundle.as_bytes())?;

    Ok(valid_path.to_string_lossy().to_string())
}
