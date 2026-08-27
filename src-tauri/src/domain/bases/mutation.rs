//! Base camp domain mutations and coordinate transformations.

use serde::{Deserialize, Serialize};

use crate::pal_save::rawdata::base_camp::{MAX_AREA_RANGE, MIN_AREA_RANGE};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdateBaseDto {
    pub base_id: String,
    pub level: Option<i32>,
    pub radius: Option<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct NudgeBaseCoordinatesDto {
    pub base_id: String,
    pub delta_x: f32,
    pub delta_y: f32,
    pub delta_z: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ImportBaseBundleDto {
    pub bundle_path: String,
    pub target_guild_id: String,
    pub offset_x: Option<f32>,
    pub offset_y: Option<f32>,
    pub offset_z: Option<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CloneBaseDto {
    pub base_id: String,
    pub target_guild_id: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MoveBaseToMapDto {
    pub base_id: String,
    pub map_x: i32,
    pub map_y: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdateBaseAreaRangeDto {
    pub base_id: String,
    /// Base camp area multiplier; validated in 50-1000% (0.5-10.0).
    pub area_range: f32,
}

/// Validates a base camp area multiplier against the save-format bounds
/// documented in `pal_save::rawdata::base_camp` (50%-1000%).
pub fn validate_area_range(range: f32) -> Result<(), String> {
    if !(MIN_AREA_RANGE..=MAX_AREA_RANGE).contains(&range) {
        return Err(format!(
            "Area range {:.0}% is out of bounds ({:.0}%-{:.0}%).",
            range * 100.0,
            MIN_AREA_RANGE * 100.0,
            MAX_AREA_RANGE * 100.0
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn area_range_bounds_match_base_camp_codec() {
        assert!(validate_area_range(0.5).is_ok());
        assert!(validate_area_range(1.0).is_ok());
        assert!(validate_area_range(10.0).is_ok());
        assert!(validate_area_range(0.49).is_err());
        assert!(validate_area_range(10.01).is_err());
        assert!(validate_area_range(-1.0).is_err());
    }
}
