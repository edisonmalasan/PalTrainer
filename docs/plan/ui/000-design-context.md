# UI Design Context — PalTrainer Overhaul

This file is the persistent source of truth for the UI overhaul's design decisions.
Any session (human or AI) continuing the overhaul must read this file first, together
with `000-index.md` and `PROGRESS.md`. Update it whenever a significant design or
architectural decision is made.

---

## 0. Overhaul reset status (2026-09-04) — READ FIRST

The original overhaul plans 001–007 were **reviewed against the audit evidence
and found insufficient**: they produced tokenization + recoloring while
preserving the old UI's structure (persistent left sidebar, global header,
right Results dock, glass card dashboard). `git diff main...HEAD` proves the
shell widget tree is identical to `main`.

- **REJECTED as design decisions:** 004 (shell & navigation), 005 (dashboard),
  006 (results/statistics panels), 007 (search screens' shell relationship).
- **RETAINED as technical infrastructure only:** 002 (token dict architecture,
  QSS builder pipeline, theme scanner, ThemeManager) and 003 (shared component
  library, safe dialog helpers, confirm system) — their palette/typography
  content is replaced by plan 019.
- **FROZEN pending re-derivation:** 008–018 (screen migrations + passes);
  each must be revised against the divergence matrix (019 §4.1) before
  execution. Status banners are on each plan file.
- **Replacement plans:** 019 (design reset), 020 (shell v2), 021 (Start v2),
  022 (dialogs, pending), 023 (tables, pending).
- Plans 001–007 must not be cited as authority for any layout, palette, or
  navigation decision. Only the infrastructure pieces named above carry over.

### How future agents can detect accidental return to the old UI

Any of these in new code means the design has regressed and must be fixed:

1. A persistent **left navigation sidebar** (`SidebarWidget`, `#sideBar`,
   `sidebarItem` property) in the live construction path.
2. A persistent **right Results dock** (`ResultsWidget`, `#resultsWidget`) or
   a `QSplitter` holding content + results as panes.
3. `QFrame#glass`, `#saveCard`, `#toolCard`, gradient canvas backgrounds,
   translucent `rgba(18,20,24,…)` surfaces.
4. Cyan `#7DD3FC` as an accent value anywhere in `tokens.py`/`constants.py`.
5. A global header bar owning nav/save/menu (header chips `#menuChip`,
   `#versionChip`, `#gameVersionChip`, `#discordChip` as chrome).
6. Any new screen composed as "content + right dock" or "sidebar + content".
7. Per-screen inline `setStyleSheet` blocks (scanner enforces).

The canonical shell is: full-bleed page canvas + right **NexusBand** rail +
per-page ribbons (plan 020). The canonical palette is warm dark + amber/teal
(plan 019 §5). Canonical fonts are Hanken Grotesk + Inter (plan 019 §6).

---

## 1. Design thesis v2 — "Deck Operations"

PalTrainer is a **flight-deck for save surgery**: a working canvas surrounded
by mission equipment. The operator never leaves the canvas; equipment comes to
them in a single rail they own.

1. **The canvas is the screen.** No permanent sidebar, no permanent results
   panel. The working page gets the full window minus one narrow instrument
   rail (NexusBand, 76px) on the right. Each page owns a **ribbon** (title +
   zone + page actions); global chrome is minimal.
2. **One rail, everything docked.** Navigation, save lifecycle, selection, and
   statistics live in the NexusBand organized by altitude: navigate → save →
   selection → statistics → utilities. Expanded detail uses a canvas-local
   **TrayDrawer** overlay (never a separate window).
3. **Warm dark, flat, ruled.** Deep warm-neutral canvas (#141312), opaque
   tonal surfaces, hairline rules instead of bordered cards. **Amber**
   (#F59E0B) is the only interactive accent (nav-active, focus, primary CTA);
   **teal** (#2DD4BF) marks success/loaded. No gradients, no glass, no glow,
   no emoji icons.
4. **Typography as structure.** Hanken Grotesk (display/headings/nav), Inter
   (body/controls/tables), mono for data. Hierarchy from type scale and
   spacing, not boxes.
5. **Data semantics are the only other color.** Pal rarity/element/rank colors
   are a data contract — never decorative, never restyled.

Anti-slop constraints (binding): no generic SaaS layouts, no recolor-only
"overhaul", no decorative effects without function, no per-screen one-off
colors, no wall-to-wall rounded cards, no oversized headings, no hiding
overflow, no removing useful data for aesthetics.

## 2. Screenshot reference protocol & image-inspection limitation

- `ib/image/` is the permanent screenshot registry: `tools-tab`,
  `base-inventory`, `player-inventory`, `pal-editor`, `search-players`,
  `search-guilds`, `search-bases`, `map-viewer`, `exclusions`,
  `json-editor`, `breeding`, `docs-tab` (+ top-level `menu.png`). They are
  functional references only — never visual templates.
- **Screenshot-based visual inspection is unavailable in this environment**
  (the model has no image input; verified 2026-09-04 by attempting to read
  `ib/image/tools-tab/tools-main.png` — the read returned a decode error).
  Consequently, **screenshot-based visual QA has not been performed and must
  not be claimed.** Fallback method: mandatory code-based structural redesign
  (audit old code on `main`, audit current branch code, rebuild with
  structurally different widget hierarchies, assert structure offscreen, save
  screenshots for the user's manual review).
- Per-screen folder-to-screen mapping and functionality inventory happens at
  migration time from the old code itself (`git show main:<screen file>`)
  plus the folder names above; each migration plan records the inventory it
  preserves. Final visual QA remains **pending manual review** until a
  capable agent or the user inspects the screenshots and captured captures.

## 3. Typography system (v2, decided 2026-09-04)

Bundled fonts (project mandate) replace the earlier system-stack decision:

| Role | Family | Stack (QFont.setFamilies) | Source |
|---|---|---|---|
| Display / headings / nav | Hanken Grotesk | `['Hanken Grotesk','Segoe UI']` | `resources/assets/fonts/HankenGrotesk-Regular.ttf` |
| Body / controls / tables / dialogs | Inter | `['Inter','Segoe UI']` | `resources/assets/fonts/Inter_28pt-Regular.ttf` |
| Data / mono (UUIDs, JSON, paths, coords) | Cascadia Mono → Consolas | `['Cascadia Mono','Consolas']` | system (no ligature risk) |
| Icons | Hack Nerd Font | `['Hack Nerd Font']` | `resources/assets/fonts/HackNerdFont-Regular.ttf` |

- **Loading:** centralized in `chrome/fonts.py::load_app_fonts()` — registers
  every TTF/OTF under `resources/assets/fonts` once at startup; per-file
  loading is banned (old `HeaderWidget._load_nerd_font` removed in 020).
- **QSS:** `font_family_qss()` emits stacks into generated rules; weights come
  from `TYPE` tokens.
- **Packaging:** fonts resolve via `boot_paths.ASSETS_DIR/fonts` in dev and
  standalone; verify the standalone copy step in plan 025.
- **Fallbacks:** `Segoe UI` in both text stacks; Qt CJK fallback automatic for
  the 9 supported languages.
- **Accessibility:** Inter 12px body minimum; nothing below 10px; Hanken
  headings ≥ 13px; `text_on_accent` #1C1206 on amber ≈ 8.7:1.

### Type scale v2

| Token | px/weight | Use |
|---|---|---|
| display | 19/700 (Hanken) | masthead, page ribbons |
| title | 14/700 (Hanken) | dialog/drawer titles |
| section | 12/600 (Hanken) | rail zone labels, group headers |
| body | 12/400 (Inter) | default |
| secondary | 11/400 (Inter) | helper text, table cells |
| micro | 10/400 (Inter) | rail micro-labels, chips |
| mono | 11/400 | data values |

## 4. Palette v2 (decided 2026-09-04 — supersedes §values of 2026-09-03)

Single source: `chrome/tokens.py::PALETTES['dark']`. Full binding values in
plan 019 §5. Summary:

- Canvas `#141312` (warm dark, opaque); surfaces `#1B1917` / `#211E1B` /
  `#262220`; warm-gray text `#ECE7E0` / `#A69F94` / `#5C564E`.
- Accent **amber `#F59E0B`** — interactive/selected/focus only.
- **Teal `#2DD4BF`** success/loaded; warning `#E8B44C`; danger `#F87171`;
  info `#93B7DD`; special/editor `#C084FC` (all with bg/border variants).
- Game-domain colors (rarity 1–5, elements, rank) preserved as-is: contract.
- Radii `{3,5,8,pill}`; 4px spacing grid; control heights 24/28/32/36; rows
  28/32 (kept from 002 — sound).
- The cyan #7DD3FC family and all translucent glass surfaces are **retired**.

## 5. Navigation philosophy (v2 — replaces "keep shell topology")

The old sidebar/header/dock topology is rejected (see §0). The shell is:

- **NexusBand** (right edge, 76px): masthead (monogram + dirty dot) →
  navigate zone (12 destinations grouped Load&Inspect / World / Edit /
  Reference, icon+micro-label, amber corner-notch active marker) →
  **InstrumentTray** (save state altitude, selection rows, metric row +
  expandable TrayDrawer) → utilities (console, guide, about).
- **Page ribbons** inside each page: display title + zone label + page-local
  actions; a single pinned `WindowControls` overlay owns min/max/close; drag
  strip = ribbon/empty canvas.
- Page ids, lazy tab construction, and `_on_nav_changed` mapping unchanged.
- Keyboard: Up/Down/Enter in band; Ctrl+1..9/0 page jumps (020).

## 6. Component conventions (kept, with v2 additions)

- Shared widgets in `chrome/components.py`; styling is QSS with objectName +
  dynamic properties; widgets never hand-build QSS strings.
- Every interactive widget defines default/hover/pressed/focus/disabled
  (+selected/checked).
- One confirm-dialog implementation; destructive actions use its danger
  variant. Toasts for success; console/log pane for operation output.
- **Dialog strategy (022, pending):** overlay-sheet dialogs over scrim
  (canvas-local), left-rule + content + right action column, danger actions
  isolated footer-right, selectors as overlay drawers.
- **Table strategy (023, pending):** dense full-bleed tables, rule-separated
  header strip, inline row tools, no per-panel inline QSS.

## 7. Behavior-preservation invariants (binding, unchanged)

- All save I/O, backups, atomic writes, path validation, session/staleness
  checks: untouched. UI never bypasses filesystem validation.
- Save mutation stays in domain functions (`managers/*`, `save_session`).
- Long-running work stays off the GUI thread (`run_with_loading`, workers,
  generation guards). Blocking `processEvents` modal loops in
  `SkillPicker.pick()` / `show_player_select_popup` must not be broken while
  restyling; party-slot lifetime handling; `SearchPanel` signals; splitter
  persistence (now removed with the splitter — settings key ignored safely);
  console detach/attach; drag-drop overlay; update checker thread.
- JSON editor stays read-only-by-default with preview + explicit confirmation.
- Destructive actions: preview + separate confirm step.
- Localization: all visible strings via `t()`; layouts tolerate CJK/Cyrillic
  expansion; no fixed-width labels.
- All 12 page destinations, deep links (`set_active` call sites), menu popup
  actions, TabGuide, about/warnings, discord, update pulse must remain
  reachable in the new shell.

## 8. Decision log

| Date | Decision | Rationale | Alternatives considered |
|------|----------|-----------|-------------------------|
| 2026-09-03 | Reject skill default fonts; adopt Segoe stacks | **SUPERSEDED 2026-09-04** — see 2026-09-04 typography decision | — |
| 2026-09-03 | Keep cyan #7DD3FC accent | **REJECTED 2026-09-04** (reset; identity change required) | — |
| 2026-09-03 | Keep shell topology (sidebar+header+dock) | **REJECTED 2026-09-04** — audit proved it locks in the old UI structure; reset mandates ≥4 structural changes | Full shell replacement via NexusBand (chosen) |
| 2026-09-03 | QSS generated from tokens; darkmode.qss generated artifact | Single source of truth; retained | Hand-written QSS (rejected) |
| 2026-09-03 | `constants.py` compat layer; canonical tokens in chrome | ~400 imports + pinned tests; retained | Big-bang rename (rejected) |
| 2026-09-04 | Mandatory Overhaul Reset: 004–007 rejected as design decisions; 002–003 infra-only; 008–018 frozen | Plans 001–007 audited vs the overhaul objective: structure identical to main (evidence in 019 §3) | Continuing 008+ on old foundation (rejected: propagates failed direction) |
| 2026-09-04 | Adopt bundled Hanken Grotesk + Inter (project mandate); system stacks become fallbacks | Mandate requires the supplied TTFs; fonts.py already auto-registers any TTF | Keep Segoe-only (rejected: conflicts with brief) |
| 2026-09-04 | Palette v2: warm dark + amber accent + teal success; glass/cyan retired | Identity must be materially different; amber/teal on warm black is structurally distinct from cyan glass | Keep cyan with new layout (rejected: brief bans palette-similarity drift toward old identity) |
| 2026-09-04 | Shell v2: full-bleed canvas + right NexusBand rail + page ribbons; no sidebar, no results dock | Navigation model, results presentation, and page composition all change structurally (≥4 required changes) | Top tab bar (rejected: density); left rail flip (rejected: same sidebar concept) |
| 2026-09-04 | Results/statistics become InstrumentTray altitudes + canvas-local TrayDrawer overlay | Removes the splitter-dock geometry; keeps all selection/stats call sites via facade | Keep right dock (rejected: old structure) |
| 2026-09-04 | Screenshot QA pending: code-based structural redesign is the verification mode | Model cannot input images; honesty requirement | Claiming visual QA (forbidden) |
| 2026-09-04 | Plan 025 close-out executed: legacy chrome files (sidebar_widget/header_widget/results_widget) deleted; NerdBtn/NerdLabel moved to chrome/components.py; facades removed; call sites direct to nexus_band/tray/_window_controls; `_setup_ui_legacy` + `use_nexus_shell` guard removed; legacy-dark.qss purged 80 dead blocks (16.3 kB → 5.0 kB); chrome/styles.py constants swept to warm palette (names preserved — ~20 consumers); default settings pruned | Transitional debt end-state; behavior verified by full suite + smokes | Keeping facades indefinitely (rejected: debt) |
| 2026-09-04 | docs/ui-system.md created as the implementation reference | Persistent how-to companion to the design thesis | Keeping reference inside plan files (rejected: scattered) |

## 9. Architectural decisions that must not be casually changed

1. Token dict `PALETTES` + `resolve()` in `chrome/tokens.py` is the only
   color source; scanner-enforced.
2. `constants.py` remains the compatibility layer; pinned by
   `tests/unit/palworld_aio_tests/test_constants.py` (update values + test in
   the same commit).
3. QSS is generated (`qss_builder.py` → `build_theme.py` → `darkmode.qss`).
4. Fonts are registered centrally once (`chrome/fonts.py`); no per-widget
   font loading.
5. Facades (`main_window.sidebar` / `main_window.results_widget`) keep legacy
   call sites working over the new band/tray; remove only in plan 025
   closeout after all call sites migrate.
6. `use_nexus_shell` setting is the rollback hatch; legacy shell code path
   remains until 025.

## 10. Known design debt

- legacy-dark.qss retains 31 blocks for objectNames still in code awaiting
  geometry-level r02 passes (pal editor family, base/player inventory
  internals, hover overlays). Shrinks per migration; delete when empty.
- Deep geometry recomposition of Base Inventory, Player Inventory, and
  Pal Editor remains open (009/010/011-r02 layouts) — palette + chrome are
  migrated, layouts not re-architected.
- MenuPopup styling predates the sheet grammar (works, tokenized; restyle
  optional).
- Old settings keys may remain in users' user.cfg files (harmless, unread).

## 11. Screenshot reference registry

| Folder | Screen | Inspected | Plan | Notes |
|---|---|---|---|---|
| `ib/image/tools-tab` | Start (Tools) | No — image input unavailable; code-audited instead | 021 | 3 files incl. loading state |
| `ib/image/base-inventory` | Base Inventory | No | 008 (revise) | incl. item picker popup |
| `ib/image/player-inventory` | Player Inventory | No | 011 (revise) | incl. slot→item picker |
| `ib/image/pal-editor` | Pal Editor | No | 010 (revise) | 8 files: slots, stats popup, skill pickers, level popup |
| `ib/image/search-players` | Search Players | No | 007 (rejected; re-plan) | incl. 4 bulk dialogs + guild assignment |
| `ib/image/search-guilds` | Search Guilds | No | 007 (rejected; re-plan) | |
| `ib/image/search-bases` | Search Bases | No | 007 (rejected; re-plan) | |
| `ib/image/map-viewer` | Map Viewer | No | 009 (revise) | |
| `ib/image/exclusions` | Exclusions | No | 014 (revise) | |
| `ib/image/json-editor` | JSON Editor | No | 013 (revise) | |
| `ib/image/breeding` | Breeding | No | 012 (revise) | incl. pal selector |
| `ib/image/docs-tab` | Docs/Wiki | No | 015 (revise) | |
| `ib/image/menu.png` | Header menu popup | No | 022 | top-level file |

All entries: screenshots are functional references only; visual QA claims are
prohibited for this session's work (see §2).

## 12. Verification vocabulary (do not conflate)

- **Implementation verification:** code exists, compiles, scanner-clean.
- **Functional verification:** pytest suite + smoke workflows offscreen.
- **Code-based structural verification:** widget-tree assertions + divergence
  matrix conformance.
- **Screenshot-based visual verification:** NOT PERFORMED (pending manual
  review). Final reports must distinguish these.
