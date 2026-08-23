//! Player domain mutations and validation.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdatePlayerDto {
    pub uid: String,
    pub nickname: Option<String>,
    pub level: Option<i32>,
    pub exp: Option<i64>,
    pub hp: Option<i32>,
    pub max_hp: Option<i32>,
    pub status: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BulkPlayerOperationDto {
    pub uids: Vec<String>,
}

pub fn normalize_player_uid(uid: &str) -> String {
    uid.replace('-', "").to_lowercase()
}
