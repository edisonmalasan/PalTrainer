//! Game data models and static resource dictionary for Pals, skills, and items.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PalSpeciesInfo {
    pub id: String,
    pub name: String,
    pub element_types: Vec<String>,
    pub rarity: i32,
    pub hp_scaling: f32,
    pub attack_scaling: f32,
    pub defense_scaling: f32,
    pub work_suitabilities: Vec<WorkSuitabilityInfo>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct WorkSuitabilityInfo {
    pub work_type: String,
    pub level: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ItemInfo {
    pub id: String,
    pub name: String,
    pub category: String,
    pub max_stack: i32,
    pub rarity: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PassiveSkillInfo {
    pub id: String,
    pub name: String,
    pub tier: i32,
    pub description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ActiveSkillInfo {
    pub id: String,
    pub name: String,
    pub element: String,
    pub power: i32,
    pub cooldown_seconds: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GameCatalog {
    pub pals: Vec<PalSpeciesInfo>,
    pub items: Vec<ItemInfo>,
    pub passives: Vec<PassiveSkillInfo>,
    pub active_skills: Vec<ActiveSkillInfo>,
}

impl Default for GameCatalog {
    fn default() -> Self {
        Self::new()
    }
}

impl GameCatalog {
    pub fn new() -> Self {
        Self {
            pals: default_pals(),
            items: default_items(),
            passives: default_passives(),
            active_skills: default_active_skills(),
        }
    }

    /// Validates static or imported game data before it is exposed to editors.
    pub fn validate_integrity(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();
        validate_ids(
            "pals",
            self.pals.iter().map(|entry| entry.id.as_str()),
            &mut errors,
        );
        validate_ids(
            "items",
            self.items.iter().map(|entry| entry.id.as_str()),
            &mut errors,
        );
        validate_ids(
            "passives",
            self.passives.iter().map(|entry| entry.id.as_str()),
            &mut errors,
        );
        validate_ids(
            "active_skills",
            self.active_skills.iter().map(|entry| entry.id.as_str()),
            &mut errors,
        );

        for pal in &self.pals {
            if pal.rarity < 0
                || pal.hp_scaling < 0.0
                || pal.attack_scaling < 0.0
                || pal.defense_scaling < 0.0
            {
                errors.push(format!(
                    "pals contains invalid numeric values for '{}'.",
                    pal.id
                ));
            }
            for suitability in &pal.work_suitabilities {
                if !(1..=4).contains(&suitability.level) || suitability.work_type.is_empty() {
                    errors.push(format!(
                        "pals contains invalid work suitability for '{}'.",
                        pal.id
                    ));
                }
            }
        }
        for item in &self.items {
            if item.max_stack <= 0 || item.rarity < 0 {
                errors.push(format!(
                    "items contains invalid numeric values for '{}'.",
                    item.id
                ));
            }
        }
        for passive in &self.passives {
            if passive.tier < 0 || passive.name.is_empty() {
                errors.push(format!(
                    "passives contains invalid values for '{}'.",
                    passive.id
                ));
            }
        }
        for skill in &self.active_skills {
            if skill.power < 0 || skill.cooldown_seconds < 0 || skill.element.is_empty() {
                errors.push(format!(
                    "active_skills contains invalid values for '{}'.",
                    skill.id
                ));
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}

fn validate_ids<'a>(
    collection: &str,
    ids: impl Iterator<Item = &'a str>,
    errors: &mut Vec<String>,
) {
    let mut seen = std::collections::HashSet::new();
    for id in ids {
        if id.is_empty() {
            errors.push(format!("{collection} contains an empty ID."));
        } else if !seen.insert(id) {
            errors.push(format!("{collection} contains duplicate ID '{id}'."));
        }
    }
}

fn default_pals() -> Vec<PalSpeciesInfo> {
    vec![
        PalSpeciesInfo {
            id: "Anubis".into(),
            name: "Anubis".into(),
            element_types: vec!["Ground".into()],
            rarity: 9,
            hp_scaling: 120.0,
            attack_scaling: 130.0,
            defense_scaling: 100.0,
            work_suitabilities: vec![
                WorkSuitabilityInfo {
                    work_type: "Handiwork".into(),
                    level: 4,
                },
                WorkSuitabilityInfo {
                    work_type: "Mining".into(),
                    level: 3,
                },
                WorkSuitabilityInfo {
                    work_type: "Transport".into(),
                    level: 2,
                },
            ],
        },
        PalSpeciesInfo {
            id: "Frostallion".into(),
            name: "Frostallion".into(),
            element_types: vec!["Ice".into()],
            rarity: 10,
            hp_scaling: 140.0,
            attack_scaling: 140.0,
            defense_scaling: 135.0,
            work_suitabilities: vec![WorkSuitabilityInfo {
                work_type: "Cooling".into(),
                level: 4,
            }],
        },
        PalSpeciesInfo {
            id: "Jormuntide".into(),
            name: "Jormuntide".into(),
            element_types: vec!["Dragon".into(), "Water".into()],
            rarity: 9,
            hp_scaling: 130.0,
            attack_scaling: 150.0,
            defense_scaling: 100.0,
            work_suitabilities: vec![WorkSuitabilityInfo {
                work_type: "Watering".into(),
                level: 4,
            }],
        },
        PalSpeciesInfo {
            id: "Lamball".into(),
            name: "Lamball".into(),
            element_types: vec!["Neutral".into()],
            rarity: 1,
            hp_scaling: 70.0,
            attack_scaling: 70.0,
            defense_scaling: 70.0,
            work_suitabilities: vec![
                WorkSuitabilityInfo {
                    work_type: "Handiwork".into(),
                    level: 1,
                },
                WorkSuitabilityInfo {
                    work_type: "Transport".into(),
                    level: 1,
                },
                WorkSuitabilityInfo {
                    work_type: "Farming".into(),
                    level: 1,
                },
            ],
        },
    ]
}

fn default_items() -> Vec<ItemInfo> {
    vec![
        ItemInfo {
            id: "PalSphere".into(),
            name: "Pal Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 1,
        },
        ItemInfo {
            id: "MegaSphere".into(),
            name: "Mega Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 2,
        },
        ItemInfo {
            id: "GigaSphere".into(),
            name: "Giga Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 3,
        },
        ItemInfo {
            id: "HyperSphere".into(),
            name: "Hyper Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 4,
        },
        ItemInfo {
            id: "UltraSphere".into(),
            name: "Ultra Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 5,
        },
        ItemInfo {
            id: "LegendarySphere".into(),
            name: "Legendary Sphere".into(),
            category: "Sphere".into(),
            max_stack: 9999,
            rarity: 6,
        },
        ItemInfo {
            id: "Cake".into(),
            name: "Cake".into(),
            category: "Food".into(),
            max_stack: 9999,
            rarity: 3,
        },
        ItemInfo {
            id: "Wood".into(),
            name: "Wood".into(),
            category: "Material".into(),
            max_stack: 9999,
            rarity: 1,
        },
        ItemInfo {
            id: "Stone".into(),
            name: "Stone".into(),
            category: "Material".into(),
            max_stack: 9999,
            rarity: 1,
        },
        ItemInfo {
            id: "Pal_crystal_and_metal".into(),
            name: "Pal Metal Ingot".into(),
            category: "Material".into(),
            max_stack: 9999,
            rarity: 4,
        },
    ]
}

fn default_passives() -> Vec<PassiveSkillInfo> {
    vec![
        PassiveSkillInfo {
            id: "Legend".into(),
            name: "Legend".into(),
            tier: 3,
            description: "Attack +20%, Defense +20%, Movement Speed +15%".into(),
        },
        PassiveSkillInfo {
            id: "Musclehead".into(),
            name: "Musclehead".into(),
            tier: 3,
            description: "Attack +30%, Work Speed -50%".into(),
        },
        PassiveSkillInfo {
            id: "Ferocious".into(),
            name: "Ferocious".into(),
            tier: 3,
            description: "Attack +20%".into(),
        },
        PassiveSkillInfo {
            id: "BurlyBody".into(),
            name: "Burly Body".into(),
            tier: 3,
            description: "Defense +20%".into(),
        },
        PassiveSkillInfo {
            id: "Runner".into(),
            name: "Runner".into(),
            tier: 2,
            description: "Movement Speed +20%".into(),
        },
        PassiveSkillInfo {
            id: "Swift".into(),
            name: "Swift".into(),
            tier: 3,
            description: "Movement Speed +30%".into(),
        },
        PassiveSkillInfo {
            id: "Artisan".into(),
            name: "Artisan".into(),
            tier: 3,
            description: "Work Speed +50%".into(),
        },
        PassiveSkillInfo {
            id: "WorkSlave".into(),
            name: "Work Slave".into(),
            tier: 1,
            description: "Work Speed +30%, Attack -30%".into(),
        },
    ]
}

fn default_active_skills() -> Vec<ActiveSkillInfo> {
    vec![
        ActiveSkillInfo {
            id: "DragonMeteor".into(),
            name: "Dragon Meteor".into(),
            element: "Dragon".into(),
            power: 150,
            cooldown_seconds: 55,
        },
        ActiveSkillInfo {
            id: "FireBall".into(),
            name: "Fire Ball".into(),
            element: "Fire".into(),
            power: 150,
            cooldown_seconds: 55,
        },
        ActiveSkillInfo {
            id: "HydroStream".into(),
            name: "Hydro Stream".into(),
            element: "Water".into(),
            power: 150,
            cooldown_seconds: 55,
        },
        ActiveSkillInfo {
            id: "SolarBeam".into(),
            name: "Solar Beam".into(),
            element: "Grass".into(),
            power: 150,
            cooldown_seconds: 55,
        },
        ActiveSkillInfo {
            id: "BlizzardSpike".into(),
            name: "Blizzard Spike".into(),
            element: "Ice".into(),
            power: 130,
            cooldown_seconds: 45,
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_catalog_passes_integrity_validation() {
        let catalog = GameCatalog::new();
        assert!(catalog.validate_integrity().is_ok());
        assert!(!catalog.pals.is_empty());
        assert!(!catalog.items.is_empty());
        assert!(!catalog.passives.is_empty());
        assert!(!catalog.active_skills.is_empty());
    }

    #[test]
    fn integrity_validation_rejects_duplicate_ids_and_schema_drift() {
        let mut catalog = GameCatalog::new();
        catalog.items.push(catalog.items[0].clone());
        catalog.pals[0].work_suitabilities[0].level = 5;
        catalog.active_skills[0].cooldown_seconds = -1;

        let errors = catalog.validate_integrity().unwrap_err();
        assert!(errors.iter().any(|error| error.contains("duplicate ID")));
        assert!(errors
            .iter()
            .any(|error| error.contains("work suitability")));
        assert!(errors.iter().any(|error| error.contains("active_skills")));
    }
}
