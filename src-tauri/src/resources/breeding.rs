//! Breeding combination calculations and lookup matrix.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PalBreedingEntry {
    pub name: String,
    pub combi_rank: i32,
    pub rarity: i32,
    pub ignore_combi: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BreedingPairResult {
    pub parent1: String,
    pub parent2: String,
    pub child: String,
    pub is_unique_combo: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BreedingLookupResult {
    pub child: Option<String>,
    pub possible_parents: Vec<(String, String)>,
    pub unique_combos: Vec<(String, String)>,
}

pub struct BreedingCalculator {
    pals: HashMap<String, PalBreedingEntry>,
    unique_combos: HashMap<(String, String), String>,
}

impl Default for BreedingCalculator {
    fn default() -> Self {
        Self::new()
    }
}

impl BreedingCalculator {
    pub fn new() -> Self {
        let mut calc = Self {
            pals: HashMap::new(),
            unique_combos: HashMap::new(),
        };
        calc.load_default_matrix();
        calc
    }

    pub fn register_pal(
        &mut self,
        name: impl Into<String>,
        combi_rank: i32,
        rarity: i32,
        ignore_combi: bool,
    ) {
        let n = name.into();
        self.pals.insert(
            n.clone(),
            PalBreedingEntry {
                name: n,
                combi_rank,
                rarity,
                ignore_combi,
            },
        );
    }

    pub fn register_unique_combo(
        &mut self,
        p1: impl Into<String>,
        p2: impl Into<String>,
        child: impl Into<String>,
    ) {
        let name1 = p1.into();
        let name2 = p2.into();
        let res = child.into();
        self.unique_combos
            .insert((name1.clone(), name2.clone()), res.clone());
        self.unique_combos.insert((name2, name1), res);
    }

    /// Computes the child of two parents using the game formula:
    /// child_rank = (parent1_rank + parent2_rank) / 2
    /// Tiebreakers: closest rarity to parent average rarity, then lower rarity.
    pub fn calculate_child(&self, parent1: &str, parent2: &str) -> Option<String> {
        // 1. Check unique combination override
        if let Some(child) = self
            .unique_combos
            .get(&(parent1.to_string(), parent2.to_string()))
        {
            return Some(child.clone());
        }

        // 2. Lookup parent stats
        let p1 = self.pals.get(parent1)?;
        let p2 = self.pals.get(parent2)?;

        if p1.combi_rank <= 0 || p2.combi_rank <= 0 {
            return None;
        }

        // Same species breeding always yields same species
        if parent1 == parent2 {
            return Some(parent1.to_string());
        }

        let target_rank = (p1.combi_rank + p2.combi_rank) / 2;
        let parent_avg_rarity = (p1.rarity + p2.rarity) as f32 / 2.0;

        // Find candidate breedable pals (ignore_combi excluded from normal pool)
        let candidates: Vec<&PalBreedingEntry> = self
            .pals
            .values()
            .filter(|p| !p.ignore_combi && p.combi_rank > 0)
            .collect();

        if candidates.is_empty() {
            return None;
        }

        // Find minimum distance to target rank
        let min_rank_diff = candidates
            .iter()
            .map(|p| (p.combi_rank - target_rank).abs())
            .min()?;

        let mut tied: Vec<&PalBreedingEntry> = candidates
            .into_iter()
            .filter(|p| (p.combi_rank - target_rank).abs() == min_rank_diff)
            .collect();

        // Sort by tiebreaker: closest rarity to parent average rarity, then lower rarity
        tied.sort_by(|a, b| {
            let diff_a = (a.rarity as f32 - parent_avg_rarity).abs();
            let diff_b = (b.rarity as f32 - parent_avg_rarity).abs();

            diff_a
                .partial_cmp(&diff_b)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| a.rarity.cmp(&b.rarity))
                .then_with(|| a.name.cmp(&b.name))
        });

        tied.first().map(|p| p.name.clone())
    }

    /// Finds all parent combinations that produce `target_child`.
    pub fn find_parents(&self, target_child: &str) -> Vec<(String, String)> {
        let mut results = Vec::new();
        let pal_names: Vec<&String> = self.pals.keys().collect();

        for i in 0..pal_names.len() {
            for j in i..pal_names.len() {
                let p1 = pal_names[i];
                let p2 = pal_names[j];
                if let Some(child) = self.calculate_child(p1, p2) {
                    if child == target_child {
                        results.push((p1.clone(), p2.clone()));
                    }
                }
            }
        }
        results.sort();
        results
    }

    fn load_default_matrix(&mut self) {
        // Essential default catalog for breeding calculations
        self.register_pal("Anubis", 570, 9, false);
        self.register_pal("Incineram", 590, 6, false);
        self.register_pal("Relaxaurus", 280, 8, false);
        self.register_pal("Sparkit", 1400, 1, false);
        self.register_pal("Quivern", 1210, 7, false);
        self.register_pal("Azurobe", 1220, 8, false);
        self.register_pal("Astegon", 490, 9, false);
        self.register_pal("Dualith", 510, 8, false);
        self.register_pal("Lamball", 1470, 1, false);
        self.register_pal("Cattiva", 1460, 1, false);
        self.register_pal("Chikipi", 1500, 1, false);
        self.register_pal("Jormuntide", 310, 9, false);
        self.register_pal("Jormuntide Ignis", 310, 9, true); // IgnoreCombi variant
        self.register_pal("Frostallion", 140, 10, false);
        self.register_pal("Frostallion Noct", 140, 10, true);
        self.register_pal("Helzephyr", 190, 8, false);
        self.register_pal("Shadowbeak", 130, 9, false);
        self.register_pal("Kitsun", 1160, 5, false);
        self.register_pal("Astegon", 490, 9, false);

        // Standard Unique Combos
        self.register_unique_combo("Frostallion", "Helzephyr", "Frostallion Noct");
        self.register_unique_combo("Kitsun", "Astegon", "Shadowbeak");
        self.register_unique_combo("Relaxaurus", "Sparkit", "Relaxaurus Lux");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_same_parent_breeding() {
        let calc = BreedingCalculator::new();
        assert_eq!(
            calc.calculate_child("Anubis", "Anubis"),
            Some("Anubis".to_string())
        );
    }

    #[test]
    fn test_unique_combo_override() {
        let calc = BreedingCalculator::new();
        assert_eq!(
            calc.calculate_child("Frostallion", "Helzephyr"),
            Some("Frostallion Noct".to_string())
        );
    }

    #[test]
    fn unique_combinations_are_symmetric() {
        let calc = BreedingCalculator::new();
        assert_eq!(
            calc.calculate_child("Helzephyr", "Frostallion"),
            calc.calculate_child("Frostallion", "Helzephyr")
        );
    }

    #[test]
    fn parent_lookup_is_sorted_and_contains_unique_pair() {
        let calc = BreedingCalculator::new();
        let parents = calc.find_parents("Frostallion Noct");
        assert!(parents.contains(&("Frostallion".into(), "Helzephyr".into())));
        let mut sorted = parents.clone();
        sorted.sort();
        assert_eq!(parents, sorted);
    }

    #[test]
    fn ignore_combi_entries_do_not_enter_standard_candidate_pool() {
        let mut calc = BreedingCalculator::new();
        calc.register_pal("TestParentA", 100, 1, false);
        calc.register_pal("TestParentB", 100, 1, false);
        calc.register_pal("IgnoredCandidate", 100, 1, true);
        assert_ne!(
            calc.calculate_child("TestParentA", "TestParentB"),
            Some("IgnoredCandidate".into())
        );
    }
}
