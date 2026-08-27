//! Cross-guild inventory helpers — mirrors `palworld_aio/inventory/inventory_manager.py`
//! `find_item_locations_efficient` and `get_container_image_path` for rarity borders.

use serde::{Deserialize, Serialize};

use crate::domain::inventory::InventoryProjection;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ItemLocation {
    pub owner_id: String,
    pub container_id: String,
    pub slot_index: usize,
    pub count: i32,
    pub rarity: i32,
}

/// Efficiently finds every slot containing `item_id` across all inventories.
/// Case-insensitive exact match on `itemId`.
pub fn find_item_locations_efficient(
    inventories: &[InventoryProjection],
    item_id: &str,
) -> Vec<ItemLocation> {
    let needle = item_id.to_ascii_lowercase();
    let mut out = Vec::new();
    for inv in inventories {
        for slot in &inv.slots {
            if slot.item_id.to_ascii_lowercase() == needle {
                out.push(ItemLocation {
                    owner_id: inv.owner_id.clone(),
                    container_id: inv.container_id.clone(),
                    slot_index: slot.slot_index,
                    count: slot.count,
                    rarity: rarity_for_item(&slot.item_id),
                });
            }
        }
    }
    out
}

/// Removes `item_id` from matching slots across inventories, optionally by percentage.
/// `percentage`: 0.0-100.0 — 100 removes all, 50 removes half rounded up per stack.
/// Returns total count removed.
pub fn remove_item_from_players(
    inventories: &mut [InventoryProjection],
    item_id: &str,
    percentage: f32,
) -> i32 {
    let pct = percentage.clamp(0.0, 100.0) / 100.0;
    let needle = item_id.to_ascii_lowercase();
    let mut removed = 0;
    for inv in inventories.iter_mut() {
        for slot in inv.slots.iter_mut() {
            if slot.item_id.to_ascii_lowercase() == needle {
                let to_remove = if pct >= 1.0 {
                    slot.count
                } else {
                    ((slot.count as f32 * pct).ceil() as i32)
                        .max(0)
                        .min(slot.count)
                };
                removed += to_remove;
                slot.count -= to_remove;
                if slot.count <= 0 {
                    slot.item_id.clear();
                    slot.count = 0;
                    slot.durability = None;
                }
            }
        }
    }
    removed
}

/// Returns a rarity-bordered container image path — mirrors `get_container_image_path`.
/// Falls back to `Common` for unknown rarities.
pub fn get_container_image_path(container_type: &str, rarity: i32) -> String {
    let rarity = rarity.clamp(0, 5);
    format!(
        "assets/containers/{}_{}.png",
        container_type.to_ascii_lowercase(),
        rarity
    )
}

fn rarity_for_item(item_id: &str) -> i32 {
    // Minimal heuristic: spheres and cake are known rarities
    match item_id.to_ascii_lowercase().as_str() {
        "palsphere" => 1,
        "megasphere" => 2,
        "gigasphere" => 3,
        "hypersphere" => 4,
        "ultrasphere" => 5,
        "legendarysphere" => 6,
        "cake" => 3,
        _ => 1,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::inventory::{InventoryProjection, InventorySlotProjection};

    fn inv(owner: &str, slots: Vec<(&str, i32)>) -> InventoryProjection {
        InventoryProjection {
            container_id: format!("inv_{owner}"),
            container_type: "Player".into(),
            owner_id: owner.into(),
            slot_capacity: 30,
            slots: slots
                .into_iter()
                .enumerate()
                .map(|(idx, (id, count))| InventorySlotProjection {
                    slot_index: idx,
                    item_id: id.into(),
                    item_name: id.into(),
                    count,
                    durability: None,
                })
                .collect(),
        }
    }

    #[test]
    fn finds_locations_case_insensitive() {
        let inventories = vec![
            inv("p1", vec![("Wood", 10), ("Stone", 5)]),
            inv("p2", vec![("wood", 7)]),
        ];
        let locs = find_item_locations_efficient(&inventories, "WOOD");
        assert_eq!(locs.len(), 2);
        assert!(locs.iter().any(|l| l.owner_id == "p1" && l.count == 10));
        assert!(locs.iter().any(|l| l.owner_id == "p2"));
    }

    #[test]
    fn remove_by_percentage() {
        let mut invs = vec![inv("p1", vec![("Wood", 10), ("Stone", 5)])];
        let removed = remove_item_from_players(&mut invs, "Wood", 50.0);
        assert_eq!(removed, 5);
        assert_eq!(invs[0].slots[0].count, 5);
        let removed_all = remove_item_from_players(&mut invs, "Wood", 100.0);
        assert_eq!(removed_all, 5);
        assert_eq!(invs[0].slots[0].item_id, "");
    }

    #[test]
    fn remove_all_when_100_pct() {
        let mut invs = vec![inv("p1", vec![("Cake", 3)])];
        let removed = remove_item_from_players(&mut invs, "cake", 100.0);
        assert_eq!(removed, 3);
        assert!(invs[0].slots[0].item_id.is_empty());
    }

    #[test]
    fn rarity_border_path() {
        assert_eq!(
            get_container_image_path("Player", 3),
            "assets/containers/player_3.png"
        );
        assert_eq!(
            get_container_image_path("GuildChest", 10),
            "assets/containers/guildchest_5.png"
        ); // clamped
        assert_eq!(
            get_container_image_path("SINGLETON", 1),
            "assets/containers/singleton_1.png"
        );
    }

    #[test]
    fn empty_search_returns_none() {
        let invs = vec![inv("p1", vec![("Wood", 10)])];
        assert!(find_item_locations_efficient(&invs, "NonExistent").is_empty());
    }
}
