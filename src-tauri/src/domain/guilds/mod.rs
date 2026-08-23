//! Guild read-only projections.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GuildMemberProjection {
    pub player_uid: String,
    pub player_name: String,
    pub is_admin: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GuildProjection {
    pub guild_id: String,
    pub name: String,
    pub admin_player_uid: String,
    pub admin_player_name: String,
    pub level: i32,
    pub base_count: usize,
    pub members: Vec<GuildMemberProjection>,
}
