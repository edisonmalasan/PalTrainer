use std::sync::Mutex;
use tauri::State;

use crate::domain::gps::{GpsSession, GpsSummaryDto};
use crate::error::AppError;

pub type GpsState = Mutex<Option<GpsSession>>;

#[tauri::command]
pub fn load_gps_storage(
    path: String,
    state: State<'_, GpsState>,
) -> Result<GpsSummaryDto, AppError> {
    let session = GpsSession::open(path)?;
    let summary = session.summary();
    let mut lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock GPS state: {e}")))?;
    *lock = Some(session);
    Ok(summary)
}

#[tauri::command]
pub fn get_gps_summary(state: State<'_, GpsState>) -> Result<Option<GpsSummaryDto>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock GPS state: {e}")))?;
    Ok(lock.as_ref().map(|s| s.summary()))
}

#[tauri::command]
pub fn close_gps_storage(state: State<'_, GpsState>) -> Result<(), AppError> {
    let mut lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock GPS state: {e}")))?;
    *lock = None;
    Ok(())
}
