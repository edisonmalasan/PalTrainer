//! Death-bag (death penalty container) scanning and protection — the Rust
//! realization of the reference tool's `scan_and_protect_death_bags` and
//! `is_death_bag_protected` exports.
//!
//! Death bags are `ItemContainerSaveData` entries created when a player dies;
//! deleting one destroys the player's dropped gear permanently. The scan
//! builds a normalized protection set from containers identified by the world
//! index. While the container `RawData` decoder is a stub the index cannot
//! positively identify death bags, so the scan reports pending status instead
//! of claiming protection it cannot prove — deletion candidates stay guarded
//! by treating the protection set as authoritative whenever it is populated.

use std::collections::HashSet;

use serde::Serialize;

use crate::domain::diagnostics::world_index::WorldIndex;
use crate::domain::diagnostics::{DiagnosticCategory, DiagnosticIssue, DiagnosticSeverity};
use crate::domain::save_session::preview::MutationPreview;

/// Normalizes a container/file id for protection comparisons: trimmed,
/// lowercased, dashes removed (Palworld UID convention).
pub fn normalize_id(value: &str) -> String {
    value.trim().to_lowercase().replace('-', "")
}

/// The set of death-bag container ids protected from every deletion path.
#[derive(Clone, Debug, Default, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DeathBagProtection {
    protected_ids: HashSet<String>,
}

impl DeathBagProtection {
    pub fn new() -> Self {
        Self::default()
    }

    /// Adds a container id to the protection set (normalized).
    pub fn protect(&mut self, container_id: &str) {
        let normalized = normalize_id(container_id);
        if !normalized.is_empty() {
            self.protected_ids.insert(normalized);
        }
    }

    /// The delete-path guard: true when `id` (raw or normalized) is a
    /// protected death-bag container.
    pub fn is_death_bag_protected(&self, id: &str) -> bool {
        self.protected_ids.contains(&normalize_id(id))
    }

    pub fn len(&self) -> usize {
        self.protected_ids.len()
    }

    pub fn is_empty(&self) -> bool {
        self.protected_ids.is_empty()
    }

    /// Sorted normalized ids for deterministic reporting.
    pub fn sorted_ids(&self) -> Vec<String> {
        let mut ids: Vec<String> = self.protected_ids.iter().cloned().collect();
        ids.sort();
        ids
    }
}

/// Result of one death-bag scan.
#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DeathBagScan {
    /// The protection set produced by this scan.
    pub protection: DeathBagProtection,
    /// Number of item containers examined.
    pub scanned_containers: usize,
    /// True when every container payload was decodable and the protection
    /// set is complete (no death bag can hide in undecoded blobs).
    pub scan_complete: bool,
}

impl DeathBagScan {
    /// Honest reporting: only claim full protection when the scan is complete.
    pub fn reports_full_protection(&self) -> bool {
        self.scan_complete
    }
}

/// Scans the harvested world index for death-bag containers and builds the
/// protection set used by every delete path.
pub fn scan_and_protect_death_bags(index: &WorldIndex) -> DeathBagScan {
    let mut protection = DeathBagProtection::new();
    for id in &index.death_bag_container_ids {
        protection.protect(id);
    }

    DeathBagScan {
        protection,
        scanned_containers: index.container_ids.len(),
        scan_complete: index.containers_decoded,
    }
}

/// Maps a death-bag scan to user-safe diagnostic issues. Never fabricates an
/// "all protected" claim when the container RawData decoder is still a stub.
pub fn death_bag_scan_to_issues(scan: &DeathBagScan) -> Vec<DiagnosticIssue> {
    let mut issues = Vec::new();

    if !scan.protection.is_empty() {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Warning,
            category: DiagnosticCategory::DeathBag,
            code: "DEATH_BAGS_FOUND".into(),
            message: format!(
                "{} death-bag container(s) detected and protected from every delete path.",
                scan.protection.len()
            ),
            target_id: "death_bags".into(),
            context: Some(scan.protection.sorted_ids().join(", ")),
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
    }

    if !scan.scan_complete {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::DeathBag,
            code: "DEATH_BAG_SCAN_PENDING".into(),
            message: format!(
                "Scanned {} item container(s), but container RawData payloads are not decoded yet, so death bags cannot be positively identified. {} container id(s) are protected from the current scan; the guard will still skip any protected id queued for deletion.",
                scan.scanned_containers,
                scan.protection.len()
            ),
            target_id: "death_bags".into(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
    } else if scan.protection.is_empty() {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::DeathBag,
            code: "DEATH_BAGS_NONE".into(),
            message: format!(
                "Scanned {} item container(s); no death-bag containers found.",
                scan.scanned_containers
            ),
            target_id: "death_bags".into(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
    }

    issues
}

/// Returns true when `path` names a file whose stem is a protected death-bag
/// id (e.g. `<uid>.sav` player death bags or container entry files).
pub fn is_path_protected(path: &std::path::Path, protection: &DeathBagProtection) -> bool {
    path.file_stem()
        .and_then(|stem| stem.to_str())
        .map(|stem| protection.is_death_bag_protected(stem))
        .unwrap_or(false)
}

/// The single delete-path choke point: removes protected entities and files
/// from a mutation preview before it is shown to the user or committed. Every
/// `delete_invalid_*` / sweep / trim queue funnels through here, so a
/// protected death bag can never reach `files_to_delete` on commit.
pub fn guard_preview_against_death_bags(
    preview: &mut MutationPreview,
    protection: &DeathBagProtection,
) {
    if protection.is_empty() {
        return;
    }

    let before_entities = preview.entities_to_delete.len();
    preview
        .entities_to_delete
        .retain(|entity| !protection.is_death_bag_protected(&entity.entity_id));
    let skipped_entities = before_entities - preview.entities_to_delete.len();

    let before_files = preview.files_to_delete.len();
    preview
        .files_to_delete
        .retain(|path| !is_path_protected(path, protection));
    let skipped_files = before_files - preview.files_to_delete.len();

    if skipped_entities > 0 {
        preview.add_warning(format!(
            "[DEATH_BAG_PROTECTED] {} deletion candidate(s) matched protected death-bag containers and were removed from the queue.",
            skipped_entities
        ));
    }
    if skipped_files > 0 {
        preview.add_warning(format!(
            "[DEATH_BAG_PROTECTED] {} queued file deletion(s) matched protected death-bag ids and were removed from the queue.",
            skipped_files
        ));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::diagnostics::world_index::WorldIndex;

    fn index_with(containers: &[&str], death_bags: &[&str], decoded: bool) -> WorldIndex {
        WorldIndex {
            container_ids: containers.iter().map(|s| s.to_string()).collect(),
            death_bag_container_ids: death_bags.iter().map(|s| s.to_string()).collect(),
            containers_decoded: decoded,
            ..WorldIndex::default()
        }
    }

    #[test]
    fn protection_normalizes_uids_case_and_dashes() {
        let mut protection = DeathBagProtection::new();
        protection.protect("01234567-89AB-CDEF-0123-456789ABCDEF");
        assert!(protection.is_death_bag_protected("0123456789abcdef0123456789abcdef"));
        assert!(protection.is_death_bag_protected("  01234567-89ab-cdef-0123-456789abcdef  "));
        assert!(!protection.is_death_bag_protected("ffffffffffffffffffffffffffffffff"));
        assert_eq!(protection.len(), 1);
    }

    #[test]
    fn blank_ids_are_never_protected() {
        let mut protection = DeathBagProtection::new();
        protection.protect("   ");
        protection.protect("---");
        assert!(protection.is_empty());
    }

    #[test]
    fn scan_builds_protection_from_index_death_bags() {
        let index = index_with(
            &["C1", "DEATH-BAG-1", "deathbag2"],
            &["DEATH-BAG-1", "deathbag2"],
            true,
        );
        let scan = scan_and_protect_death_bags(&index);
        assert_eq!(scan.scanned_containers, 3);
        assert!(scan.scan_complete);
        assert!(scan.reports_full_protection());
        assert!(scan.protection.is_death_bag_protected("death-bag-1"));
        assert!(scan.protection.is_death_bag_protected("DEATHBAG2"));
        assert_eq!(scan.protection.sorted_ids(), vec!["deathbag1", "deathbag2"]);
    }

    #[test]
    fn incomplete_scan_reports_pending_and_never_claims_full_protection() {
        let index = index_with(&["C1", "C2"], &[], false);
        let scan = scan_and_protect_death_bags(&index);
        assert!(!scan.reports_full_protection());

        let issues = death_bag_scan_to_issues(&scan);
        assert!(issues
            .iter()
            .any(|i| i.code == "DEATH_BAG_SCAN_PENDING" && i.severity == DiagnosticSeverity::Info));
        assert!(issues.iter().all(|i| i.code != "DEATH_BAGS_NONE"));
    }

    #[test]
    fn complete_scan_without_death_bags_reports_clean() {
        let index = index_with(&["C1"], &[], true);
        let scan = scan_and_protect_death_bags(&index);
        let issues = death_bag_scan_to_issues(&scan);
        assert!(issues
            .iter()
            .any(|i| i.code == "DEATH_BAGS_NONE" && i.message.contains("1 item container(s)")));
        assert!(issues.iter().all(|i| i.code != "DEATH_BAG_SCAN_PENDING"));
    }

    #[test]
    fn found_death_bags_map_to_warning_with_context() {
        let index = index_with(&["C1"], &["bag-9"], true);
        let scan = scan_and_protect_death_bags(&index);
        let issues = death_bag_scan_to_issues(&scan);
        let found = issues
            .iter()
            .find(|i| i.code == "DEATH_BAGS_FOUND")
            .expect("found issue");
        assert_eq!(found.severity, DiagnosticSeverity::Warning);
        assert_eq!(found.context.as_deref(), Some("bag9"));
        assert_eq!(found.category, DiagnosticCategory::DeathBag);
    }

    #[test]
    fn guard_removes_protected_entities_and_files_from_preview() {
        let mut protection = DeathBagProtection::new();
        protection.protect("deathbag1");

        let mut preview = MutationPreview::new("cleanup_test", "save_root");
        preview.add_delete_entity(
            "CharacterSaveParameterMap",
            "Death-Bag-1",
            "orphan",
            "delete",
        );
        preview.add_delete_entity(
            "CharacterSaveParameterMap",
            "orphan_normal",
            "orphan",
            "delete",
        );
        preview.files_to_delete.push(std::path::PathBuf::from(
            "save_root/Containers/DEATHBAG1.sav",
        ));
        preview
            .files_to_delete
            .push(std::path::PathBuf::from("save_root/Containers/keepme.sav"));

        guard_preview_against_death_bags(&mut preview, &protection);

        assert_eq!(preview.entities_to_delete.len(), 1);
        assert_eq!(preview.entities_to_delete[0].entity_id, "orphan_normal");
        assert_eq!(preview.files_to_delete.len(), 1);
        assert!(preview.files_to_delete[0].ends_with("keepme.sav"));
        assert!(preview
            .warnings
            .iter()
            .any(|w| w.contains("[DEATH_BAG_PROTECTED]")));
    }

    #[test]
    fn guard_is_a_noop_with_empty_protection() {
        let mut preview = MutationPreview::new("cleanup_test", "save_root");
        preview.add_delete_entity("X", "keep", "k", "d");
        guard_preview_against_death_bags(&mut preview, &DeathBagProtection::new());
        assert_eq!(preview.entities_to_delete.len(), 1);
        assert!(preview.warnings.is_empty());
    }

    #[test]
    fn path_guard_matches_file_stems() {
        let mut protection = DeathBagProtection::new();
        protection.protect("abc123");
        assert!(is_path_protected(
            std::path::Path::new("saves/Players/ABC-123.sav"),
            &protection
        ));
        assert!(!is_path_protected(
            std::path::Path::new("saves/Level.sav"),
            &protection
        ));
    }
}
