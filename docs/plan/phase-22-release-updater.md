# Phase 22 — Release & Updater

**Goal:** Windows-first bundle ready for users.

**Source:** `build/nuitka/build_nuitka.py --onefile` → `dist/`, `scripts/build_cx.cmd` parity → Tauri `tauri build` + `tauri-plugin-updater`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 22.1 | `feat/updater` | `tauri-plugin-updater` + `GITHUB_LATEST_ZIP` `https://api.github.com/repos/.../releases/latest` + branch `stable` pulse animation `update_version_text` | update check `UpdateChecker` QThread parity |
| 22.2 | `feat/packaging-linux-macos` | Linux `AppImage` + macOS `dmg` (`xattr -d com.apple.quarantine` note) | `tauri build --bundles` |
| 22.3 | `feat/release-notes` | `RELEASE_NOTES_TEMPLATE.md` already + `SUPPORTED_VERSIONS.md`/`TROUBLESHOOTING.md` provenance note | docs build |

**Outcome:** `pnpm tauri build` produces signed `PalTrainer*.exe/.AppImage/.dmg` with updater.
