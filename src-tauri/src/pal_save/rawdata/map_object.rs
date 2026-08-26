//! Codec for MapObjectSaveData and Booths
//!
//! Booth lock semantics per binary-schemas: the GUID stays non-zero in both
//! states; only `is_private_lock` controls the lock. Unlocking must not zero
//! the GUID and must preserve surrounding unknown bytes.

use crate::error::SaveError;

#[derive(Debug, Clone, PartialEq)]
pub struct MapObjectSaveData {
    pub trailing_bytes: Vec<u8>,
}

impl MapObjectSaveData {
    pub fn decode(data: &[u8]) -> Result<Self, SaveError> {
        Ok(Self {
            trailing_bytes: data.to_vec(),
        })
    }

    pub fn encode(&self) -> Result<Vec<u8>, SaveError> {
        Ok(self.trailing_bytes.clone())
    }

    /// Returns `Some(locked)` for booth objects, `None` otherwise.
    /// ItemBooth 20B: flag at 12, PalBooth 236B: flag at 224.
    pub fn booth_locked(&self) -> Option<bool> {
        match self.trailing_bytes.len() {
            20 => Some(self.trailing_bytes[12] != 0),
            236 => Some(self.trailing_bytes[224] != 0),
            _ => None,
        }
    }

    /// Sets the booth lock flag without touching the GUID.
    /// Preserves the non-zero `private_lock_player_uid` required by the game.
    pub fn set_booth_locked(&mut self, locked: bool) {
        let v = if locked { 1u8 } else { 0u8 };
        match self.trailing_bytes.len() {
            20 => self.trailing_bytes[12] = v,
            236 => self.trailing_bytes[224] = v,
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn item_booth_lock_flag_is_source_of_truth() {
        let mut locked = vec![0u8; 20];
        locked[12] = 1;
        // Simulate non-zero GUID in surrounding bytes (should be ignored)
        locked[0] = 0xAA;
        locked[19] = 0xBB;
        let mut m = MapObjectSaveData {
            trailing_bytes: locked,
        };
        assert_eq!(m.booth_locked(), Some(true));
        m.set_booth_locked(false);
        assert_eq!(m.booth_locked(), Some(false));
        // GUID bytes preserved, only flag cleared
        assert_eq!(m.trailing_bytes[0], 0xAA);
        assert_eq!(m.trailing_bytes[19], 0xBB);
        assert_eq!(m.trailing_bytes[12], 0);
        assert_eq!(m.trailing_bytes.len(), 20);
    }

    #[test]
    fn pal_booth_lock_at_224_preserves_guid() {
        let mut data = vec![0u8; 236];
        data[0] = 0x11;
        data[224] = 1;
        data[235] = 0x22;
        let mut m = MapObjectSaveData {
            trailing_bytes: data,
        };
        assert_eq!(m.booth_locked(), Some(true));
        m.set_booth_locked(false);
        assert_eq!(m.trailing_bytes[224], 0);
        assert_eq!(m.trailing_bytes[0], 0x11);
        assert_eq!(m.trailing_bytes[235], 0x22);
    }

    #[test]
    fn unlocking_preserves_non_zero_uid() {
        // Real game keeps GUID non-zero even when unlocked — we must not zero it.
        let mut data = vec![0u8; 20];
        data[12] = 1;
        // Fill GUID region with non-zero
        for v in &mut data[0..12] {
            *v = 0xFF;
        }
        let mut m = MapObjectSaveData {
            trailing_bytes: data.clone(),
        };
        m.set_booth_locked(false);
        for &b in &m.trailing_bytes[0..12] {
            assert_eq!(b, 0xFF);
        }
    }

    #[test]
    fn non_booth_returns_none() {
        let m = MapObjectSaveData {
            trailing_bytes: vec![0u8; 10],
        };
        assert_eq!(m.booth_locked(), None);
    }

    #[test]
    fn roundtrip_preserves_all_bytes_except_flag() {
        let raw = (0..20).map(|i| i as u8).collect::<Vec<_>>();
        let mut m = MapObjectSaveData {
            trailing_bytes: raw.clone(),
        };
        m.set_booth_locked(true);
        let mut expected = raw.clone();
        expected[12] = 1;
        assert_eq!(m.trailing_bytes, expected);
        assert_eq!(m.encode().unwrap(), expected);
    }
}
