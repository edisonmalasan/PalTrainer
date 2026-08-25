//! Outer `.sav` container header.
//!
//! Layout: `uncompressed_len (4B, LE) | compressed_len (4B, LE) | magic (3B)
//! | save_type (1B)`. CNK saves carry a nested second header at offset
//! 12..24 whose fields supersede the outer ones; payload data starts at
//! offset 24 for CNK and offset 12 otherwise.

use crate::error::SaveError;

pub const MAGIC_CNK: [u8; 3] = *b"CNK";
pub const MAGIC_PLM: [u8; 3] = *b"PlM";
pub const MAGIC_PLZ: [u8; 3] = *b"PlZ";

const HEADER_SIZE: usize = 12;
/// CNK nests a second 12-byte header before the compressed payload.
const NESTED_HEADER_SIZE: usize = 24;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SaveType {
    Cnk,
    Plm,
    Plz,
}

impl SaveType {
    pub fn from_byte(byte: u8, magic: [u8; 3]) -> Result<Self, SaveError> {
        match byte {
            0x30 => Ok(SaveType::Cnk),
            0x31 => Ok(SaveType::Plm),
            0x32 => Ok(SaveType::Plz),
            _ => Err(SaveError::UnknownSaveType {
                magic,
                save_type: byte,
            }),
        }
    }

    pub fn to_byte(self) -> u8 {
        match self {
            SaveType::Cnk => 0x30,
            SaveType::Plm => 0x31,
            SaveType::Plz => 0x32,
        }
    }

    pub fn magic(self) -> [u8; 3] {
        match self {
            SaveType::Cnk => MAGIC_CNK,
            SaveType::Plm => MAGIC_PLM,
            SaveType::Plz => MAGIC_PLZ,
        }
    }

    /// Label used in user-facing error messages.
    pub fn label(self) -> &'static str {
        match self {
            SaveType::Cnk => "CNK",
            SaveType::Plm => "PLM",
            SaveType::Plz => "PLZ",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct SavHeader {
    pub uncompressed_len: u32,
    pub compressed_len: u32,
    pub save_type: SaveType,
    /// Offset of the compressed payload within the `.sav` file
    /// (12 for PLZ/PLM, 24 for CNK with its nested header).
    pub data_offset: usize,
}

impl SavHeader {
    /// Parses the outer header, resolving the CNK nested header when present.
    ///
    /// For CNK files the nested header's lengths and save type are
    /// authoritative; the outer lengths are ignored (they do not reliably
    /// describe the payload).
    pub fn parse(data: &[u8]) -> Result<Self, SaveError> {
        if data.len() < HEADER_SIZE {
            return Err(SaveError::HeaderTooSmall {
                actual: data.len(),
                needed: HEADER_SIZE,
            });
        }

        let mut uncompressed_len = u32::from_le_bytes(data[0..4].try_into().expect("4 bytes"));
        let mut compressed_len = u32::from_le_bytes(data[4..8].try_into().expect("4 bytes"));
        let mut magic: [u8; 3] = data[8..11].try_into().expect("3 bytes");
        let mut save_type = SaveType::from_byte(data[11], magic)?;
        let mut data_offset = HEADER_SIZE;

        if magic == MAGIC_CNK {
            if data.len() < NESTED_HEADER_SIZE {
                return Err(SaveError::HeaderTooSmall {
                    actual: data.len(),
                    needed: NESTED_HEADER_SIZE,
                });
            }
            // The nested header replaces the outer values entirely.
            uncompressed_len = u32::from_le_bytes(data[12..16].try_into().expect("4 bytes"));
            compressed_len = u32::from_le_bytes(data[16..20].try_into().expect("4 bytes"));
            magic = data[20..23].try_into().expect("3 bytes");
            save_type = SaveType::from_byte(data[23], magic)?;
            data_offset = NESTED_HEADER_SIZE;
        }

        match magic {
            MAGIC_PLZ | MAGIC_PLM | MAGIC_CNK => {}
            other => {
                return Err(SaveError::UnknownMagic {
                    magic: other,
                    offset: if data_offset == HEADER_SIZE { 8 } else { 20 },
                });
            }
        }

        Ok(Self {
            uncompressed_len,
            compressed_len,
            save_type,
            data_offset,
        })
    }

    /// Builds a flat `.sav` container from a single-pass compressed payload.
    ///
    /// `compressed_len` is the length recorded in the header. For PLZ this is
    /// the size after the first zlib pass, while the stored payload is the
    /// double-compressed stream — matching the reference tool behavior.
    pub fn build(
        compressed_data: &[u8],
        uncompressed_len: u32,
        compressed_len: u32,
        save_type: SaveType,
    ) -> Vec<u8> {
        let mut out = Vec::with_capacity(HEADER_SIZE + compressed_data.len());
        out.extend_from_slice(&uncompressed_len.to_le_bytes());
        out.extend_from_slice(&compressed_len.to_le_bytes());
        out.extend_from_slice(&save_type.magic());
        out.push(save_type.to_byte());
        out.extend_from_slice(compressed_data);
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn save_type_roundtrips_through_bytes_and_magic() {
        for st in [SaveType::Cnk, SaveType::Plm, SaveType::Plz] {
            assert_eq!(SaveType::from_byte(st.to_byte(), st.magic()).unwrap(), st);
            assert_eq!(st.magic().len(), 3);
        }
    }

    #[test]
    fn unknown_save_type_is_rejected() {
        let err = SaveType::from_byte(0x99, MAGIC_PLZ).unwrap_err();
        assert!(matches!(
            err,
            SaveError::UnknownSaveType {
                save_type: 0x99,
                ..
            }
        ));
    }

    #[test]
    fn parse_rejects_short_input() {
        let err = SavHeader::parse(&[0u8; 11]).unwrap_err();
        assert!(matches!(
            err,
            SaveError::HeaderTooSmall {
                actual: 11,
                needed: 12
            }
        ));
    }

    #[test]
    fn parse_plz_header() {
        let mut data = Vec::new();
        data.extend_from_slice(&100u32.to_le_bytes());
        data.extend_from_slice(&50u32.to_le_bytes());
        data.extend_from_slice(&MAGIC_PLZ);
        data.push(0x32);
        data.extend_from_slice(&[0u8; 16]);

        let header = SavHeader::parse(&data).unwrap();
        assert_eq!(header.save_type, SaveType::Plz);
        assert_eq!(header.uncompressed_len, 100);
        assert_eq!(header.compressed_len, 50);
        assert_eq!(header.data_offset, 12);
    }

    #[test]
    fn parse_cnk_uses_nested_header_and_ignores_outer_lengths() {
        let mut data = Vec::new();
        // Deliberately bogus outer values to prove they are ignored.
        data.extend_from_slice(&[0xFFu8; 8]);
        data.extend_from_slice(&MAGIC_CNK);
        data.push(0x30);
        // Nested header.
        data.extend_from_slice(&200u32.to_le_bytes());
        data.extend_from_slice(&120u32.to_le_bytes());
        data.extend_from_slice(&MAGIC_PLZ);
        data.push(0x30);
        data.extend_from_slice(&[0u8; 8]);

        let header = SavHeader::parse(&data).unwrap();
        assert_eq!(header.save_type, SaveType::Cnk);
        assert_eq!(header.uncompressed_len, 200);
        assert_eq!(header.compressed_len, 120);
        assert_eq!(header.data_offset, 24);
    }

    #[test]
    fn parse_cnk_with_unknown_inner_magic_fails() {
        let mut data = Vec::new();
        data.extend_from_slice(&[0u8; 8]);
        data.extend_from_slice(&MAGIC_CNK);
        data.push(0x30);
        // Nested header: lengths, then the bogus magic at 20..23.
        data.extend_from_slice(&[0u8; 8]);
        data.extend_from_slice(b"XYZ");
        data.push(0x30);

        let err = SavHeader::parse(&data).unwrap_err();
        assert!(matches!(
            err,
            SaveError::UnknownMagic {
                magic,
                offset: 20
            }
            if magic == *b"XYZ"
        ));
    }

    #[test]
    fn build_produces_reference_layout() {
        let sav = SavHeader::build(&[1, 2, 3], 10, 3, SaveType::Plz);
        assert_eq!(
            &sav[..12],
            &[
                10, 0, 0, 0, // uncompressed_len
                3, 0, 0, 0, // compressed_len
                b'P', b'l', b'Z', 0x32,
            ]
        );
        assert_eq!(&sav[12..], &[1, 2, 3]);
    }

    #[test]
    fn parse_plm_header() {
        let mut data = Vec::new();
        data.extend_from_slice(&500u32.to_le_bytes());
        data.extend_from_slice(&250u32.to_le_bytes());
        data.extend_from_slice(&MAGIC_PLM);
        data.push(0x31);
        data.extend_from_slice(&[0u8; 10]);

        let header = SavHeader::parse(&data).unwrap();
        assert_eq!(header.save_type, SaveType::Plm);
        assert_eq!(header.uncompressed_len, 500);
        assert_eq!(header.compressed_len, 250);
        assert_eq!(header.data_offset, 12);
    }

    #[test]
    fn parse_unknown_outer_magic_fails() {
        let mut data = Vec::new();
        data.extend_from_slice(&100u32.to_le_bytes());
        data.extend_from_slice(&50u32.to_le_bytes());
        data.extend_from_slice(b"BAD");
        data.push(0x32);
        data.extend_from_slice(&[0u8; 10]);

        let err = SavHeader::parse(&data).unwrap_err();
        assert!(matches!(
            err,
            SaveError::UnknownMagic {
                magic,
                offset: 8
            }
            if magic == *b"BAD"
        ));
    }
}
