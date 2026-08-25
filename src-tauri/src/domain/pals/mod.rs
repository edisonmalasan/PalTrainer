//! Pal domain: read-only projections and mutation models.

pub mod mutation;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PalProjection {
    pub instance_id: String,
    pub owner_uid: String,
    pub species_id: String,
    pub nickname: Option<String>,
    pub gender: String,
    pub level: i32,
    pub exp: i64,
    pub hp: i32,
    pub max_hp: i32,
    pub attack: i32,
    pub defense: i32,
    pub work_speed: i32,
    pub iv_hp: i32,
    pub iv_attack: i32,
    pub iv_defense: i32,
    pub rank: i32,
    pub souls: i32,
    pub is_lucky: bool,
    pub is_boss: bool,
    pub passive_skills: Vec<String>,
    pub active_skills: Vec<String>,
    pub location: String,
}
