//! Central dispatch for custom property codecs.

use std::collections::HashMap;
use std::sync::OnceLock;

use crate::error::SaveError;
use crate::pal_save::gvas::model::PropertyValue;
use crate::pal_save::gvas::reader::FArchiveReader;

/// Returns the type hint map (path -> expected inner struct type).
/// Used to disambiguate map/array structs when the UE header is generic.
pub fn get_type_hints() -> &'static HashMap<String, String> {
    static HINTS: OnceLock<HashMap<String, String>> = OnceLock::new();
    HINTS.get_or_init(|| {
        let mut m = HashMap::new();
        m.insert(
            ".worldSaveData.CharacterSaveParameterMap.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.MapObjectSaveData.MapObjectSaveData.Model.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.FoliageGridSaveDataMap.Value.ModelMap.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.BaseCampSaveData.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.ItemContainerSaveData.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.CharacterContainerSaveData.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.GroupSaveDataMap.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".worldSaveData.WorkSaveData.Value.RawData".to_string(),
            "ArrayProperty".to_string(),
        );
        m.insert(
            ".SaveData.Local_MaxFriendshipPalIds.Key".to_string(),
            "StructProperty".to_string(),
        );
        m.insert(
            ".SaveData.Local_MaxFriendshipPalIds.Value".to_string(),
            "IntProperty".to_string(),
        );
        m
    })
}

/// Dispatches decoding to custom rawdata decoders if the path matches a known
/// custom property. Returns Ok(Some(value)) if handled, or Ok(None) if it
/// should fall back to the standard generic property reader.
pub fn decode_custom_property(
    _reader: &mut FArchiveReader,
    _type_name: &str,
    _path: &str,
) -> Result<Option<PropertyValue>, SaveError> {
    // TODO: Wire up actual rawdata decoders here in Phase 2.
    // For now, we return None to let the standard parser try to handle it.
    Ok(None)
}
