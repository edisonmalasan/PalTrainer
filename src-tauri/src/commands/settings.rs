use tauri::AppHandle;

use crate::error::AppError;
use crate::storage::settings::{read_settings, write_settings, AppSettings};

#[tauri::command]
pub fn get_settings(app: AppHandle) -> Result<AppSettings, AppError> {
    read_settings(&app)
}

#[tauri::command]
pub fn save_settings(app: AppHandle, settings: AppSettings) -> Result<AppSettings, AppError> {
    write_settings(&app, &settings)?;
    Ok(settings)
}
