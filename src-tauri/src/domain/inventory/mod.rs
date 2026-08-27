//! Inventory and container read-only projections and mutations.

pub mod dynamic;
pub mod mutation;

pub use dynamic::{DynamicContainerReport, DynamicItem, DynamicItemManager};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct InventorySlotProjection {
    pub slot_index: usize,
    pub item_id: String,
    pub item_name: String,
    pub count: i32,
    pub durability: Option<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct InventoryProjection {
    pub container_id: String,
    pub container_type: String,
    pub owner_id: String,
    pub slot_capacity: usize,
    pub slots: Vec<InventorySlotProjection>,
}
