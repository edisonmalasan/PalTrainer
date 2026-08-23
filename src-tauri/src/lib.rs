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
        ])
        .run(tauri::generate_context!())
        .expect("failed to run PalTrainer");
}
