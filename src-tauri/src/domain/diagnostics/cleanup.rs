//! Cleanup and deletion models for server and save file maintenance.

use serde::{Deserialize, Serialize};

/// Target entity type or cleanup category to purge.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CleanupTarget {
    EmptyGuilds,
    InactivePlayers,
    DuplicatePlayers,
    UnreferencedData,
    NonBaseMapObjects,
    InvalidStructureObjects,
    AllSkins,
    ImportedDnaPals,
    InvalidItems,
    InvalidPals,
    InvalidPassives,
}

impl CleanupTarget {
    pub fn label(&self) -> &'static str {
        match self {
            Self::EmptyGuilds => "Empty Guilds",
            Self::InactivePlayers => "Inactive Players",
            Self::DuplicatePlayers => "Duplicate Player Saves",
            Self::UnreferencedData => "Unreferenced Character & Map Data",
            Self::NonBaseMapObjects => "Non-Base Map Objects",
            Self::InvalidStructureObjects => "Invalid Structure Map Objects",
            Self::AllSkins => "All Pal & Character Skins",
            Self::ImportedDnaPals => "Imported / DNA Pals",
            Self::InvalidItems => "Invalid / Modded Items",
            Self::InvalidPals => "Invalid / Modded Pals",
            Self::InvalidPassives => "Invalid Passives & Skills",
        }
    }
}

/// Parameters for running a cleanup operation.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CleanupParams {
    pub target: CleanupTarget,
    pub inactivity_days_threshold: Option<u32>,
    pub protect_death_bags: bool,
    pub scope_player_uid: Option<String>,
}

impl Default for CleanupParams {
    fn default() -> Self {
        Self {
            target: CleanupTarget::EmptyGuilds,
            inactivity_days_threshold: Some(30),
            protect_death_bags: true,
            scope_player_uid: None,
        }
    }
}
