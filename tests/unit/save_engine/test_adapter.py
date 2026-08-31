from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

import pytest
from tests.dynamic_importer import import_from
from tests.test_registry import SAVE_TEST_DIR

_save_engine = import_from('save_engine')
load_save = _save_engine.load_save
save_save = _save_engine.save_save
inspect_save = _save_engine.inspect_save
SaveEngineError = _save_engine.SaveEngineError
StorageError = _save_engine.StorageError
CodecError = _save_engine.CodecError
SaveDocument = _save_engine.SaveDocument
SaveInspection = _save_engine.SaveInspection


@pytest.fixture
def level_sav() -> pathlib.Path:
    return SAVE_TEST_DIR / 'Level.sav'


@pytest.fixture
def local_data_sav() -> pathlib.Path:
    return SAVE_TEST_DIR / 'LocalData.sav'


@pytest.fixture
def player_sav() -> pathlib.Path:
    return SAVE_TEST_DIR / 'Players' / '00000000000000000000000000000001.sav'


class TestLoad:
    def test_load_returns_document(self, level_sav):
        doc = load_save(level_sav)
        assert isinstance(doc, SaveDocument)
        assert doc.header.save_game_class_name == '/Script/Pal.PalWorldSaveGame'
        assert 'worldSaveData' in doc.properties
        assert doc.properties['Version'] is not None
        assert isinstance(doc.trailer, bytes)
        assert doc.save_type == 50

    def test_load_local_data(self, local_data_sav):
        doc = load_save(local_data_sav)
        assert doc.header.save_game_class_name == '/Script/Pal.PalLocalWorldSaveGame'
        assert 'SaveData' in doc.properties

    def test_load_player(self, player_sav):
        doc = load_save(player_sav)
        assert doc.header.save_game_class_name == '/Script/Pal.PalWorldPlayerSaveGame'
        assert 'SaveData' in doc.properties

    def test_missing_file_raises_storage_error(self):
        with pytest.raises(StorageError):
            load_save(pathlib.Path('nonexistent_Level.sav'))

    def test_corrupt_file_raises_codec_error(self, tmp_path):
        bad = tmp_path / 'bad.sav'
        bad.write_bytes(b'\x00' * 12)
        with pytest.raises(CodecError):
            load_save(bad)


class TestSave:
    def test_roundtrip_preserves_bytes(self, level_sav, tmp_path):
        doc = load_save(level_sav)
        out = tmp_path / 'Level.sav'
        save_save(doc, out)
        original = level_sav.read_bytes()
        saved = out.read_bytes()
        assert saved == original

    def test_roundtrip_properties_identical(self, level_sav, tmp_path):
        doc = load_save(level_sav)
        out = tmp_path / 'Level.sav'
        save_save(doc, out)
        doc2 = load_save(out)
        assert doc2.properties.keys() == doc.properties.keys()
        assert doc2.header.save_game_class_name == doc.header.save_game_class_name

    def test_trailer_preserved(self, level_sav, tmp_path):
        doc = load_save(level_sav)
        out = tmp_path / 'Level.sav'
        save_save(doc, out)
        doc2 = load_save(out)
        assert doc2.trailer == doc.trailer

    def test_local_data_save_type(self, local_data_sav, tmp_path):
        doc = load_save(local_data_sav)
        assert doc.save_type == 50
        out = tmp_path / 'LocalData.sav'
        save_save(doc, out)
        doc2 = load_save(out)
        assert doc2.save_type == 50


class TestInspect:
    def test_inspect_metadata(self, level_sav):
        info = inspect_save(level_sav)
        assert isinstance(info, SaveInspection)
        assert info.file_size > 0
        assert info.uncompressed_size > info.file_size
        assert info.save_type == 50
        assert info.save_game_class_name == '/Script/Pal.PalWorldSaveGame'

    def test_inspect_missing_file_raises_storage_error(self):
        with pytest.raises(StorageError):
            inspect_save(pathlib.Path('nonexistent_Level.sav'))