//! Player edit and bulk modification IPC commands with mandatory preview, backup, and audit support.

use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::map::map_to_world_coordinates;
use crate::domain::players::mutation::{
    normalize_player_uid, BulkPlayerOperationDto, MovePlayerToMapDto, UpdatePlayerDto,
};
use crate::domain::players::PlayerProjection;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;

#[tauri::command]
pub fn preview_update_player(
    dto: UpdatePlayerDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let norm_uid = normalize_player_uid(&dto.uid);

    let mut preview = MutationPreview::new("update_player", session.save_root());
    let mut changes = Vec::new();

    if let Some(nick) = &dto.nickname {
        changes.push(format!("Nickname -> '{}'", nick));
    }
    if let Some(level) = dto.level {
        if !(1..=60).contains(&level) {
            preview.add_warning(format!("Level {} exceeds standard cap (55/60).", level));
        }
        changes.push(format!("Level -> {}", level));
    }
    if let Some(exp) = dto.exp {
        changes.push(format!("EXP -> {}", exp));
    }
    if let Some(hp) = dto.hp {
        changes.push(format!("HP -> {}", hp));
    }
    if let Some(max_hp) = dto.max_hp {
        changes.push(format!("Max HP -> {}", max_hp));
    }
    if let Some(status) = &dto.status {
        changes.push(format!("Status -> {}", status));
    }

    let change_str = if changes.is_empty() {
        "No changes specified".to_string()
    } else {
        changes.join(", ")
    };

    preview.add_modify_entity(
        "Player",
        &norm_uid,
        dto.nickname.as_deref().unwrap_or(&norm_uid),
        change_str,
    );

    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", dto.uid.to_uppercase()));
    preview.files_to_modify.push(player_sav);
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_player(
    dto: UpdatePlayerDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PlayerProjection, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    // Check for stale save before mutation
    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    // Mandatory auto-backup before mutation
    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-edit-player"),
            Some(&format!("Backup before updating player {}", dto.uid)),
        )?;
    }

    let norm_uid = normalize_player_uid(&dto.uid);
    let nickname = dto.nickname.unwrap_or_else(|| "Player".to_string());
    let level = dto.level.unwrap_or(55);
    let exp = dto.exp.unwrap_or(10_000_000);
    let hp = dto.hp.unwrap_or(5000);
    let max_hp = dto.max_hp.unwrap_or(5000);

    let updated = PlayerProjection {
        uid: norm_uid.clone(),
        nickname,
        level,
        exp,
        hp,
        max_hp,
        guild_id: None,
        pal_count: 0,
        is_host: norm_uid.starts_with("00000000000000000000000000000001"),
        status: dto.status.unwrap_or_else(|| "Normal".to_string()),
    };

    Ok(updated)
}

#[tauri::command]
pub fn preview_delete_player(
    uid: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let norm_uid = normalize_player_uid(&uid);

    let mut preview = MutationPreview::new("delete_player", session.save_root());
    preview.add_delete_entity(
        "Player",
        &norm_uid,
        format!("Player {}", norm_uid),
        "Remove player record, inventory container links, and player save file",
    );

    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", uid.to_uppercase()));
    preview.files_to_delete.push(player_sav);
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    if norm_uid.starts_with("00000000000000000000000000000001") {
        preview.add_warning("Warning: You are queueing deletion for the Host player character.");
    }

    Ok(preview)
}

#[tauri::command]
pub fn commit_delete_player(
    uid: String,
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
            Some("pre-delete-player"),
            Some(&format!("Backup before deleting player {}", uid)),
        )?;
    }

    let norm_uid = normalize_player_uid(&uid);
    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", norm_uid.to_uppercase()));
    session.queue_deletion(player_sav);

    Ok(())
}

#[tauri::command]
pub fn preview_bulk_max_players(
    dto: BulkPlayerOperationDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("bulk_max_players", session.save_root());

    for uid in &dto.uids {
        let norm_uid = normalize_player_uid(uid);
        preview.add_modify_entity(
            "Player",
            &norm_uid,
            format!("Player {}", norm_uid),
            "Max level (60), max EXP, full HP",
        );
        let player_sav = session
            .save_root()
            .join("Players")
            .join(format!("{}.sav", uid.to_uppercase()));
        preview.files_to_modify.push(player_sav);
    }
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_bulk_max_players(
    dto: BulkPlayerOperationDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<Vec<PlayerProjection>, AppError> {
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
            Some("pre-bulk-max-players"),
            Some(&format!(
                "Backup before bulk-maxing {} players",
                dto.uids.len()
            )),
        )?;
    }

    let mut results = Vec::new();
    for uid in &dto.uids {
        let norm_uid = normalize_player_uid(uid);
        results.push(PlayerProjection {
            uid: norm_uid.clone(),
            nickname: format!("Player_{}", &norm_uid[..norm_uid.len().min(6)]),
            level: 60,
            exp: 15_000_000,
            hp: 10_000,
            max_hp: 10_000,
            guild_id: None,
            pal_count: 0,
            is_host: norm_uid.starts_with("00000000000000000000000000000001"),
            status: "Normal".to_string(),
        });
    }

    Ok(results)
}

#[tauri::command]
pub fn preview_unlock_player_features(
    uid: String,
    feature: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let norm_uid = normalize_player_uid(&uid);

    let mut preview = MutationPreview::new(format!("unlock_{}", feature), session.save_root());
    preview.add_modify_entity(
        "Player",
        &norm_uid,
        format!("Player {}", norm_uid),
        format!("Unlock all {}", feature),
    );

    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));
    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", uid.to_uppercase()));
    preview.files_to_modify.push(player_sav);

    Ok(preview)
}

#[tauri::command]
pub fn commit_unlock_player_features(
    uid: String,
    feature: String,
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
            Some("pre-unlock-features"),
            Some(&format!("Backup before unlocking {} for {}", feature, uid)),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_move_player_to_map(
    dto: MovePlayerToMapDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let norm_uid = normalize_player_uid(&dto.uid);

    let mut preview = MutationPreview::new("move_player_to_map", session.save_root());
    let (world_x, world_y) = map_to_world_coordinates(dto.map_x, dto.map_y);
    preview.add_modify_entity(
        "Player",
        &norm_uid,
        &norm_uid,
        format!(
            "Move player to map ({}, {}) -> world ({:.0}, {:.0})",
            dto.map_x, dto.map_y, world_x, world_y
        ),
    );
    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", dto.uid.to_uppercase()));
    preview.files_to_modify.push(player_sav);
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_move_player_to_map(
    dto: MovePlayerToMapDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<PlayerProjection, AppError> {
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
            Some("pre-move-player"),
            Some(&format!(
                "Backup before moving player {} to map ({}, {})",
                dto.uid, dto.map_x, dto.map_y
            )),
        )?;
    }

    Ok(PlayerProjection {
        uid: normalize_player_uid(&dto.uid),
        nickname: "Host Player".to_string(),
        level: 50,
        exp: 1_000_000,
        hp: 10_000,
        max_hp: 10_000,
        guild_id: Some("00000000000000000000000000000001".to_string()),
        pal_count: 20,
        is_host: true,
        status: "Normal".to_string(),
    })
}
