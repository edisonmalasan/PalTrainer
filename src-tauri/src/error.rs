//! Errors for the PalTrainer backend.
//!
//! `AppError` is the user-safe error payload exchanged with the frontend.
//! `SaveError` is the typed error for the save pipeline; it converts into
//! `AppError` at command boundaries.

use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AppError {
    pub code: &'static str,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<String>,
}

impl AppError {
    pub fn new(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            details: None,
        }
    }

    pub fn with_details(
        code: &'static str,
        message: impl Into<String>,
        details: impl Into<String>,
    ) -> Self {
        Self {
            code,
            message: message.into(),
            details: Some(details.into()),
        }
    }

    pub fn io(
        code: &'static str,
        message: impl Into<String>,
        error: impl std::error::Error,
    ) -> Self {
        Self::with_details(code, message, error.to_string())
    }
}

impl From<crate::pal_save::SaveError> for AppError {
    fn from(error: crate::pal_save::SaveError) -> Self {
        AppError::new("save_error", error.to_string())
    }
}

impl From<crate::security::SecurityError> for AppError {
    fn from(error: crate::security::SecurityError) -> Self {
        AppError::new("security_error", error.to_string())
    }
}

impl From<crate::storage::StorageError> for AppError {
    fn from(error: crate::storage::StorageError) -> Self {
        AppError::new("storage_error", error.to_string())
    }
}

impl From<crate::domain::save_session::SessionError> for AppError {
    fn from(error: crate::domain::save_session::SessionError) -> Self {
        AppError::new("session_error", error.to_string())
    }
}

impl From<std::io::Error> for AppError {
    fn from(error: std::io::Error) -> Self {
        AppError::new("io_error", error.to_string())
    }
}

/// Typed errors for the Palworld save pipeline.
///
/// All variants carry user-safe messages; internal details (byte offsets,
/// sizes) are included only where they help users diagnose broken saves.
#[derive(Debug, Error)]
pub enum SaveError {
    #[error("File is too small to contain a SAV header ({actual} bytes, need at least {needed}).")]
    HeaderTooSmall { actual: usize, needed: usize },

    #[error("Unknown save format: unrecognized magic bytes {magic:?} at offset {offset}.")]
    UnknownMagic { magic: [u8; 3], offset: usize },

    #[error("Unknown save type byte 0x{save_type:02X} for magic {magic:?}.")]
    UnknownSaveType { magic: [u8; 3], save_type: u8 },

    #[error(
        "This save uses the PLM (Oodle/Kraken) container. Oodle support is not \
         integrated yet; see docs/PLAN.md open decisions."
    )]
    OodleUnsupported,

    #[error("Writing {label} containers is not supported yet; only PLZ (double zlib) writes are implemented.")]
    CompressUnsupported { label: &'static str },

    #[error("zlib decompression failed: {message}")]
    ZlibDecompress { message: String },

    #[error("zlib compression failed: {message}")]
    ZlibCompress { message: String },

    #[error(
        "Corrupt save: first-pass decompressed size {actual} does not match \
         header compressed length {expected}."
    )]
    CompressedLengthMismatch { expected: u32, actual: usize },

    #[error(
        "Corrupt save: decompressed size {actual} does not match header \
         uncompressed length {expected}."
    )]
    UncompressedLengthMismatch { expected: u32, actual: usize },

    #[error("Unexpected end of save data at byte {offset} (needed {needed} more bytes).")]
    UnexpectedEof { offset: usize, needed: usize },

    #[error("Invalid GVAS header magic 0x{magic:08X}. This is not a GVAS payload.")]
    InvalidGvasMagic { magic: u32 },

    #[error(
        "Unsupported save game version {found}; PalTrainer currently reads \
         version 3 saves."
    )]
    UnsupportedSaveGameVersion { found: i32 },

    #[error(
        "Unsupported custom version format {found}; PalTrainer currently reads \
         format 3."
    )]
    UnsupportedCustomVersionFormat { found: i32 },

    #[error("Unknown property type \"{type_name}\" at {path}. The save may use a newer format.")]
    UnknownPropertyType { type_name: String, path: String },

    #[error("Unknown array element type \"{array_type}\" at {path}.")]
    UnknownArrayType { array_type: String, path: String },

    #[error("Malformed string data in save at offset {offset}.")]
    InvalidFString { offset: usize },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn messages_are_user_safe_and_actionable() {
        let err = SaveError::OodleUnsupported.to_string();
        assert!(err.contains("Oodle"));
        assert!(!err.contains("panicked"));

        let err = SaveError::HeaderTooSmall {
            actual: 4,
            needed: 12,
        }
        .to_string();
        assert!(err.contains("4 bytes"));
        assert!(err.contains("12"));
    }
}
