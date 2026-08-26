# Phase 10 — Test Hardening, Packaging & Release

**Goal:** Release-ready with repeatable builds.

| Task | Branch | Status | Verification |
|------|--------|--------|--------------|
| 10.1 | `test/save-engine-units` | Done | GVAS error, UUID, compression archive |
| 10.2 | `test/security-storage-units` | Done | traversal, atomic, backup, stale, task runner |
| 10.3a | `test/domain-tools` | Done | CityHash vectors, UID normalize |
| 10.3b | `test/domain-conversion-tools` | Done | SAV↔JSON validation |
| 10.3c | `test/domain-transfer-tools` | Done | host-swap exchange semantics |
| 10.3d | `test/domain-map-tools` | Done | map restore + slot calc |
| 10.3e | `test/domain-xgp-tools` | Done | `containers.index` v14 |
| 10.3f | `test/domain-diagnostic-tools` | Done | report contracts |
| 10.4 | `test/resource-integrity` | Done | duplicate IDs, schema drift |
| 10.5 | `test/frontend-units` | Done | Vitest jsdom + Testing Library |
| 10.6 | `feat/windows-packaging` | Done | NSIS `currentUser` + `embedBootstrapper` |
| 10.7 | `docs/release-documentation` | Done | `SUPPORTED_VERSIONS.md` etc. |
| 10.8 | `ci/release-verification` | Done | `pnpm test` + `cargo test --lib` + Playwright 2 tests |

Add crash-safe write tests + `tests/fixtures/*.sav` slow opt-in after 10.8.
