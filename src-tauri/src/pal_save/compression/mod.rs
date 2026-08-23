//! Compression dispatch for `.sav` containers.
//!
//! - `PLZ` (0x32): double zlib — the only write path, matching the
//!   reference implementation.
//! - `CNK` (0x30): single zlib stream after a nested header (data at
//!   offset 24).
//! - `PLM` (0x31): Oodle/Kraken — decompression is not integrated yet and
//!   reports a typed error instead of failing opaquely.

use std::io::{Read, Write};

use flate2::read::ZlibDecoder;
use flate2::write::ZlibEncoder;
use flate2::Compression;

use super::archive::{SavHeader, SaveType};
use crate::error::SaveError;

/// Decompresses a `.sav` container into its raw GVAS payload.
///
/// Returns the payload together with the detected save type so callers can
/// preserve the original container format on write.
pub fn decompress_sav(data: &[u8]) -> Result<(Vec<u8>, SaveType), SaveError> {
    let header = SavHeader::parse(data)?;

    match header.save_type {
        SaveType::Plm => Err(SaveError::OodleUnsupported),
        SaveType::Plz => {
            let first_pass = inflate(&data[header.data_offset..])?;
            if first_pass.len() != header.compressed_len as usize {
                return Err(SaveError::CompressedLengthMismatch {
                    expected: header.compressed_len,
                    actual: first_pass.len(),
                });
            }
            let payload = inflate(&first_pass)?;
            if payload.len() != header.uncompressed_len as usize {
                return Err(SaveError::UncompressedLengthMismatch {
                    expected: header.uncompressed_len,
                    actual: payload.len(),
                });
            }
            Ok((payload, SaveType::Plz))
        }
        SaveType::Cnk => {
            let payload = inflate(&data[header.data_offset..])?;
            if payload.len() != header.uncompressed_len as usize {
                return Err(SaveError::UncompressedLengthMismatch {
                    expected: header.uncompressed_len,
                    actual: payload.len(),
                });
            }
            Ok((payload, SaveType::Cnk))
        }
    }
}

/// Compresses a raw GVAS payload into a `.sav` container.
///
/// Only PLZ writes are supported, matching the reference tool; CNK/PLM
/// writes return typed errors until their strategies are decided.
pub fn compress_gvas_to_sav(gvas_data: &[u8], save_type: SaveType) -> Result<Vec<u8>, SaveError> {
    match save_type {
        SaveType::Plz => {
            // The header records the size after the FIRST pass; the stored
            // payload is the double-compressed stream. Decompressors rely on
            // this to validate the intermediate layer.
            let first_pass = deflate(gvas_data)?;
            let compressed_len = first_pass.len() as u32;
            let second_pass = deflate(&first_pass)?;
            Ok(SavHeader::build(
                &second_pass,
                gvas_data.len() as u32,
                compressed_len,
                SaveType::Plz,
            ))
        }
        other => Err(SaveError::CompressUnsupported {
            label: other.label(),
        }),
    }
}

fn deflate(data: &[u8]) -> Result<Vec<u8>, SaveError> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder
        .write_all(data)
        .map_err(|e| SaveError::ZlibCompress {
            message: e.to_string(),
        })?;
    encoder.finish().map_err(|e| SaveError::ZlibCompress {
        message: e.to_string(),
    })
}

fn inflate(data: &[u8]) -> Result<Vec<u8>, SaveError> {
    let mut decoder = ZlibDecoder::new(data);
    let mut out = Vec::new();
    decoder
        .read_to_end(&mut out)
        .map_err(|e| SaveError::ZlibDecompress {
            message: e.to_string(),
        })?;
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pal_save::archive::MAGIC_CNK;
    use crate::pal_save::archive::MAGIC_PLM;
    use crate::pal_save::archive::MAGIC_PLZ;

    fn zlib_compress(data: &[u8]) -> Vec<u8> {
        let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(data).unwrap();
        encoder.finish().unwrap()
    }

    #[test]
    fn plz_roundtrip_preserves_payload() {
        let payload: Vec<u8> = (0..10_000u32).map(|i| (i % 251) as u8).collect();
        let sav = compress_gvas_to_sav(&payload, SaveType::Plz).unwrap();
        let (decoded, save_type) = decompress_sav(&sav).unwrap();
        assert_eq!(save_type, SaveType::Plz);
        assert_eq!(decoded, payload);
    }

    #[test]
    fn plz_header_records_first_pass_length() {
        let payload = b"hello palworld".repeat(50);
        let sav = compress_gvas_to_sav(&payload, SaveType::Plz).unwrap();

        assert_eq!(&sav[8..11], b"PlZ");
        assert_eq!(sav[11], 0x32);
        let recorded_compressed_len = u32::from_le_bytes(sav[4..8].try_into().unwrap());
        let uncompressed_len = u32::from_le_bytes(sav[0..4].try_into().unwrap());
        assert_eq!(uncompressed_len, payload.len() as u32);

        // The recorded length equals the first-pass output, not the stored
        // double-compressed stream.
        let first_pass_len = zlib_compress(&payload).len();
        assert_eq!(recorded_compressed_len as usize, first_pass_len);
        assert_ne!(recorded_compressed_len as usize, sav.len() - 12);
    }

    #[test]
    fn cnk_synthetic_container_decompresses_with_single_zlib_stream() {
        let payload = b"chunked save data".repeat(20);
        let compressed = zlib_compress(&payload);

        let mut sav = Vec::new();
        // Outer header: lengths ignored by the parser, magic marks CNK.
        sav.extend_from_slice(&0u32.to_le_bytes());
        sav.extend_from_slice(&0u32.to_le_bytes());
        sav.extend_from_slice(&MAGIC_CNK);
        sav.push(0x30);
        // Nested authoritative header reuses PlZ magic with type 0x30,
        // mirroring files produced by the game/reference tooling.
        sav.extend_from_slice(&(payload.len() as u32).to_le_bytes());
        sav.extend_from_slice(&(compressed.len() as u32).to_le_bytes());
        sav.extend_from_slice(&MAGIC_PLZ);
        sav.push(0x30);
        sav.extend_from_slice(&compressed);

        let (decoded, save_type) = decompress_sav(&sav).unwrap();
        assert_eq!(save_type, SaveType::Cnk);
        assert_eq!(decoded, payload);
    }

    #[test]
    fn plm_reports_typed_oodle_error_on_decompress() {
        let mut sav = Vec::new();
        sav.extend_from_slice(&10u32.to_le_bytes());
        sav.extend_from_slice(&10u32.to_le_bytes());
        sav.extend_from_slice(&MAGIC_PLM);
        sav.push(0x31);
        sav.extend_from_slice(&[0u8; 16]);

        let err = decompress_sav(&sav).unwrap_err();
        assert!(matches!(err, SaveError::OodleUnsupported));
        assert!(err.to_string().contains("Oodle"));
    }

    #[test]
    fn unknown_magic_is_rejected() {
        let mut sav = Vec::new();
        sav.extend_from_slice(&[0u8; 8]);
        sav.extend_from_slice(b"BAD");
        sav.push(0x32);

        let err = decompress_sav(&sav).unwrap_err();
        assert!(matches!(
            err,
            SaveError::UnknownMagic {
                magic,
                offset: 8
            }
            if magic == *b"BAD"
        ));
    }

    #[test]
    fn corrupted_uncompressed_length_fails_validation() {
        let payload = b"deterministic payload";
        let sav = compress_gvas_to_sav(payload, SaveType::Plz).unwrap();
        let mut corrupted = sav.clone();
        // Claim a wrong uncompressed size while keeping a valid zlib stream.
        corrupted[0..4].copy_from_slice(&(payload.len() as u32 + 7).to_le_bytes());

        let err = decompress_sav(&corrupted).unwrap_err();
        assert!(matches!(
            err,
            SaveError::UncompressedLengthMismatch {
                expected: 28,
                actual: 21
            }
        ));
    }

    #[test]
    fn corrupted_first_pass_length_fails_validation() {
        let payload = b"another deterministic payload";
        let sav = compress_gvas_to_sav(payload, SaveType::Plz).unwrap();
        let mut corrupted = sav.clone();
        corrupted[4] = 0xFF; // break compressed_len

        let err = decompress_sav(&corrupted).unwrap_err();
        assert!(matches!(err, SaveError::CompressedLengthMismatch { .. }));
    }

    #[test]
    fn cnk_and_plm_writes_report_typed_unsupported_errors() {
        for st in [SaveType::Cnk, SaveType::Plm] {
            let err = compress_gvas_to_sav(b"data", st).unwrap_err();
            assert!(matches!(err, SaveError::CompressUnsupported { .. }));
        }
    }

    #[test]
    fn empty_payload_roundtrips() {
        let sav = compress_gvas_to_sav(&[], SaveType::Plz).unwrap();
        let (decoded, _) = decompress_sav(&sav).unwrap();
        assert!(decoded.is_empty());
    }
}
