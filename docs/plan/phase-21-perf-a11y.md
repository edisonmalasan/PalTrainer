# Phase 21 — Perf, A11y & Command Palette

**Goal:** Keyboard-first workbench (`?` help, `Ctrl+1-0` already done) + a11y.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 21.1 | `feat/command-palette` | `Cmd+K` palette searching routes + players/guilds/bases/pals | `KeyboardShortcutOverlay` |
| 21.2 | `feat/focus-a11y` | `focus-visible:ring-shell-accent` on every interactive, `aria-*` on tables/dialogs | `axe` lint |
| 21.3 | `feat/web-perf` | Grain filter `fixed inset-0 pointer-events-none` only, `will-change: transform` sparing, isolate `staggerChildren` in `React.memo` leaf | Lighthouse 90+ |

**Outcome:** Power users navigate via keyboard; heavy pal grids stay 60fps.
