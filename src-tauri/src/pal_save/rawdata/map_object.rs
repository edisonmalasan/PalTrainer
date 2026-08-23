//! Codec for MapObjectSaveData and Booths

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
}
