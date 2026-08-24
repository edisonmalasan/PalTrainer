//! Guild mutation and administration IPC commands with mandatory preview, backup, and audit support.

use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::guilds::mutation::{TransferGuildAdminDto, UpdateGuildDto};
use crate::domain::guilds::GuildProjection;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;

#[tauri::command]
pub fn preview_update_guild(
    dto: UpdateGuildDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("update_guild", session.save_root());
    let mut changes = Vec::new();

    if let Some(name) = &dto.name {
        changes.push(format!("Guild Name -> '{}'", name));
    }
    if let Some(level) = dto.level {
        changes.push(format!("Level -> {}", level));
    }

    let change_str = if changes.is_empty() {
        "No changes specified".to_string()
    } else {
        changes.join(", ")
    };

    preview.add_modify_entity(
        "Guild",
        &dto.guild_id,
        dto.name.as_deref().unwrap_or(&dto.guild_id),
        change_str,
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_guild(
    dto: UpdateGuildDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<GuildProjection, AppError> {
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
            Some("pre-edit-guild"),
            Some(&format!("Backup before updating guild {}", dto.guild_id)),
        )?;
    }

    let updated = GuildProjection {
        guild_id: dto.guild_id.clone(),
        name: dto.name.unwrap_or_else(|| "Guild".to_string()),
        admin_player_uid: "00000000000000000000000000000001".to_string(),
        admin_player_name: "Admin".to_string(),
        level: dto.level.unwrap_or(1),
        base_count: 1,
        members: Vec::new(),
    };

    Ok(updated)
}

#[tauri::command]
pub fn preview_transfer_guild_admin(
    dto: TransferGuildAdminDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("transfer_guild_admin", session.save_root());

    preview.add_modify_entity(
        "Guild",
        &dto.guild_id,
        format!("Guild {}", dto.guild_id),
        format!("Transfer leadership to UID {}", dto.new_admin_uid),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_transfer_guild_admin(
    dto: TransferGuildAdminDto,
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
            Some("pre-transfer-guild-admin"),
            Some(&format!(
                "Backup before transferring guild {} admin to {}",
                dto.guild_id, dto.new_admin_uid
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_delete_guild(
    guild_id: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("delete_guild", session.save_root());

    preview.add_delete_entity(
        "Guild",
        &guild_id,
        format!("Guild {}", guild_id),
        "Disband guild, reset member memberships to solo, and unregister guild bases",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_delete_guild(
    guild_id: String,
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
            Some("pre-delete-guild"),
            Some(&format!("Backup before disbanding guild {}", guild_id)),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_disband_empty_guilds(
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("disband_empty_guilds", session.save_root());

    preview.add_delete_entity(
        "Guilds",
        "empty_guilds",
        "All 0-member guilds",
        "Disband and clean up all abandoned guilds with 0 active members",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_disband_empty_guilds(
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

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-disband-empty-guilds"),
            Some("Backup before disbanding empty guilds"),
        )?;
    }

    Ok(0)
}

#[tauri::command]
pub fn preview_unlock_all_lab_research(
    guild_id: String,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("unlock_all_lab_research", session.save_root());

    preview.add_modify_entity(
        "Guild",
        &guild_id,
        format!("Guild {}", guild_id),
        "Unlock all lab research and technology upgrades",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_unlock_all_lab_research(
    guild_id: String,
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
            Some("pre-unlock-lab-research"),
            Some(&format!(
                "Backup before unlocking lab research for guild {}",
                guild_id
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_move_guild_member(
    dto: crate::domain::guilds::mutation::MoveGuildMemberDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("move_guild_member", session.save_root());

    preview.add_modify_entity(
        "Player",
        &dto.player_uid,
        format!("Player {}", dto.player_uid),
        format!(
            "Move from guild {} to guild {}",
            dto.source_guild_id, dto.target_guild_id
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_move_guild_member(
    dto: crate::domain::guilds::mutation::MoveGuildMemberDto,
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
            Some("pre-move-guild-member"),
            Some(&format!(
                "Backup before moving player {} to guild {}",
                dto.player_uid, dto.target_guild_id
            )),
        )?;
    }

    Ok(())
}
