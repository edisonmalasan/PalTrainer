from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SaveHeader:
    """Application-owned view of the GVAS header metadata."""
    magic: int
    save_game_version: int
    package_file_version_ue4: int
    package_file_version_ue5: int
    engine_version_major: int
    engine_version_minor: int
    engine_version_patch: int
    engine_version_changelist: int
    engine_version_branch: str
    custom_version_format: int
    custom_versions: list[tuple[str, int]]
    save_game_class_name: str


@dataclass
class SaveDocument:
    """Application-owned view of a loaded save file.

    The ``properties`` dict holds the full GVAS property tree as decoded
    by ``palsav``.  The ``trailer`` bytes are the raw GVAS trailer (normally
    ``b'\\x00\\x00\\x00\\x00'``).  ``save_type`` is the compression format
    identifier (e.g. 48 for CNK, 49 for PLM, 50 for PLZ).
    """
    header: SaveHeader
    properties: dict[str, Any]
    trailer: bytes
    save_type: int


@dataclass
class SaveInspection:
    """Lightweight inspection result without a full GVAS parse."""
    file_size: int
    compressed_size: int
    uncompressed_size: int
    save_type: int
    save_game_class_name: Optional[str] = None