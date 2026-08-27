//! Dynamic item registry — mirrors `palworld_aio/inventory/dynamic_item_manager.py`.
//!
//! Singleton-type items (weapons, armor, etc.) carry a separate `DynamicItemSaveData`
//! entry keyed by a UUID. The manager tracks live entries, generates fresh UUIDs for
//! newly added equipment, and purges orphans whose slot no longer references them.

use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct DynamicItem {
    pub id: String,
    pub item_id: String,
    pub durability: Option<f32>,
}

#[derive(Debug, Default)]
pub struct DynamicItemManager {
    items: HashMap<String, DynamicItem>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DynamicContainerReport {
    pub total_dynamic_items: usize,
    pub orphaned: usize,
    pub containers_checked: usize,
}

impl DynamicItemManager {
    pub fn new() -> Self {
        Self {
            items: HashMap::new(),
        }
    }

    /// Generates a fresh dynamic-item UUID in `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` form.
    /// Uses `fastrand` to avoid pulling `uuid` crate; sufficient for manager-local uniqueness.
    pub fn generate_dynamic_item_uuid() -> String {
        let a = fastrand::u32(..);
        let b = fastrand::u16(..);
        let c = fastrand::u16(..);
        let d = fastrand::u16(..);
        let e_high = fastrand::u32(..);
        let e_low = fastrand::u16(..);
        format!("{a:08x}-{b:04x}-{c:04x}-{d:04x}-{e_high:08x}{e_low:04x}")
    }

    pub fn insert(&mut self, item: DynamicItem) {
        self.items.insert(item.id.clone(), item);
    }

    pub fn get(&self, id: &str) -> Option<&DynamicItem> {
        self.items.get(id)
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    /// Sync from raw save JSON — stub that clears and repopulates from a `DynamicItemSaveData` array.
    /// In PST `sync_with_save_data` walks `DynamicItemSaveData.value` entries.
    pub fn sync_with_save_data(&mut self, dynamic_data: Option<&Vec<DynamicItem>>) {
        self.items.clear();
        for item in dynamic_data.into_iter().flatten() {
            self.items.insert(item.id.clone(), item.clone());
        }
    }

    /// Removes entries not referenced by any slot's `dynamic_item_id`.
    /// Returns the number of orphaned entries removed.
    pub fn delete_orphaned_dynamic_items(&mut self, referenced_ids: &HashSet<String>) -> usize {
        let before = self.items.len();
        self.items.retain(|id, _| referenced_ids.contains(id));
        before - self.items.len()
    }

    /// Reports on dynamic containers without mutating — used by `check_dynamic_containers_with_reporting`.
    pub fn check_dynamic_containers_with_reporting(
        &self,
        containers: &[Vec<Option<String>>],
    ) -> DynamicContainerReport {
        let mut orphaned = 0;
        for id in containers.iter().flatten().flatten() {
            if !self.items.contains_key(id) {
                orphaned += 1;
            }
        }
        DynamicContainerReport {
            total_dynamic_items: self.items.len(),
            orphaned,
            containers_checked: containers.len(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generate_uuid_is_unique_and_formatted() {
        let a = DynamicItemManager::generate_dynamic_item_uuid();
        let b = DynamicItemManager::generate_dynamic_item_uuid();
        assert_ne!(a, b);
        assert_eq!(a.len(), 36);
        assert_eq!(a.chars().filter(|&c| c == '-').count(), 4);
    }

    #[test]
    fn sync_and_retrieve() {
        let mut mgr = DynamicItemManager::new();
        let items = vec![
            DynamicItem {
                id: "id-1".into(),
                item_id: "WeaponA".into(),
                durability: Some(100.0),
            },
            DynamicItem {
                id: "id-2".into(),
                item_id: "ArmorB".into(),
                durability: None,
            },
        ];
        mgr.sync_with_save_data(Some(&items));
        assert_eq!(mgr.len(), 2);
        assert_eq!(mgr.get("id-1").unwrap().item_id, "WeaponA");
    }

    #[test]
    fn delete_orphaned_removes_unreferenced() {
        let mut mgr = DynamicItemManager::new();
        mgr.insert(DynamicItem {
            id: "keep-1".into(),
            item_id: "Sword".into(),
            durability: Some(50.0),
        });
        mgr.insert(DynamicItem {
            id: "orphan-1".into(),
            item_id: "Shield".into(),
            durability: None,
        });
        let mut referenced = HashSet::new();
        referenced.insert("keep-1".to_string());
        let removed = mgr.delete_orphaned_dynamic_items(&referenced);
        assert_eq!(removed, 1);
        assert_eq!(mgr.len(), 1);
        assert!(mgr.get("orphan-1").is_none());
    }

    #[test]
    fn check_reports_orphaned_slots() {
        let mut mgr = DynamicItemManager::new();
        mgr.insert(DynamicItem {
            id: "dyn-1".into(),
            item_id: "ItemX".into(),
            durability: None,
        });
        let containers = vec![
            vec![
                Some("dyn-1".to_string()),
                Some("missing-1".to_string()),
                None,
            ],
            vec![None, None],
        ];
        let report = mgr.check_dynamic_containers_with_reporting(&containers);
        assert_eq!(report.total_dynamic_items, 1);
        assert_eq!(report.orphaned, 1);
        assert_eq!(report.containers_checked, 2);
    }

    #[test]
    fn durability_preserved_through_sync() {
        let mut mgr = DynamicItemManager::new();
        let item = DynamicItem {
            id: "dur-1".into(),
            item_id: "Bow".into(),
            durability: Some(123.5),
        };
        mgr.insert(item.clone());
        assert_eq!(mgr.get("dur-1").unwrap().durability, Some(123.5));
    }
}
