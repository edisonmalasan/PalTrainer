//! Player projections, mutation types, and helpers.

pub mod mutation;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PlayerProjection {
    pub uid: String,
    pub nickname: String,
    pub level: i32,
    pub exp: i64,
    pub hp: i32,
    pub max_hp: i32,
    pub guild_id: Option<String>,
    pub pal_count: usize,
    pub is_host: bool,
    pub status: String,
}
