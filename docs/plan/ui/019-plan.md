# 019 — Design Reset: "Deck Operations" (Foundation v2)

> **Status: ACTIVE — supersedes the design direction of plans 002–007.**
> This plan is the Mandatory Overhaul Reset required by the project brief.
> It re-derives the design thesis, palette, typography, and navigation model
> from scratch and defines the divergence matrix that every later plan must
> satisfy. Plans 008–018 are frozen pending this reset (see 000-index.md).

## 1. Objective

Re-establish the design foundation so the application is **structurally
different** from the old UI (persistent left sidebar + header + right results
dock), not a reskin of it. This plan changes *what the shell is*, not just what
it looks like. It is executed together with plan 020 (shell) and plan 021
(Start page).

## 2. Scope

**In scope:** design thesis v2, palette v2 (new hue family), typography v2
(bundled Hanken Grotesk + Inter as mandated), navigation model replacement,
results/statistics presentation replacement, start-page composition, token
infrastructure changes, font loading, constants compatibility layer, pinned
test updates, scanner whitelist additions.

**Out of scope:** the 12 feature screens' internal layouts (plans 008–018,
frozen), dialogs (022), a11y pass (024), regression/cleanup (025).

## 3. Audit findings (evidence)

### 3.1 Old shell (main branch, pre-overhaul)

Frameless 1448×800 window, `header → [sidebar 48/168px | QSplitter → [12-page
QStackedWidget | ResultsWidget dock 320–480px]] → hidden QStatusBar + detachable
console window`. Glass-gradient cards (`rgba(18,20,24,0.65)`), cyan `#7DD3FC`
accent everywhere, chip-based header, 12-item flat sidebar.

### 3.2 Current branch after plans 001–007

`git diff main...HEAD --stat` + code audit prove the shell topology is
**identical to main**:

| Evidence | Finding |
|---|---|
| `main_window.py:_setup_ui` | Same skeleton: `HeaderWidget` → `QHBoxLayout` → `SidebarWidget` + `QSplitter` → `QStackedWidget` + `ResultsWidget` |
| `sidebar_widget.py` diff comment | *"Visual groups; page ids and tab indexes are unchanged (grouping is labels only)."* |
| `results_widget.py` | Same 320–480px right dock, same value cards; inline styles removed, geometry unchanged |
| `tools_tab.py` | Same save-card + two glass card grids (Converting / Management) |
| QSS | Hand-written 1693-line QSS → generated from tokens; palette nearly unchanged (`canvas #0A0B0E → #0A0C10`, same `#7DD3FC`) |

**Verdict: tokenization + recoloring, not an overhaul.** Plans 004–007 are
REJECTED as design decisions; 002–003 (tokens/components) are retained as
infrastructure only, with the palette/typography content of 002 replaced by
this plan.

## 4. Design thesis v2 — "Deck Operations"

PalTrainer is a **flight-deck for save surgery**: a working canvas surrounded
by mission equipment. The operator never leaves the canvas; equipment comes to
them in a single rail they own.

1. **The canvas is the screen.** No permanent sidebar, no permanent results
   panel. The working page gets the full window minus one narrow control rail
   (the NexusBand, 76px). Global chrome is minimal; each page owns a "page
   ribbon" (title + zone label + page actions) instead of a global bar owning
   half the identity.
2. **One rail, everything docked.** Navigation, save lifecycle, selection, and
   statistics live in a **single vertical instrument rail** on the right edge
   (`chrome/nexus_band.py`), organized by altitude: navigate → save state →
   selection → statistics → utilities.
3. **Warm dark, flat surfaces, structure from rules not boxes.** Deep
   warm-neutral canvas (#141312 family), **amber** (`#F59E0B`) interactive
   accent, **teal** (`#2DD4BF`) loaded/success semantics. Amber+teal on warm
   near-black replaces the old cyan-on-blue-black glass. No gradients, no
   glass, no glow; hierarchy via 4px-grid spacing and hairline rules.
4. **Typography as structure.** Bundled Hanken Grotesk for display/heading/nav;
   Inter for body/controls/tables (see §6).
5. **Data semantics are the only other color.** Pal rarity/element/rank colors
   untouched (data contract); semantic hues re-derived for the warm canvas.

### 4.1 Divergence matrix (binding for all later plans)

| Area | Existing (old + current) | New (v2) | Why it is different |
|---|---|---|---|
| Shell | Persistent left sidebar (48/200px) + top header bar + right Results dock (320–480px) in a splitter + detachable console window | **No left sidebar.** Full-bleed canvas; right-edge **NexusBand** rail (76px) owning nav + save state + selection; console moves into the rail's tray | Navigation model replaced: sidebar → integrated right instrument rail; results dock deleted as a geometry concept |
| Navigation | 12 flat icon/label buttons in left panel, painted accent bar | NexusBand: icon+micro-label stacked buttons grouped into mission zones, amber active state with corner-notch marker, save-state + dirty dot at rail top | Different widget type, position, grouping, active-state geometry |
| Results | Permanent right dock with player/guild/base value cards + stats grid, splitter-resizable | **InstrumentTray** (rail sections + overlay drawer on canvas, not a window) with selection rows and stats deltas | Results are rail altitude + overlay drawer, not a dockable pane |
| Statistics | Stats grid inside results dock | Statistics altitude in the rail; full grid in tray drawer | Stats move from dock to rail + overlay |
| Start page | Centered 340px save card + two glass card grids of tool cards | **Operations masthead** (save lifecycle ledger) + mission-zone **columns of text-first operation rows** (no cards) | Card grid → ledger + text rows |
| Page composition | Content + global header above all pages | **Page ribbon** (title + zone + page-local actions) inside each page; global chrome minimal | Global header demoted; pages own their ribbon |
| Dialogs | Styled QMessageBox-family with one-off styles | Overlay-sheet dialogs (canvas-local frame over scrim), left-rule + content + action column; danger isolated footer-right | New dialog strategy (plan 022) |
| Tables | SearchPanel tree with per-panel inline QSS | Dense full-bleed tables, rule-separated header strip, inline row tools, no per-panel QSS | New table strategy (plan 023) |
| Palette | Near-black cool canvas, glass panels, cyan accent, 10px pills | Warm dark #141312, opaque flat surfaces, amber accent + teal success, radius 3/5/8 | Different hue family, translucency removed |
| Typography | Segoe UI Variable system stacks | Bundled Hanken Grotesk + Inter | Different families, centrally loaded, packaged |

### 4.2 Acceptance gate (binding)

A screen passes only if old vs new reads as a *different application*. Every
major screen must change composition, hierarchy, navigation relationship,
spacing rhythm, and information grouping — colors/fonts alone never suffice.

## 5. Palette v2 (binding values)

In `chrome/tokens.py` `PALETTES['dark']` (same dict shape, new values):

```python
# surfaces — warm dark, opaque
'canvas':        '#141312',
'surface':       '#1B1917',
'surface_raised':'#211E1B',
'surface_input': '#262220',
'surface_hover': rgba('#F59E0B', 0.07),
'surface_active':rgba('#F59E0B', 0.12),
# text — warm grays
'text':          '#ECE7E0',
'text_secondary':'#A69F94',
'text_disabled': '#5C564E',
'text_on_accent':'#1C1206',
# borders
'border':        rgba('#ECE7E0', 0.10),
'border_strong': rgba('#ECE7E0', 0.18),
# accent — amber, interactive only
'accent':        '#F59E0B',
'accent_hover':  '#F7B03A',
'accent_pressed':'#D98A06',
'accent_bg':        rgba('#F59E0B', 0.10),
'accent_bg_strong': rgba('#F59E0B', 0.18),
'accent_border':    rgba('#F59E0B', 0.30),
'accent_border_strong': rgba('#F59E0B', 0.50),
# secondary semantic — teal (loaded/success + editor-link)
'success':        '#2DD4BF',
'success_bg':     rgba('#2DD4BF', 0.10),
'success_border': rgba('#2DD4BF', 0.30),
'warning':        '#E8B44C',
'warning_bg':     rgba('#E8B44C', 0.12),
'warning_border': rgba('#E8B44C', 0.35),
'danger':         '#F87171',
'danger_bg':      rgba('#F87171', 0.12),
'danger_border':  rgba('#F87171', 0.35),
'info':           '#93B7DD',
'info_bg':        rgba('#93B7DD', 0.10),
'info_border':    rgba('#93B7DD', 0.30),
'special':        '#C084FC',
'special_bg':     rgba('#C084FC', 0.12),
'special_border': rgba('#C084FC', 0.30),
'error':          '#F87171',
# floating
'tooltip_bg':     rgba('#211E1B', 0.98),
'menu_bg':        rgba('#1B1917', 0.98),
'overlay_scrim':  rgba('#0D0C0B', 0.62),
```

`warning` is amber-family but distinct from the accent by treatment: accent
never appears on non-interactive elements; warning chips carry bg+border+icon.

Game-domain colors (rarity/element/rank) **unchanged**.

### 5.1 Constants compatibility layer

`constants.py` re-points: `BG='#141312'`, `GLASS='#1B1917'`,
`ACCENT='#F59E0B'`, `TEXT='#ECE7E0'`, `MUTED='#A69F94'`,
`TEXT_DISABLED='#5C564E'`, `SUCCESS='#2DD4BF'`, `ERROR/DANGER='#F87171'`,
`WARNING/ALERT='#E8B44C'`, `INFO='#93B7DD'`, `SPECIAL='#C084FC'`,
`SURFACE_ELEVATED='#211E1B'`, `BORDER='#2A2624'`, `BUTTON_FG='#F59E0B'`,
`BUTTON_HOVER='#2E2A26'`, `SURFACE_HOVER='rgba(245,158,11,0.07)'`,
`BORDER_SUBTLE='rgba(245,158,11,0.15)'`, `ACCENT_BG='rgba(245,158,11,0.10)'`,
`ACCENT_BG_STRONG='rgba(245,158,11,0.18)'`,
`ACCENT_BORDER='rgba(245,158,11,0.20)'`,
`ACCENT_BORDER_HOVER='rgba(245,158,11,0.35)'`,
`ACCENT_BORDER_FOCUS='rgba(245,158,11,0.40)'`. Pinned test updated same commit.

## 6. Typography v2 (binding)

| Role | Family (TTF bundled in resources/assets/fonts/) | Stack | Use |
|---|---|---|---|
| Display/heading/nav | Hanken Grotesk | `['Hanken Grotesk','Segoe UI']` | Page ribbons, section titles, NexusBand labels, CTA labels |
| Body/data | Inter | `['Inter','Segoe UI']` | Body text, controls, tables, dialogs |
| Data/mono | Cascadia Mono / Consolas (system) | unchanged | UUIDs, paths, JSON, coords |
| Icons | Hack Nerd Font (bundled) | unchanged | icons.py registry only |

- Loading: `chrome/fonts.py` registers every TTF under `resources/assets/fonts`
  (both new TTFs already present); stacks change to the above;
  `heading_font()` default weight 700.
- QSS: `font_family_qss()` flows into generated rules.
- Packaging: fonts load from `ASSETS_DIR/fonts` in dev and standalone
  (existing copy step; verify in plan 025).
- Fallbacks: `Segoe UI`; CJK fallback automatic via Qt.
- Accessibility: Inter 12px body; minimum 10px; Hanken ≥13px headings.

### Type scale v2

| Token | px/weight | Use |
|---|---|---|
| display | 19 / 700 (Hanken) | masthead, page ribbons |
| title | 14 / 700 (Hanken) | dialog/drawer titles |
| section | 12 / 600 (Hanken) | rail zone labels, group headers |
| body | 12 / 400 (Inter) | default |
| secondary | 11 / 400 (Inter) | helper text, table cells |
| micro | 10 / 400 (Inter) | rail micro-labels, chips |
| mono | 11 / 400 | data values |

## 7. Token scale adjustments

- `RADIUS`: `{sm:3, md:5, lg:8, pill:9999}` (was 4/6/8).
- `SPACING`, `HEIGHT`, `ROW`: unchanged (retained from 002 — sound).
- `TYPE`: updated per §6.

## 8. Downstream plan dependencies

- **020** shell v2 (NexusBand + ribbon) implements §4.
- **021** Start page v2 implements the masthead/ledger composition.
- **022** (new) dialog strategy: overlay-sheet dialogs, action column, danger
  isolation, selector drawers.
- **023** (new) table strategy: dense full-bleed tables, no per-panel QSS.
- Plans 008–018 frozen; each must be revised against the divergence matrix
  before execution (banners added in this session).

## 9. Implementation tasks

1. `chrome/tokens.py`: palette v2; `TYPE` per §6; `RADIUS` per §7; transitional
   aliases re-derived (names kept, values amber/teal).
2. `constants.py`: compatibility values per §5.1.
3. `chrome/fonts.py`: stacks per §6; `heading_font()` default 700.
4. `chrome/qss_builder.py`: verify token flow; emit new stacks; shell-specific
   rules rewritten in plan 020.
5. `tests/.../test_constants.py`: pinned hexes updated same commit.
6. `tests/.../test_design_tokens.py`: palette assertions updated if pinned.
7. `scripts/scrs/check_theme_violations.py`: whitelist `chrome/nexus_band.py`,
   `chrome/instrument_tray.py`.
8. Rebuild theme: `uv run python scripts/scrs/build_theme.py`.

## 10. Tests

- Unit: pinned-constants + token tests pass with new values.
- `uv run pytest -c tests/pytest.ini` full suite green.
- `uv run python -m compileall -q src tests scripts`.
- `uv run pyright src`: no new error classes vs 523-error main baseline.
- Scanner: `uv run python scripts/scrs/check_theme_violations.py` ≤ 1390.

## 11. Visual QA

- **Screenshot inspection unavailable** (model has no image input — recorded
  in 000-design-context.md §12). QA is code-based: offscreen smoke launch +
  captured screenshots for the user's manual review + structural assertions
  (no sidebar object, rail present, no right dock widget).
- Marked pending manual review until a capable agent or the user inspects.
- Old-vs-new must confirm: no left sidebar; amber/teal identity; Hanken/Inter
  rendering; rail navigation.

## 12. Risks

- ~400 `constants.*` consumers shift hue silently — pinned tests + full suite;
  scanner catches literals.
- Contrast: `text_on_accent` on amber ≈ 8.7:1; accent on canvas ≈ 6.9:1;
  muted on surface ≈ 5.2:1 — all pass UI thresholds.
- Rail + content on 1200px min width: content ≥ 1100px — safe.
- Unmigrated screens inherit alias hue shift — desired; fix unreadable combos
  via alias values, not screen reverts.

## 13. Rollback

Two-file revert (`tokens.py`, `fonts.py`) + constants + tests. Shell v2 (020)
separately revertable via `use_nexus_shell` user-setting (legacy construction
path retained during transition; legacy files removed only in plan 025
closeout).
