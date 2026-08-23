//! Save file diagnostic reporting models.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticIssue {
    pub severity: String, // "Info", "Warning", "Error"
    pub category: String, // "OrphanedPlayer", "BrokenGuild", "IllegalPal", "OverfilledContainer"
    pub target_id: String,
    pub description: String,
    pub can_auto_repair: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticReportDto {
    pub total_issues: usize,
    pub warnings: usize,
    pub errors: usize,
    pub issues: Vec<DiagnosticIssue>,
}
