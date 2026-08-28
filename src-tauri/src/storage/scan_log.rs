//! Optional scan-activity logging behind the `Logs / Scan Save Logger`
//! settings toggle. When enabled, every diagnostic scan and cleanup preview
//! appends a timestamped entry to `Logs/scan-save.log` inside the app log
//! directory. Logging failures never abort the underlying scan.

use std::fs::OpenOptions;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::error::AppError;

/// Default file name for the scan log inside the log directory.
pub const SCAN_LOG_FILE: &str = "scan-save.log";

/// Appends `entries` to `<log_dir>/Logs/scan-save.log` when `enabled`.
/// Returns the log path when written, `None` when the toggle is off.
pub fn write_scan_log(
    log_dir: &Path,
    enabled: bool,
    entries: &[String],
) -> Result<Option<PathBuf>, AppError> {
    if !enabled || entries.is_empty() {
        return Ok(None);
    }

    std::fs::create_dir_all(log_dir).map_err(|error| {
        AppError::io(
            "scan_log_dir_unavailable",
            "Could not create the scan log directory.",
            error,
        )
    })?;

    let path = log_dir.join(SCAN_LOG_FILE);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .map_err(|error| {
            AppError::io(
                "scan_log_write_failed",
                "Could not open the scan log for writing.",
                error,
            )
        })?;

    for entry in entries {
        writeln!(file, "[{timestamp}] {entry}").map_err(|error| {
            AppError::io(
                "scan_log_write_failed",
                "Could not write to the scan log.",
                error,
            )
        })?;
    }

    Ok(Some(path))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disabled_toggle_writes_nothing() {
        let temp = tempfile::tempdir().unwrap();
        let result = write_scan_log(temp.path(), false, &["scan ran".to_string()]).unwrap();
        assert!(result.is_none());
        assert!(!temp.path().join(SCAN_LOG_FILE).exists());
    }

    #[test]
    fn enabled_toggle_appends_timestamped_entries() {
        let temp = tempfile::tempdir().unwrap();
        let log_dir = temp.path().join("Logs");

        write_scan_log(&log_dir, true, &["first".to_string()]).unwrap();
        write_scan_log(&log_dir, true, &["second".to_string(), "third".to_string()]).unwrap();

        let text = std::fs::read_to_string(log_dir.join(SCAN_LOG_FILE)).unwrap();
        let lines: Vec<&str> = text.lines().collect();
        assert_eq!(lines.len(), 3);
        assert!(lines[0].ends_with("] first"));
        assert!(lines[2].ends_with("] third"));
    }

    #[test]
    fn empty_entries_are_a_noop_even_when_enabled() {
        let temp = tempfile::tempdir().unwrap();
        let result = write_scan_log(temp.path(), true, &[]).unwrap();
        assert!(result.is_none());
    }
}
