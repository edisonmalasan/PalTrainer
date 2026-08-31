from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Union

from save_engine.document import SaveDocument, SaveHeader, SaveInspection
from save_engine.errors import CodecError, SaveFormatError, StorageError


def _gvas_header_to_save_header(header: Any) -> SaveHeader:
    return SaveHeader(
        magic=header.magic,
        save_game_version=header.save_game_version,
        package_file_version_ue4=header.package_file_version_ue4,
        package_file_version_ue5=header.package_file_version_ue5,
        engine_version_major=header.engine_version_major,
        engine_version_minor=header.engine_version_minor,
        engine_version_patch=header.engine_version_patch,
        engine_version_changelist=header.engine_version_changelist,
        engine_version_branch=header.engine_version_branch,
        custom_version_format=header.custom_version_format,
        custom_versions=header.custom_versions,
        save_game_class_name=header.save_game_class_name,
    )


def _decode_codec(exc: BaseException) -> CodecError:
    return CodecError(str(exc))


def _read_bytes(path: Union[str, os.PathLike]) -> bytes:
    try:
        return Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise StorageError(f'save file not found: {path}') from exc
    except IsADirectoryError as exc:
        raise StorageError(f'save path is a directory: {path}') from exc
    except OSError as exc:
        raise StorageError(f'failed to read save file {path}: {exc}') from exc


def _write_bytes(path: Union[str, os.PathLike], data: bytes) -> None:
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    except OSError as exc:
        raise StorageError(f'failed to write save file {path}: {exc}') from exc


class SaveEngine:
    """Application-owned adapter over the ``palsav`` save engine.

    All compression, GVAS, property-dispatch, rawdata, unknown-property,
    and trailer handling stays inside ``palsav``; this adapter only exposes
    stable, application-facing load/save/inspect operations.
    """

    def __init__(self, custom_properties: Optional[dict] = None) -> None:
        from palsav.paltypes import PALWORLD_CUSTOM_PROPERTIES

        self._custom_properties = (
            custom_properties if custom_properties is not None else PALWORLD_CUSTOM_PROPERTIES
        )

    def load(self, path: Union[str, os.PathLike]) -> SaveDocument:
        data = _read_bytes(path)
        try:
            from palsav.core import decompress_sav_to_gvas
            from palsav.gvas import GvasFile
            from palsav.paltypes import PALWORLD_TYPE_HINTS

            raw_gvas, save_type = decompress_sav_to_gvas(data)
            gvas = GvasFile.read(
                raw_gvas,
                type_hints=PALWORLD_TYPE_HINTS,
                custom_properties=self._custom_properties,
            )
        except Exception as exc:
            raise _decode_codec(exc) from exc
        return SaveDocument(
            header=_gvas_header_to_save_header(gvas.header),
            properties=gvas.properties,
            trailer=gvas.trailer,
            save_type=save_type,
        )

    def save(self, document: SaveDocument, path: Union[str, os.PathLike]) -> None:
        target = Path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f'failed to create save directory {target.parent}: {exc}') from exc
        try:
            from palsav.gvas import GvasFile
            from palsav.io import save_sav

            gvas = GvasFile()
            gvas.header = _reconstruct_gvas_header(document.header)
            gvas.properties = document.properties
            gvas.trailer = document.trailer
            save_sav(gvas, str(target), custom_properties=self._custom_properties, save_type=document.save_type)
        except Exception as exc:
            raise _decode_codec(exc) from exc

    def inspect(self, path: Union[str, os.PathLike]) -> SaveInspection:
        data = _read_bytes(path)
        try:
            from palsav.core import decompress_sav_to_gvas
            from palsav.gvas import GvasFile
            from palsav.paltypes import PALWORLD_TYPE_HINTS

            raw_gvas, save_type = decompress_sav_to_gvas(data)
            gvas = GvasFile.read(
                raw_gvas,
                type_hints=PALWORLD_TYPE_HINTS,
                custom_properties=self._custom_properties,
            )
            class_name = gvas.header.save_game_class_name
        except Exception as exc:
            raise _decode_codec(exc) from exc
        return SaveInspection(
            file_size=len(data),
            compressed_size=len(data),
            uncompressed_size=len(raw_gvas),
            save_type=save_type,
            save_game_class_name=class_name,
        )


def _reconstruct_gvas_header(save_header: SaveHeader):
    from palsav.gvas import GvasHeader

    header = GvasHeader()
    header.magic = save_header.magic
    header.save_game_version = save_header.save_game_version
    header.package_file_version_ue4 = save_header.package_file_version_ue4
    header.package_file_version_ue5 = save_header.package_file_version_ue5
    header.engine_version_major = save_header.engine_version_major
    header.engine_version_minor = save_header.engine_version_minor
    header.engine_version_patch = save_header.engine_version_patch
    header.engine_version_changelist = save_header.engine_version_changelist
    header.engine_version_branch = save_header.engine_version_branch
    header.custom_version_format = save_header.custom_version_format
    header.custom_versions = save_header.custom_versions
    header.save_game_class_name = save_header.save_game_class_name
    return header


_ENGINE: Optional[SaveEngine] = None


def _default_engine() -> SaveEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = SaveEngine()
    return _ENGINE


def load_save(path: Union[str, os.PathLike]) -> SaveDocument:
    """Load a save file through the application-owned boundary."""
    return _default_engine().load(path)


def save_save(document: SaveDocument, path: Union[str, os.PathLike]) -> None:
    """Serialize a save document back through the boundary."""
    _default_engine().save(document, path)


def inspect_save(path: Union[str, os.PathLike]) -> SaveInspection:
    """Inspect a save file (compression metadata and GVAS class name)."""
    return _default_engine().inspect(path)
