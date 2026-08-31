# PalTrainer Scripts and Core Refactoring Roadmap

This roadmap covers the current Python/PyQt6 migration branch only. It is intentionally independent of the separate production UI redesign roadmap in `docs/plan/ui/`.

## Scope

- Preserve current save formats, workflows, fallback behavior, and edge cases.
- Keep the existing Python package name and migrate imports consistently.
- Keep `palsav` isolated behind application-owned interfaces; do not clean up its internals until characterization coverage exists.
- Prefer `pyproject.toml` as the authoritative dependency and project configuration.
- Restore or replace the missing sanitized save fixtures before evaluating slow integration tests.
- Do not include licensing, attribution, or external provenance documentation work in this roadmap.

## Order

`001-plan` establishes contracts. `002-plan` and `003-plan` establish runtime and save boundaries. `004-plan` and `005-plan` establish session and read-model boundaries. `006-plan`, `007-plan`, and `008-plan` then split domain operations. `009-plan` cleans supporting scripts. `010-plan` and `011-plan` reduce UI coupling without redesigning the UI. `012-plan` is the final migration validation gate.

## Highest-risk areas

Save byte preservation, compression dispatch, XGP workflows, shared-memory lifecycle, Qt worker ownership, and frozen-build resource resolution require characterization tests before structural changes.

