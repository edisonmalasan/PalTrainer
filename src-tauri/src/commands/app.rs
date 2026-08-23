use serde::Serialize;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AppInfo {
    name: &'static str,
    version: &'static str,
    tauri_version: &'static str,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FeatureFlag {
    id: &'static str,
    label: &'static str,
    enabled: bool,
    description: &'static str,
}

#[tauri::command]
pub fn get_app_info() -> AppInfo {
    AppInfo {
        name: "PalTrainer",
        version: env!("CARGO_PKG_VERSION"),
        tauri_version: "2",
    }
}

#[tauri::command]
pub fn get_feature_flags() -> Vec<FeatureFlag> {
    vec![
        FeatureFlag {
            id: "save_session",
            label: "Save sessions",
            enabled: false,
            description: "Locked until the Rust parser, backups, and path policy exist.",
        },
        FeatureFlag {
            id: "advanced_tools",
            label: "Advanced tools",
            enabled: false,
            description: "Future raw JSON and recovery workflows require stronger guardrails.",
        },
        FeatureFlag {
            id: "xgp_tools",
            label: "XGP tools",
            enabled: false,
            description: "Windows-only platform tools are planned for a later phase.",
        },
    ]
}
