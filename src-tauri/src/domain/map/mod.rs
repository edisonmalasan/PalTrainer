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
    /// Base camp area multiplier (0.5-10.0) for Base markers; None for others.
    pub area_range: Option<f32>,
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

/// Converts 2D map grid coordinates back into UE world-space coordinates.
/// Exact inverse of `world_to_map_coordinates` (post-Sakurajima calibration):
/// world_y = map_x * scale + transl_y, world_x = map_y * scale - transl_x
pub fn map_to_world_coordinates(map_x: i32, map_y: i32) -> (f32, f32) {
    let world_y = map_x as f32 * POST_SAKURAJIMA_SCALE + POST_SAKURAJIMA_TRANSL_Y;
    let world_x = map_y as f32 * POST_SAKURAJIMA_SCALE - POST_SAKURAJIMA_TRANSL_X;
    (world_x, world_y)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_world_to_map_coordinates() {
        let (mx, my) = world_to_map_coordinates(0.0, 0.0);
        assert_eq!(mx, 0);
        assert_eq!(
            my,
            (POST_SAKURAJIMA_TRANSL_X / POST_SAKURAJIMA_SCALE).round() as i32
        );
    }

    #[test]
    fn test_map_to_world_is_the_inverse() {
        // Known marker: world (12000, -85000) -> map -> world roundtrip.
        let (mx, my) = world_to_map_coordinates(12000.0, -85000.0);
        let (wx, wy) = map_to_world_coordinates(mx, my);
        assert!((wx - 12000.0).abs() < POST_SAKURAJIMA_SCALE);
        assert!((wy - -85000.0).abs() < POST_SAKURAJIMA_SCALE);
    }

    #[test]
    fn test_map_to_world_roundtrip_across_grid() {
        for gx in [-500i32, 0, 1, 123, 535] {
            for gy in [-500i32, 0, 42, 907] {
                let (wx, wy) = map_to_world_coordinates(gx, gy);
                let (mx, my) = world_to_map_coordinates(wx, wy);
                assert_eq!((mx, my), (gx, gy), "roundtrip failed for grid ({gx},{gy})");
            }
        }
    }
}
