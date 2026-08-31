from __future__ import annotations


class SaveEngineError(Exception):
    """Base exception for all save-engine errors."""


class SaveFormatError(SaveEngineError):
    """The save file does not match a known format."""


class CodecError(SaveEngineError):
    """Error originating from the palsav codec layer (decompression, GVAS parse)."""


class StorageError(SaveEngineError):
    """Error originating from I/O or filesystem access."""