# Phase 03 — Save Sessions, Backups & Safety

**Goal:** Every later feature gets load/save, preview, backup, stale detection by default.

**Source:** `palworld_aio/managers/save_manager.py` (triplicated reset), `managers/backup_manager.py`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 03.1 | `feat/save-session-lifecycle` | `domain/save_session/session.rs` `FileSnapshot`, `open`, `is_stale`, `queue_delete` | `cargo test` session open/stale |
| 03.2 | `feat/backup-atomic` | `storage/backup.rs` `create_backup` + `backup_meta.json`, `storage/atomic.rs` temp→rename | backup create/list/restore tests |
| 03.3 | `feat/path-policy` | `security/path_policy.rs` `canonicalize_safe`, `validate_save_root`, `resolve_save_root`, `allowlist` | path traversal + `Level.sav` resolve tests |
| 03.4 | `feat/mutation-preview` | `domain/save_session/preview.rs` `MutationPreview` builder + `AppError` | preview serialization tests |

**Outcome:** `load_save_session` → `SaveSummaryDto` → `check_stale` → `create_manual_backup` all via least-privilege IPC.
