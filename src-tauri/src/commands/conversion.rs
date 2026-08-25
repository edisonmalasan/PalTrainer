//! IPC command handlers for identifier and format conversions.

use tauri::State;

use crate::commands::save_session::SessionState;
use crate::domain::save_session::SessionError;
use crate::domain::tools::conversion::{
    calculate_ids, convert_json_to_sav as domain_convert_json_to_sav,
    convert_sav_to_json as domain_convert_sav_to_json, inspect_raw_json as domain_inspect_raw_json,
    ConversionResult, ConvertJsonToSavDto, ConvertSavToJsonDto, IdConversionResult, RawJsonSummary,
};
use crate::error::AppError;

#[tauri::command]
pub fn calculate_identifier_conversion(input: String) -> Result<IdConversionResult, AppError> {
    calculate_ids(&input)
}

#[tauri::command]
pub fn convert_sav_to_json(dto: ConvertSavToJsonDto) -> Result<ConversionResult, AppError> {
    domain_convert_sav_to_json(dto)
}

#[tauri::command]
pub fn convert_json_to_sav(dto: ConvertJsonToSavDto) -> Result<ConversionResult, AppError> {
    domain_convert_json_to_sav(dto)
}

#[tauri::command]
pub fn inspect_raw_json(state: State<'_, SessionState>) -> Result<RawJsonSummary, AppError> {
    let guard = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let active = guard.as_ref().ok_or(SessionError::NoActiveSession)?;

    domain_inspect_raw_json(active)
}
