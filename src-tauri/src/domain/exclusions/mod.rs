//! Exclusion zones and entity protection models.

pub mod store;

use serde::{Deserialize, Serialize};

use crate::domain::map::map_to_world_post_sakurajima;
use crate::error::AppError;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Point2D {
    pub x: f32,
    pub y: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ZoneExclusion {
    pub id: String,
    pub name: String,
    pub zone_type: String, // "rectangle" or "polygon"
    pub points: Vec<Point2D>,
    pub protect_bases: bool,
    pub protect_players: bool,
    pub protect_structures: bool,
}

impl ZoneExclusion {
    /// Checks if a world coordinate (x, y) falls within this exclusion zone.
    pub fn contains_point(&self, px: f32, py: f32) -> bool {
        if self.points.len() < 3 {
            // Rectangle with 2 diagonal corner points
            if self.points.len() == 2 {
                let min_x = self.points[0].x.min(self.points[1].x);
                let max_x = self.points[0].x.max(self.points[1].x);
                let min_y = self.points[0].y.min(self.points[1].y);
                let max_y = self.points[0].y.max(self.points[1].y);
                return px >= min_x && px <= max_x && py >= min_y && py <= max_y;
            }
            return false;
        }

        // Ray-casting algorithm for general polygon
        let mut inside = false;
        let mut j = self.points.len() - 1;

        for i in 0..self.points.len() {
            let pi = &self.points[i];
            let pj = &self.points[j];

            if ((pi.y > py) != (pj.y > py))
                && (px < (pj.x - pi.x) * (py - pi.y) / (pj.y - pi.y) + pi.x)
            {
                inside = !inside;
            }
            j = i;
        }

        inside
    }
}

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExclusionConfig {
    pub excluded_player_uids: Vec<String>,
    pub excluded_guild_ids: Vec<String>,
    pub excluded_base_ids: Vec<String>,
    pub zones: Vec<ZoneExclusion>,
}

/// Map-grid point for a canvas-drawn zone (post-Sakurajima grid units).
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapPointDto {
    pub x: i32,
    pub y: i32,
}

/// Draft zone drawn on the map canvas in map-grid space. The backend converts
/// points to world coordinates so the coordinate transform stays authoritative
/// in Rust instead of being duplicated in the UI.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ZoneFromMapDraft {
    pub name: String,
    pub zone_type: String,
    pub points: Vec<MapPointDto>,
    pub protect_bases: bool,
    pub protect_players: bool,
    pub protect_structures: bool,
}

/// Builds a persistable `ZoneExclusion` from a canvas-drawn map-grid draft.
/// `id` is assigned by the caller (the command handler) so this stays pure.
pub fn build_zone_from_map(draft: &ZoneFromMapDraft, id: &str) -> Result<ZoneExclusion, AppError> {
    let name = draft.name.trim();
    if name.is_empty() {
        return Err(AppError::new(
            "zone_name_required",
            "Exclusion zone name cannot be empty.",
        ));
    }
    let geometry_ok = match draft.zone_type.as_str() {
        "rectangle" => draft.points.len() == 2,
        "polygon" => draft.points.len() >= 3,
        _ => false,
    };
    if !geometry_ok {
        return Err(AppError::new(
            "zone_geometry_invalid",
            "A rectangle zone needs exactly 2 corner points and a polygon zone needs at least 3 points.",
        ));
    }
    let points = draft
        .points
        .iter()
        .map(|p| {
            let (world_x, world_y) = map_to_world_post_sakurajima(p.x, p.y);
            Point2D {
                x: world_x,
                y: world_y,
            }
        })
        .collect();
    Ok(ZoneExclusion {
        id: id.to_string(),
        name: name.to_string(),
        zone_type: draft.zone_type.clone(),
        points,
        protect_bases: draft.protect_bases,
        protect_players: draft.protect_players,
        protect_structures: draft.protect_structures,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rectangle_exclusion() {
        let rect = ZoneExclusion {
            id: "z1".into(),
            name: "Spawn Zone".into(),
            zone_type: "rectangle".into(),
            points: vec![
                Point2D { x: 0.0, y: 0.0 },
                Point2D {
                    x: 1000.0,
                    y: 1000.0,
                },
            ],
            protect_bases: true,
            protect_players: true,
            protect_structures: true,
        };

        assert!(rect.contains_point(500.0, 500.0));
        assert!(!rect.contains_point(1500.0, 500.0));
    }

    #[test]
    fn rectangle_draft_converts_corners_to_world_grid() {
        let draft = ZoneFromMapDraft {
            name: "Spawn".into(),
            zone_type: "rectangle".into(),
            points: vec![MapPointDto { x: 10, y: 20 }, MapPointDto { x: 30, y: 40 }],
            protect_bases: true,
            protect_players: true,
            protect_structures: true,
        };

        let zone = build_zone_from_map(&draft, "zone_1").unwrap();
        assert_eq!(zone.id, "zone_1");
        assert_eq!(zone.name, "Spawn");
        assert_eq!(zone.zone_type, "rectangle");
        // The axis-swapped inverse calibration round-trips drawn grid corners.
        for (point, (gx, gy)) in zone.points.iter().zip([(10i32, 20i32), (30, 40)]) {
            let (mx, my) = crate::domain::map::world_to_map_post_sakurajima(point.x, point.y);
            assert_eq!((mx, my), (gx, gy));
        }
    }

    #[test]
    fn polygon_draft_keeps_all_vertices() {
        let draft = ZoneFromMapDraft {
            name: "Outpost".into(),
            zone_type: "polygon".into(),
            points: vec![
                MapPointDto { x: 0, y: 0 },
                MapPointDto { x: 100, y: 0 },
                MapPointDto { x: 50, y: 100 },
                MapPointDto { x: 25, y: 60 },
            ],
            protect_bases: true,
            protect_players: false,
            protect_structures: true,
        };

        let zone = build_zone_from_map(&draft, "zone_2").unwrap();
        assert_eq!(zone.points.len(), 4);
        let (mx, my) =
            crate::domain::map::world_to_map_post_sakurajima(zone.points[2].x, zone.points[2].y);
        assert_eq!((mx, my), (50, 100));
    }

    #[test]
    fn drawn_zone_contains_points_in_world_space() {
        let draft = ZoneFromMapDraft {
            name: "Safe".into(),
            zone_type: "rectangle".into(),
            points: vec![MapPointDto { x: 0, y: 0 }, MapPointDto { x: 100, y: 100 }],
            protect_bases: true,
            protect_players: true,
            protect_structures: true,
        };
        let zone = build_zone_from_map(&draft, "zone_3").unwrap();

        let (inside_x, inside_y) = crate::domain::map::map_to_world_post_sakurajima(50, 50);
        assert!(zone.contains_point(inside_x, inside_y));
        let (outside_x, outside_y) = crate::domain::map::map_to_world_post_sakurajima(500, 500);
        assert!(!zone.contains_point(outside_x, outside_y));
    }

    #[test]
    fn invalid_drawn_drafts_are_rejected() {
        let base = |zone_type: &str, count: usize| ZoneFromMapDraft {
            name: "Zone".into(),
            zone_type: zone_type.into(),
            points: (0..count)
                .map(|i| MapPointDto {
                    x: i as i32,
                    y: i as i32,
                })
                .collect(),
            protect_bases: true,
            protect_players: true,
            protect_structures: true,
        };

        assert_eq!(
            build_zone_from_map(&base("rectangle", 3), "z")
                .unwrap_err()
                .code,
            "zone_geometry_invalid"
        );
        assert_eq!(
            build_zone_from_map(&base("polygon", 2), "z")
                .unwrap_err()
                .code,
            "zone_geometry_invalid"
        );
        assert_eq!(
            build_zone_from_map(&base("circle", 4), "z")
                .unwrap_err()
                .code,
            "zone_geometry_invalid"
        );

        let unnamed = ZoneFromMapDraft {
            name: "   ".into(),
            ..base("rectangle", 2)
        };
        assert_eq!(
            build_zone_from_map(&unnamed, "z").unwrap_err().code,
            "zone_name_required"
        );
    }
}
