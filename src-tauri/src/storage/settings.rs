use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

use crate::error::AppError;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppSettings {
    #[serde(default = "default_theme")]
    pub theme: ThemePreference,
    #[serde(default = "default_language")]
    pub language: LanguagePreference,
    #[serde(default)]
    pub show_advanced_tools: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ThemePreference {
    System,
    Light,
    Dark,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum LanguagePreference {
    En,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            theme: default_theme(),
            language: default_language(),
            show_advanced_tools: false,
        }
    }
}

pub fn read_settings(app: &AppHandle) -> Result<AppSettings, AppError> {
    let path = settings_path(app)?;
    read_settings_from_path(&path)
}

pub fn write_settings(app: &AppHandle, settings: &AppSettings) -> Result<(), AppError> {
    let path = settings_path(app)?;
    write_settings_to_path(&path, settings)
}

fn settings_path(app: &AppHandle) -> Result<PathBuf, AppError> {
    let config_dir = app.path().app_config_dir().map_err(|error| {
        AppError::io(
            "settings_dir_unavailable",
            "Could not locate the PalTrainer settings directory.",
            error,
        )
    })?;

    Ok(config_dir.join("settings.json"))
}

fn read_settings_from_path(path: &Path) -> Result<AppSettings, AppError> {
    if !path.exists() {
        return Ok(AppSettings::default());
    }

    let text = fs::read_to_string(path).map_err(|error| {
        AppError::io(
            "settings_read_failed",
            "Could not read PalTrainer settings.",
            error,
        )
    })?;

    serde_json::from_str(&text).map_err(|error| {
        AppError::io(
            "settings_parse_failed",
            "PalTrainer settings are not valid JSON.",
            error,
        )
    })
}

fn write_settings_to_path(path: &Path, settings: &AppSettings) -> Result<(), AppError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            AppError::io(
                "settings_dir_create_failed",
                "Could not create the PalTrainer settings directory.",
                error,
            )
        })?;
    }

    let text = serde_json::to_string_pretty(settings).map_err(|error| {
        AppError::io(
            "settings_serialize_failed",
            "Could not serialize PalTrainer settings.",
            error,
        )
    })?;

    fs::write(path, text).map_err(|error| {
        AppError::io(
            "settings_write_failed",
            "Could not write PalTrainer settings.",
            error,
        )
    })
}

fn default_theme() -> ThemePreference {
    ThemePreference::System
}

fn default_language() -> LanguagePreference {
    LanguagePreference::En
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_settings_match_frontend_contract() {
        assert_eq!(
            AppSettings::default(),
            AppSettings {
                theme: ThemePreference::System,
                language: LanguagePreference::En,
                show_advanced_tools: false,
            },
        );
    }

    #[test]
    fn reads_missing_settings_as_defaults() {
        let temp = tempfile::tempdir().expect("temp dir");
        let path = temp.path().join("settings.json");

        assert_eq!(
            read_settings_from_path(&path).expect("settings"),
            AppSettings::default(),
        );
    }

    #[test]
    fn writes_and_reads_settings_file() {
        let temp = tempfile::tempdir().expect("temp dir");
        let path = temp.path().join("nested").join("settings.json");
        let settings = AppSettings {
            theme: ThemePreference::Dark,
            language: LanguagePreference::En,
            show_advanced_tools: true,
        };

        write_settings_to_path(&path, &settings).expect("write settings");

        assert_eq!(
            read_settings_from_path(&path).expect("read settings"),
            settings
        );
    }
}
