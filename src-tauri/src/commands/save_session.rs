//! Tauri IPC commands for SaveSession lifecycle and stale save detection.

use std::sync::Mutex;
use tauri::State;

use crate::domain::save_session::{SaveSession, SaveSummaryDto, SessionError};
use crate::error::AppError;

pub type SessionState = Mutex<Option<SaveSession>>;

#[tauri::command]
pub fn load_save_session(
    path: String,
    state: State<'_, SessionState>,
) -> Result<SaveSummaryDto, AppError> {
    let session = SaveSession::open(path)?;
    let summary = session.summary();

    let mut lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    *lock = Some(session);

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
