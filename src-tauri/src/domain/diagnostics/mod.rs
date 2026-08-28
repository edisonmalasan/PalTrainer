//! Save file diagnostic reporting, cleanup, and repair models.

pub mod cleanup;
pub mod orphans;
pub mod repair;
pub mod reset;
pub mod world_index;

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

impl DiagnosticIssue {
    /// Builds a finding with safe defaults for optional repair metadata.
    pub fn new(
        severity: DiagnosticSeverity,
        category: DiagnosticCategory,
        code: impl Into<String>,
        message: impl Into<String>,
        target_id: impl Into<String>,
    ) -> Self {
        Self {
            severity,
            category,
            code: code.into(),
            message: message.into(),
            target_id: target_id.into(),
            context: None,
            can_auto_repair: false,
            repair_action: None,
            cleanup_action: None,
        }
    }
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

impl DiagnosticReportDto {
    /// Aggregates issue counts in one place so frontend totals cannot drift
    /// from the findings returned by a scanner.
    pub fn from_issues(
        issues: Vec<DiagnosticIssue>,
        scan_meta: DiagnosticScanMeta,
        scanned_at: impl Into<String>,
    ) -> Self {
        let errors = issues
            .iter()
            .filter(|issue| issue.severity == DiagnosticSeverity::Error)
            .count();
        let warnings = issues
            .iter()
            .filter(|issue| issue.severity == DiagnosticSeverity::Warning)
            .count();
        let infos = issues
            .iter()
            .filter(|issue| issue.severity == DiagnosticSeverity::Info)
            .count();

        Self {
            total_issues: issues.len(),
            errors,
            warnings,
            infos,
            issues,
            scan_meta,
            scanned_at: scanned_at.into(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::diagnostics::cleanup::{CleanupParams, CleanupTarget};
    use crate::domain::diagnostics::repair::{RepairParams, RepairTarget};
    use crate::domain::diagnostics::reset::{ResetParams, ResetTarget};

    fn scan_meta() -> DiagnosticScanMeta {
        DiagnosticScanMeta {
            scan_duration_ms: 12,
            player_count: 2,
            guild_count: 1,
            base_count: 3,
            pal_count: 4,
            container_count: 5,
            save_root: "C:/Palworld/World".into(),
        }
    }

    #[test]
    fn issue_builder_sets_safe_defaults_and_preserves_contract_fields() {
        let issue = DiagnosticIssue::new(
            DiagnosticSeverity::Warning,
            DiagnosticCategory::StaleFile,
            "stale_file",
            "Save changed outside PalTrainer.",
            "Level.sav",
        );

        assert_eq!(issue.code, "stale_file");
        assert_eq!(issue.target_id, "Level.sav");
        assert!(!issue.can_auto_repair);
        assert!(issue.repair_action.is_none());
        assert!(issue.cleanup_action.is_none());
        let json = serde_json::to_value(issue).unwrap();
        assert_eq!(json["targetId"], "Level.sav");
        assert_eq!(json["severity"], "warning");
        assert_eq!(json["category"], "stale_file");
    }

    #[test]
    fn report_builder_counts_each_severity_deterministically() {
        let issues = vec![
            DiagnosticIssue::new(
                DiagnosticSeverity::Error,
                DiagnosticCategory::Integrity,
                "integrity_error",
                "Broken save.",
                "Level.sav",
            ),
            DiagnosticIssue::new(
                DiagnosticSeverity::Warning,
                DiagnosticCategory::StaleFile,
                "stale_file",
                "Changed save.",
                "Players/a.sav",
            ),
            DiagnosticIssue::new(
                DiagnosticSeverity::Info,
                DiagnosticCategory::Skin,
                "skin_info",
                "Optional skin data.",
                "skin-1",
            ),
            DiagnosticIssue::new(
                DiagnosticSeverity::Info,
                DiagnosticCategory::DeathBag,
                "death_bag_info",
                "Death bag found.",
                "bag-1",
            ),
        ];

        let report = DiagnosticReportDto::from_issues(issues, scan_meta(), "2026-08-26T00:00:00Z");
        assert_eq!(report.total_issues, 4);
        assert_eq!(report.errors, 1);
        assert_eq!(report.warnings, 1);
        assert_eq!(report.infos, 2);
        assert_eq!(report.scan_meta.player_count, 2);
    }

    #[test]
    fn repair_cleanup_and_reset_models_have_stable_labels_and_serialization() {
        assert_eq!(CleanupTarget::EmptyGuilds.label(), "Empty Guilds");
        assert_eq!(
            RepairTarget::PrivateChests.label(),
            "Unlock Private Chests (Booth Locks)"
        );
        assert_eq!(
            ResetTarget::OilRig.label(),
            "Reset Oil Rig Barriers & Chests"
        );

        let cleanup = serde_json::to_value(CleanupParams::default()).unwrap();
        assert_eq!(cleanup["target"], "empty_guilds");
        assert_eq!(cleanup["protectDeathBags"], true);

        let repair = serde_json::to_value(RepairParams::default()).unwrap();
        assert_eq!(repair["target"], "structures");
        assert_eq!(repair["clampStats"], true);

        let reset = serde_json::to_value(ResetParams::default()).unwrap();
        assert_eq!(reset["targets"][0], "dungeons");
        assert_eq!(reset["targets"][1], "oil_rig");
    }

    #[test]
    fn every_diagnostic_category_has_snake_case_wire_name() {
        let categories = [
            DiagnosticCategory::StaleFile,
            DiagnosticCategory::Integrity,
            DiagnosticCategory::OrphanedPlayer,
            DiagnosticCategory::DuplicatePlayer,
            DiagnosticCategory::BrokenGuild,
            DiagnosticCategory::EmptyGuild,
            DiagnosticCategory::IllegalPal,
            DiagnosticCategory::InvalidPalSpecies,
            DiagnosticCategory::InvalidPassives,
            DiagnosticCategory::InvalidActiveSkills,
            DiagnosticCategory::UnassignedPal,
            DiagnosticCategory::OverfilledContainer,
            DiagnosticCategory::InvalidItem,
            DiagnosticCategory::UnreferencedData,
            DiagnosticCategory::InvalidStructure,
            DiagnosticCategory::StaleTimestamp,
            DiagnosticCategory::DynamicContainerLink,
            DiagnosticCategory::PrivateChestLock,
            DiagnosticCategory::DeathBag,
            DiagnosticCategory::ImportedDnaPal,
            DiagnosticCategory::NonBaseMapObject,
            DiagnosticCategory::Skin,
        ];

        for category in categories {
            let wire = serde_json::to_value(category).unwrap();
            assert!(wire.as_str().unwrap().contains('_') || wire == "integrity" || wire == "skin");
        }
    }
}
