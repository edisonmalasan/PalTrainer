//! Guild domain mutations and administration models.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdateGuildDto {
    pub guild_id: String,
    pub name: Option<String>,
    pub level: Option<i32>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TransferGuildAdminDto {
    pub guild_id: String,
    pub new_admin_uid: String,
}
