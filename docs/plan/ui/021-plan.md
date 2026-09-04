# 021 — Start Page v2: Operations Masthead + Mission Columns

> **Status: ACTIVE — implements the Start ("Tools") page per the 019 reset.**
> Supersedes plan 005 (dashboard), REJECTED as a design decision: the 005
> result kept the old save-card + two glass card grids. Retained from 005:
> token migration technique, drag-drop wiring, stat deep-links concept,
> status property transitions.

## 1. Objective

Recompose the Start page (page id `tools`, tab 0, `tools_tab.py`) as the
Deck Operations home: a horizontal **operations masthead** (save lifecycle as
a ledger, not a card), a **campaign strip** (conversion + transfer tools as a
single sequence), and **mission-zone columns** of text-first operation rows.
Zero cards, zero glass panels.

## 2. Scope

**In scope:** `ui/tabs/tools_tab.py` full recomposition; qss_builder rules for
new objectNames; drop-overlay integration; stat deep-links (now via
`window.set_active_page(id)`).

**Out of scope:** dialog bodies opened by tools (022); shell (020).

## 3. Functionality inventory to preserve (from current code)

- Load Steam save / Load XGP save buttons; drag-and-drop save loading
  (window-level `DropOverlay` stays).
- Save path display (mono, click opens folder) + save status label.
- Post-load stats: players/guilds/bases/pals counts with deep-link nav to
  their screens (tools_tab.py:338 `sidebar.set_active(k)` +
  `_on_nav_changed(k)` — retarget via band facade).
- All 7 tools in two groups — Converting: convert saves, gamepass↔steam,
  steamid, restore map; Management: slot injector, character transfer,
  host-save fix — each currently a `ToolCard` with icon/title/desc emitting
  `clicked` → dialog flows. **All 7 must remain one click away.**
- `refresh()` updates stats + status; `refresh_stats_after()` hook.
- DropOverlay paint logic reused.

## 4. New composition

```
┌──────────────────────────────────────────────────────────────────┐
│ ribbon: START · zone Load & Inspect          [window controls]   │
├──────────────────────────────────────────────────────────────────┤
│ OPERATIONS MASTHEAD (no card; ruled top/bottom, 2 rows)          │
│  row1: WORLD SAVE  ▸ world-name-or-'No save loaded'  [state dot] │
│        path.mono (or 'Load a world to begin')        [pulse]     │
│  row2: [ LOAD STEAM ]  [ LOAD XGP ]   · drop hint text           │
├──────────────────────────────────────────────────────────────────┤
│ FIELD REPORT:  12 PLAYERS · 3 GUILDS · 8 BASES · 412 PALS        │
│ (single text-first metric line, mono digits, each count is a     │
│  deep-link trigger; before/after deltas shown after operations)  │
├──────────────────────────────────────────────────────────────────┤
│ CAMPAIGN STRIP (numbered 01→04, single row, rule-separated):     │
│  01 Convert Save · 02 GamePass⇄Steam · 03 Transfer Characters    │
│  04 Fix Host Save                                                │
├──────────────────────────────────────────────────────────────────┤
│ MISSION COLUMNS (4 text-first columns under zone headings)       │
│  CONVERT              WORLD DATA           MAINTENANCE   REFERENCE│
│  ─ Convert saves      ─ Slot injector      ─ Restore map ─ Tab guide│
│  ─ GamePass⇄Steam     ─ Character transfer │             │          │
│  ─ Steam ID           ─ Host-save fix      │             │          │
│ rows = icon+label+desc (Inter 12/11), hover=warm surface + amber │
│ title, click opens the same dialog flow as old ToolCard          │
└──────────────────────────────────────────────────────────────────┘
```

Differences vs old (binding): no centered 340px card; no `#saveCard`,
no `#toolCard`, no `QFrame#glass` sections; masthead is full-width ledger
rows; operations are text rows in columns (scan by reading, not by hunting
card tiles); campaign strip gives the 4 critical ops a numbered sequence;
field report replaces the 4 stat boxes-with-icons.

## 5. Implementation tasks

1. `tools_tab.py`: rebuild `_setup_ui` — masthead builder, field-report
   builder, campaign strip builder, mission columns builder. Keep
   `DropOverlay`, all dialog-launch slots, `refresh()`,
   `refresh_stats_after()`, deep-link targets (swap `sidebar.set_active`
   → band facade).
2. `qss_builder.py`: delete `#saveCard/#toolCard/#dashboardIconLabel/
   #statValueLabel/#statNameLabel/#statIconBtn/#loadSteamBtn/#loadXgpBtn/
   #saveStatusLabel/#savePathLabel/#dragHintLabel` blocks; add
   `#opsMasthead`, `#opsWorldName`, `#opsSavePath`, `#opsStateDot`,
   `#opsLoadBtn` (primary CTA amber, secondary quiet), `#fieldReport`,
   `#fieldMetric` (mono), `#campaignStrip` + `#campaignStep`,
   `#missionColumn`, `#missionRow` (hover/pressed/disabled states).
3. Empty state (no save): masthead shows quiet prompt + primary Load buttons;
   field report shows em-dash metrics — no blank void.
4. Loaded state: world name (from save manager when available), path, state
   dot amber pulsing when dirty (port pulse logic).
5. Localization: all strings via `t()`; columns are stretch-equal so CJK
   expansion is safe; campaign strip min-width via `adjustSize()` fallback.

## 6. Behavior preservation checklist

- Same 7 dialog entry points, same slots, same argument wiring.
- Steam/XGP load buttons call the same handlers.
- Deep links: players/guilds/bases/pals counts navigate to the same pages.
- `refresh()` called by `main_window.refresh_all()` keeps semantics.
- Drag-drop still loads a save via the same path validation flow.

## 7. Tests

- Smoke: masthead renders 2 rows; field report shows 4 metrics; 7 mission
  rows present; each row's click emits expected handler (assert wiring);
  deep-link click calls facade `set_active`.
- Full suite + compileall + pyright delta + scanner count drop (old card
  blocks removed).

## 8. Visual QA

Code-based: structural assertions (no `#saveCard`/`#toolCard` objects in
tree; masthead present; 4 columns), offscreen screenshots saved for manual
review. Screenshot-based QA pending (see 019 §11).

## 9. Risks

- Mission columns on 1200px width: 4 columns ≈ 280px each — desc text
  wraps; keep desc to one line with ellipsis.
- World-name availability varies by save state — use save-manager API
  defensively with em-dash fallback.

## 10. Rollback

Single-file revert (`tools_tab.py`) + qss block restore; dialog slots
untouched.
