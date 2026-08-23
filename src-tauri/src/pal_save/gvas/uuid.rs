//! Palworld/Unreal GUID handling.
//!
//! GVAS stores GUIDs as 16 raw bytes in a mixed-endian layout. The first
//! three groups are little-endian, the last two are big-endian. `PalUuid`
//! keeps the exact raw bytes so roundtrips stay byte-perfect; display and
//! parsing use the canonical dashed hex form.

use std::fmt;

/// Canonical display format used by the reference tooling.
///
/// Storage order packs the first three groups little-endian and the rest
/// as big-endian pairs/quads; rendering them this way reproduces the
/// original canonical dashed UUID string.
fn format_groups(b: &[u8; 16]) -> String {
    format!(
        "{:08x}-{:04x}-{:04x}-{:04x}-{:04x}{:08x}",
        u32::from_le_bytes([b[0], b[1], b[2], b[3]]),
        u16::from_be_bytes([b[7], b[6]]),
        u16::from_be_bytes([b[5], b[4]]),
        u16::from_be_bytes([b[11], b[10]]),
        u16::from_be_bytes([b[9], b[8]]),
        u32::from_be_bytes([b[15], b[14], b[13], b[12]]),
    )
}

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct PalUuid {
    pub raw_bytes: [u8; 16],
}

impl PalUuid {
    pub fn from_raw(bytes: [u8; 16]) -> Self {
        Self { raw_bytes: bytes }
    }

    /// Parses a canonical dashed UUID string into storage-order raw bytes.
    pub fn parse(s: &str) -> Option<Self> {
        let clean: String = s.chars().filter(|&c| c != '-').collect();
        if clean.len() != 32 || !clean.chars().all(|c| c.is_ascii_hexdigit()) {
            return None;
        }
        // Canonical (big-endian) UUID byte order.
        let mut canonical = [0u8; 16];
        for (i, chunk) in clean.as_bytes().chunks(2).enumerate() {
            let hi = (chunk[0] as char).to_digit(16)? as u8;
            let lo = (chunk[1] as char).to_digit(16)? as u8;
            canonical[i] = hi << 4 | lo;
        }
        Some(Self::from_canonical(canonical))
    }

    /// Converts canonical (big-endian) UUID bytes to GVAS storage order.
    pub fn from_canonical(b: [u8; 16]) -> Self {
        Self {
            raw_bytes: [
                b[3], b[2], b[1], b[0], b[7], b[6], b[5], b[4], b[11], b[10], b[9], b[8], b[15],
                b[14], b[13], b[12],
            ],
        }
    }

    /// Converts GVAS storage-order bytes back to canonical UUID order.
    pub fn to_canonical(&self) -> [u8; 16] {
        PalUuid::from_canonical(self.raw_bytes).raw_bytes
    }

    /// Lowercase hex without dashes, for consistent UID comparison.
    pub fn normalized(&self) -> String {
        self.raw_bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

impl fmt::Display for PalUuid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&format_groups(&self.raw_bytes))
    }
}

impl fmt::Debug for PalUuid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PalUuid({})", self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE_RAW: [u8; 16] = [
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
        0x10,
    ];

    #[test]
    fn display_uses_mixed_endian_layout() {
        let uuid = PalUuid::from_raw(SAMPLE_RAW);
        assert_eq!(uuid.to_string(), "04030201-0605-0807-0c0b-0a09100f0e0d");
    }

    #[test]
    fn parse_roundtrips_display() {
        let text = "04030201-0605-0807-0c0b-0a09100f0e0d";
        let uuid = PalUuid::parse(text).unwrap();
        assert_eq!(uuid.raw_bytes, SAMPLE_RAW);
        assert_eq!(uuid.to_string(), text);
    }

    #[test]
    fn canonical_conversion_is_involutive() {
        let uuid = PalUuid::from_raw(SAMPLE_RAW);
        let canonical = uuid.to_canonical();
        assert_eq!(PalUuid::from_canonical(canonical), uuid);
    }

    #[test]
    fn normalized_strips_dashes_and_lowercases() {
        let uuid = PalUuid::parse("04030201-0605-0807-090A-0B0C0D0E0F10").unwrap();
        assert_eq!(uuid.normalized(), "0102030405060708090a0b0c0d0e0f10");
    }

    #[test]
    fn zero_guid_is_stable() {
        let uuid = PalUuid::parse("00000000-0000-0000-0000-000000000000").unwrap();
        assert!(uuid.raw_bytes.iter().all(|&b| b == 0));
        assert_eq!(uuid.to_string(), "00000000-0000-0000-0000-000000000000");
    }

    #[test]
    fn rejects_invalid_input() {
        assert!(PalUuid::parse("not-a-uuid").is_none());
        assert!(PalUuid::parse("04030201-0605-0807-090a-0b0c0d0e0f1").is_none());
    }
}
