# 009-plan — Consolidate scripts and build tooling

## Objective

Make maintenance, translation, testing, and packaging commands safe and predictable.

## Tasks

- Convert scripts into thin CLI entry points calling reusable library functions.
- Remove automatic dependency installation from ordinary utilities.
- Route save mutations through backup and atomic storage services.
- Prevent scripts and builds from deleting or rewriting lockfiles.
- Consolidate version extraction, dependency configuration, UTF-8 output, and structured logging.
- Make build verification provide real help and actionable failures.

## Files and areas

`scripts/`, `scripts/scrs/`, `build/`, `start.py`, `test.cmd`, `pyproject.toml`, `requirements.txt`, and `uv.lock`.

## Dependencies

`002-plan`, `004-plan`, `008-plan`.

## Acceptance

Commands are independently invocable, do not mutate unrelated project state, and use one version/dependency configuration.

