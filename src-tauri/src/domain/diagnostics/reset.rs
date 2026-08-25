//! World event reset and PalDefender administration models.

use serde::{Deserialize, Serialize};

/// Target world event, cooldown, or gimmick to reset.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ResetTarget {
    Missions,
    Dungeons,
    OilRig,
    Invaders,
    SupplyDrops,
    AntiAirTurrets,
    LockGimmicks,
}

impl ResetTarget {
    pub fn label(&self) -> &'static str {
        match self {
            Self::Missions => "Reset Boss & Tutorial Missions",
            Self::Dungeons => "Reset Dungeon Timers & Cooldowns",
            Self::OilRig => "Reset Oil Rig Barriers & Chests",
            Self::Invaders => "Reset Base Raid & Invader Timers",
            Self::SupplyDrops => "Reset Meteorite & Supply Drops",
            Self::AntiAirTurrets => "Reset / Disable Anti-Air Defense",
            Self::LockGimmicks => "Reset Sanctuary & Door Lock Gimmicks",
        }
    }
}

/// Parameters for executing world event resets.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ResetParams {
    pub targets: Vec<ResetTarget>,
    pub scope_player_uid: Option<String>,
}

impl Default for ResetParams {
    fn default() -> Self {
        Self {
            targets: vec![
                ResetTarget::Dungeons,
                ResetTarget::OilRig,
                ResetTarget::SupplyDrops,
            ],
            scope_player_uid: None,
        }
    }
}

/// Generated server / admin console command for PalDefender integration.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PalDefenderCommand {
    pub command: String,
    pub description: String,
    pub category: String,
}
