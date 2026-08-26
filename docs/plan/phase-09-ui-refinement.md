# Phase 09 — UI/UX Refinement & Accessibility

**Goal:** Feels like a workbench, not a clone.

**Source:** `design-taste-frontend-v1` 8/6/4 (Variance 8, Motion 6, Density 4).

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 09.1 | `feat/navigation-refinement` | Grouped sidebar `routeGroups` 4 groups, active `accent` + `Shortcut` `Ctrl+N` | keyboard overlay test |
| 09.2 | `feat/keyboard-shortcuts` | `useKeyboardShortcut`, `KeyboardShortcutOverlay` `?`, `Ctrl+1-0` | `useKeyboardShortcut.test` |
| 09.3 | `feat/design-system-hardening` | `tailwind.config` shell tokens `#16181c/#1e2126` teal `#58b6a0`, `styles.css` `fade/slide` | visual snapshot |
| 09.4 | `feat/destructive-warnings` | `WarningBanner`, `DestructiveConfirmModal` | shared-components test |
| 09.5 | `feat/state-polish` | `EmptyState` geometric glyph + CTA, `DataTable` sort/search | `DataTable` empty |
| 09.6 | `feat/viewshell-component-upgrades` | `ViewShell` skeleton/error, `PreviewModal` `role=dialog` + `Esc/Ctrl+Enter` | `PreviewModal` a11y |

**Outcome:** Dense tables scannable, wizards clear, warnings before destructive ops.
