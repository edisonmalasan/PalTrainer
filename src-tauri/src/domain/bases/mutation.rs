//! Base camp domain mutations and coordinate transformations.

use serde::{Deserialize, Serialize};

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
