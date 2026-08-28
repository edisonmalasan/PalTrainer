//! Map marker projections and world/treemap coordinate transformations.
//!
//! Calibration constants and axis-swap rule come from the coordinate skill:
//! out.x = (world_y - transl_y) / scale, out.y = (world_x + transl_x) / scale.
//! Which map is used depends on the Z threshold (Sakurajima post-map vs the
//! pre-Sakurajima map).

use serde::{Deserialize, Serialize};

// Pre-Sakurajima map.
pub const PRE_SAKURAJIMA_TRANSL_X: f32 = 123888.0;
pub const PRE_SAKURAJIMA_TRANSL_Y: f32 = 158000.0;
pub const PRE_SAKURAJIMA_SCALE: f32 = 459.0;

// Post-Sakurajima map.
pub const POST_SAKURAJIMA_TRANSL_X: f32 = 375247.0;
pub const POST_SAKURAJIMA_TRANSL_Y: f32 = -18.0;
pub const POST_SAKURAJIMA_SCALE: f32 = 725.0;

// Treemap overlay.
pub const TREEMAP_TRANSL_X: f64 = 358000.0;
pub const TREEMAP_TRANSL_Y: f64 = -382365.0;
pub const TREEMAP_SCALE: f64 = 724.0;

/// World Z above which the post-Sakurajima map is used.
pub const MAP_Z_THRESHOLD: f32 = 5000.0;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapMarkerProjection {
    pub id: String,
    pub marker_type: String, // "Player", "Base", "FastTravel", "Boss"
    pub label: String,
    pub world_x: f32,
    pub world_y: f32,
    pub world_z: f32,
    /// Which map calibration placed this marker: "PreSakurajima" | "PostSakurajima".
    pub map_version: String,
    pub map_x: i32,
    pub map_y: i32,
    /// Treemap overlay pixel position (world -> treemap pixel).
    pub treemap_x: i32,
    pub treemap_y: i32,
    /// Base camp area multiplier (0.5-10.0) for Base markers; None for others.
    pub area_range: Option<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapDataProjection {
    pub map_version: String,
    pub markers: Vec<MapMarkerProjection>,
}

/// Axis-swapped world -> grid translation for a map/treemap transform.
fn world_to_map_with(
    world_x: f32,
    world_y: f32,
    transl_x: f32,
    transl_y: f32,
    scale: f32,
) -> (i32, i32) {
    let map_x = ((world_y - transl_y) / scale).round() as i32;
    let map_y = ((world_x + transl_x) / scale).round() as i32;
    (map_x, map_y)
}

/// Inverse of `world_to_map_with` (cursor -> world).
fn map_to_world_with(
    map_x: i32,
    map_y: i32,
    transl_x: f32,
    transl_y: f32,
    scale: f32,
) -> (f32, f32) {
    let world_y = map_x as f32 * scale + transl_y;
    let world_x = map_y as f32 * scale - transl_x;
    (world_x, world_y)
}

/// Pre-Sakurajima map placement.
#[allow(non_snake_case)]
pub fn world_to_map_pre_sakurajima(world_x: f32, world_y: f32) -> (i32, i32) {
    world_to_map_with(
        world_x,
        world_y,
        PRE_SAKURAJIMA_TRANSL_X,
        PRE_SAKURAJIMA_TRANSL_Y,
        PRE_SAKURAJIMA_SCALE,
    )
}

/// Post-Sakurajima map placement.
#[allow(non_snake_case)]
pub fn world_to_map_post_sakurajima(world_x: f32, world_y: f32) -> (i32, i32) {
    world_to_map_with(
        world_x,
        world_y,
        POST_SAKURAJIMA_TRANSL_X,
        POST_SAKURAJIMA_TRANSL_Y,
        POST_SAKURAJIMA_SCALE,
    )
}

/// Picks the map transform by Z height: above the threshold use post-Sakurajima.
pub fn sav_to_map_by_z(world_x: f32, world_y: f32, world_z: f32) -> (i32, i32) {
    if world_z.abs() >= MAP_Z_THRESHOLD {
        world_to_map_post_sakurajima(world_x, world_y)
    } else {
        world_to_map_pre_sakurajima(world_x, world_y)
    }
}

/// Inverse (cursor -> world) for the post-Sakurajima map.
#[allow(non_snake_case)]
pub fn map_to_world_post_sakurajima(map_x: i32, map_y: i32) -> (f32, f32) {
    map_to_world_with(
        map_x,
        map_y,
        POST_SAKURAJIMA_TRANSL_X,
        POST_SAKURAJIMA_TRANSL_Y,
        POST_SAKURAJIMA_SCALE,
    )
}

/// Inverse (cursor -> world) for the pre-Sakurajima map.
#[allow(non_snake_case)]
pub fn map_to_world_pre_sakurajima(map_x: i32, map_y: i32) -> (f32, f32) {
    map_to_world_with(
        map_x,
        map_y,
        PRE_SAKURAJIMA_TRANSL_X,
        PRE_SAKURAJIMA_TRANSL_Y,
        PRE_SAKURAJIMA_SCALE,
    )
}

/// World -> treemap overlay pixel.
pub fn treemap_to_pixel(world_x: f32, world_y: f32) -> (i32, i32) {
    let pixel_x = ((world_y as f64 - TREEMAP_TRANSL_Y) / TREEMAP_SCALE).round() as i32;
    let pixel_y = ((world_x as f64 + TREEMAP_TRANSL_X) / TREEMAP_SCALE).round() as i32;
    (pixel_x, pixel_y)
}

/// Inverse of `treemap_to_pixel`: pixel -> world (a.k.a. pixel_to_cursor).
pub fn pixel_to_cursor(pixel_x: i32, pixel_y: i32) -> (f32, f32) {
    let world_y = pixel_x as f64 * TREEMAP_SCALE + TREEMAP_TRANSL_Y;
    let world_x = pixel_y as f64 * TREEMAP_SCALE - TREEMAP_TRANSL_X;
    (world_x as f32, world_y as f32)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_world_to_map_coordinates_post() {
        let (mx, my) = world_to_map_post_sakurajima(0.0, 0.0);
        assert_eq!(mx, 0);
        assert_eq!(
            my,
            (POST_SAKURAJIMA_TRANSL_X / POST_SAKURAJIMA_SCALE).round() as i32
        );
    }

    #[test]
    fn test_post_inverse_roundtrip_across_grid() {
        for gx in [-500i32, 0, 1, 123, 535] {
            for gy in [-500i32, 0, 42, 907] {
                let (wx, wy) = map_to_world_post_sakurajima(gx, gy);
                let (mx, my) = world_to_map_post_sakurajima(wx, wy);
                assert_eq!((mx, my), (gx, gy));
            }
        }
    }

    #[test]
    fn test_pre_inverse_roundtrip_across_grid() {
        for gx in [-500i32, 0, 1, 123, 535] {
            for gy in [-500i32, 0, 42, 907] {
                let (wx, wy) = map_to_world_pre_sakurajima(gx, gy);
                let (mx, my) = world_to_map_pre_sakurajima(wx, wy);
                assert_eq!((mx, my), (gx, gy));
            }
        }
    }

    #[test]
    fn test_z_dispatch_selects_map_by_height() {
        let (pre_mx, pre_my) = sav_to_map_by_z(0.0, 0.0, 0.0);
        let (post_mx, post_my) = sav_to_map_by_z(0.0, 0.0, 6000.0);
        assert_eq!((pre_mx, pre_my), world_to_map_pre_sakurajima(0.0, 0.0));
        assert_eq!((post_mx, post_my), world_to_map_post_sakurajima(0.0, 0.0));
        // The two maps differ at the same world point.
        assert_ne!((pre_mx, pre_my), (post_mx, post_my));
    }

    #[test]
    fn test_treemap_pixel_inverse() {
        let (px, py) = treemap_to_pixel(0.0, 0.0);
        let (wx, wy) = pixel_to_cursor(px, py);
        assert!((wx - 0.0).abs() < TREEMAP_SCALE as f32);
        assert!((wy - 0.0).abs() < TREEMAP_SCALE as f32);

        let (px, py) = treemap_to_pixel(12000.0, -85000.0);
        let (wx, wy) = pixel_to_cursor(px, py);
        assert!((wx - 12000.0).abs() < TREEMAP_SCALE as f32);
        assert!((wy - -85000.0).abs() < TREEMAP_SCALE as f32);
    }

    #[test]
    fn test_calibration_vector_is_consistent_with_constants() {
        // The negative translate origin maps to grid (0,0) on the post map.
        let origin =
            world_to_map_post_sakurajima(-POST_SAKURAJIMA_TRANSL_X, -POST_SAKURAJIMA_TRANSL_Y);
        assert_eq!(origin, (0, 0));
        // Moving +1 scale in world_x moves +1 in grid y.
        let (_, my) = world_to_map_post_sakurajima(
            -POST_SAKURAJIMA_TRANSL_X + POST_SAKURAJIMA_SCALE,
            -POST_SAKURAJIMA_TRANSL_Y,
        );
        assert_eq!(my, 1);
    }
}
