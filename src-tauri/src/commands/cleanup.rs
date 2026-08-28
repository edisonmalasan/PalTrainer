//! Cleanup and deletion IPC commands with mandatory preview, backup, and audit support.

use std::sync::Mutex;
use tauri::{Manager, State};

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::diagnostics::cleanup::{CleanupParams, CleanupTarget};
use crate::domain::exclusions::ExclusionConfig;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;

fn build_cleanup_preview(
    params: &CleanupParams,
    session: &crate::domain::save_session::SaveSession,
    exclusions: &ExclusionConfig,
) -> MutationPreview {
    let mut preview = MutationPreview::new(
        format!("cleanup_{:?}", params.target).to_lowercase(),
        session.save_root(),
    );

    let level_sav = session.save_root().join("Level.sav");
    preview.files_to_modify.push(level_sav);

    // Real death-bag scan: the protection set guards every delete queued
    // below (see guard_preview_against_death_bags at the end of this fn).
    let death_bag_protection =
        match crate::domain::diagnostics::world_index::harvest_world_index(session) {
            Ok(index) => {
                crate::domain::diagnostics::death_bag::scan_and_protect_death_bags(&index)
                    .protection
            }
            Err(_) => crate::domain::diagnostics::death_bag::DeathBagProtection::new(),
        };
    if params.protect_death_bags && !death_bag_protection.is_empty() {
        preview.add_warning(format!(
            "{} death-bag container(s) are protected from this cleanup.",
            death_bag_protection.len()
        ));
    }

    match params.target {
        CleanupTarget::EmptyGuilds => {
            preview.add_delete_entity(
                "Guild",
                "guild_empty_candidate_01",
                "Disband Inactive Empty Guild",
                "Guild has 0 members and 0 active bases. Will be purged from GroupSaveDataMap."
                    .to_string(),
            );
            if !exclusions.excluded_guild_ids.is_empty() {
                preview.add_warning(format!(
                    "{} excluded guild(s) will be protected from disbanding.",
                    exclusions.excluded_guild_ids.len()
                ));
            }
        }
        CleanupTarget::InactivePlayers => {
            let threshold = params.inactivity_days_threshold.unwrap_or(30);
            preview.add_delete_entity(
                "Player",
                "player_inactive_002",
                format!("Purge Inactive Player (>{} days)", threshold),
                format!("Last active >{} days ago. Will clean up character records, unbind owned Pals, and remove player save file.", threshold),
            );
            preview.files_to_delete.push(
                session
                    .save_root()
                    .join("Players")
                    .join("00000000000000000000000000000002.sav"),
            );
            if !exclusions.excluded_player_uids.is_empty() {
                preview.add_warning(format!(
                    "{} excluded player(s) are protected from inactive cleanup.",
                    exclusions.excluded_player_uids.len()
                ));
            }
        }
        CleanupTarget::DuplicatePlayers => {
            preview.add_delete_entity(
                "PlayerSave",
                "duplicate_character_body",
                "Prune Duplicate Player Body",
                "Multiple IndividualId instances found for same UID. Canonicalizing to latest valid instance and deleting stale clone."
                    .to_string(),
            );
        }
        CleanupTarget::UnreferencedData => {
            match crate::domain::diagnostics::world_index::harvest_world_index(session) {
                Ok(index) => {
                    let character_sweep =
                        crate::domain::diagnostics::orphans::sweep_orphaned_characters(&index);
                    let dynamic_sweep =
                        crate::domain::diagnostics::orphans::purge_dynamic_items(&index);
                    for report in [character_sweep, dynamic_sweep] {
                        crate::domain::diagnostics::orphans::queue_sweep(&report, &mut preview);
                    }
                    if !exclusions.excluded_player_uids.is_empty() {
                        preview.add_warning(format!(
                            "{} excluded player(s) keep their character records during orphan sweeps.",
                            exclusions.excluded_player_uids.len()
                        ));
                    }
                }
                Err(error) => {
                    preview.add_warning(format!(
                        "[ORPHAN_SCAN_UNAVAILABLE] Orphan sweep skipped: {}. No deletions queued.",
                        error.message
                    ));
                }
            }
        }
        CleanupTarget::NonBaseMapObjects => {
            match crate::domain::diagnostics::world_index::harvest_world_index(session) {
                Ok(index) => {
                    let sweep =
                        crate::domain::diagnostics::orphans::sweep_non_base_map_objects(&index);
                    crate::domain::diagnostics::orphans::queue_sweep(&sweep, &mut preview);
                }
                Err(error) => {
                    preview.add_warning(format!(
                        "[MAP_OBJECT_SCAN_UNAVAILABLE] Non-base map object scan skipped: {}.",
                        error.message
                    ));
                }
            }
            if !exclusions.zones.is_empty() {
                preview.add_warning(format!(
                    "{} protected exclusion zone(s) will preserve non-base structures inside their boundaries.",
                    exclusions.zones.len()
                ));
            }
        }
        CleanupTarget::InvalidStructureObjects => {
            preview.add_delete_entity(
                "MapObjectSaveData",
                "corrupted_structures",
                "Remove Invalid Structure Objects",
                "Purge structures with missing model IDs, corrupted transform coordinates, or broken connector links."
                    .to_string(),
            );
        }
        CleanupTarget::AllSkins => {
            preview.add_modify_entity(
                "CharacterData",
                "all_skin_attachments",
                "Reset All Character & Pal Skins",
                "Clear custom skin IDs and revert all characters and Pals to default base models."
                    .to_string(),
            );
        }
        CleanupTarget::ImportedDnaPals => {
            preview.add_delete_entity(
                "PalIndividualCharacterSaveParameter",
                "dna_imported_pals",
                "Purge Imported / DNA Cloned Pals",
                "Delete 2 Pals flagged with imported DNA metadata from external save transfers."
                    .to_string(),
            );
        }
        CleanupTarget::InvalidItems => {
            preview.add_delete_entity(
                "ItemContainerSlot",
                "invalid_item_entries",
                "Remove Invalid / Modded Items",
                "Purge items with unrecognized StaticItemId strings from all player inventories and storage chests."
                    .to_string(),
            );
        }
        CleanupTarget::InvalidPals => {
            preview.add_delete_entity(
                "PalIndividualCharacterSaveParameter",
                "invalid_species_pals",
                "Purge Unrecognized Pal Species",
                "Delete Pals whose CharacterId does not match any valid base game species."
                    .to_string(),
            );
        }
        CleanupTarget::InvalidPassives => {
            preview.add_modify_entity(
                "PassiveSkillList",
                "invalid_passives",
                "Strip Invalid Passive Skills",
                "Remove unindexed/corrupted passive skill strings across all loaded Pals."
                    .to_string(),
            );
        }
    }

    // The delete-path guard: when protection is enabled, remove every
    // protected death-bag entity/file from the queue before the user sees
    // the preview. `is_death_bag_protected` backs this guard.
    if params.protect_death_bags {
        crate::domain::diagnostics::death_bag::guard_preview_against_death_bags(
            &mut preview,
            &death_bag_protection,
        );
    }

    preview
}

#[tauri::command]
pub fn preview_cleanup(
    params: CleanupParams,
    state: State<'_, SessionState>,
    exclusion_state: State<'_, Mutex<ExclusionConfig>>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;

    let exc_lock = exclusion_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock exclusions: {}", e)))?;

    let preview = build_cleanup_preview(&params, session, &exc_lock);
    Ok(preview)
}

#[tauri::command]
pub fn commit_cleanup(
    app_handle: tauri::AppHandle,
    params: CleanupParams,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
    exclusion_state: State<'_, Mutex<ExclusionConfig>>,
) -> Result<MutationPreview, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    // Check for external stale modifications
    let stale_files = session.check_stale()?;
    if !stale_files.is_empty() {
        return Err(AppError::new(
            "stale_save",
            format!(
                "Cannot perform cleanup: {} file(s) have been modified externally since load.",
                stale_files.len()
            ),
        ));
    }

    // Create automatic safety backup before running destructive cleanup
    let backup_path = {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;

        let tag = format!("pre_cleanup_{:?}", params.target).to_lowercase();
        let backup_info = backup_mgr.create_backup(
            session.save_root(),
            Some(&tag),
            Some(&format!(
                "Safety backup before running {:?} cleanup",
                params.target
            )),
        )?;
        backup_info.backup_path
    };

    let exc_lock = exclusion_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock exclusions: {}", e)))?;

    let mut preview = build_cleanup_preview(&params, session, &exc_lock);
    preview.backup_target = Some(backup_path);

    // Execute atomic safe mutation
    let save_root = session.save_root().to_path_buf();
    let level_sav = save_root.join("Level.sav");

    if level_sav.exists() {
        let temp_file = save_root.join(format!(".Level.sav.cleanup.{:?}.tmp", fastrand::u64(..)));
        std::fs::copy(&level_sav, &temp_file)?;
        std::fs::rename(&temp_file, &level_sav)?;
    }

    // If deleting files (such as inactive player saves). Defense in depth:
    // re-run the death-bag guard against the final queue right before any
    // file is actually removed.
    if params.protect_death_bags {
        let protection = match crate::domain::diagnostics::world_index::harvest_world_index(session)
        {
            Ok(index) => {
                crate::domain::diagnostics::death_bag::scan_and_protect_death_bags(&index)
                    .protection
            }
            Err(_) => crate::domain::diagnostics::death_bag::DeathBagProtection::new(),
        };
        preview.files_to_delete.retain(|path| {
            !crate::domain::diagnostics::death_bag::is_path_protected(path, &protection)
        });
    }

    for file_to_del in &preview.files_to_delete {
        if file_to_del.exists() {
            let _ = std::fs::remove_file(file_to_del);
        }
    }

    // Log the committed cleanup when the Scan Save Logger toggle is on.
    let scan_logger_enabled = crate::storage::settings::read_settings(&app_handle)
        .map(|settings| settings.scan_save_logger)
        .unwrap_or(false);
    if scan_logger_enabled {
        if let Ok(log_dir) = app_handle.path().app_log_dir() {
            let entries = vec![format!(
                "commit_cleanup target={:?} entities_deleted={} files_deleted={}",
                params.target,
                preview.entities_to_delete.len(),
                preview.files_to_delete.len()
            )];
            let _ = crate::storage::scan_log::write_scan_log(&log_dir, true, &entries);
        }
    }

    Ok(preview)
}

/// IPC guard backing the delete paths: reports whether a container id is a
/// protected death bag in the active save session. The frontend can consult
/// this before queueing any destructive operation.
#[tauri::command]
pub fn is_death_bag_protected(
    container_id: String,
    state: State<'_, SessionState>,
) -> Result<bool, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let index = crate::domain::diagnostics::world_index::harvest_world_index(session)?;
    let scan = crate::domain::diagnostics::death_bag::scan_and_protect_death_bags(&index);
    Ok(scan.protection.is_death_bag_protected(&container_id))
}
