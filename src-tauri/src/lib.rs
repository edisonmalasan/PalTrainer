use std::path::PathBuf;
use std::sync::Mutex;

mod commands;
pub mod domain;
mod error;
pub mod pal_save;
pub mod resources;
pub mod security;
pub mod storage;
pub mod tasks;

pub fn run() {
    let default_backup_root = dirs::data_dir()
        .map(|d| d.join("PalTrainer").join("Backups"))
        .unwrap_or_else(|| PathBuf::from("Backups"));

    tauri::Builder::default()
        .manage(Mutex::new(None::<domain::save_session::SaveSession>))
        .manage(Mutex::new(storage::BackupManager::new(default_backup_root)))
        .manage(Mutex::new(domain::exclusions::ExclusionConfig::default()))
        .manage(tasks::TaskTracker::new())
        .invoke_handler(tauri::generate_handler![
            commands::app::get_app_info,
            commands::app::get_feature_flags,
            commands::settings::get_settings,
            commands::settings::save_settings,
            commands::save_session::load_save_session,
            commands::save_session::get_save_summary,
            commands::save_session::check_stale_save,
            commands::save_session::close_save_session,
            commands::backup::list_backups,
            commands::backup::create_manual_backup,
            commands::backup::restore_backup,
            commands::inspect::get_players,
            commands::inspect::get_guilds,
            commands::inspect::get_bases,
            commands::inspect::get_pals,
            commands::inspect::get_inventory,
            commands::inspect::get_map_markers,
            commands::inspect::run_save_diagnostics,
            commands::inspect::lookup_breeding,
            commands::inspect::get_game_catalog,
            commands::player::preview_update_player,
            commands::player::commit_update_player,
            commands::player::preview_delete_player,
            commands::player::commit_delete_player,
            commands::player::preview_bulk_max_players,
            commands::player::commit_bulk_max_players,
            commands::player::preview_unlock_player_features,
            commands::player::commit_unlock_player_features,
            commands::pal::preview_update_pal,
            commands::pal::commit_update_pal,
            commands::pal::preview_create_pal,
            commands::pal::commit_create_pal,
            commands::pal::preview_import_pal,
            commands::pal::commit_import_pal,
            commands::pal::preview_clone_pal,
            commands::pal::commit_clone_pal,
            commands::pal::preview_delete_pal,
            commands::pal::commit_delete_pal,
            commands::pal::preview_bulk_max_pals,
            commands::pal::commit_bulk_max_pals,
            commands::pal::preview_bulk_sync_pal_skills,
            commands::pal::commit_bulk_sync_pal_skills,
            commands::pal::export_pal_bundle,
            commands::inventory::preview_update_inventory_slot,
            commands::inventory::commit_update_inventory_slot,
            commands::inventory::preview_add_item,
            commands::inventory::commit_add_item,
            commands::inventory::preview_remove_item,
            commands::inventory::commit_remove_item,
            commands::inventory::preview_clear_container,
            commands::inventory::commit_clear_container,
            commands::inventory::preview_resize_container,
            commands::inventory::commit_resize_container,
            commands::inventory::preview_bulk_add_key_items,
            commands::inventory::commit_bulk_add_key_items,
            commands::guild::preview_update_guild,
            commands::guild::commit_update_guild,
            commands::guild::preview_transfer_guild_admin,
            commands::guild::commit_transfer_guild_admin,
            commands::guild::preview_delete_guild,
            commands::guild::commit_delete_guild,
            commands::guild::preview_disband_empty_guilds,
            commands::guild::commit_disband_empty_guilds,
            commands::guild::preview_unlock_all_lab_research,
            commands::guild::commit_unlock_all_lab_research,
            commands::guild::preview_move_guild_member,
            commands::guild::commit_move_guild_member,
            commands::base::preview_update_base,
            commands::base::commit_update_base,
            commands::base::preview_nudge_base_coordinates,
            commands::base::commit_nudge_base_coordinates,
            commands::base::preview_delete_base,
            commands::base::commit_delete_base,
            commands::base::export_base_bundle,
            commands::base::preview_import_base_bundle,
            commands::base::commit_import_base_bundle,
            commands::base::preview_clone_base,
            commands::base::commit_clone_base,
            commands::base::preview_repair_base_structures,
            commands::base::commit_repair_base_structures,
            commands::exclusions::get_exclusion_config,
            commands::exclusions::save_exclusion_config,
            commands::exclusions::add_zone_exclusion,
            commands::exclusions::remove_zone_exclusion,
            commands::exclusions::check_coordinate_excluded,
            commands::world::get_world_options,
            commands::world::preview_save_world_options,
            commands::world::commit_save_world_options,
            commands::world::get_world_meta,
            commands::world::preview_save_world_meta,
            commands::world::commit_save_world_meta,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run PalTrainer");
}
