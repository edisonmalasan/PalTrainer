//! Save file diagnostic reporting, cleanup, and repair models.

pub mod cleanup;

use serde::{Deserialize, Serialize};

/// Severity level for a diagnostic issue.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "lowercase")]
pub enum DiagnosticSeverity {
    Info,
    Warning,
    Error,
}

/// Category of a diagnostic issue — covers all Phase 7 scan targets.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum DiagnosticCategory {
    StaleFile,
    Integrity,
    OrphanedPlayer,
    DuplicatePlayer,
    BrokenGuild,
    EmptyGuild,
    IllegalPal,
    InvalidPalSpecies,
    InvalidPassives,
    InvalidActiveSkills,
    UnassignedPal,
    OverfilledContainer,
    InvalidItem,
    UnreferencedData,
    InvalidStructure,
    StaleTimestamp,
    DynamicContainerLink,
    PrivateChestLock,
    DeathBag,
    ImportedDnaPal,
    NonBaseMapObject,
    Skin,
}

/// Describes what an auto-repair action would do for a specific issue.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RepairActionDescriptor {
    pub label: String,
    pub description: String,
    pub affected_entity_count: usize,
}

/// Describes what a cleanup/deletion action would do for a specific issue.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CleanupActionDescriptor {
    pub label: String,
    pub description: String,
    pub entities_to_remove: usize,
}

/// A single diagnostic finding.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticIssue {
    pub severity: DiagnosticSeverity,
    pub category: DiagnosticCategory,
    pub code: String,
    pub message: String,
    pub target_id: String,
    pub context: Option<String>,
    pub can_auto_repair: bool,
    pub repair_action: Option<RepairActionDescriptor>,
    pub cleanup_action: Option<CleanupActionDescriptor>,
}

/// Metadata about a completed diagnostic scan.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticScanMeta {
    pub scan_duration_ms: u64,
    pub player_count: usize,
    pub guild_count: usize,
    pub base_count: usize,
    pub pal_count: usize,
    pub container_count: usize,
    pub save_root: String,
}

/// Full diagnostic report returned to the frontend.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticReportDto {
    pub total_issues: usize,
    pub errors: usize,
    pub warnings: usize,
    pub infos: usize,
    pub issues: Vec<DiagnosticIssue>,
    pub scan_meta: DiagnosticScanMeta,
    pub scanned_at: String,
}
