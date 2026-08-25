//! Repair and recovery domain models for save corruption and state fixes.

use serde::{Deserialize, Serialize};

/// Target component or anomaly to repair.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RepairTarget {
    Structures,
    Items,
    Pals,
    IllegalPals,
    IllegalPlayers,
    InvalidActiveSkills,
    OverfilledInventories,
    Guilds,
    Timestamps,
    UnassignedPals,
    DynamicContainers,
    PrivateChests,
}

impl RepairTarget {
    pub fn label(&self) -> &'static str {
        match self {
            Self::Structures => "Repair Damaged Structures",
            Self::Items => "Fix & Restore Item Durability",
            Self::Pals => "Heal Sickness, Sanity & Fullness",
            Self::IllegalPals => "Normalize Out-of-Bounds Pal Stats",
            Self::IllegalPlayers => "Normalize Illegal Player Stats",
            Self::InvalidActiveSkills => "Clean Invalid Pal Active Skills",
            Self::OverfilledInventories => "Trim Overfilled Inventory Containers",
            Self::Guilds => "Rebuild Guild Member & Admin Indices",
            Self::Timestamps => "Reset Corrupted Entity Timestamps",
            Self::UnassignedPals => "Assign Orphaned Base Worker Pals",
            Self::DynamicContainers => "Repair Dynamic Container References",
            Self::PrivateChests => "Unlock Private Chests (Booth Locks)",
        }
    }
}

/// Parameters for running a repair operation.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RepairParams {
    pub target: RepairTarget,
    pub scope_entity_id: Option<String>,
    pub auto_heal: bool,
    pub clamp_stats: bool,
}

impl Default for RepairParams {
    fn default() -> Self {
        Self {
            target: RepairTarget::Structures,
            scope_entity_id: None,
            auto_heal: true,
            clamp_stats: true,
        }
    }
}
