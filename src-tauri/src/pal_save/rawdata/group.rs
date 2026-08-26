//! Codec for GroupSaveDataMap (Guilds)
//!
//! Preserves `V1_MARKER` handling per binary-schemas skill: the ~480B
//! pre-marker region must be kept byte-exact, marker is found dynamically.

use crate::error::SaveError;

/// `02 00 00 00 02 03 00 00 00 00` — new tail marker inserted after Sakurajima.
pub const V1_MARKER: &[u8] = &[0x02, 0x00, 0x00, 0x00, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00];

#[derive(Debug, Clone, PartialEq)]
pub struct GroupSaveData {
    /// Raw bytes as stored — kept for perfect roundtrip.
    pub trailing_bytes: Vec<u8>,
    /// Bytes before the dynamically found marker (preserved verbatim).
    pub pre_marker: Vec<u8>,
    /// Whether the marker was found.
    pub marker_found: bool,
    /// Bytes after the marker (v1/v2 tail, preserved).
    pub post_marker: Vec<u8>,
}

impl GroupSaveData {
    pub fn decode(data: &[u8]) -> Result<Self, SaveError> {
        if let Some(pos) = find_marker(data) {
            let pre = data[..pos].to_vec();
            let post = data[pos + V1_MARKER.len()..].to_vec();
            Ok(Self {
                trailing_bytes: data.to_vec(),
                pre_marker: pre,
                marker_found: true,
                post_marker: post,
            })
        } else {
            // Fallback v1: no marker — entire payload is opaque.
            Ok(Self {
                trailing_bytes: data.to_vec(),
                pre_marker: Vec::new(),
                marker_found: false,
                post_marker: data.to_vec(),
            })
        }
    }

    pub fn encode(&self) -> Result<Vec<u8>, SaveError> {
        // Byte-exact roundtrip: if we found a marker, reconstruct; else return raw.
        if self.marker_found {
            let mut out = Vec::with_capacity(
                self.pre_marker.len() + V1_MARKER.len() + self.post_marker.len(),
            );
            out.extend_from_slice(&self.pre_marker);
            out.extend_from_slice(V1_MARKER);
            out.extend_from_slice(&self.post_marker);
            // If original had extra bytes before marker due to newer version, they are in pre_marker
            // so roundtrip is guaranteed byte-for-byte.
            Ok(out)
        } else {
            Ok(self.trailing_bytes.clone())
        }
    }

    /// Attempt v2 tail decode first, fallback to v1 if it would overshoot.
    /// For hardening we only validate that post_marker can be probed without panic;
    /// real guild field parsing is handled in domain layer.
    pub fn try_v2_then_v1(&self) -> bool {
        // Stub probe: v2 expects at least a guild_chest_allowed_roles array header (4 bytes) + etc.
        // If post_marker is extremely short, treat as v1.
        self.marker_found && self.post_marker.len() >= 4
    }
}

fn find_marker(data: &[u8]) -> Option<usize> {
    data.windows(V1_MARKER.len()).position(|w| w == V1_MARKER)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_pre_marker_bytes_byte_exact() {
        let pre = vec![0xAA; 480];
        let post = vec![0xBB; 64];
        let mut raw = Vec::new();
        raw.extend_from_slice(&pre);
        raw.extend_from_slice(V1_MARKER);
        raw.extend_from_slice(&post);
        let decoded = GroupSaveData::decode(&raw).unwrap();
        assert_eq!(decoded.pre_marker, pre);
        assert!(decoded.marker_found);
        assert_eq!(decoded.post_marker, post);
        assert_eq!(decoded.encode().unwrap(), raw);
    }

    #[test]
    fn dynamically_finds_marker_not_at_zero() {
        let mut raw = vec![0xCC; 100];
        raw.extend_from_slice(V1_MARKER);
        raw.extend_from_slice(&[0x01, 0x02]);
        let d = GroupSaveData::decode(&raw).unwrap();
        assert_eq!(d.pre_marker.len(), 100);
        assert!(d.marker_found);
    }

    #[test]
    fn fallback_v1_when_no_marker() {
        let raw = vec![0x11; 64];
        let d = GroupSaveData::decode(&raw).unwrap();
        assert!(!d.marker_found);
        assert_eq!(d.encode().unwrap(), raw);
    }

    #[test]
    fn v2_probe_fallback_logic() {
        let mut raw = vec![0xAA; 10];
        raw.extend_from_slice(V1_MARKER);
        raw.extend_from_slice(&[0x01; 2]); // too short for v2
        let d = GroupSaveData::decode(&raw).unwrap();
        assert!(!d.try_v2_then_v1());
        let mut raw2 = vec![0xAA; 10];
        raw2.extend_from_slice(V1_MARKER);
        raw2.extend_from_slice(&[0x01; 8]);
        let d2 = GroupSaveData::decode(&raw2).unwrap();
        assert!(d2.try_v2_then_v1());
    }
}
