//! Defines property paths that should be skipped (read as opaque bytes)
//! to speed up parsing and reduce memory for heavy, unedited data.

use std::collections::HashSet;
use std::sync::OnceLock;

pub fn get_skipped_properties() -> &'static HashSet<&'static str> {
    static SKIPPED: OnceLock<HashSet<&'static str>> = OnceLock::new();
    SKIPPED.get_or_init(|| {
        let mut set = HashSet::new();
        // Foliage is heavy and currently unused by the UI
        set.insert(".worldSaveData.FoliageGridSaveDataMap");
        set.insert(".worldSaveData.MapObjectSpawnerInStageSaveData");

        // Detailed map object transformations can be skipped for performance
        set.insert(".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldLocation");
        set.insert(".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldRotation");
        set.insert(".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldScale3D");
        set.insert(".worldSaveData.MapObjectSaveData.MapObjectSaveData.Model.EffectMap");
        set
    })
}

pub fn should_skip(path: &str) -> bool {
    get_skipped_properties().contains(path)
}

/// Full-decode profile for CLI/diagnostic use — nothing is skipped.
pub fn should_skip_cli(_path: &str) -> bool {
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gui_profile_has_six_paths() {
        assert_eq!(get_skipped_properties().len(), 6);
        assert!(should_skip(".worldSaveData.FoliageGridSaveDataMap"));
        assert!(should_skip(
            ".worldSaveData.MapObjectSpawnerInStageSaveData"
        ));
        assert!(should_skip(
            ".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldLocation"
        ));
    }

    #[test]
    fn cli_profile_skips_nothing() {
        assert!(!should_skip_cli(".worldSaveData.FoliageGridSaveDataMap"));
    }

    #[test]
    fn opaque_skipped_property_roundtrips_byte_exact() {
        use crate::pal_save::gvas::model::{Property, PropertyEntry, PropertyValue};
        use crate::pal_save::gvas::reader::FArchiveReader;
        use crate::pal_save::gvas::writer::FArchiveWriter;
        // Simulate heavy foliage path that should be skipped in GUI profile.
        let raw = vec![0xDE, 0xAD, 0xBE, 0xEF, 0x01, 0x02];
        let entry = PropertyEntry {
            name: "FoliageGridSaveDataMap".to_string(),
            property: Property {
                type_name: "ArrayProperty".to_string(),
                custom_type: None,
                value: PropertyValue::Opaque { raw: raw.clone() },
            },
        };
        let mut writer = FArchiveWriter::new();
        writer.write_properties(std::slice::from_ref(&entry));
        let bytes = writer.into_bytes();
        // Reader with path ".worldSaveData" should treat ".worldSaveData.FoliageGridSaveDataMap" as skipped.
        let mut reader = FArchiveReader::new(&bytes);
        let decoded = reader.properties_until_end(".worldSaveData").unwrap();
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0].name, "FoliageGridSaveDataMap");
        match &decoded[0].property.value {
            PropertyValue::Opaque { raw: decoded_raw } => assert_eq!(decoded_raw, &raw),
            other => panic!("expected Opaque, got {other:?}"),
        }
        // Full roundtrip via writer again should be byte-exact.
        let mut writer2 = FArchiveWriter::new();
        writer2.write_properties(&decoded);
        assert_eq!(writer2.into_bytes(), bytes);
    }
}
