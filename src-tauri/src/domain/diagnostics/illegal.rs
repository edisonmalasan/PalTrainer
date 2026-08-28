//! Illegal / invalid entity scanning — the Rust realization of the reference
//! tool's `scan_illegal_pals_by_owner`, `check_is_illegal_pal`, and
//! `_scan_dps_for_illegals` exports, plus invalid item/passive/skill checks.
//!
//! Validation bounds come from the pal-editor skill: level 1-80, IVs 0-100,
//! souls/rank 0-20, max 4 passives, max 3 equipped active skills. Species,
//! passive, active-skill, and item IDs are validated case-insensitively
//! against the `GameCatalog`.

use serde::Serialize;

use crate::domain::diagnostics::{
    DiagnosticCategory, DiagnosticIssue, DiagnosticSeverity, RepairActionDescriptor,
};
use crate::domain::pals::PalProjection;
use crate::resources::loader::GameCatalog;

// Bounds from the pal-editor skill.
pub const MAX_LEVEL: i32 = 80;
pub const MAX_IV: i32 = 100;
pub const MAX_SOULS: i32 = 20;
pub const MAX_PASSIVES: usize = 4;
pub const MAX_EQUIPPED_SKILLS: usize = 3;

/// A single illegal-pal finding.
#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct IllegalPalFinding {
    pub instance_id: String,
    pub species_id: String,
    pub owner_uid: Option<String>,
    /// Source `.sav` path for deep scans, if known.
    pub source_save: Option<String>,
    /// Human-readable violations, in deterministic order.
    pub violations: Vec<String>,
}

impl IllegalPalFinding {
    pub fn is_illegal(&self) -> bool {
        !self.violations.is_empty()
    }
}

/// Unit-testable legality check for a projected pal. Returns an empty list
/// when the pal is legal.
pub fn check_is_illegal_pal(pal: &PalProjection, catalog: &GameCatalog) -> Vec<String> {
    let mut violations = Vec::new();

    if !catalog
        .pals
        .iter()
        .any(|k| k.id.eq_ignore_ascii_case(&pal.species_id))
    {
        violations.push(format!(
            "Species '{}' is not in the game catalog.",
            pal.species_id
        ));
    }
    if !(1..=MAX_LEVEL).contains(&pal.level) {
        violations.push(format!(
            "Level {} is outside the 1-{MAX_LEVEL} range.",
            pal.level
        ));
    }
    for (name, value) in [
        ("HP IV", pal.iv_hp),
        ("Attack IV", pal.iv_attack),
        ("Defense IV", pal.iv_defense),
    ] {
        if !(0..=MAX_IV).contains(&value) {
            violations.push(format!("{name} {value} is outside the 0-{MAX_IV} range."));
        }
    }
    for (name, value) in [("Rank", pal.rank), ("Souls", pal.souls)] {
        if !(0..=MAX_SOULS).contains(&value) {
            violations.push(format!(
                "{name} {value} is outside the 0-{MAX_SOULS} range."
            ));
        }
    }
    if pal.passive_skills.len() > MAX_PASSIVES {
        violations.push(format!(
            "Has {} passive skills (max {MAX_PASSIVES}).",
            pal.passive_skills.len()
        ));
    }
    for passive in &pal.passive_skills {
        if !catalog
            .passives
            .iter()
            .any(|k| k.id.eq_ignore_ascii_case(passive))
        {
            violations.push(format!(
                "Passive skill '{passive}' is not in the game catalog."
            ));
        }
    }
    if pal.active_skills.len() > MAX_EQUIPPED_SKILLS {
        violations.push(format!(
            "Has {} equipped active skills (max {MAX_EQUIPPED_SKILLS}).",
            pal.active_skills.len()
        ));
    }
    for skill in &pal.active_skills {
        if !catalog
            .active_skills
            .iter()
            .any(|k| k.id.eq_ignore_ascii_case(skill))
        {
            violations.push(format!(
                "Active skill '{skill}' is not in the game catalog."
            ));
        }
    }

    violations
}

/// Groups illegal pals by owner UID — mirrors `scan_illegal_pals_by_owner`.
pub fn scan_illegal_pals_by_owner(
    pals: &[PalProjection],
    catalog: &GameCatalog,
) -> Vec<IllegalPalFinding> {
    let mut findings: Vec<IllegalPalFinding> = pals
        .iter()
        .filter_map(|pal| {
            let violations = check_is_illegal_pal(pal, catalog);
            if violations.is_empty() {
                return None;
            }
            Some(IllegalPalFinding {
                instance_id: pal.instance_id.clone(),
                species_id: pal.species_id.clone(),
                owner_uid: Some(pal.owner_uid.clone()),
                source_save: None,
                violations,
            })
        })
        .collect();
    // Deterministic order: owner first, then instance.
    findings.sort_by(|a, b| {
        a.owner_uid
            .cmp(&b.owner_uid)
            .then_with(|| a.instance_id.cmp(&b.instance_id))
    });
    findings
}

/// A batch of decoded pal projections from a single deep-scan source.
#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DeepPalScan {
    /// The `.sav` path the pals were decoded from (for reporting/dedup).
    pub source_save: String,
    pub palbatch: Vec<PalProjection>,
}

/// Deep-scan each player `.sav` payload for illegal pals — mirrors
/// `_scan_dps_for_illegals`. Findings carry their source save path.
pub fn scan_dps_for_illegals(
    scans: &[DeepPalScan],
    catalog: &GameCatalog,
) -> Vec<IllegalPalFinding> {
    let mut findings = Vec::new();
    for scan in scans {
        for pal in &scan.palbatch {
            let violations = check_is_illegal_pal(pal, catalog);
            if !violations.is_empty() {
                findings.push(IllegalPalFinding {
                    instance_id: pal.instance_id.clone(),
                    species_id: pal.species_id.clone(),
                    owner_uid: Some(pal.owner_uid.clone()),
                    source_save: Some(scan.source_save.clone()),
                    violations,
                });
            }
        }
    }
    findings
}

/// Returns item IDs present in `catalog` that are invalid (empty or
/// whitespace), and any IDs not known to the catalog. Mirrors the reference
/// tool's invalid-item sweep backed by the data manager's item map.
pub fn scan_invalid_items(item_ids: &[String], catalog: &GameCatalog) -> Vec<String> {
    let mut invalid = Vec::new();
    for id in sort_uniq(item_ids) {
        if id.trim().is_empty() {
            invalid.push(id.clone());
            continue;
        }
        if !catalog.items.iter().any(|k| k.id.eq_ignore_ascii_case(&id)) {
            invalid.push(id.clone());
        }
    }
    invalid
}

/// Passives that are empty or missing from the catalog.
pub fn scan_invalid_passives(passive_ids: &[String], catalog: &GameCatalog) -> Vec<String> {
    let mut invalid = Vec::new();
    for id in sort_uniq(passive_ids) {
        if id.trim().is_empty() {
            invalid.push(id.clone());
            continue;
        }
        if !catalog
            .passives
            .iter()
            .any(|k| k.id.eq_ignore_ascii_case(&id))
        {
            invalid.push(id.clone());
        }
    }
    invalid
}

fn sort_uniq(values: &[String]) -> Vec<String> {
    let mut out: Vec<String> = values
        .iter()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
        .collect();
    out.sort();
    out.dedup();
    out
}

/// Maps illegal-pal findings into diagnostic issues, one per pal.
pub fn illegal_findings_to_issues(findings: &[IllegalPalFinding]) -> Vec<DiagnosticIssue> {
    findings
        .iter()
        .map(|f| {
            let owner = f.owner_uid.clone().unwrap_or_else(|| "unknown".into());
            DiagnosticIssue {
                severity: DiagnosticSeverity::Warning,
                category: DiagnosticCategory::IllegalPal,
                code: "ILLEGAL_PAL".into(),
                message: format!(
                    "{} illegal Pal '{}' owned by {}: {}",
                    f.species_id,
                    f.instance_id,
                    owner,
                    f.violations.join("; ")
                ),
                target_id: f.instance_id.clone(),
                context: Some(format!("owner: {owner}, species: {}", f.species_id)),
                can_auto_repair: true,
                repair_action: Some(RepairActionDescriptor {
                    label: "Clamp Illegal Pal Stats".into(),
                    description: "Clamp level, IVs, and souls, and strip unknown passives/skills."
                        .into(),
                    affected_entity_count: 1,
                }),
                cleanup_action: None,
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::pals::PalProjection;

    fn legal_pal(id: &str) -> PalProjection {
        PalProjection {
            instance_id: format!("inst_{id}"),
            owner_uid: "owner1".into(),
            species_id: "Anubis".into(),
            nickname: None,
            gender: "Male".into(),
            level: 50,
            exp: 10000,
            hp: 2000,
            max_hp: 2000,
            attack: 600,
            defense: 500,
            work_speed: 100,
            iv_hp: 90,
            iv_attack: 80,
            iv_defense: 70,
            rank: 10,
            souls: 5,
            is_lucky: false,
            is_boss: false,
            passive_skills: vec!["Legend".into()],
            active_skills: vec!["FireBall".into()],
            location: "Palbox".into(),
        }
    }

    #[test]
    fn legal_pal_has_no_violations() {
        let catalog = GameCatalog::new();
        assert!(check_is_illegal_pal(&legal_pal("a"), &catalog).is_empty());
    }

    #[test]
    fn illegal_pal_flags_species_level_iv_souls_passive_and_skill_bounds() {
        let catalog = GameCatalog::new();
        let mut pal = legal_pal("a");
        pal.species_id = "NotAPal".into();
        pal.level = 999;
        pal.iv_attack = 200;
        pal.rank = -1;
        pal.passive_skills = vec!["FakePassive".into(); 5];
        pal.active_skills = vec!["FakeSkill".into(); 4];

        let violations = check_is_illegal_pal(&pal, &catalog);
        assert!(violations.iter().any(|v| v.contains("Species 'NotAPal'")));
        assert!(violations.iter().any(|v| v.contains("Level 999")));
        assert!(violations.iter().any(|v| v.contains("Attack IV 200")));
        assert!(violations.iter().any(|v| v.contains("Rank -1")));
        assert!(violations.iter().any(|v| v.contains("5 passive skills")));
        assert!(violations
            .iter()
            .any(|v| v.contains("4 equipped active skills")));
        assert!(violations.iter().any(|v| v.contains("FakePassive")));
        assert!(violations.iter().any(|v| v.contains("FakeSkill")));
    }

    #[test]
    fn scan_illegal_pals_by_owner_filters_and_sorts() {
        let catalog = GameCatalog::new();
        let good = legal_pal("good");
        let mut bad_a = legal_pal("bad_a");
        bad_a.level = 999;
        bad_a.owner_uid = "owner_b".into();
        let mut bad_b = legal_pal("bad_b");
        bad_b.species_id = "Mewtoo".into();

        let findings = scan_illegal_pals_by_owner(&[good, bad_a.clone(), bad_b], &catalog);
        assert_eq!(findings.len(), 2);
        // Sorted by owner then instance.
        assert_eq!(findings[0].owner_uid.as_deref(), Some("owner1"));
        assert_eq!(findings[0].instance_id, "inst_bad_b");
        assert_eq!(findings[1].owner_uid.as_deref(), Some("owner_b"));
        assert_eq!(findings[1].instance_id, "inst_bad_a");
        assert!(findings.iter().all(|f| f.is_illegal()));
    }

    #[test]
    fn deep_scan_tags_findings_with_source_save() {
        let catalog = GameCatalog::new();
        let mut bad = legal_pal("deep");
        bad.level = 0;
        let scans = vec![DeepPalScan {
            source_save: "/saves/Player/a.sav".into(),
            palbatch: vec![bad],
        }];
        let findings = scan_dps_for_illegals(&scans, &catalog);
        assert_eq!(findings.len(), 1);
        assert_eq!(
            findings[0].source_save.as_deref(),
            Some("/saves/Player/a.sav")
        );
    }

    #[test]
    fn invalid_items_and_passives_are_reported_case_insensitively() {
        let catalog = GameCatalog::new();
        let items = vec![
            "PalSphere".to_string(),
            "  ".to_string(),
            "not_a_real_item".to_string(),
        ];
        let invalid_items = scan_invalid_items(&items, &catalog);
        assert!(invalid_items.contains(&"not_a_real_item".to_string()));
        assert!(!invalid_items.contains(&"PalSphere".to_string()));

        let passives = vec!["Legend".to_string(), "FakePassive".to_string()];
        let invalid_passives = scan_invalid_passives(&passives, &catalog);
        assert_eq!(invalid_passives, vec!["FakePassive".to_string()]);
    }

    #[test]
    fn findings_map_to_repairable_illegal_pal_issues() {
        let catalog = GameCatalog::new();
        let mut bad = legal_pal("map");
        bad.owner_uid = "abc".into();
        bad.souls = 99;
        let findings = scan_illegal_pals_by_owner(&[bad], &catalog);
        let issues = illegal_findings_to_issues(&findings);
        assert_eq!(issues.len(), 1);
        assert_eq!(issues[0].category, DiagnosticCategory::IllegalPal);
        assert_eq!(issues[0].severity, DiagnosticSeverity::Warning);
        assert!(issues[0].can_auto_repair);
        assert!(issues[0].context.as_deref().unwrap().contains("owner: abc"));
    }
}
