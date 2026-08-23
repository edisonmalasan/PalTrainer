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
