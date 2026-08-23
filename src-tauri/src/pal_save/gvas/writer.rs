//! FArchive-style binary writer producing GVAS payloads.
//!
//! Property-tree writing lives in [`super::write_properties`].

use super::uuid::PalUuid;

#[derive(Debug, Default)]
pub struct FArchiveWriter {
    buf: Vec<u8>,
}

impl FArchiveWriter {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn into_bytes(self) -> Vec<u8> {
        self.buf
    }

    pub fn position(&self) -> usize {
        self.buf.len()
    }

    pub(crate) fn write_bytes(&mut self, bytes: &[u8]) {
        self.buf.extend_from_slice(bytes);
    }

    /// Overwrites a previously reserved little-endian u64 slot (used for
    /// declared property sizes).
    pub(crate) fn patch_u64(&mut self, at: usize, value: u64) {
        self.buf[at..at + 8].copy_from_slice(&value.to_le_bytes());
    }

    pub fn u8(&mut self, v: u8) {
        self.buf.push(v);
    }

    pub fn bool(&mut self, v: bool) {
        self.buf.push(u8::from(v));
    }

    pub fn i16(&mut self, v: i16) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn u16(&mut self, v: u16) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn i32(&mut self, v: i32) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn u32(&mut self, v: u32) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn i64(&mut self, v: i64) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn u64(&mut self, v: u64) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn f32(&mut self, v: f32) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    pub fn f64(&mut self, v: f64) {
        self.buf.extend_from_slice(&v.to_le_bytes());
    }

    /// Writes a UE string: ASCII/UTF-8 when possible (positive length),
    /// otherwise UTF-16-LE with a negative length counting code units.
    /// Both forms include a NUL terminator outside the length-prefixed
    /// character count, matching the reference encoder.
    pub fn fstring(&mut self, s: &str) {
        if s.is_empty() {
            self.i32(0);
            return;
        }
        if s.is_ascii() {
            self.i32(s.len() as i32 + 1);
            self.buf.extend_from_slice(s.as_bytes());
            self.u8(0);
        } else {
            let units: Vec<u16> = s.encode_utf16().collect();
            self.i32(-(units.len() as i32 + 1));
            for unit in units {
                self.buf.extend_from_slice(&unit.to_le_bytes());
            }
            self.buf.extend_from_slice(&[0, 0]);
        }
    }

    pub fn guid(&mut self, g: &PalUuid) {
        self.buf.extend_from_slice(&g.raw_bytes);
    }

    pub fn optional_guid(&mut self, g: Option<&PalUuid>) {
        match g {
            None => self.bool(false),
            Some(guid) => {
                self.bool(true);
                self.guid(guid);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fstring_ascii_matches_reference_layout() {
        let mut w = FArchiveWriter::new();
        w.fstring("Pal");
        assert_eq!(w.into_bytes(), vec![4, 0, 0, 0, b'P', b'a', b'l', 0]);
    }

    #[test]
    fn fstring_empty_is_a_single_zero_i32() {
        let mut w = FArchiveWriter::new();
        w.fstring("");
        assert_eq!(w.into_bytes(), vec![0, 0, 0, 0]);
    }

    #[test]
    fn fstring_non_ascii_uses_negative_utf16_length() {
        let mut w = FArchiveWriter::new();
        w.fstring("\u{1F98A}"); // one code point, two UTF-16 units
        assert_eq!(
            w.into_bytes(),
            vec![
                0xFD, 0xFF, 0xFF, 0xFF, // -3
                0x3E, 0xD8, 0x9A, 0xDE, // surrogate pair LE
                0x00, 0x00,
            ]
        );
    }

    #[test]
    fn patch_u64_rewrites_reserved_slot() {
        let mut w = FArchiveWriter::new();
        let at = w.position();
        w.u64(0);
        w.u32(0xDEAD);
        w.patch_u64(at, 4);
        let out = w.into_bytes();
        assert_eq!(&out[..8], &4u64.to_le_bytes());
    }
}
