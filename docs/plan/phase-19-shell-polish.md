# Phase 19 — Shell Polish (Your 14 Screenshots, Readable Not White)

**Goal:** Copy PST chrome but polished via `design-taste-frontend-v1` 8/6/4.

**Source:** `ui/main_window.py MainWindow` 1600 lines, `chrome/{header,sidebar,results,styles}`, `widgets/search_panel`, `docs/PalworldSaveTools` screenshots 1-14.

**Already done (keep):** `feat/save-session-load-ui` (file filter) + `feat/ui dark readable shell` (`#16181c/#1e2126` + teal `#58b6a0`, `Geist/Satoshi` + `JetBrains Mono`, `index.html bg` no flash, no `Phase N` overline).

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 19.1 | `feat/shell-header` | `HeaderWidget`: `Menu` + `2.4.0` yellow / `1.0.3` green badges + 4 status icons `i/!/bag/save` + Discord/min/close | header vitest |
| 19.2 | `feat/shell-sidebar` | 12 entries `Tools/Map/Base Inv./Player Inv./Pal Editor/Search Players/Guilds/Bases/Exclusions/JSON Editor/Breeding/Docs` with collapse `<< / >>` + `Detach / Show Results` bottom | `App.tsx` `<<` collapse |
| 19.3 | `feat/shell-tables` | `SearchPanel _SortableItem` sortable headers + context menus + `Bulk Actions: Bulk Item/Pal/Tech/Guild Assignments` footer bar (Image 10) | `DataTable` headers |
| 19.4 | `feat/shell-empty-loading` | `EmptyState` dashed `border-shell-line/50` glyph (Image 3 `No Pal Data`), skeleton bars `ViewSkeleton` | `EmptyState` empty |

**Design tokens:** `panel #16181c`, `surface #1e2126`, `line #2b2f36`, `ink #e8eaed`, `muted #9aa0a8`, accent teal desaturated <80% (no Lila purple), `rounded-[2.5rem] diffusion shadow`, `transform/opacity` only, `staggerChildren` per Bento.

**Outcome:** `<<` collapsed sidebar `lg:grid-[240px_1fr]`, active `accent-subtle`, `QSplitter [1000,400]` feel via `Splitter`.
