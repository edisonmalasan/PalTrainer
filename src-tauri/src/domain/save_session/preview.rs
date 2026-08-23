//! Mutation preview infrastructure for user-safe reviews before committing changes.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct EntityDiffSummary {
    pub entity_type: String,
    pub entity_id: String,
    pub label: String,
    pub change_description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MutationPreview {
    pub operation: String,
    pub target_save_root: PathBuf,
    pub entities_to_modify: Vec<EntityDiffSummary>,
    pub entities_to_delete: Vec<EntityDiffSummary>,
    pub files_to_modify: Vec<PathBuf>,
    pub files_to_delete: Vec<PathBuf>,
    pub backup_target: Option<PathBuf>,
    pub warnings: Vec<String>,
    pub is_safe: bool,
}

impl MutationPreview {
    pub fn new(operation: impl Into<String>, target_save_root: impl Into<PathBuf>) -> Self {
        Self {
            operation: operation.into(),
            target_save_root: target_save_root.into(),
            entities_to_modify: Vec::new(),
            entities_to_delete: Vec::new(),
            files_to_modify: Vec::new(),
            files_to_delete: Vec::new(),
            backup_target: None,
            warnings: Vec::new(),
            is_safe: true,
        }
    }

    pub fn add_modify_entity(
        &mut self,
        entity_type: impl Into<String>,
        entity_id: impl Into<String>,
        label: impl Into<String>,
        change_description: impl Into<String>,
    ) {
        self.entities_to_modify.push(EntityDiffSummary {
            entity_type: entity_type.into(),
            entity_id: entity_id.into(),
            label: label.into(),
            change_description: change_description.into(),
        });
    }

    pub fn add_delete_entity(
        &mut self,
        entity_type: impl Into<String>,
        entity_id: impl Into<String>,
        label: impl Into<String>,
        change_description: impl Into<String>,
    ) {
        self.entities_to_delete.push(EntityDiffSummary {
            entity_type: entity_type.into(),
            entity_id: entity_id.into(),
            label: label.into(),
            change_description: change_description.into(),
        });
    }

    pub fn add_warning(&mut self, warning: impl Into<String>) {
        self.warnings.push(warning.into());
    }

    pub fn mark_unsafe(&mut self) {
        self.is_safe = false;
    }
}
