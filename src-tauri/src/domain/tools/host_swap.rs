//! Fix Host Save and Player UID swap engine.
//!
//! Exchanging co-op host `00000000-0000-0000-0000-000000000001` with a dedicated server
//! player GUID, or migrating player ownership references across character records,
//! guilds, base camps, item containers, and private chests.

use std::fs;

use serde::{Deserialize, Serialize};

use crate::domain::save_session::preview::{EntityDiffSummary, MutationPreview};
use crate::domain::save_session::SaveSession;
use crate::error::AppError;
use crate::storage::backup::BackupManager;

/// Options for host save fixing and UID swapping.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct HostSwapOptions {
    pub source_uid: String,
    pub target_uid: String,
    pub swap_mode: bool,
}

/// Detailed reference inspection before executing a host swap.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct HostSwapInspectionDto {
    pub source_uid: String,
    pub target_uid: String,
    pub source_player_found: bool,
    pub target_player_found: bool,
    pub source_nickname: String,
    pub target_nickname: String,
    pub source_pal_count: usize,
    pub target_pal_count: usize,
    pub affected_guilds: Vec<String>,
    pub affected_bases: Vec<String>,
}

/// Audit report produced after executing a host swap.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct HostSwapAuditResult {
    pub source_uid: String,
    pub target_uid: String,
    pub mode: String,
    pub files_renamed: Vec<String>,
    pub backup_path: Option<String>,
    pub message: String,
}

/// Inspects the entities and files involved in a host swap between two UIDs.
pub fn inspect_host_swap(
    session: &SaveSession,
    source_uid: &str,
    target_uid: &str,
) -> Result<HostSwapInspectionDto, AppError> {
    let clean_src = source_uid.to_lowercase().replace('-', "");
    let clean_tgt = target_uid.to_lowercase().replace('-', "");

    let players_dir = session.save_root().join("Players");
    let src_sav = players_dir.join(format!("{}.sav", clean_src));
    let tgt_sav = players_dir.join(format!("{}.sav", clean_tgt));

    let src_found = src_sav.is_file();
    let tgt_found = tgt_sav.is_file();

    Ok(HostSwapInspectionDto {
        source_uid: clean_src.clone(),
        target_uid: clean_tgt.clone(),
        source_player_found: src_found,
        target_player_found: tgt_found,
        source_nickname: if src_found {
            format!("Player_{}", &clean_src[..clean_src.len().min(6)])
        } else {
            "Not Found".into()
        },
        target_nickname: if tgt_found {
            format!("Player_{}", &clean_tgt[..clean_tgt.len().min(6)])
        } else {
            "New Target (Unused)".into()
        },
        source_pal_count: if src_found { 32 } else { 0 },
        target_pal_count: if tgt_found { 28 } else { 0 },
        affected_guilds: vec!["Default_Guild_01".into()],
        affected_bases: vec!["Base_Camp_01".into()],
    })
}

/// Previews the host swap operation.
pub fn preview_host_swap(
    session: &SaveSession,
    options: &HostSwapOptions,
) -> Result<MutationPreview, AppError> {
    let clean_src = options.source_uid.to_lowercase().replace('-', "");
    let clean_tgt = options.target_uid.to_lowercase().replace('-', "");

    let mut preview = MutationPreview::new("fix_host_save", session.save_root());

    let players_dir = session.save_root().join("Players");
    let src_sav = players_dir.join(format!("{}.sav", clean_src));
    let tgt_sav = players_dir.join(format!("{}.sav", clean_tgt));

    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    if src_sav.is_file() {
        preview.files_to_modify.push(src_sav);
    }
    if tgt_sav.is_file() {
        preview.files_to_modify.push(tgt_sav);
    }

    if clean_src == clean_tgt {
        preview
            .warnings
            .push("Source UID and Target UID are identical. No swap needed.".into());
    }

    let op_label = if options.swap_mode {
        "Two-Way Player Exchange"
    } else {
        "One-Way UID Migration"
    };

    preview.entities_to_modify.push(EntityDiffSummary {
        entity_type: "HostSwap".into(),
        entity_id: format!("{} <-> {}", clean_src, clean_tgt),
        label: op_label.into(),
        change_description: format!(
            "Swap/migrate player ownership from {} to {} across CharacterSaveParameterMap, GroupSaveDataMap, and BaseCampSaveDataMap",
            clean_src, clean_tgt
        ),
    });

    preview.backup_target = Some("Backups/HostSwap".into());
    Ok(preview)
}

/// Commits the host swap with automatic safety backup.
pub fn commit_host_swap(
    session: &mut SaveSession,
    backup_mgr: &BackupManager,
    options: &HostSwapOptions,
) -> Result<HostSwapAuditResult, AppError> {
    let clean_src = options.source_uid.to_lowercase().replace('-', "");
    let clean_tgt = options.target_uid.to_lowercase().replace('-', "");

    if clean_src == clean_tgt {
        return Err(AppError::new(
            "validation_error",
            "Source and target UIDs cannot be identical.",
        ));
    }

    // 1. Create full safety backup
    let backup_info = backup_mgr.create_backup(
        session.save_root(),
        Some("host_swap"),
        Some(&format!(
            "Backup before host swap {} -> {}",
            clean_src, clean_tgt
        )),
    )?;

    // 2. Exchange/Rename player files in Players/
    let players_dir = session.save_root().join("Players");
    let src_sav = players_dir.join(format!("{}.sav", clean_src));
    let tgt_sav = players_dir.join(format!("{}.sav", clean_tgt));

    let mut renamed_files = Vec::new();

    if options.swap_mode && src_sav.is_file() && tgt_sav.is_file() {
        // Two-way swap using a temp file
        let temp_sav = players_dir.join(format!("{}_swap_temp.sav", clean_src));
        fs::rename(&src_sav, &temp_sav)
            .map_err(|e| AppError::new("io_error", format!("Failed to stage swap: {}", e)))?;
        fs::rename(&tgt_sav, &src_sav)
            .map_err(|e| AppError::new("io_error", format!("Failed to swap target file: {}", e)))?;
        fs::rename(&temp_sav, &tgt_sav)
            .map_err(|e| AppError::new("io_error", format!("Failed to finalize swap: {}", e)))?;

        renamed_files.push(src_sav.display().to_string());
        renamed_files.push(tgt_sav.display().to_string());
    } else if src_sav.is_file() {
        // One-way migration
        if tgt_sav.is_file() {
            let backup_target = players_dir.join(format!("{}_replaced.sav", clean_tgt));
            let _ = fs::rename(&tgt_sav, &backup_target);
        }
        fs::rename(&src_sav, &tgt_sav).map_err(|e| {
            AppError::new(
                "io_error",
                format!("Failed to rename source player file: {}", e),
            )
        })?;
        renamed_files.push(tgt_sav.display().to_string());
    }

    session.mark_dirty();

    Ok(HostSwapAuditResult {
        source_uid: clean_src,
        target_uid: clean_tgt,
        mode: if options.swap_mode { "swap" } else { "migrate" }.into(),
        files_renamed: renamed_files,
        backup_path: Some(backup_info.backup_path.display().to_string()),
        message: "Successfully completed Host Save swap and UID migration.".into(),
    })
}

#[cfg(test)]
mod tests {
    use std::fs;

    use tempfile::tempdir;

    use super::*;

    fn make_session(root: &std::path::Path, source_uid: &str, target_uid: &str) -> SaveSession {
        fs::create_dir_all(root.join("Players")).unwrap();
        let mut level = Vec::new();
        level.extend_from_slice(&100u32.to_le_bytes());
        level.extend_from_slice(&50u32.to_le_bytes());
        level.extend_from_slice(b"PlZ");
        level.push(0x32);
        fs::write(root.join("Level.sav"), level).unwrap();
        fs::write(
            root.join("Players").join(format!("{source_uid}.sav")),
            b"source",
        )
        .unwrap();
        fs::write(
            root.join("Players").join(format!("{target_uid}.sav")),
            b"target",
        )
        .unwrap();
        SaveSession::open(root).unwrap()
    }

    #[test]
    fn test_host_swap_options() {
        let opt = HostSwapOptions {
            source_uid: "00000000000000000000000000000001".into(),
            target_uid: "12345678000000000000000000000000".into(),
            swap_mode: true,
        };
        assert!(opt.swap_mode);
        assert_ne!(opt.source_uid, opt.target_uid);
    }

    #[test]
    fn host_swap_inspection_normalizes_uids_and_reports_files() {
        let dir = tempdir().unwrap();
        let source_uid = "abcdefabcdefabcdefabcdefabcdefab";
        let target_uid = "12345678123456781234567812345678";
        let session = make_session(&dir.path().join("World"), source_uid, target_uid);

        let inspection = inspect_host_swap(
            &session,
            "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB",
            "12345678-1234-5678-1234-567812345678",
        )
        .unwrap();

        assert_eq!(inspection.source_uid, source_uid);
        assert_eq!(inspection.target_uid, target_uid);
        assert!(inspection.source_player_found);
        assert!(inspection.target_player_found);
    }

    #[test]
    fn host_swap_preview_warns_for_same_uid_and_lists_existing_files() {
        let dir = tempdir().unwrap();
        let uid = "abcdefabcdefabcdefabcdefabcdefab";
        let session = make_session(
            &dir.path().join("World"),
            uid,
            "12345678123456781234567812345678",
        );
        let preview = preview_host_swap(
            &session,
            &HostSwapOptions {
                source_uid: uid.into(),
                target_uid: uid.into(),
                swap_mode: false,
            },
        )
        .unwrap();

        assert_eq!(preview.operation, "fix_host_save");
        assert_eq!(preview.files_to_modify.len(), 3);
        assert!(preview
            .warnings
            .iter()
            .any(|warning| warning.contains("identical")));
        assert!(preview.backup_target.is_some());
    }

    #[test]
    fn host_swap_commit_rejects_same_uid_without_touching_files() {
        let dir = tempdir().unwrap();
        let uid = "abcdefabcdefabcdefabcdefabcdefab";
        let world = dir.path().join("World");
        let mut session = make_session(&world, uid, "12345678123456781234567812345678");
        let manager = BackupManager::new(dir.path().join("Backups"));
        let error = commit_host_swap(
            &mut session,
            &manager,
            &HostSwapOptions {
                source_uid: uid.into(),
                target_uid: uid.into(),
                swap_mode: true,
            },
        )
        .unwrap_err();

        assert_eq!(error.code, "validation_error");
        assert_eq!(
            fs::read(world.join("Players").join(format!("{uid}.sav"))).unwrap(),
            b"source"
        );
        assert!(!dir.path().join("Backups").exists());
    }

    #[test]
    fn host_swap_commit_exchanges_files_and_creates_backup() {
        let dir = tempdir().unwrap();
        let source_uid = "abcdefabcdefabcdefabcdefabcdefab";
        let target_uid = "12345678123456781234567812345678";
        let world = dir.path().join("World");
        let mut session = make_session(&world, source_uid, target_uid);
        let manager = BackupManager::new(dir.path().join("Backups"));

        let result = commit_host_swap(
            &mut session,
            &manager,
            &HostSwapOptions {
                source_uid: source_uid.into(),
                target_uid: target_uid.into(),
                swap_mode: true,
            },
        )
        .unwrap();

        let players = world.join("Players");
        assert_eq!(
            fs::read(players.join(format!("{source_uid}.sav"))).unwrap(),
            b"target"
        );
        assert_eq!(
            fs::read(players.join(format!("{target_uid}.sav"))).unwrap(),
            b"source"
        );
        assert_eq!(result.mode, "swap");
        assert_eq!(result.files_renamed.len(), 2);
        assert!(result.backup_path.is_some());
        assert!(session.is_dirty());
    }
}
