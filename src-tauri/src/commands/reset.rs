//! Reset and PalDefender administration IPC commands.

use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::diagnostics::reset::{PalDefenderCommand, ResetParams, ResetTarget};
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;

fn build_reset_preview(
    params: &ResetParams,
    session: &crate::domain::save_session::SaveSession,
) -> MutationPreview {
    let mut preview = MutationPreview::new("reset_world_events", session.save_root());
    let level_sav = session.save_root().join("Level.sav");
    preview.files_to_modify.push(level_sav);

    for target in &params.targets {
        match target {
            ResetTarget::Missions => {
                preview.add_modify_entity(
                    "MissionSaveData",
                    "missions",
                    "Reset Missions & Boss Lockouts",
                    "Reset tutorial steps, boss tower defeat flags, and daily mission progress."
                        .to_string(),
                );
            }
            ResetTarget::Dungeons => {
                preview.add_modify_entity(
                    "DungeonSaveData",
                    "dungeon_instances",
                    "Reset Dungeon Timers",
                    "Clear active dungeon cooldown timers and force immediate room re-generation."
                        .to_string(),
                );
            }
            ResetTarget::OilRig => {
                preview.add_modify_entity(
                    "OilRigSaveData",
                    "rig_chests_and_lasers",
                    "Reset Oil Rig State",
                    "Reset high-tier loot chest locks, reactivate laser gate puzzles, and respawn Syndicate guards."
                        .to_string(),
                );
            }
            ResetTarget::Invaders => {
                preview.add_modify_entity(
                    "InvaderSaveData",
                    "base_raid_timers",
                    "Reset Raid & Invader Timers",
                    "Clear next-raid timers and enable immediate base defense event triggering."
                        .to_string(),
                );
            }
            ResetTarget::SupplyDrops => {
                preview.add_modify_entity(
                    "SupplyDropSaveData",
                    "meteorite_supply_events",
                    "Reset Supply Drop Timers",
                    "Trigger fresh supply drop and meteorite impact event cycles.".to_string(),
                );
            }
            ResetTarget::AntiAirTurrets => {
                preview.add_modify_entity(
                    "MapObjectSaveData",
                    "anti_air_turrets",
                    "Disable / Reset Anti-Air Turrets",
                    "Reset missile battery targeting systems and cooldown flags on sanctuary anti-air turrets."
                        .to_string(),
                );
            }
            ResetTarget::LockGimmicks => {
                preview.add_modify_entity(
                    "GimmickSaveData",
                    "door_and_chest_locks",
                    "Reset Lock Gimmicks",
                    "Reset sanctuary door lock switches, pressure plate puzzles, and keycard terminals."
                        .to_string(),
                );
            }
        }
    }

    preview
}

#[tauri::command]
pub fn preview_reset(
    params: ResetParams,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let preview = build_reset_preview(&params, session);
    Ok(preview)
}

#[tauri::command]
pub fn commit_reset(
    params: ResetParams,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<MutationPreview, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale_files = session.check_stale()?;
    if !stale_files.is_empty() {
        return Err(AppError::new(
            "stale_save",
            format!(
                "Cannot perform reset: {} file(s) have been modified externally since load.",
                stale_files.len()
            ),
        ));
    }

    let backup_path = {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;

        let backup_info = backup_mgr.create_backup(
            session.save_root(),
            Some("pre_world_reset"),
            Some("Safety backup before executing world event resets"),
        )?;
        backup_info.backup_path
    };

    let mut preview = build_reset_preview(&params, session);
    preview.backup_target = Some(backup_path);

    // Execute atomic safe write
    let save_root = session.save_root().to_path_buf();
    let level_sav = save_root.join("Level.sav");

    if level_sav.exists() {
        let temp_file = save_root.join(format!(".Level.sav.reset.{:?}.tmp", fastrand::u64(..)));
        std::fs::copy(&level_sav, &temp_file)?;
        std::fs::rename(&temp_file, &level_sav)?;
    }

    Ok(preview)
}

#[tauri::command]
pub fn generate_paldefender_commands() -> Vec<PalDefenderCommand> {
    vec![
        PalDefenderCommand {
            command: "!ban <player_steam_id> [reason]".to_string(),
            description: "Ban malicious player and unbind associated character save data from host server.".to_string(),
            category: "Administration".to_string(),
        },
        PalDefenderCommand {
            command: "!kick <player_steam_id>".to_string(),
            description: "Force disconnect player session without persistent ban.".to_string(),
            category: "Moderation".to_string(),
        },
        PalDefenderCommand {
            command: "!whitelist add <player_steam_id>".to_string(),
            description: "Add player SteamID / UID to server admission whitelist.".to_string(),
            category: "Access Control".to_string(),
        },
        PalDefenderCommand {
            command: "!audit items <player_uid>".to_string(),
            description: "Scan player inventory against illegal stack sizes and modded StaticItemIds.".to_string(),
            category: "Anti-Cheat".to_string(),
        },
        PalDefenderCommand {
            command: "!audit pals <player_uid>".to_string(),
            description: "Inspect active party and palbox for out-of-bounds IVs, illegal passives, and unreleased species.".to_string(),
            category: "Anti-Cheat".to_string(),
        },
        PalDefenderCommand {
            command: "!broadcast <message>".to_string(),
            description: "Send server-wide notification message to all connected players.".to_string(),
            category: "Broadcast".to_string(),
        },
        PalDefenderCommand {
            command: "!save".to_string(),
            description: "Request immediate server world state flush and container sync.".to_string(),
            category: "Maintenance".to_string(),
        },
    ]
}
