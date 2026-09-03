# UI Design Context — PalTrainer Overhaul

This file is the persistent source of truth for the UI overhaul's design decisions.
Any session (human or AI) continuing the overhaul must read this file first, together
with `000-index.md` and `PROGRESS.md`. Update it whenever a significant design or
architectural decision is made.

---

## 1. Design thesis

**"The Save Workshop" — an instrument-grade workstation for editing a living save file.**

PalTrainer is not a consumer app and must not look like a generic admin dashboard.
Every screen is a workbench surface over one shared artifact: the loaded save.
The visual language therefore:

1. **Data is the protagonist.** Tables, stats, inventories and maps carry the visual
   weight. Application chrome (sidebar, header, panels) recedes: quiet surfaces,
   hairline borders, no decorative glow.
2. **One accent, many meanings.** A single cool accent (existing PalTrainer cyan)
   marks interactivity and selection — nothing else. Color otherwise communicates
   *meaning only*: success / warning / danger / info / special states, plus the
   game-domain rarity and element colors, which are a data contract and never
   decorative.
3. **Density with rhythm.** A 4px grid, fixed control heights and row heights keep
   dense data calm. Reference screens (Dashboard, Docs) may breathe; data screens
   stay compact.
4. **Safe by design.** Destructive flows are visibly distinct (danger styling),
   always previewed, always confirmed. Save state (no save / loading / loaded /
   dirty / saving / error) is surfaced in the shell, not buried in logs.
5. **Cohesion over decoration.** No gradients as decoration, no glassmorphism,
   no neon glow, no emoji icons. Elevation is expressed with tonal surfaces and
   1px borders; shadows are reserved for true floating layers (menus, popups).

Anti-slop constraints adopted (binding for all plans): no generic SaaS layouts,
no recolor-only "overhaul", no decorative effects without function, no per-screen
one-off colors, no wall-to-wall rounded cards, no oversized headings, no hiding of
overflow to mask layout bugs, no removal of useful information for aesthetics.

---

## 2. Typography (decided)

The pyqt6-ui-designer skill defaults (Hanken Grotesk headings / Inter body) are
**rejected** for this project: neither font is installed on target machines, and the
app is an offline Windows-first desktop tool. Verified installed fonts (Win11 host):
Segoe UI Variable (Text/Display/Small), Segoe UI, Cascadia Code/Mono, Consolas,
Bahnschrift, Leelawadee UI, Malgun/Yu Gothic; bundled font: `HackNerdFont-Regular.ttf`.

| Role | Font stack (QFont.setFamilies) | Notes |
|------|-------------------------------|-------|
| Body / UI | `Segoe UI Variable Text`, `Segoe UI` | Win11 variable font; clean Win10 fallback |
| Headings / display | `Segoe UI Variable Display`, `Segoe UI` | heavier weights, tighter tracking |
| Data / mono (UUIDs, JSON, counts, coords) | `Cascadia Mono`, `Consolas` | mono without ligatures — data integrity |
| Icons | `Hack Nerd Font` (bundled) | existing `chrome/icons.py` registry; registered via `QFontDatabase` |

Rationale: zero new font assets or licenses, native Windows rendering at small sizes,
automatic CJK fallback for the 9 supported languages. A future OFL font bundle can be
added under `resources/assets/fonts/` — the loader must register any TTF found there.

### Type scale (kept deliberately compact — this is a dense data tool)

| Token | px / weight | Use |
|-------|-------------|-----|
| display | 20 / 600 | page titles only |
| title   | 15 / 600 | section titles, dialog titles |
| section | 13 / 600 | panel headers, group labels |
| body    | 12 / 400 | default UI text |
| secondary | 11 / 400 | muted helper text, table cells |
| micro   | 10 / 400 | status bar, chips, captions |
| mono    | 11 / 400 (12 in JSON editor) | data values, UUIDs, paths |

Oversized headings are banned: workspace stays with the data.

---

## 3. Color tokens (decided)

Palette is defined **once** in `palworld_aio/ui/chrome/tokens.py` as a theme dict.
Dark ships first (see theme decision); the dict shape is the contract for a future
light theme.

- Canvas: deep neutral slate (near-black, slightly cool), **flat** — no gradient wash.
- Surfaces: 3 levels — `canvas < panel < raised` — separated by tonal steps and
  hairline borders, not shadows.
- Accent: existing `#7DD3FC` family retained (brand continuity, game-adjacent cyan),
  used **only** for interactive/selected/focus states. Accent-tinted borders are
  demoted from "everything" to "focus + selection".
- Semantic: success / warning / danger / info / special with bg + border variants.
- Game data colors (rarity 1–5, elements, rank) are preserved as-is: contract, not style.
- The old decorative rainbow (gold version chip, purple menu chip, green game-version
  chip, blurple Discord chip as *styles*) is dissolved into neutral chips with
  semantic states. Brand hue stays on interactive elements.

`constants.py` color names (BG, ACCENT, TEXT, …) remain as a compatibility layer for
the ~400 existing imports and are re-pointed at the token dict (values pinned by
`tests/unit/palworld_aio_tests/test_constants.py` — the test is updated in the same
commit when values change).

---

## 4. Spacing / radius / elevation (decided)

- 4px grid: 4 / 8 / 12 / 16 / 24 / 32. `SPACE_MD=12` stays (existing convention).
- Control heights: 24 (compact) / 28 (default) / 32 (comfortable) / 36 (primary CTA).
- Table/tree rows: 28 dense (default for data screens) / 32 standard.
- Radius scale: 4 (inputs, small controls) / 6 (buttons, chips, menus) /
  8 (panels, cards, dialogs). Pills (9999) only for status dots and badges.
- Elevation: 0 = canvas, 1 = panel/raised (1px border, tonal), 2 = floating
  (menus, popups, tooltips — 1px border + soft shadow allowed). No shadows on
  static layout elements.

---

## 5. Icon strategy (decided)

Hack Nerd Font glyphs via the central registry `palworld_aio/ui/chrome/icons.py`
(nerdfont package → canonical codepoint fallback → `'?'`). One icon style only.
No emoji as icons (existing emoji fallbacks already removed by `icons.py`; plan 018
removes remaining stragglers). New icons must be registered in `icons.py`, never
inlined per-file.

---

## 6. Theme strategy (decided)

**Dark-only at ship time; architecture theme-ready.**

Reason: every one of the ~390 inline `setStyleSheet` call sites and the whole QSS
surface assumes dark; shipping a light theme in the same pass would multiply QA
surface without user demand. The token module is nevertheless built as
`PALETTES = {'dark': {...}}` + `resolve(theme)` so a light theme is a new dict plus
QSS regeneration — not a rewrite. `ThemeManager` gains a `theme` concept and the
generated QSS builder lives in the chrome layer. `resources/ui/themes/darkmode.qss`
stays as the deployed artifact for the boot splash; it is regenerated from the same
tokens (script) rather than hand-maintained.

---

## 7. Shell & navigation philosophy (decided)

Keep the proven shell topology — **sidebar (left, collapsible) + custom header
(frameless window controls) + tab stack + right results dock + detachable console** —
and renovate it, not replace it:

- Sidebar: 12 entries grouped into labeled sections (Load & Inspect / World Data /
  Editing / Reference), active indicator as a left accent bar, icon+label rows,
  keyboard navigable. Existing page ids and lazy-load indexes unchanged.
- Header: app identity left; save-state chip and dirty indicator center-right;
  actions right; window controls far right. The update pulse, warnings button,
  about, guide, save, discord, console controls are preserved functionally.
- Results dock: collapsible, splitter-driven, unchanged behavior.
- Save lifecycle (from `palworld_aio.shell_state.ShellStateModel`) becomes visible
  in the header: NO_SAVE / LOADING / LOADED / DIRTY / SAVING / ERROR.

---

## 8. Component conventions (decided)

- Shared widgets live in `palworld_aio/ui/chrome/components.py` (new) and
  `palworld_aio/widgets/` (existing, migrated).
- Styling is QSS with objectName + dynamic-property selectors; widgets set
  properties, never hand-built QSS strings. `style().polish()` after property
  changes (existing pattern, kept).
- Factories over subclasses where a widget is config-only (buttons, badges, chips).
- Every interactive widget defines default/hover/pressed/focus/disabled (+selected,
  +checked where applicable).
- One confirm-dialog implementation; destructive actions use its danger variant.
- Toasts for success feedback; status bar/console remains for operation logs.

---

## 9. Behavior-preservation invariants (binding)

- All save I/O, backups, atomic writes, path validation, session/staleness checks:
  untouched by UI work. UI never bypasses filesystem validation.
- Save mutation stays in domain functions (`managers/*`, `save_session`); where UI
  dialogs currently violate this (technology dialog writes saves), the fix must
  move logic to domain code, not change behavior.
- Long-running work stays off the GUI thread (`run_with_loading`, worker threads,
  generation guards) — preserved and extended, never removed.
- Known fragile spots that must NOT be broken while restyling: blocking
  `processEvents` modal loops in `SkillPicker.pick()` / `show_player_select_popup`;
  party-slot widget lifetime handling; `SearchPanel` signals; splitter persistence;
  console detach/attach; drag-drop overlay; update checker thread.
- JSON editor stays read-only-by-default with preview + explicit confirmation.
- Localization: all visible strings through `t()`; layouts must tolerate
  zh/ja/ko/ru/de/es/fr/pt text expansion (no fixed-width labels).

---

## 10. Decision log

| Date | Decision | Rationale | Alternatives considered |
|------|----------|-----------|-------------------------|
| 2026-09-03 | Reject skill default fonts (Hanken/Inter); adopt Segoe UI Variable + Cascadia Mono stacks | Not installed on hosts; Windows-first app; no new assets; CJK safety | Bundling Inter/Hanken TTFs (OFL) — possible future enhancement, loader already supports it |
| 2026-09-03 | Keep cyan `#7DD3FC` accent family | Brand continuity, game-adjacent, pinned by tests; hue is fine — its *overuse* was the problem | Full hue change (rejected: gratuitous recolor risk, test churn) |
| 2026-09-03 | Dark-only theme, theme-ready token architecture | ~390 dark-assuming call sites; QA surface control | Ship light+dark together (rejected: risk without demand) |
| 2026-09-03 | Keep shell topology; renovate not replace | Existing shell is recent, functional, user-tested | Full shell rewrite (rejected: churn without gain) |
| 2026-09-03 | Sidebar gains section grouping; page ids unchanged | 12 flat items scan poorly; grouping aids navigation | Two-column nav, top tabs (rejected: density + muscle memory) |
| 2026-09-03 | QSS generated from tokens in chrome layer; darkmode.qss becomes generated artifact | Single source of truth; scanner whitelist already covers chrome | Keep hand-written QSS (rejected: drift caused current mess) |
| 2026-09-03 | `constants.py` remains compatibility layer; canonical tokens move to `chrome/tokens.py` | ~400 imports + pinned tests; gradual migration path | Big-bang rename (rejected: enormous diff, review risk) |
