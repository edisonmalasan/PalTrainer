"""Bounded product and diagnostics metadata for System workspaces."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import sys
from typing import Mapping

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR


@dataclass(frozen=True, slots=True)
class ProductInfo:
    app_version: str
    game_version: str
    developer: str = 'PalTrainer Team'
    project_url: str = 'https://github.com/edisonmalasan/PalTrainer'


@dataclass(frozen=True, slots=True)
class DiagnosticsInfo:
    app_version: str
    game_version: str
    python_version: str
    qt_version: str
    pyqt_version: str
    operating_system: str
    architecture: str
    packaged: bool
    paths: Mapping[str, str]

    def report(self) -> str:
        mode = 'Packaged application' if self.packaged else 'Development checkout'
        lines = [
            'PalTrainer Diagnostics',
            f'Application version: {self.app_version}',
            f'Supported game version: {self.game_version}',
            f'Python: {self.python_version}',
            f'Qt: {self.qt_version}',
            f'PyQt: {self.pyqt_version}',
            f'Operating system: {self.operating_system}',
            f'Architecture: {self.architecture}',
            f'Launch mode: {mode}',
            '',
            'Paths',
        ]
        lines.extend(
            f'{label.replace("_", " ").title()}: {value}'
            for label, value in self.paths.items())
        lines.extend((
            '',
            'Privacy: save paths, save data, player identifiers, and console output '
            'are excluded from this report.',
        ))
        return '\n'.join(lines)


def build_product_info() -> ProductInfo:
    from common import get_versions

    app_version, game_version = get_versions()
    return ProductInfo(app_version, game_version)


def build_diagnostics_info() -> DiagnosticsInfo:
    """Build diagnostics without inspecting the current save or its contents."""
    from boot_paths import ROOT_DIR, USER_CONFIG_DIR, get_data_base, is_frozen
    from common import get_versions
    from palworld_aio.application.backup_catalog import default_backups_root

    app_version, game_version = get_versions()
    paths = {
        'application': str(Path(ROOT_DIR).resolve()),
        'configuration': str(Path(USER_CONFIG_DIR).resolve()),
        'data': str(Path(get_data_base()).resolve()),
        'backups': str(default_backups_root().resolve()),
    }
    return DiagnosticsInfo(
        app_version=app_version,
        game_version=game_version,
        python_version=platform.python_version(),
        qt_version=QT_VERSION_STR,
        pyqt_version=PYQT_VERSION_STR,
        operating_system=platform.platform(),
        architecture=platform.machine() or 'Unknown',
        packaged=is_frozen(),
        paths=paths,
    )


__all__ = [
    'DiagnosticsInfo', 'ProductInfo', 'build_diagnostics_info',
    'build_product_info',
]
