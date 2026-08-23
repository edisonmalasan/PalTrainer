//! FArchive-style binary primitives over a GVAS payload.
//!
//! Property-tree reading lives in [`super::read_properties`].

use std::collections::HashMap;

use crate::error::SaveError;

use super::uuid::PalUuid;

#[derive(Debug)]
pub struct FArchiveReader<'a> {
    data: &'a [u8],
    pos: usize,
    /// Path-keyed struct layout hints for ambiguous map keys/values.
    pub type_hints: HashMap<String, String>,
}

impl<'a> FArchiveReader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self {
            data,
            pos: 0,
            type_hints: HashMap::new(),
        }
    }

    pub fn with_type_hints(data: &'a [u8], type_hints: HashMap<String, String>) -> Self {
        Self {
            data,
            pos: 0,
            type_hints,
        }
    }

    pub(crate) fn take(&mut self, n: usize) -> Result<&'a [u8], SaveError> {
        if self.pos + n > self.data.len() {
            return Err(SaveError::UnexpectedEof {
                offset: self.pos,
                needed: n,
            });
        }
        let slice = &self.data[self.pos..self.pos + n];
        self.pos += n;
        Ok(slice)
    }

    pub fn position(&self) -> usize {
        self.pos
    }

    pub fn eof(&self) -> bool {
        self.pos >= self.data.len()
    }

    /// Consumes and returns every remaining byte (the GVAS trailer).
    pub fn read_to_end(&mut self) -> Vec<u8> {
        let rest = self.data[self.pos..].to_vec();
        self.pos = self.data.len();
        rest
    }

    pub fn u8(&mut self) -> Result<u8, SaveError> {
        Ok(self.take(1)?[0])
    }

    pub fn bool(&mut self) -> Result<bool, SaveError> {
        Ok(self.u8()? != 0)
    }

    pub fn i16(&mut self) -> Result<i16, SaveError> {
        let b = self.take(2)?;
        Ok(i16::from_le_bytes([b[0], b[1]]))
    }

    pub fn u16(&mut self) -> Result<u16, SaveError> {
        let b = self.take(2)?;
        Ok(u16::from_le_bytes([b[0], b[1]]))
    }

    pub fn i32(&mut self) -> Result<i32, SaveError> {
        let b = self.take(4)?;
        Ok(i32::from_le_bytes(b.try_into().expect("4 bytes")))
    }

    pub fn u32(&mut self) -> Result<u32, SaveError> {
        let b = self.take(4)?;
        Ok(u32::from_le_bytes(b.try_into().expect("4 bytes")))
    }

    pub fn i64(&mut self) -> Result<i64, SaveError> {
        let b = self.take(8)?;
        Ok(i64::from_le_bytes(b.try_into().expect("8 bytes")))
    }

    pub fn u64(&mut self) -> Result<u64, SaveError> {
        let b = self.take(8)?;
        Ok(u64::from_le_bytes(b.try_into().expect("8 bytes")))
    }

    pub fn f32(&mut self) -> Result<f32, SaveError> {
        let b = self.take(4)?;
        Ok(f32::from_le_bytes(b.try_into().expect("4 bytes")))
    }

    pub fn f64(&mut self) -> Result<f64, SaveError> {
        let b = self.take(8)?;
        Ok(f64::from_le_bytes(b.try_into().expect("8 bytes")))
    }

    /// Reads a UE string: positive length = ASCII/UTF-8 bytes with NUL,
    /// negative length = UTF-16-LE code units with a 2-byte NUL.
    pub fn fstring(&mut self) -> Result<String, SaveError> {
        let offset = self.pos;
        let size = self.i32()?;
        if size == 0 {
            return Ok(String::new());
        }
        if size < 0 {
            // Negative: UTF-16-LE code units including the trailing NUL.
            let units = size.unsigned_abs() as usize;
            let bytes = self.take(units * 2)?;
            let Some(without_nul) = bytes.get(..units * 2 - 2) else {
                return Err(SaveError::InvalidFString { offset });
            };
            let pairs: Vec<u16> = without_nul
                .chunks_exact(2)
                .map(|p| u16::from_le_bytes([p[0], p[1]]))
                .collect();
            return String::from_utf16(&pairs).map_err(|_| SaveError::InvalidFString { offset });
        }
        let bytes = self.take(size as usize)?;
        let Some(without_nul) = bytes.get(..size as usize - 1) else {
            return Err(SaveError::InvalidFString { offset });
        };
        String::from_utf8(without_nul.to_vec()).map_err(|_| SaveError::InvalidFString { offset })
    }

    pub fn guid(&mut self) -> Result<PalUuid, SaveError> {
        let b = self.take(16)?;
        Ok(PalUuid::from_raw(b.try_into().expect("16 bytes")))
    }

    pub fn optional_guid(&mut self) -> Result<Option<PalUuid>, SaveError> {
        if self.bool()? {
            Ok(Some(self.guid()?))
        } else {
            Ok(None)
        }
    }

    pub(crate) fn type_or(&self, path: &str, default: &str) -> String {
        self.type_hints
            .get(path)
            .cloned()
            .unwrap_or_else(|| default.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn primitives_roundtrip_through_manual_bytes() {
        let mut buf = Vec::new();
        buf.extend_from_slice(&7u32.to_le_bytes());
        buf.extend_from_slice(&(-3i64).to_le_bytes());
        buf.extend_from_slice(&1.5f32.to_le_bytes());
        buf.extend_from_slice(&2.25f64.to_le_bytes());

        let mut r = FArchiveReader::new(&buf);
        assert_eq!(r.u32().unwrap(), 7);
        assert_eq!(r.i64().unwrap(), -3);
        assert_eq!(r.f32().unwrap(), 1.5);
        assert_eq!(r.f64().unwrap(), 2.25);
        assert!(r.eof());
    }

    #[test]
    fn reading_past_end_is_an_error() {
        let mut r = FArchiveReader::new(&[0u8; 3]);
        assert!(matches!(
            r.i32().unwrap_err(),
            SaveError::UnexpectedEof { offset: 0, needed: 4 }
        ));
    }

    #[test]
    fn fstring_ascii_and_empty() {
        // "Pal" with NUL terminator, length 4.
        let data = [4, 0, 0, 0, b'P', b'a', b'l', 0];
        let mut r = FArchiveReader::new(&data);
        assert_eq!(r.fstring().unwrap(), "Pal");

        let data = [0, 0, 0, 0];
        let mut r = FArchiveReader::new(&data);
        assert_eq!(r.fstring().unwrap(), "");
    }

    #[test]
    fn fstring_utf16_with_surrogate_pair() {
        // "fox emoji" (U+1F98A) as UTF-16-LE surrogate pair + NUL terminator.
        let text_bytes: [u8; 6] = [0x3E, 0xD8, 0x9A, 0xDE, 0x00, 0x00];
        let mut data = Vec::new();
        data.extend_from_slice(&(-3i32).to_le_bytes()); // 2 units + NUL
        data.extend_from_slice(&text_bytes);

        let mut r = FArchiveReader::new(&data);
        assert_eq!(r.fstring().unwrap(), "\u{1F98A}");
    }

    #[test]
    fn guid_reads_storage_order_bytes_verbatim() {
        let raw: [u8; 16] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
        let mut r = FArchiveReader::new(&raw);
        assert_eq!(r.guid().unwrap().raw_bytes, raw);
    }

    #[test]
    fn optional_guid_absent_and_present() {
        let absent = {
            let mut data = Vec::new();
            data.push(0);
            data.extend_from_slice(&42i32.to_le_bytes());
            data
        };
        let mut r = FArchiveReader::new(&absent);
        assert_eq!(r.optional_guid().unwrap(), None);
        assert_eq!(r.i32().unwrap(), 42);

        let present = {
            let mut data = Vec::new();
            data.push(1);
            data.extend_from_slice(&[0xAB; 16]);
            data
        };
        let mut r = FArchiveReader::new(&present);
        let guid = r.optional_guid().unwrap().unwrap();
        assert!(guid.raw_bytes.iter().all(|&b| b == 0xAB));
    }

    #[test]
    fn read_to_end_consumes_trailer() {
        let mut r = FArchiveReader::new(&[9, 8, 7]);
        assert_eq!(r.read_to_end(), vec![9, 8, 7]);
        assert!(r.eof());
    }
}
