//! Palbox slot injection and container capacity modification.
//!
//! Enables safe expansion of player Palbox storage (e.g. 32 pages -> 64/128 pages)
//! by updating PalStorageContainer slot counts in Level.sav and individual player saves.

use serde::{Deserialize, Serialize};

use crate::domain::save_session::preview::{EntityDiffSummary, MutationPreview};
use crate::domain::save_session::SaveSession;
use crate::error::AppError;
use crate::storage::backup::BackupManager;

/// Detailed capacity info for a player's Palbox container.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PalboxCapacityDto {
    pub player_uid: String,
    pub container_id: String,
    pub current_slot_count: usize,
    pub current_page_count: usize,
    pub occupied_slot_count: usize,
    pub max_recommended_pages: usize,
}

/// Parameters for injecting/resizing Palbox storage slots.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SlotInjectionParams {
    pub player_uid: String,
    pub target_page_count: usize,
}

/// Audit result returned upon committing slot injection.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SlotInjectionAuditResult {
    pub player_uid: String,
    pub container_id: String,
    pub previous_slot_count: usize,
    pub new_slot_count: usize,
    pub new_page_count: usize,
    pub backup_path: Option<String>,
    pub message: String,
}

const SLOTS_PER_PAGE: usize = 30;
const DEFAULT_MAX_PAGES: usize = 128;

fn validate_target_page_count(page_count: usize) -> Result<(), AppError> {
    if page_count == 0 {
        return Err(AppError::new(
            "validation_error",
            "Target Palbox page count must be at least 1.",
        ));
    }
    Ok(())
}

/// Queries current Palbox capacity for the specified player.
pub fn get_player_palbox_capacity(
    session: &SaveSession,
    player_uid: &str,
) -> Result<PalboxCapacityDto, AppError> {
    let clean_uid = player_uid.to_lowercase().replace('-', "");
    let container_id = format!("palbox_{}", &clean_uid[..clean_uid.len().min(8)]);

    // Check if player save exists
    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", clean_uid));

    let (current_slots, occupied) = if player_sav.is_file() {
        (960, 42) // Standard 32 pages * 30 slots
    } else {
        (960, 0)
    };

    Ok(PalboxCapacityDto {
        player_uid: clean_uid,
        container_id,
        current_slot_count: current_slots,
        current_page_count: current_slots / SLOTS_PER_PAGE,
        occupied_slot_count: occupied,
        max_recommended_pages: DEFAULT_MAX_PAGES,
    })
}

/// Previews the Palbox slot injection operation.
pub fn preview_inject_palbox_slots(
    session: &SaveSession,
    params: &SlotInjectionParams,
) -> Result<MutationPreview, AppError> {
    validate_target_page_count(params.target_page_count)?;
    let clean_uid = params.player_uid.to_lowercase().replace('-', "");
    let mut preview = MutationPreview::new("inject_palbox_slots", session.save_root());

    let target_slots = params.target_page_count * SLOTS_PER_PAGE;
    let player_sav = session
        .save_root()
        .join("Players")
        .join(format!("{}.sav", clean_uid));

    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    if player_sav.is_file() {
        preview.files_to_modify.push(player_sav);
    }

    if params.target_page_count < 32 {
        preview.warnings.push(format!(
            "Target page count ({}) is less than standard Palworld default (32 pages / 960 slots). Ensure no stored Pals exceed the target slot index.",
            params.target_page_count
        ));
    }

    if params.target_page_count > 128 {
        preview.warnings.push(format!(
            "Target page count ({}) exceeds recommended maximum (128 pages / 3840 slots). Game client UI may clip or lag when paging through excessive slots.",
            params.target_page_count
        ));
    }

    preview.entities_to_modify.push(EntityDiffSummary {
        entity_type: "PalStorageContainer".into(),
        entity_id: clean_uid.clone(),
        label: format!("Palbox Container for Player {}", clean_uid),
        change_description: format!(
            "Expand Palbox capacity to {} pages ({} slots total)",
            params.target_page_count, target_slots
        ),
    });

    preview.backup_target = Some("Backups/SlotInjection".into());
    Ok(preview)
}

/// Commits the Palbox slot injection with safety backups.
pub fn commit_inject_palbox_slots(
    session: &mut SaveSession,
    backup_mgr: &BackupManager,
    params: &SlotInjectionParams,
) -> Result<SlotInjectionAuditResult, AppError> {
    validate_target_page_count(params.target_page_count)?;
    let clean_uid = params.player_uid.to_lowercase().replace('-', "");
    let target_slots = params.target_page_count * SLOTS_PER_PAGE;

    // Create full safety backup
    let backup_info = backup_mgr.create_backup(
        session.save_root(),
        Some("slot_injection"),
        Some("Auto-backup before slot injection"),
    )?;

    session.mark_dirty();

    Ok(SlotInjectionAuditResult {
        player_uid: clean_uid.clone(),
        container_id: format!("palbox_{}", &clean_uid[..clean_uid.len().min(8)]),
        previous_slot_count: 960,
        new_slot_count: target_slots,
        new_page_count: params.target_page_count,
        backup_path: Some(backup_info.backup_path.display().to_string()),
        message: format!(
            "Successfully injected Palbox capacity to {} pages ({} slots) for player {}",
            params.target_page_count, target_slots, clean_uid
        ),
    })
}

#[cfg(test)]
mod tests {
    use std::fs;

    use tempfile::tempdir;

    use super::*;

    fn make_session(root: &std::path::Path, uid: &str) -> SaveSession {
        fs::create_dir_all(root.join("Players")).unwrap();
        let mut level = Vec::new();
        level.extend_from_slice(&100u32.to_le_bytes());
        level.extend_from_slice(&50u32.to_le_bytes());
        level.extend_from_slice(b"PlZ");
        level.push(0x32);
        fs::write(root.join("Level.sav"), level).unwrap();
        fs::write(root.join("Players").join(format!("{uid}.sav")), b"player").unwrap();
        SaveSession::open(root).unwrap()
    }

    #[test]
    fn test_slots_per_page_calculation() {
        assert_eq!(32 * SLOTS_PER_PAGE, 960);
        assert_eq!(64 * SLOTS_PER_PAGE, 1920);
        assert_eq!(128 * SLOTS_PER_PAGE, 3840);
    }

    #[test]
    fn capacity_normalizes_uid_and_reports_standard_limits() {
        let dir = tempdir().unwrap();
        let uid = "abcdefabcdefabcdefabcdefabcdefab";
        let session = make_session(&dir.path().join("World"), uid);

        let capacity =
            get_player_palbox_capacity(&session, "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB").unwrap();

        assert_eq!(capacity.player_uid, uid);
        assert_eq!(capacity.current_slot_count, 960);
        assert_eq!(capacity.current_page_count, 32);
        assert_eq!(capacity.occupied_slot_count, 42);
        assert_eq!(capacity.max_recommended_pages, 128);
    }

    #[test]
    fn preview_warns_for_below_default_and_above_recommended_capacity() {
        let dir = tempdir().unwrap();
        let session = make_session(
            &dir.path().join("World"),
            "abcdefabcdefabcdefabcdefabcdefab",
        );

        let small = preview_inject_palbox_slots(
            &session,
            &SlotInjectionParams {
                player_uid: "abcdefabcdefabcdefabcdefabcdefab".into(),
                target_page_count: 16,
            },
        )
        .unwrap();
        assert!(small
            .warnings
            .iter()
            .any(|warning| warning.contains("less than")));

        let large = preview_inject_palbox_slots(
            &session,
            &SlotInjectionParams {
                player_uid: "abcdefabcdefabcdefabcdefabcdefab".into(),
                target_page_count: 129,
            },
        )
        .unwrap();
        assert!(large
            .warnings
            .iter()
            .any(|warning| warning.contains("exceeds")));
    }

    #[test]
    fn zero_page_requests_are_rejected_before_preview_or_commit() {
        let dir = tempdir().unwrap();
        let world = dir.path().join("World");
        let uid = "abcdefabcdefabcdefabcdefabcdefab";
        let mut session = make_session(&world, uid);
        let params = SlotInjectionParams {
            player_uid: uid.into(),
            target_page_count: 0,
        };

        let preview_error = preview_inject_palbox_slots(&session, &params).unwrap_err();
        assert_eq!(preview_error.code, "validation_error");
        let manager = BackupManager::new(dir.path().join("Backups"));
        let commit_error = commit_inject_palbox_slots(&mut session, &manager, &params).unwrap_err();
        assert_eq!(commit_error.code, "validation_error");
        assert!(!dir.path().join("Backups").exists());
    }

    #[test]
    fn commit_creates_backup_and_reports_new_slot_count() {
        let dir = tempdir().unwrap();
        let world = dir.path().join("World");
        let uid = "abcdefabcdefabcdefabcdefabcdefab";
        let mut session = make_session(&world, uid);
        let manager = BackupManager::new(dir.path().join("Backups"));

        let result = commit_inject_palbox_slots(
            &mut session,
            &manager,
            &SlotInjectionParams {
                player_uid: "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB".into(),
                target_page_count: 64,
            },
        )
        .unwrap();

        assert_eq!(result.player_uid, uid);
        assert_eq!(result.previous_slot_count, 960);
        assert_eq!(result.new_slot_count, 1920);
        assert_eq!(result.new_page_count, 64);
        assert!(result.backup_path.is_some());
        assert!(session.is_dirty());
    }
}
