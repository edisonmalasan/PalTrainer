//! Orphan sweeps over the harvested [`WorldIndex`] — the Rust realization of
//! the reference tool's `_sweep_orphaned_*` and `_purge_dynamic_items` exports.
//!
//! Sweeps only produce deletion candidates when the reference graph is
//! complete (`WorldIndex::references_complete`). While RawData decoders are
//! stubs, sweeps emit partial-scan Info issues instead of guessing which
//! records are safe to remove.

use crate::domain::diagnostics::world_index::WorldIndex;
use crate::domain::diagnostics::{
    CleanupActionDescriptor, DiagnosticCategory, DiagnosticIssue, DiagnosticSeverity,
};
use crate::domain::save_session::preview::MutationPreview;

/// One deletion candidate found by a sweep.
#[derive(Clone, Debug, PartialEq)]
pub struct OrphanRecord {
    pub id: String,
    pub source_map: &'static str,
}

/// Result of one sweep: verified candidates plus reportable issues.
#[derive(Clone, Debug, PartialEq)]
pub struct SweepReport {
    /// Number of records examined (deduplicated).
    pub scanned: usize,
    /// Records verified safe to delete; empty unless references are complete.
    pub deletion_candidates: Vec<OrphanRecord>,
    pub issues: Vec<DiagnosticIssue>,
}

fn normalize(values: &[String]) -> Vec<String> {
    let mut seen = std::collections::HashSet::new();
    values
        .iter()
        .map(|v| v.trim().to_lowercase().replace('-', ""))
        .filter(|v| !v.is_empty() && seen.insert(v.clone()))
        .collect()
}

#[allow(clippy::too_many_arguments)]
fn diff_sweep(
    scanned: &[String],
    referenced: &[String],
    references_complete: bool,
    opaque_blob_count: usize,
    source_map: &'static str,
    code: &'static str,
    label: &'static str,
    description: &'static str,
) -> SweepReport {
    let scanned = normalize(scanned);
    let referenced: std::collections::HashSet<String> = normalize(referenced).into_iter().collect();
    let orphans: Vec<OrphanRecord> = scanned
        .iter()
        .filter(|id| !referenced.contains(*id))
        .map(|id| OrphanRecord {
            id: id.clone(),
            source_map,
        })
        .collect();

    let mut issues = Vec::new();
    if !references_complete {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::UnreferencedData,
            code: format!("{code}_PARTIAL"),
            message: format!(
                "{label}: {} record(s) scanned from {source_map}, but {} RawData reference blob(s) are not decoded yet. Deletion candidates are suppressed until the reference graph is complete.",
                scanned.len(),
                opaque_blob_count
            ),
            target_id: source_map.to_string(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
        return SweepReport {
            scanned: scanned.len(),
            deletion_candidates: Vec::new(),
            issues,
        };
    }

    if orphans.is_empty() {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::UnreferencedData,
            code: format!("{code}_CLEAN"),
            message: format!(
                "{label}: no orphans — all {} record(s) are referenced.",
                scanned.len()
            ),
            target_id: source_map.to_string(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
    } else {
        issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Warning,
            category: DiagnosticCategory::UnreferencedData,
            code: format!("{code}_FOUND"),
            message: format!(
                "{label}: {} orphaned record(s) in {source_map} are not referenced by any player, container, or work assignment.",
                orphans.len()
            ),
            target_id: source_map.to_string(),
            context: Some(
                orphans
                    .iter()
                    .map(|r| r.id.as_str())
                    .collect::<Vec<_>>()
                    .join(", "),
            ),
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: Some(CleanupActionDescriptor {
                label: label.to_string(),
                description: description.to_string(),
                entities_to_remove: orphans.len(),
            }),
        });
    }

    SweepReport {
        scanned: scanned.len(),
        deletion_candidates: orphans,
        issues,
    }
}

/// `CharacterSaveParameterMap` entries not owned by any player or referenced
/// by any verified container/work source.
pub fn sweep_orphaned_characters(index: &WorldIndex) -> SweepReport {
    diff_sweep(
        &index.character_ids,
        &index.referenced_character_ids,
        index.references_complete,
        index.opaque_blob_count,
        "CharacterSaveParameterMap",
        "ORPHAN_CHARACTERS",
        "Orphaned Character Records",
        "Purge character records not linked to any player, pal container, or work assignment.",
    )
}

/// `WorkSaveData` entries whose assigned character IDs are missing from the
/// character map.
pub fn sweep_orphaned_works(index: &WorldIndex) -> SweepReport {
    diff_sweep(
        &index.work_ids,
        &index.character_ids,
        index.references_complete,
        index.opaque_blob_count,
        "WorkSaveData",
        "ORPHAN_WORK",
        "Orphaned Work Entries",
        "Purge work entries whose assigned characters no longer exist.",
    )
}

/// `ItemContainerSaveData` entries with no verified owner.
pub fn sweep_orphaned_containers(index: &WorldIndex) -> SweepReport {
    diff_sweep(
        &index.container_ids,
        &index.referenced_character_ids,
        index.references_complete,
        index.opaque_blob_count,
        "ItemContainerSaveData",
        "ORPHAN_CONTAINERS",
        "Orphaned Item Containers",
        "Purge item containers no longer owned by any map object or player.",
    )
}

/// `_purge_dynamic_items`: `DynamicItemSaveData` entries no longer referenced
/// by any container slot.
pub fn purge_dynamic_items(index: &WorldIndex) -> SweepReport {
    diff_sweep(
        &index.dynamic_item_ids,
        &index.referenced_dynamic_ids,
        index.references_complete,
        index.opaque_blob_count,
        "DynamicItemSaveData",
        "ORPHAN_DYNAMIC",
        "Orphaned Dynamic Items",
        "Purge singleton dynamic items no longer referenced by any container slot.",
    )
}

/// `FoliageGridSaveDataMap` audit — foliage grids carry no verifiable
/// references yet, so this reports counts only.
pub fn sweep_orphaned_foliage(index: &WorldIndex) -> SweepReport {
    let mut report = diff_sweep(
        &index.foliage_grid_ids,
        &[],
        index.references_complete,
        index.opaque_blob_count,
        "FoliageGridSaveDataMap",
        "ORPHAN_FOLIAGE",
        "Unreferenced Foliage Grids",
        "Purge foliage grids whose model instances are all gone.",
    );
    if index.references_complete {
        // Foliage references are never verifiable: keep candidates empty.
        report.deletion_candidates.clear();
        report.issues.push(DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::UnreferencedData,
            code: "ORPHAN_FOLIAGE_MANUAL".into(),
            message: format!(
                "{} foliage grid(s) found; foliage models are opaque, review manually before removal.",
                report.scanned
            ),
            target_id: "FoliageGridSaveDataMap".into(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        });
    }
    report
}

/// Non-base map objects: real count from `MapObjectSaveData`; placement
/// attribution (base camp vs dungeon) lives in RawData and stays opaque.
pub fn sweep_non_base_map_objects(index: &WorldIndex) -> SweepReport {
    SweepReport {
        scanned: index.map_object_count,
        deletion_candidates: Vec::new(),
        issues: vec![DiagnosticIssue {
            severity: DiagnosticSeverity::Info,
            category: DiagnosticCategory::NonBaseMapObject,
            code: "MAP_OBJECTS_SCANNED".into(),
            message: format!(
                "{} map object(s) scanned; non-base placement attribution requires the map object RawData decoder, so no objects are queued for deletion yet.",
                index.map_object_count
            ),
            target_id: "MapObjectSaveData".into(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        }],
    }
}

/// Queues verified deletion candidates into a mutation preview. The preview's
/// `files_to_delete`/`files_to_modify` remain authoritative — commit only
/// executes after backup and stale-save checks pass.
pub fn queue_sweep(report: &SweepReport, preview: &mut MutationPreview) {
    for issue in &report.issues {
        preview.add_warning(format!("[{}] {}", issue.code, issue.message));
    }
    for candidate in &report.deletion_candidates {
        preview.add_delete_entity(
            candidate.source_map,
            candidate.id.clone(),
            "Orphaned record",
            "Verified unreferenced by every decoded source; removed on commit after backup.",
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::diagnostics::world_index::WorldIndex;

    fn index_with(
        characters: &[&str],
        referenced: &[&str],
        dynamic: &[&str],
        dynamic_refs: &[&str],
        complete: bool,
    ) -> WorldIndex {
        WorldIndex {
            character_ids: characters.iter().map(|s| s.to_string()).collect(),
            referenced_character_ids: referenced.iter().map(|s| s.to_string()).collect(),
            dynamic_item_ids: dynamic.iter().map(|s| s.to_string()).collect(),
            referenced_dynamic_ids: dynamic_refs.iter().map(|s| s.to_string()).collect(),
            references_complete: complete,
            opaque_blob_count: 2,
            ..WorldIndex::default()
        }
    }

    #[test]
    fn orphan_characters_are_diffed_against_verified_references() {
        let index = index_with(&["AAAA", "BBBB", "CCCC"], &["aaaa", "dddd"], &[], &[], true);
        let report = sweep_orphaned_characters(&index);
        assert_eq!(report.scanned, 3);
        let ids: Vec<&str> = report
            .deletion_candidates
            .iter()
            .map(|r| r.id.as_str())
            .collect();
        assert_eq!(ids, vec!["bbbb", "cccc"]);
        assert!(report
            .issues
            .iter()
            .any(|i| i.code == "ORPHAN_CHARACTERS_FOUND"
                && i.severity == DiagnosticSeverity::Warning));
        assert_eq!(
            report.issues[0]
                .cleanup_action
                .as_ref()
                .unwrap()
                .entities_to_remove,
            2
        );
    }

    #[test]
    fn incomplete_references_suppress_candidates_and_report_partial_scan() {
        let index = index_with(&["AAAA", "BBBB"], &["aaaa"], &[], &[], false);
        let report = sweep_orphaned_characters(&index);
        assert!(report.deletion_candidates.is_empty());
        assert!(report
            .issues
            .iter()
            .any(|i| i.code == "ORPHAN_CHARACTERS_PARTIAL"
                && i.severity == DiagnosticSeverity::Info
                && i.message.contains("suppressed")));
    }

    #[test]
    fn complete_references_with_no_orphans_report_clean() {
        let index = index_with(&["aaaa"], &["aaaa"], &[], &[], true);
        let report = sweep_orphaned_characters(&index);
        assert!(report.deletion_candidates.is_empty());
        assert!(report
            .issues
            .iter()
            .any(|i| i.code == "ORPHAN_CHARACTERS_CLEAN"));
    }

    #[test]
    fn purge_dynamic_items_removes_unreferenced_singletons() {
        let index = index_with(&[], &[], &["item-1", "item-2", "item-3"], &["ITEM2"], true);
        let report = purge_dynamic_items(&index);
        let ids: Vec<&str> = report
            .deletion_candidates
            .iter()
            .map(|r| r.id.as_str())
            .collect();
        assert_eq!(ids, vec!["item1", "item3"]);
        assert_eq!(
            report.deletion_candidates[0].source_map,
            "DynamicItemSaveData"
        );
    }

    #[test]
    fn queue_sweep_adds_entities_and_warnings_to_preview() {
        let index = index_with(&["ORPHAN-1"], &[], &[], &[], true);
        let report = sweep_orphaned_characters(&index);
        let mut preview = MutationPreview::new("cleanup_unreferenced_data", "save_root");
        queue_sweep(&report, &mut preview);

        assert_eq!(preview.entities_to_delete.len(), 1);
        assert_eq!(preview.entities_to_delete[0].entity_id, "orphan1");
        assert_eq!(
            preview.entities_to_delete[0].entity_type,
            "CharacterSaveParameterMap"
        );
        assert!(!preview.warnings.is_empty());
    }

    #[test]
    fn foliage_and_map_object_sweeps_never_queue_deletions() {
        let mut index = index_with(&[], &[], &[], &[], true);
        index.foliage_grid_ids = vec!["grid-1".into()];
        index.map_object_count = 7;

        let foliage = sweep_orphaned_foliage(&index);
        assert!(foliage.deletion_candidates.is_empty());

        let map_objects = sweep_non_base_map_objects(&index);
        assert_eq!(map_objects.scanned, 7);
        assert!(map_objects.deletion_candidates.is_empty());
        assert!(map_objects.issues[0].message.contains("7 map object(s)"));
    }
}
