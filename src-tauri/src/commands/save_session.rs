//! Tauri IPC commands for SaveSession lifecycle and stale save detection.

use std::sync::Mutex;
use tauri::{AppHandle, State};

use crate::domain::save_session::{SaveSession, SaveSummaryDto, SessionError};
use crate::error::AppError;
use crate::storage::settings::{push_recent_save_path, read_settings, write_settings};

pub type SessionState = Mutex<Option<SaveSession>>;

#[tauri::command]
pub fn load_save_session(
    app: AppHandle,
    path: String,
    state: State<'_, SessionState>,
) -> Result<SaveSummaryDto, AppError> {
    let session = SaveSession::open(&path)?;
    let summary = session.summary();
    let save_root_str = summary.save_root.to_string_lossy().to_string();

    {
        let mut lock = state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock session state: {}", e))
        })?;
        *lock = Some(session);
    }

    // Record recent path best-effort — failure must not block a successful load.
    if let Ok(mut settings) = read_settings(&app) {
        push_recent_save_path(&mut settings, save_root_str);
        let _ = write_settings(&app, &settings);
    }

    Ok(summary)
}

#[tauri::command]
pub fn get_save_summary(state: State<'_, SessionState>) -> Result<SaveSummaryDto, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    match &*lock {
        Some(session) => Ok(session.summary()),
        None => Err(SessionError::NoActiveSession.into()),
    }
}

#[tauri::command]
pub fn check_stale_save(state: State<'_, SessionState>) -> Result<Vec<String>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    match &*lock {
        Some(session) => {
            let stale_paths = session.check_stale()?;
            Ok(stale_paths
                .into_iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect())
        }
        None => Err(SessionError::NoActiveSession.into()),
    }
}

#[tauri::command]
pub fn close_save_session(state: State<'_, SessionState>) -> Result<(), AppError> {
    let mut lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    *lock = None;
    Ok(())
}
