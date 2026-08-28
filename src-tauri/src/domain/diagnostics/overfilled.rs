//! Overfilled inventory detection and trim preview — the Rust realization of
//! the reference tool's `detect_and_trim_overfilled_inventories`.
//!
//! A container is "overfilled" when its occupied slot count exceeds its
//! declared `slot_capacity` by a safety buffer (default 50). Trimming is a
//! preview-only operation: the excess slots are queued as modifications and
//! only removed on commit after a safety backup.

use serde::{Deserialize, Serialize};

use crate::domain::diagnostics::{
    DiagnosticCategory, DiagnosticIssue, DiagnosticSeverity, RepairActionDescriptor,
};
use crate::domain::inventory::InventoryProjection;
use crate::domain::save_session::preview::MutationPreview;

/// Default safety margin of extra occupied slots a container may hold before
/// being flagged. Mirrors the reference tool's +50 buffer.
pub const DEFAULT_OVERFILL_BUFFER: usize = 50;

/// An inventory whose occupied slots exceed its capacity (+ buffer).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct OverfilledInventory {
    pub container_id: String,
    pub container_type: String,
    pub owner_id: String,
    pub slot_capacity: usize,
    pub occupied_slots: usize,
    /// `occupied_slots - (slot_capacity + buffer)`; capped at 0.
    pub overflow_count: usize,
}

/// Detects inventories whose occupied slot count exceeds their declared
/// capacity plus the safety buffer.
pub fn detect_overfilled_inventories(
    inventories: &[InventoryProjection],
    buffer: usize,
) -> Vec<OverfilledInventory> {
    let mut out = Vec::new();
    for inv in inventories {
        let occupied = inv.slots.len();
        let capacity_plus_buffer = inv.slot_capacity.saturating_add(buffer);
        if occupied > capacity_plus_buffer {
            out.push(OverfilledInventory {
                container_id: inv.container_id.clone(),
                container_type: inv.container_type.clone(),
                owner_id: inv.owner_id.clone(),
                slot_capacity: inv.slot_capacity,
                occupied_slots: occupied,
                overflow_count: occupied - capacity_plus_buffer,
            });
        }
    }
    // Deterministic order by container id.
    out.sort_by(|a, b| a.container_id.cmp(&b.container_id));
    out
}

/// Number of slots that would need to be trimmed to bring a container back
/// within (capacity + buffer). Used for preview descriptions.
pub fn trim_count(overfilled: &OverfilledInventory) -> usize {
    overfilled.overflow_count
}

/// Queues trim operations for overfilled inventories into a preview. Each
/// excess slot past (capacity + buffer) is recorded as a modification on the
/// owning container's Level.sav entry.
pub fn queue_trim(
    overfilled: &[OverfilledInventory],
    preview: &mut MutationPreview,
    save_root: &std::path::Path,
) {
    let buffer = DEFAULT_OVERFILL_BUFFER;
    preview.files_to_modify.push(save_root.join("Level.sav"));
    for inv in overfilled {
        let overflow = trim_count(inv);
        preview.add_modify_entity(
            "ItemContainerSaveData",
            inv.container_id.clone(),
            format!("Trim {}", inv.container_type),
            format!(
                "Container '{}' holds {} slots against capacity {} (+{} buffer). Trim {} excess slot(s) on commit after backup.",
                inv.container_id,
                inv.occupied_slots,
                inv.slot_capacity + buffer,
                buffer,
                overflow
            ),
        );
        preview.add_warning(format!(
            "[OVERFILLED] Container '{}' ({} slots) exceeds capacity {} by {} slot(s).",
            inv.container_id, inv.occupied_slots, inv.slot_capacity, inv.overflow_count
        ));
    }
}

/// Maps overfilled inventories to repairable diagnostic issues.
pub fn overfilled_to_issues(overfilled: &[OverfilledInventory]) -> Vec<DiagnosticIssue> {
    overfilled
        .iter()
        .map(|inv| DiagnosticIssue {
            severity: DiagnosticSeverity::Warning,
            category: DiagnosticCategory::OverfilledContainer,
            code: "OVERFILLED_CONTAINER".into(),
            message: format!(
                "Container '{}' holds {} slots against capacity {} (+{} buffer), overflow {}.",
                inv.container_id,
                inv.occupied_slots,
                inv.slot_capacity,
                DEFAULT_OVERFILL_BUFFER,
                inv.overflow_count
            ),
            target_id: inv.container_id.clone(),
            context: Some(format!(
                "type: {}, owner: {}",
                inv.container_type, inv.owner_id
            )),
            can_auto_repair: true,
            repair_action: Some(RepairActionDescriptor {
                label: "Trim Overfilled Containers".into(),
                description: "Remove slots beyond capacity + the safety buffer.".into(),
                affected_entity_count: 1,
            }),
            cleanup_action: None,
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::inventory::InventorySlotProjection;

    fn inv(container_id: &str, capacity: usize, occupied: usize) -> InventoryProjection {
        let slots: Vec<InventorySlotProjection> = (0..occupied)
            .map(|i| InventorySlotProjection {
                slot_index: i,
                item_id: format!("Item{i}"),
                item_name: format!("Item {i}"),
                count: 1,
                durability: None,
            })
            .collect();
        InventoryProjection {
            container_id: container_id.into(),
            container_type: "Palbox".into(),
            owner_id: "owner1".into(),
            slot_capacity: capacity,
            slots,
        }
    }

    #[test]
    fn within_buffer_is_not_flagged() {
        // Capacity 30 + buffer 50 = 80. 70 occupied is fine.
        let inventories = vec![inv("c1", 30, 70)];
        let overfilled = detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER);
        assert!(overfilled.is_empty());
    }

    #[test]
    fn at_capacity_plus_buffer_is_not_flagged() {
        let inventories = vec![inv("c1", 30, 80)];
        assert!(detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER).is_empty());
    }

    #[test]
    fn over_capacity_plus_buffer_is_flagged_with_overflow_count() {
        let inventories = vec![inv("c1", 30, 85)];
        let overfilled = detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER);
        assert_eq!(overfilled.len(), 1);
        assert_eq!(overfilled[0].overflow_count, 5);
    }

    #[test]
    fn results_are_sorted_by_container_id() {
        let inventories = vec![inv("z", 1, 100), inv("a", 1, 100), inv("m", 1, 100)];
        let overfilled = detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER);
        let ids: Vec<&str> = overfilled.iter().map(|o| o.container_id.as_str()).collect();
        assert_eq!(ids, vec!["a", "m", "z"]);
    }

    #[test]
    fn queue_trim_adds_modifications_and_level_sav_to_preview() {
        let inventories = vec![inv("c1", 30, 90)];
        let overfilled = detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER);
        let mut preview = MutationPreview::new("cleanup_overfilled", "save_root");
        queue_trim(&overfilled, &mut preview, std::path::Path::new("save_root"));

        assert_eq!(preview.entities_to_modify.len(), 1);
        assert_eq!(
            preview.entities_to_modify[0].entity_type,
            "ItemContainerSaveData"
        );
        assert!(preview
            .files_to_modify
            .contains(&std::path::PathBuf::from("save_root/Level.sav")));
        assert!(preview.warnings.iter().any(|w| w.contains("[OVERFILLED]")));
    }

    #[test]
    fn overfilled_maps_to_repairable_issues() {
        let inventories = vec![inv("c1", 20, 100)];
        let overfilled = detect_overfilled_inventories(&inventories, DEFAULT_OVERFILL_BUFFER);
        let issues = overfilled_to_issues(&overfilled);
        assert_eq!(issues.len(), 1);
        assert_eq!(issues[0].category, DiagnosticCategory::OverfilledContainer);
        assert_eq!(issues[0].severity, DiagnosticSeverity::Warning);
        assert!(issues[0].can_auto_repair);
        assert!(issues[0].message.contains("overflow 30"));
    }
}
