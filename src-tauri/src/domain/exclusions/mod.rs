//! Exclusion zones and entity protection models.

use serde::{Deserialize, Serialize};

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
}
