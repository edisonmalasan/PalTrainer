mod commands;
pub mod domain;
mod error;
pub mod pal_save;
pub mod resources;
pub mod security;
mod storage;
pub mod tasks;

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::app::get_app_info,
            commands::app::get_feature_flags,
            commands::settings::get_settings,
            commands::settings::save_settings,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run PalTrainer");
}
