//! Map tile asset delivery over IPC.
//!
//! Tile assets are bundled with the app and served through this allowlisted
//! command; the frontend never resolves or reads asset paths itself.

use std::fs;
use std::path::PathBuf;

use serde::Serialize;
use tauri::Manager;

use crate::error::AppError;

/// Allowlisted map assets: (request name, bundled file name, MIME type).
/// Anything outside this table is rejected before any path is resolved.
const MAP_ASSETS: &[(&str, &str, &str)] = &[
    ("world-map", "world-map.png", "image/png"),
    ("treemap-overlay", "treemap-overlay.png", "image/png"),
];

#[derive(Clone, Debug, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MapAssetPayload {
    pub name: String,
    pub mime_type: String,
    pub base64_data: String,
}

const B64_ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

fn base64_encode(data: &[u8]) -> String {
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let b0 = chunk[0] as u32;
        let b1 = *chunk.get(1).unwrap_or(&0) as u32;
        let b2 = *chunk.get(2).unwrap_or(&0) as u32;
        let n = (b0 << 16) | (b1 << 8) | b2;
        out.push(B64_ALPHABET[((n >> 18) & 63) as usize] as char);
        out.push(B64_ALPHABET[((n >> 12) & 63) as usize] as char);
        out.push(if chunk.len() > 1 {
            B64_ALPHABET[((n >> 6) & 63) as usize] as char
        } else {
            '='
        });
        out.push(if chunk.len() > 2 {
            B64_ALPHABET[(n & 63) as usize] as char
        } else {
            '='
        });
    }
    out
}

fn lookup_asset(name: &str) -> Option<(&'static str, &'static str)> {
    MAP_ASSETS
        .iter()
        .find(|(requested, _, _)| *requested == name)
        .map(|(_, file_name, mime)| (*file_name, *mime))
}

fn dev_asset_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../resources/assets/map")
}

fn resolve_asset_path(app: &tauri::AppHandle, file_name: &str) -> Option<PathBuf> {
    let dev = dev_asset_dir().join(file_name);
    if dev.is_file() {
        return Some(dev);
    }
    let resource_dir = app.path().resource_dir().ok()?;
    for base in [
        resource_dir.join("resources").join("assets").join("map"),
        resource_dir.join("assets").join("map"),
        resource_dir,
    ] {
        let candidate = base.join(file_name);
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}

#[tauri::command]
pub fn get_map_asset(name: String, app: tauri::AppHandle) -> Result<MapAssetPayload, AppError> {
    let (file_name, mime_type) = lookup_asset(&name).ok_or_else(|| {
        AppError::new(
            "asset_not_allowed",
            format!("Map asset '{name}' is not in the allowlist."),
        )
    })?;

    let path = resolve_asset_path(&app, file_name).ok_or_else(|| {
        AppError::new(
            "asset_missing",
            format!("Map asset '{file_name}' is missing from the app resources."),
        )
    })?;

    let bytes = fs::read(&path).map_err(|e| {
        AppError::io(
            "asset_read_failed",
            format!("Failed to read map asset '{file_name}'."),
            e,
        )
    })?;

    Ok(MapAssetPayload {
        name,
        mime_type: mime_type.to_string(),
        base64_data: base64_encode(&bytes),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lookup_accepts_only_allowlisted_names() {
        assert_eq!(
            lookup_asset("world-map"),
            Some(("world-map.png", "image/png"))
        );
        assert_eq!(
            lookup_asset("treemap-overlay"),
            Some(("treemap-overlay.png", "image/png"))
        );
        assert_eq!(lookup_asset("../Cargo.toml"), None);
        assert_eq!(lookup_asset("catalog"), None);
        assert_eq!(lookup_asset(""), None);
    }

    #[test]
    fn base64_matches_known_vectors() {
        assert_eq!(base64_encode(b""), "");
        assert_eq!(base64_encode(b"f"), "Zg==");
        assert_eq!(base64_encode(b"fo"), "Zm8=");
        assert_eq!(base64_encode(b"foo"), "Zm9v");
        assert_eq!(base64_encode(b"foob"), "Zm9vYg==");
        assert_eq!(base64_encode(b"fooba"), "Zm9vYmE=");
        assert_eq!(base64_encode(b"foobar"), "Zm9vYmFy");
    }

    #[test]
    fn placeholder_tiles_exist_in_dev_resources() {
        // The dev fallback path must hold both bundled tiles so the canvas
        // renders outside of a packaged build.
        for (_, file_name, _) in MAP_ASSETS {
            let path = dev_asset_dir().join(file_name);
            assert!(path.is_file(), "missing dev map asset: {}", path.display());
            let bytes = fs::read(&path).expect("read map asset");
            assert!(bytes.len() > 8);
            assert_eq!(
                &bytes[0..8],
                &[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A],
                "{file_name} is not a PNG"
            );
        }
    }
}
