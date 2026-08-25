//! Path validation and directory traversal protection for PalTrainer.

use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SecurityError {
    #[error("Path does not exist: {0}")]
    NotFound(PathBuf),

    #[error("Expected a directory, but found a file: {0}")]
    NotADirectory(PathBuf),

    #[error("Expected a file, but found a directory: {0}")]
    NotAFile(PathBuf),

    #[error("Path escapes the approved root: path '{path}' is not inside root '{root}'")]
    PathEscapesRoot { path: PathBuf, root: PathBuf },

    #[error("Invalid save root directory: '{0}' does not contain Level.sav")]
    InvalidSaveRoot(PathBuf),

    #[error("Disallowed file extension for export/import: {0}")]
    DisallowedExtension(String),

    #[error("IO error during path validation: {0}")]
    Io(#[from] std::io::Error),
}

/// Allowed extensions for import/export operations.
const ALLOWED_EXPORT_EXTENSIONS: &[&str] = &["sav", "savc", "json", "pstbase", "pstpal", "zip"];

/// Canonicalizes a path and confirms it exists.
pub fn canonicalize_safe(path: impl AsRef<Path>) -> Result<PathBuf, SecurityError> {
    let p = path.as_ref();
    dunce::canonicalize(p).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => SecurityError::NotFound(p.to_path_buf()),
        _ => SecurityError::Io(e),
    })
}

/// Validates that `target` is strictly within `root`.
pub fn ensure_within_root(
    target: impl AsRef<Path>,
    root: impl AsRef<Path>,
) -> Result<PathBuf, SecurityError> {
    let canon_root = canonicalize_safe(root.as_ref())?;
    let target_ref = target.as_ref();

    let canon_target = if target_ref.exists() {
        canonicalize_safe(target_ref)?
    } else {
        // If target does not exist yet (e.g. pending file write), canonicalize parent
        let parent = target_ref
            .parent()
            .ok_or_else(|| SecurityError::NotFound(target_ref.to_path_buf()))?;
        let canon_parent = canonicalize_safe(parent)?;
        let filename = target_ref
            .file_name()
            .ok_or_else(|| SecurityError::NotFound(target_ref.to_path_buf()))?;
        canon_parent.join(filename)
    };

    if canon_target.starts_with(&canon_root) {
        Ok(canon_target)
    } else {
        Err(SecurityError::PathEscapesRoot {
            path: canon_target,
            root: canon_root,
        })
    }
}

/// Validates that a folder is a valid Palworld world save root directory (contains `Level.sav`).
pub fn validate_save_root(dir: impl AsRef<Path>) -> Result<PathBuf, SecurityError> {
    let canon_dir = canonicalize_safe(dir.as_ref())?;
    if !canon_dir.is_dir() {
        return Err(SecurityError::NotADirectory(canon_dir));
    }

    let level_sav = canon_dir.join("Level.sav");
    if !level_sav.is_file() {
        return Err(SecurityError::InvalidSaveRoot(canon_dir));
    }

    Ok(canon_dir)
}

/// Validates an export/import file target path.
pub fn validate_import_export_path(
    path: impl AsRef<Path>,
    must_exist: bool,
) -> Result<PathBuf, SecurityError> {
    let p = path.as_ref();
    if let Some(ext) = p.extension().and_then(|e| e.to_str()) {
        let ext_lower = ext.to_lowercase();
        if !ALLOWED_EXPORT_EXTENSIONS.contains(&ext_lower.as_str()) {
            return Err(SecurityError::DisallowedExtension(ext_lower));
        }
    } else {
        return Err(SecurityError::DisallowedExtension("none".to_string()));
    }

    if must_exist {
        let canon = canonicalize_safe(p)?;
        if !canon.is_file() {
            return Err(SecurityError::NotAFile(canon));
        }
        Ok(canon)
    } else {
        let parent = p
            .parent()
            .ok_or_else(|| SecurityError::NotFound(p.to_path_buf()))?;
        let canon_parent = canonicalize_safe(parent)?;
        let filename = p
            .file_name()
            .ok_or_else(|| SecurityError::NotFound(p.to_path_buf()))?;
        Ok(canon_parent.join(filename))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_validate_save_root() {
        let dir = tempdir().unwrap();
        let save_root = dir.path().join("world_save");
        fs::create_dir_all(&save_root).unwrap();

        // Fails when Level.sav is missing
        assert!(validate_save_root(&save_root).is_err());

        // Passes when Level.sav exists
        fs::write(save_root.join("Level.sav"), b"mock").unwrap();
        assert!(validate_save_root(&save_root).is_ok());
    }

    #[test]
    fn test_ensure_within_root() {
        let dir = tempdir().unwrap();
        let root = dir.path().join("root");
        fs::create_dir_all(&root).unwrap();

        let valid_file = root.join("child.sav");
        fs::write(&valid_file, b"test").unwrap();
        assert!(ensure_within_root(&valid_file, &root).is_ok());

        let outside_file = dir.path().join("outside.sav");
        fs::write(&outside_file, b"test").unwrap();
        assert!(ensure_within_root(&outside_file, &root).is_err());
    }

    #[test]
    fn test_validate_import_export_path() {
        let dir = tempdir().unwrap();
        let valid = dir.path().join("base.pstbase");
        fs::write(&valid, b"data").unwrap();
        assert!(validate_import_export_path(&valid, true).is_ok());

        let valid_json = dir.path().join("export.JSON");
        fs::write(&valid_json, b"data").unwrap();
        assert!(validate_import_export_path(&valid_json, true).is_ok());

        let valid_zip = dir.path().join("backup.zip");
        fs::write(&valid_zip, b"data").unwrap();
        assert!(validate_import_export_path(&valid_zip, true).is_ok());

        let invalid_ext = dir.path().join("malicious.exe");
        fs::write(&invalid_ext, b"data").unwrap();
        assert!(matches!(
            validate_import_export_path(&invalid_ext, true),
            Err(SecurityError::DisallowedExtension(_))
        ));

        let script_ext = dir.path().join("hack.bat");
        fs::write(&script_ext, b"data").unwrap();
        assert!(matches!(
            validate_import_export_path(&script_ext, true),
            Err(SecurityError::DisallowedExtension(_))
        ));

        let no_ext = dir.path().join("unknown_file");
        fs::write(&no_ext, b"data").unwrap();
        assert!(matches!(
            validate_import_export_path(&no_ext, true),
            Err(SecurityError::DisallowedExtension(_))
        ));
    }

    #[test]
    fn test_path_traversal_detection() {
        let dir = tempdir().unwrap();
        let root = dir.path().join("safe_dir");
        fs::create_dir_all(&root).unwrap();

        let secret = dir.path().join("secret.txt");
        fs::write(&secret, b"sensitive").unwrap();

        // Path with traversal attempting to escape root
        let escape_attempt = root.join("..").join("secret.txt");
        assert!(ensure_within_root(&escape_attempt, &root).is_err());
    }
}
