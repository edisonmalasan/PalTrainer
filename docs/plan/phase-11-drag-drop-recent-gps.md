# Phase 11 — Drag-Drop, Recent Paths & GPS Session

**Goal:** Loader reaches PST parity (`Menu → Load Save` + drop + GPS separate).

**Source:** `save_manager.load_save` `QFileDialog.getOpenFileName(..., 'Select Level.sav', default_dir, 'SAV Files(*.sav)')`, `save_manager.load_gps`, `save_manager.load_xgp_save`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 11.1 | `feat/session-drag-drop` | Tauri drop `Level.sav` onto window → `resolve_save_root` → `load_save_session` (`DropOverlay` as in `tools_tab.py`) | Playwright drop e2e |
| 11.2 | `feat/session-recent-paths` | `storage/settings.rs` recent 5 `PathBuf`, `get_preferred_save_path` default dir, header recent menu | `settings` JSON roundtrip |
| 11.3 | `feat/session-gps` | `commands::gps::load_gps/save_gps` isolated `GlobalPalStorage.sav` (`gps_gvas` separate) | `gps_editor.py` parity: grid load |

**Outcome:** Your `C:\...\SaveGames\7656...\6EA...` browsed via picker *or* drop both show `Level.sav` (file filter, not directory-hidden). Already fixed in `feat/save-session-folder-picker` + `feat/save-session-load-ui`; this phase adds the remaining drop/recent/GPS polish.

**UI:** Header `Load Save…` remains single button; drop zone `or drag & drop a Level.sav file here` caption as in Image 1.
