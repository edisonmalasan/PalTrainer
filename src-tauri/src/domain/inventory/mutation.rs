//! Inventory mutation DTOs for modifying slots, containers, items, and key items.

use serde::{Deserialize, Serialize};

/// Update a specific slot within an inventory or container.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdateInventorySlotDto {
    pub owner_uid: String,
    pub container_id: String,
    pub slot_index: usize,
    pub item_id: String,
    pub count: i32,
    pub durability: Option<f32>,
}

/// Add an item into the first available or specified slot.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct AddItemDto {
    pub owner_uid: String,
    pub container_id: String,
    pub item_id: String,
    pub count: i32,
    pub durability: Option<f32>,
    pub slot_index: Option<usize>,
}

/// Remove an item from a specific slot.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RemoveItemDto {
    pub owner_uid: String,
    pub container_id: String,
    pub slot_index: usize,
    pub count: Option<i32>,
}

/// Clear all items from a container.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ClearContainerDto {
    pub owner_uid: String,
    pub container_id: String,
}

/// Resize the total slot capacity of a container.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ResizeContainerDto {
    pub owner_uid: String,
    pub container_id: String,
    pub new_capacity: usize,
}

/// Bulk add key items / relics / technology items to a player.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BulkAddKeyItemsDto {
    pub player_uid: String,
    pub key_item_ids: Vec<String>,
}
