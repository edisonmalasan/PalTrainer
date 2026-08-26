use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::error::AppError;
use crate::security::path_policy::canonicalize_safe;

/// Summary projection for the isolated GlobalPalStorage session.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GpsSummaryDto {
    pub path: PathBuf,
    pub file_size: u64,
    pub loaded_at: u64,
}

#[derive(Debug, Clone)]
pub struct GpsSession {
    path: PathBuf,
    file_size: u64,
    loaded_at: u64,
}

impl GpsSession {
    pub fn open(path: impl AsRef<Path>) -> Result<Self, AppError> {
        let canon = canonicalize_safe(path.as_ref())?;
        let meta = fs::metadata(&canon).map_err(|e| {
            AppError::with_details(
                "gps_not_found",
                format!("GlobalPalStorage file not found: {}", canon.display()),
                e.to_string(),
            )
        })?;
        if !meta.is_file() {
            return Err(AppError::new(
                "gps_not_file",
                format!("Expected a file for GlobalPalStorage: {}", canon.display()),
            ));
        }
        // Basic extension allowlist — reuses existing export/import policy spirit.
        if let Some(ext) = canon.extension().and_then(|e| e.to_str()) {
            if !ext.eq_ignore_ascii_case("sav") {
                return Err(AppError::new(
                    "gps_bad_extension",
                    format!("GlobalPalStorage must be a .sav file: {}", canon.display()),
                ));
            }
        }
        // Filename should be GlobalPalStorage.sav (case-insensitive) — warn but allow any .sav for flexibility.
        let loaded_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        Ok(Self {
            path: canon,
            file_size: meta.len(),
            loaded_at,
        })
    }

    pub fn summary(&self) -> GpsSummaryDto {
        GpsSummaryDto {
            path: self.path.clone(),
            file_size: self.file_size,
            loaded_at: self.loaded_at,
        }
    }

    pub fn path(&self) -> &Path {
        &self.path
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::tempdir;

    #[test]
    fn open_and_summary_roundtrip() {
        let dir = tempdir().unwrap();
        let p = dir.path().join("GlobalPalStorage.sav");
        let mut f = fs::File::create(&p).unwrap();
        f.write_all(b"mock gps").unwrap();
        let sess = GpsSession::open(&p).unwrap();
        let s = sess.summary();
        assert_eq!(s.path, dunce::canonicalize(&p).unwrap());
        assert!(s.file_size > 0);
    }

    #[test]
    fn open_rejects_missing_file() {
        let dir = tempdir().unwrap();
        let p = dir.path().join("GlobalPalStorage.sav");
        assert!(GpsSession::open(&p).is_err());
    }

    #[test]
    fn open_rejects_bad_extension() {
        let dir = tempdir().unwrap();
        let p = dir.path().join("not_gps.txt");
        fs::write(&p, b"x").unwrap();
        assert!(GpsSession::open(&p).is_err());
    }
}
