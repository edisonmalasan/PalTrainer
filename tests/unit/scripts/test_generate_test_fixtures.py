from __future__ import annotations

from pathlib import Path
import pytest
from tests.dynamic_importer import import_from

generate_sanitized_fixtures = import_from(
    'generate_test_fixtures', 'generate_sanitized_fixtures'
)
create_header = import_from('generate_test_fixtures', 'create_header')


class TestGenerateTestFixtures:
    def test_create_header(self):
        hdr = create_header('/Script/Pal.PalWorldSaveGame')
        assert hdr['magic'] == 1396790855
        assert hdr['save_game_version'] == 3
        assert hdr['save_game_class_name'] == '/Script/Pal.PalWorldSaveGame'

    def test_generate_sanitized_fixtures_creates_files(self, tmp_path: Path):
        target = tmp_path / 'custom_save_test'
        out = generate_sanitized_fixtures(target)
        assert out == target
        assert (target / 'Level.sav').is_file()
        assert (target / 'Level.sav').stat().st_size > 0
        assert (target / 'LocalData.sav').is_file()
        assert (target / 'Players' / '00000000000000000000000000000001.sav').is_file()
        assert (
            target / 'Players' / '00000000000000000000000000000001_dps.sav'
        ).is_file()
