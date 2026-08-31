# 012-plan — Migration regression and release gates

## Objective

Prove that the refactor preserves behavior and improves maintainability.

## Tasks

- Restore or replace sanitized save fixtures and enable slow integration tests.
- Add save byte-roundtrip, unknown-property, trailer, compression, Booth, Guild, XGP, and stale-file tests.
- Add tests for sessions, storage, projections, use cases, Pal validation, stats, breeding, and coordinates.
- Add focused GUI smoke tests for navigation, dirty state, workers, dialogs, and errors.
- Update the dynamic importer and structural audit as modules move.
- Run compilation, imports, fast/slow tests, Pyright, resource audits, theme checks, and frozen-build verification.

## Files and areas

`tests/test_registry.py`, `tests/dynamic_importer.py`, `tests/unit/`, `tests/integration/`, `tests/conftest.py`, and build verification scripts.

## Dependencies

All previous scripts plans.

## Acceptance

The compatibility matrix passes, required fixtures are usable, high-risk workflows have regression coverage, and remaining tool/type warnings are documented rather than hidden.

