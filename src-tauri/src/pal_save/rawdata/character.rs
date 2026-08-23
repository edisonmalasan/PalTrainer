//! Codec for CharacterSaveParameterMap

use crate::error::SaveError;

#[derive(Debug, Clone, PartialEq)]
pub struct CharacterSaveData {
    // Basic structural fields to be parsed
    pub trailing_bytes: Vec<u8>,
}

impl CharacterSaveData {
    pub fn decode(data: &[u8]) -> Result<Self, SaveError> {
        // TODO: Implement parsing logic for character data.
        Ok(Self {
            trailing_bytes: data.to_vec(),
        })
    }

    pub fn encode(&self) -> Result<Vec<u8>, SaveError> {
        // TODO: Implement encoding logic for character data.
        Ok(self.trailing_bytes.clone())
    }
}
