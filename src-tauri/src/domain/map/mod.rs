//! Map marker projections and world coordinate transformations.

use serde::{Deserialize, Serialize};

pub const POST_SAKURAJIMA_TRANSL_X: f32 = 375247.0;
pub const POST_SAKURAJIMA_TRANSL_Y: f32 = -18.0;
pub const POST_SAKURAJIMA_SCALE: f32 = 725.0;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapMarkerProjection {
    pub id: String,
    pub marker_type: String, // "Player", "Base", "FastTravel", "Boss"
    pub label: String,
    pub world_x: f32,
    pub world_y: f32,
    pub world_z: f32,
    pub map_x: i32,
    pub map_y: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapDataProjection {
    pub map_version: String,
    pub markers: Vec<MapMarkerProjection>,
}

/// Converts UE world-space coordinates into 2D map pixel coordinates.
/// Axes are swapped per Palworld coordinate system:
/// out.x = (world_y - transl_y) / scale
/// out.y = (world_x + transl_x) / scale
pub fn world_to_map_coordinates(world_x: f32, world_y: f32) -> (i32, i32) {
    let map_x = ((world_y - POST_SAKURAJIMA_TRANSL_Y) / POST_SAKURAJIMA_SCALE).round() as i32;
    let map_y = ((world_x + POST_SAKURAJIMA_TRANSL_X) / POST_SAKURAJIMA_SCALE).round() as i32;
    (map_x, map_y)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_world_to_map_coordinates() {
        let (mx, my) = world_to_map_coordinates(0.0, 0.0);
        assert_eq!(mx, 0);
        assert_eq!(my, (POST_SAKURAJIMA_TRANSL_X / POST_SAKURAJIMA_SCALE).round() as i32);
    }
}
