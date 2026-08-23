//! Base camp read-only projections.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BaseProjection {
    pub base_id: String,
    pub guild_id: String,
    pub world_coord_x: f32,
    pub world_coord_y: f32,
    pub world_coord_z: f32,
    pub map_x: i32,
    pub map_y: i32,
    pub worker_count: usize,
    pub container_count: usize,
    pub structure_count: usize,
}
