from __future__ import annotations

"""Application-owned save engine adapter boundary.

This package is the only surface application code should use to load,
inspect, and save Palworld saves. Compression, GVAS parsing, property
dispatch, rawdata codecs, unknown properties, and trailing bytes all
live behind this boundary inside ``palsav``.

Codec failures are raised as :class:`CodecError`; filesystem/input
failures as :class:`StorageError`; both derive from
:class:`SaveEngineError`.
"""

from save_engine.errors import SaveEngineError, SaveFormatError, CodecError, StorageError
from save_engine.document import SaveHeader, SaveDocument, SaveInspection
from save_engine.adapter import SaveEngine, load_save, inspect_save, save_save

__all__ = [
    'SaveEngineError',
    'SaveFormatError',
    'CodecError',
    'StorageError',
    'SaveHeader',
    'SaveDocument',
    'SaveInspection',
    'SaveEngine',
    'load_save',
    'inspect_save',
    'save_save',
]
