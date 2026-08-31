# 002-plan — Consolidate runtime, configuration, resources, and imports

## Objective

Give startup, paths, resources, configuration, and dependencies one predictable ownership model.

## Tasks

- Make `pyproject.toml` authoritative for project metadata and dependencies.
- Decide whether `requirements.txt` is retained only as a generated compatibility artifact.
- Separate environment preparation, process startup, CLI parsing, and Qt startup.
- Consolidate `boot_paths.py`, `path_setup.py`, `resource_resolver.py`, and `common.py` responsibilities.
- Replace wildcard use of `import_libs.py` with explicit imports.
- Preserve standalone, frozen, development, localized, and user-config behavior.

## Files and areas

`start.py`, `start.cmd`, `src/bootup.py`, `src/path_setup.py`, `src/boot_paths.py`, `src/resource_resolver.py`, `src/common.py`, `src/i18n/`, `src/import_libs.py`, `src/qt_imports.py`, `pyproject.toml`, `requirements.txt`.

## Dependencies

`001-plan`.

## Acceptance

All supported launch modes resolve the same configuration and resources, and dependency/version information has one authoritative source.

