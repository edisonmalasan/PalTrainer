//! Pal mutation DTOs for editing, creation, cloning, and bulk operations.

use serde::{Deserialize, Serialize};

/// Update a single Pal's editable fields.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UpdatePalDto {
    pub instance_id: String,
    pub nickname: Option<String>,
    pub level: Option<i32>,
    pub exp: Option<i64>,
    /// Gender string: "Male", "Female", or "Unknown".
    pub gender: Option<String>,
    /// Individual value overrides (0–100).
    pub iv_hp: Option<i32>,
    pub iv_attack: Option<i32>,
    pub iv_defense: Option<i32>,
    /// Soul bonus rank (0–4, condenser).
    pub souls: Option<i32>,
    /// Condenser rank (0–5).
    pub condenser_rank: Option<i32>,
    /// Replace all passive skill IDs.
    pub passive_skills: Option<Vec<String>>,
    /// Replace equipped active skill IDs (max 3).
    pub active_skills: Option<Vec<String>>,
    /// Boss / alpha flag.
    pub is_boss: Option<bool>,
    /// Lucky flag.
    pub is_lucky: Option<bool>,
    /// When true, the backend applies cheat-mode caps instead of normal caps.
    pub cheat_mode: bool,
}

/// Create a brand-new Pal and place it into a target container slot.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CreatePalDto {
    pub species_id: String,
    pub nickname: Option<String>,
    pub level: i32,
    pub gender: String,
    /// Target container type: "palbox", "party", "base", "dps", "gps".
    pub container_type: String,
    /// Owner player UID (not required for base/gps containers).
    pub owner_uid: Option<String>,
    pub cheat_mode: bool,
}

/// Import a Pal from a `.pstpal`-style JSON or PalTrainer bundle file.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ImportPalDto {
    pub bundle_path: String,
    pub target_container_type: String,
    pub target_owner_uid: Option<String>,
    pub cheat_mode: bool,
}

/// Duplicate a Pal into the same or a different container.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ClonePalDto {
    pub instance_id: String,
    pub target_container_type: String,
    pub target_owner_uid: Option<String>,
}

/// Delete one or more Pals by instance ID.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DeletePalDto {
    pub instance_ids: Vec<String>,
}

/// Max all stats for a set of Pals (or all Pals if instance_ids is empty).
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BulkMaxPalsDto {
    /// Empty means "all Pals in the loaded save".
    pub instance_ids: Vec<String>,
    pub cheat_mode: bool,
}

/// Copy skills and passives from a source Pal to a set of target Pals.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BulkSyncPalSkillsDto {
    pub source_instance_id: String,
    pub target_instance_ids: Vec<String>,
    pub sync_passives: bool,
    pub sync_active_skills: bool,
}

/// Export a Pal bundle to a file path.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExportPalBundleDto {
    pub instance_id: String,
    pub export_path: String,
}
