# PalTrainer

PalTrainer is a desktop utility for inspecting, repairing, converting, and editing Palworld save data. It is built with Python, PyQt6, and the local `palsav` serialization engine.

## Capabilities

- Inspect and write compressed world, player, and global storage saves.
- Edit players, guilds, bases, Pals, inventories, equipment, technology, and world options.
- Export and import Pals and base data in JSON and legacy compact formats.
- Convert save formats, transfer characters between worlds, and repair host-save data.
- Discover, extract, and package Xbox Game Pass save containers.
- Restore map exploration, unlock fast travel, adjust coordinates, and inject Palbox slots.
- Find invalid, orphaned, duplicated, inactive, and overfilled data before cleanup.
- Reset supported world events and protect selected entities with persistent exclusions.
- Browse world and tree maps with markers, calibration, and exclusion zones.
- Use localized UI text, in-app guides, backups, and diagnostic logging.

Every write operation must create a backup, validate the selected save location, and use an atomic replacement path. Real save files should be copied to a disposable test directory before editing.

## Requirements

- Python 3.11 or newer.
- `uv` for dependency and environment management.
- PyQt6 runtime libraries supplied by the project dependencies.

## Setup and launch

```bash
uv sync
uv run start.py
```

On Windows, `start.cmd` provides the same launcher. For direct application startup after dependencies are installed:

```bash
uv run python src/palworld_aio/main.py
```

## Tests and checks

```bash
uv run pytest -c tests/pytest.ini
uv run python -m compileall -q src tests
uv run pyright
```

The test harness includes structural import/resource audits and opt-in save fixtures. Do not place personal saves in the repository; use documented fixture directories and sanitized copies.

## Building

The supported release paths are kept under `build/`:

```bash
uv run python build/nuitka/build_nuitka.py --onefile
uv run python build/cx_freeze/build_cx.py
```

Build output is written to ignored directories. Packaging metadata, platform requirements, and release verification are documented alongside those build scripts.

## Project layout

```text
src/palsav/               Save serialization and compression engine
src/palworld_aio/         PyQt6 application, managers, editors, and widgets
src/palworld_toolsets/    Conversion, transfer, map, and slot tools
src/palworld_xgp_import/  Xbox Game Pass discovery and packaging
src/palworld_coord/       Coordinate transforms
resources/                Game data, translations, guides, maps, and assets
tests/                    Structural, integration, and unit tests
build/                    Nuitka, cx_Freeze, installer, and verification tools
```

## License

PalTrainer is distributed under the MIT License. See [LICENSE](LICENSE).
