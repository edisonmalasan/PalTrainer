# PalTrainer UI/UX Improvement Plan

This document operationalizes the previous UI redesign milestones (UI-001…UI-008, now superseded by this plan) into a concrete, evidence-based implementation plan. It replaces the earlier milestone-only roadmap in this file.

## Scope and non-goals (inherited from the previous roadmap)

- Preserve the existing feature scope and save behavior. No new save-editing capabilities.
- No change to serialization, storage, backup, stale-file, or mutation semantics.
- One intentional, flagged exception: the JSON tab import guard (Section 6.10, P1) — approved separately because it closes a safety-invariant gap.
- No direct coupling between visual components and raw save data.
- The redesign may improve navigation, layout, hierarchy, components, styling, responsiveness, accessibility, and usability. Existing visual styling and widget arrangement need not be preserved, but every workflow must remain available.

## Evidence base

All findings below were verified against the source (file:line references). The project's own scanner, `scripts/scrs/check_theme_violations.py`, is the baseline metric:

```text
FAIL — 1445 violations found across 50 files (798 errors, 647 warnings)
```

Related code metrics: 1,027 `setStyleSheet` calls across `src/` (~90 distinct hard-coded hex values); `resources/ui/themes/darkmode.qss` is 1,533 lines; `src/palworld_aio/ui/main_window.py` is ~2,500 lines. Launching the app for a live visual pass was not performed as part of this audit; visual claims below are inferred from code and marked where runtime confirmation is needed ("Needs verification").

---

## 1. Executive Summary

PalTrainer's UI does not lack design intent — it lacks **enforcement**. A dark theme exists (`darkmode.qss` + `ThemeManager` in `src/palworld_aio/ui/chrome/styles.py`), design tokens exist in `src/palworld_aio/constants.py`, and several shared styles (`DIALOG_STYLE`, slot helpers) are already defined centrally. In practice, the token layer is bypassed: over a thousand inline styles re-declare near-identical QSS with drifting values, producing ~90 distinct hex colors, four off-whites for primary text, four reds, six greens, eight button heights, and a second, conflicting accent (`constants.ACCENT = '#3B8ED0'` vs the de-facto accent `#7DD3FC` used ~214 times).

The plan therefore prioritizes in this order:

1. **Token foundation (P0)** — one semantic token vocabulary in code + QSS, deduplicated, with the existing `check_theme_violations.py` scanner wired into verification so violations cannot regrow.
2. **Shared components (P1)** — button/input/tree/dialog/menu/tooltip/loading building blocks so screens stop re-inlining styles.
3. **Shell fixes (P0/P1)** — the 7 pt sidebar labels, hard-locked 350 px results panel, header button inconsistency.
4. **Screen-level polish (P1/P2)** — density and hierarchy fixes in the pal editor and inventory screens first (highest visual complexity), then the rest.
5. **States and accessibility (P0/P1)** — focus visibility (currently absent everywhere), distinct multi-select, minimum font size 11 px, emoji removal from chrome, empty/loading/error consistency.

Only one behavior change is proposed (JSON import preview/confirmation). Everything else is visual and structural refactoring with functional parity.

## 2. Current UI Assessment

### 2.1 Application shell

Verified from `src/palworld_aio/ui/main_window.py`:

- Frameless `QMainWindow` (`Qt.FramelessWindowHint`, line 272), custom drag handling (lines 757–778). Minimum 1200×750 (line 267); initial size clamped to screen minus 40 px (lines 268–271). App style: `Fusion` (`main.py:199`).
- Layout: `HeaderWidget` → horizontal body of `SidebarWidget` + `QSplitter` containing [`QStackedWidget` (12 pages, lazily instantiated) + `ResultsWidget`] → hidden `QStatusBar` (`setFixedHeight(0)`, lines 338–341) → `DropOverlay` for save-file drag-and-drop.
- The sidebar sits **outside** the splitter; the splitter's right pane (`ResultsWidget`) is hard-locked to 350 px (`results_widget.py:28-29`, min=max=350, `QSizePolicy.Fixed`), making the splitter decorative.
- Navigation: sidebar emits `nav_changed(str)`; ids map to page indices in an inline dict (`main_window.py:537`). F5 refreshes all (`keyPressEvent`, lines 2481–2485).
- Status output is rerouted (`StatusBarStream`, lines 136–184) either into the hidden status bar or a detachable console window (`DetachedStatusWindow`, lines 40–135, min 600×400, fade-in animation).
- Shell state model exists (`src/palworld_aio/shell_state.py`: `NO_SAVE/LOADING/LOADED/DIRTY/SAVING/ERROR` with `can_load/can_save/can_edit` gates) but much of the window still reads `constants.loaded_level_json` directly (e.g., `main_window.py:1361, 1463`).

### 2.2 Header (`ui/chrome/header_widget.py`)

Single row: logo (44 px, from `resources/assets/branding/`), menu chip, app-version chip, game-version chip, then five 40×36 fixed icon buttons (about, warning, toolbox, save, loading spinner) + spacer + discord, minimize/maximize/close. All nine buttons get inline `padding: 0; margin: 0` overrides (line 105) that neutralize QSS padding. Loading spinner is a rotating text glyph on a 200 ms `QTimer` (lines 45–62). Update pulse animates a dynamic property every 500 ms (lines 219–246). No global search, no theme toggle (QSS for a `themeChip` exists but matches no widget).

### 2.3 Sidebar (`ui/chrome/sidebar_widget.py`)

Fixed widths 48 collapsed / 150 expanded, item height 44. `NavItem.paintEvent` draws Nerd Font glyphs and labels — labels at **7 pt on Windows** (`LABEL_FONT_SIZE = 10 if darwin else 7`, line 16), below any reasonable legibility floor. Active indicator is a hand-painted 5×24 bar in `#7DD3FC`, with the painting code duplicated between `NavItem` and `BottomBtn` (lines 122–130 vs 203–211). The two classes disagree on label x-offset by 4 px (42 vs 46). `set_lock_state()` is a no-op stub (lines 317–318).

### 2.4 Styling stack

- `ThemeManager` (`ui/chrome/styles.py`) applies `resources/ui/themes/darkmode.qss` globally; `_GLOBAL_FALLBACK_STYLE` duplicates much of it inline.
- Constant styles exist: `DIALOG_STYLE`, `MENU_STYLE`, `STATS_PANEL_STYLE`, `PICKER_*`, `TOOLTIP_STYLE`, `CONTENT_PANEL_STYLE`, slot styles + builders (lines 60–86). Only `stats_panel.py`, `player_select_popup.py`, and `FramelessDialog` actually consume them.
- `main.py:200-202` applies a third tooltip style that competes with `TOOLTIP_STYLE` and the QSS `QToolTip` block — last-applied wins.
- `darkmode.qss` contains self-duplicates: `QMenu` ×2 (lines 337–362, 575–602), `QWidget#resultsWidget` ×2, `QFrame#palCard` ×2, `QTabWidget#editPalsTab::pane` ×2, `QPushButton#discordChip` ×2; dead selectors (`sidebarChip`, `themeChip`); gray override vocabulary (`QComboBox` `#444444`, `QStackedWidget QPushButton` `#555555`) that overrides accent buttons inside every stacked page.

### 2.5 Screens (12)

| Page | Module | Notes |
|---|---|---|
| Tools (dashboard) | `ui/tabs/tools_tab.py` | 18 px margins, save card 340 px fixed, 42 px-tall load buttons, 2-col tool card grid, DropOverlay, dialog re-parent hack |
| Base inventory | `ui/tabs/base_inventory_tab.py` (4,212 lines) | 8 inline-styled header buttons, splitter 300/700, card-style container list, **legacy blue theme in `_update_theme` (line 3050-3051)** |
| Player inventory | `ui/tabs/inventory_tab.py` (4,228 lines) | 6 sub-tabs + equipment panel (min 400), 156 inline styles, duplicated `_make_tech_button`, duplicated `sort_btn` |
| Pal editor | `ui/tabs/pal_editor_tab.py` + `editor/pal_editor/*` | Densest visual surface: 64 px slot cards, hand-painted badges, 10 individually colored toggle chips, always-running 33 ms `RotatingCircleWidget` timer |
| Players / Guilds / Bases / Exclusions | built inline in `main_window.py` (lines 375–483) | plain trees + 4 bulk buttons sharing one copy-pasted QSS ×4 (lines 391–403) |
| Map | `ui/tabs/map_tab.py` + `ui/map_view/*` | 3:2 fixed split (no splitter), marker config dict, `PlayerMarker` bypasses the config `BaseMarker` uses, effects with raw RGB tuples |
| Exclusions | inline in `main_window.py` | tree + context menu |
| JSON editor | `ui/tabs/json_editor_tab.py` | read-only tree, the only alternating-row tree, monospace, **unguarded Import (see 6.10)** |
| Docs | `ui/tabs/docs_tab.py` + `ui/tabs/docs/wiki_tab.py` | single-button sub-tab bar; wiki = 160 px category pane + lazy pages |
| Breeding | `ui/tabs/breeding_tab.py` | module-constant styles (good pattern), dialog subclass reuses `PalCreateDialog` by string-matching button text |

### 2.6 Dialogs

`ThemedDialog` (`editor/dialogs.py:11-71`) provides gradient chrome + parent-centered positioning, but most dialogs subclass raw `QDialog` with their own styles. Min widths range 300–1200; button min-heights vary 32–40; button order varies (left-aligned OK/Cancel vs right-aligned vs stacked); Close is danger-styled in fix dialogs but default elsewhere. Emoji in labels (`⚠` at `dialogs.py:384, 529`).

### 2.7 States

- **Loading:** two unrelated popups — `LoadingPopup` (200×120 fixed) and `LoadingOverlay` (850×500 fixed, mascot + gradient bar + rotating phrases). Tabs integrate via `run_with_loading`.
- **Empty:** consistent centered-placeholder pattern duplicated 3× (pal_editor_tab 52–57, inventory_tab 2553–2558, base_inventory_tab 2960–2965); Mission and Technology panels render nothing when empty.
- **Error:** inline status labels (good), plus `print()` in `pal_editor_global_ops.py` (lines 87, 164, 229, 348) violating the user-safe-error convention.
- **Focus:** no `:focus` styling found anywhere in the audit.
- **Multi-select:** `SLOT_MULTI_SELECTED_STYLE == SLOT_SELECTED_STYLE` byte-for-byte (`styles.py:71-72`) — multi-selection is visually indistinguishable from single selection in palbox/party slots.
- **Selection jitter:** empty→selected changes border 1 px→2 px with no compensation (`styles.py:69` vs 71) — 1 px layout shift on every slot selection.

## 3. Design Problems Identified

### 3.1 Color (P0)

- Two competing accents: named token `constants.ACCENT = '#3B8ED0'` vs de-facto `#7DD3FC` (214 uses). Legacy third blue in `base_inventory_tab._update_theme` (`rgba(74,144,226,…)`, line 3051).
- Four near-identical off-whites: `#dfeefc` (QSS), `#E2E8F0` (fallback/f-inline), `#E6EEF6` (`constants.TEXT`), `#E0E0E0` (`styled_combo.py`).
- Four reds: `#FB7185`, `#F87171`, `#ff6b6b`, `rgba(255,80,80,…)`; plus `#EF4444` for semantic-bad. Six greens: `#4ADE80`, `#22C55E`, `#43B581`, `#00C878`, `#10B981`, `QColor(0,255,150)`.
- Four input-background families: `rgba(255,255,255,0.06)`, `rgba(18,20,24,0.65)`, `rgba(30,35,45,0.8)`, `#1A1D23`.
- Malformed hexes in QSS strings: `#7F7DD3FC`, `#FFFFFFFF`, `#7FFFD700`, `#7FFF5050`.
- Map layer uses raw RGB tuples unrelated to tokens (`map_effects.py:28-37`, `map_markers.py:123`, `map_items.py:17-25`).
- Rarity ladder implemented 3×; element color map duplicated verbatim (`pal_info_display.py:27-28` == `pal_info_widget.py:27-28`).

### 3.2 Typography (P0)

- Sizes range 6–20 px with no scale; `LABEL_FONT_SIZE = 7` pt sidebar labels (Windows); 6 px shrink-to-fit loops (`pal_info_display.py:601-624`, `player_pal_dialog.py:404-431`); `font-size: 6px` inside HP bars (`party_slot_widget.py:563`); 8 px bar text and partner-skill HTML (`icons.py:222`).
- `constants.FONT_SIZE*` values exist but are largely unused by inline styles.
- `QFont('', 14, …)` empty-family fallback for the logo (`header_widget.py:216`).
- Fonts themselves are fine (Segoe UI + Hack Nerd Font + Consolas; Nerd font registered at `header_widget.py:65-72`).

### 3.3 Layout and spacing (P1)

- Tab root margins: `(0,0,0,0)` map/docs, `(10,10,10,10)` pal editor/inventory/base inventory/JSON, `(10,4,10,10)` breeding, `(18,18,18,18)` tools.
- Eight button heights observed: 20/22/24/28/30/32/36/42 px.
- Magic child-position offsets in `resizeEvent`/`paintEvent` (inventory slots, palbox, party slot, header/nav painting).
- HP fill width math `max(4, ratio*200)` (`card_widgets.py:709`) vs `max(3, ratio*180)` (`party_slot_widget.py:581`).
- Results panel fixed 350 px; map split 3:2 with no splitter; tools margins 18 with no grid alignment.

### 3.4 Duplication (P0 for maintainability)

- `QToolTip` block ×15 in `pal_info_widget.py` alone (+3 in `pal_info_display.py`) while `TOOLTIP_STYLE` exists.
- Green apply-button QSS ×10; gray cancel-button QSS ×8; scroll-area QSS ×11; tree QSS verbatim ×2 (`map_tab.py:345-384` == `search_panel.py:71-110`); search-input QSS ×2; `RarityBorderDelegate` ×2 (`inventory_tab.py:2247-2268` == `base_inventory_tab.py:32-53`); passive-card QSS ×5; status-label QSS ×14; menu QSS ×6 variants; sectionHeader override ×7.
- Dead/duplicated code: `menus.py` context-menu builders unused (main_window builds its own); `_make_tech_button` ×2 and `sort_btn` ×2 in `inventory_tab.py`; `exec` ×2 in `scrollable_context_menu.py`; skill-slot construction ×3; `_PalSlotDelegate` ×2; bulk-dialog list block ×5; `legacy_frame.py` light-theme leftovers; `is_dark` flags never toggled.
- Slot style helpers exist but `card_widgets.py:284, 514-539` re-declare the same values inline.

### 3.5 Icons (P1)

- Nerd Font PUA glyphs with per-file fallback dicts; missing-key fallbacks are literal emoji (`🐾 🔒 🔥 🧬 📁 ⚙️ 🗺️`), including the egg nav fallback `'⭕'` (wrong glyph) at `sidebar_widget.py:12`.
- `_get_ui_icon_pixmap` returns `None` on unknown key, so callers silently fall back to emoji (`party_slot_widget.py:621, 657, 693`, `palbox_slot_widget.py:554, 606`, `pal_info_widget.py:320, 528`).

### 3.6 Interaction and desktop UX (P1)

- No keyboard navigation management, no `setTabOrder`, no accessible names; icon-only 18×18 buttons rely on tooltips only.
- Drag-and-drop slot reordering has no keyboard alternative.
- Destructive double-click delete on occupied pal slots with no confirm (`palbox_slot_widget.py:237-249`, `party_slot_widget.py:223-235`) — behavior, not styling; **flagged, not planned** (would change behavior; needs product decision).
- Blocking `processEvents` loops: `player_select_popup.py:61-63`, `skill_picker.py:328-330`; nested `QEventLoop` in `scrollable_context_menu.py:292-304`; dialog re-parent + `setQuitOnLastWindowClosed` hack (`tools_tab.py:496-534`); calibration rewrites `palworld_coord/__init__.py` via regex (`map_tab.py:664-672`). These are correctness/lifecycle risks noted for the roadmap's cleanup phase, not visual changes.
- Perpetually running timers (`RotatingCircleWidget` 33 ms, per-effect 30 ms timers) — CPU cost with no user value.

## 4. Design System

All tokens live in `constants.py` (existing import path, scanner-whitelisted) plus a new `src/palworld_aio/ui/chrome/tokens.py` for QSS-specific derived strings (rgba composites, gradients). Rationale: the scanner (`check_theme_violations.py`) whitelists `constants.py`/`styles.py`; extending them keeps enforcement intact without touching tooling.

### 4.1 Typography

Fonts stay as-is — Segoe UI (Windows-native, excellent hinting at small sizes, already the app default), Hack Nerd Font (bundled, runtime-registered, used for all iconography), Consolas → falls back to Cascadia Mono where available for JSON/IDs/logs. No new fonts are introduced.

| Element | Font | Size | Weight | Usage |
|---|---|---|---|---|
| Page title | Segoe UI | 15 px | 600 | One per screen (`sectionHeader`), replaces current 10 pt bold |
| Section title | Segoe UI | 13 px | 600 | Panel/card headers, dialog titles |
| Body | Segoe UI | 12 px | 400 | Default text, tree/table cells, form labels |
| Secondary text | Segoe UI | 11 px | 400 | Muted/supporting text, hints (`TEXT_MUTED`) |
| Button | Segoe UI | 12 px | 600 | All push buttons |
| Caption/badge | Segoe UI | 11 px | 500–700 | Level badges, chips, bar overlays (replaces 6–9 px) |
| Display | Segoe UI | 20 px | 700 | Stat values, pal level (existing 20 px retained as the only display size) |
| Code/mono | Consolas | 11 px | 400 | JSON editor, IDs, logs, coordinates |

Rules:

- **Minimum 11 px** anywhere in the UI. All 6–9 px text is raised (bar overlays, hint chips `[C][A][L]`, skill HTML, shrink-loops replaced with `QFontMetrics.elidedText`).
- Line spacing is carried by widget padding/heights, not `line-height` (Qt QSS support is limited); rich-text HTML blocks (partner skills, tooltips) use `line-height: 150%`.
- Point sizes in code (`setFont(QFont(..., N))`) convert to px via the table above; `constants.FONT_SIZE` stays 10 pt as the QApplication default but explicit UI text uses the table.

### 4.2 Color Palette

Dark-only. A light theme is explicitly out of scope; tokens are named semantically so a light palette could be added later by re-pointing values. Contrast ratios below are computed (WCAG relative luminance).

| Token | Value (dark) | Purpose | Contrast on surface |
|---|---|---|---|
| `BG` | `#0A0B0E` | Window base (behind gradient) | — |
| `SURFACE` | `rgba(18,20,24,0.65)` | Panels, content frames, popups | — |
| `SURFACE_ELEVATED` | `#161A20` | Cards, dialogs, menus, tooltips | — |
| `SURFACE_HOVER` | `rgba(125,211,252,0.08)` | Hover fill on rows/items | — |
| `BORDER_SUBTLE` | `rgba(125,211,252,0.15)` | Panel/card outlines (current idiom, formalized) | — |
| `BORDER_STRONG` | `#1E2128` | Dividers, input borders (existing `constants.BORDER`) | — |
| `TEXT` | `#E6EEF6` | Primary text (existing `constants.TEXT`; retires `#E2E8F0`, `#dfeefc`, `#E0E0E0`) | 15.7:1 |
| `TEXT_MUTED` | `#94A3B8` | Secondary text (retires `#9CA3AF`, `#A6B8C8` as body text, `#888`) | 7.2:1 |
| `TEXT_DISABLED` | `#475569` | Disabled controls | 2.6:1 (exempt) |
| `ACCENT` | `#7DD3FC` | Primary actions, selection, active nav (de-facto accent formalized; `ACCENT` token repointed from `#3B8ED0`) | 11.1:1 |
| `ACCENT_BG` | `rgba(125,211,252,0.12)` | Tinted button fill | — |
| `ACCENT_BG_STRONG` | `rgba(125,211,252,0.2)` | Hover/checked fill, selection fill | — |
| `SUCCESS` | `#4ADE80` | Success states, loaded/valid, "good" stat values (retires `#22C55E`, `#43B581`, `#00C878` as status colors) | 10.6:1 |
| `WARNING` | `#FBBF24` | Warnings, costs, pending (retires `#F59E0B` as status; boss badge keeps `F59E0B` mapped to `SPECIAL`) | 11.0:1 |
| `DANGER` | `#FB7185` | Destructive actions, errors (retires `#EF4444`, `#F87171`, `#ff6b6b`, `rgba(255,80,80)`) | 6.9:1 |
| `INFO` | `#818CF8` | Informational accents (key items, discord) | 6.2:1 |
| `SPECIAL` | `#A78BFA` | Rare/special entities: lucky, boss `α`, menu chip (retires `#A855F7`, `#9333EA`, `#C084FC`) | 6.8:1 |
| Rarity ladder | `RARITY_1..5` = `#9CA3AF` `#4ADE80` `#60A5FA` `#A78BFA` `#FBBF24` | Item rarity borders/text (existing ladder at `player_item_dialog.py:23-31`, single source) | 7.2:1 (blue) |
| `FOCUS_RING` | `#7DD3FC` (2 px) | Keyboard focus indicator | — |
| Element map | existing 10-color dict | Single shared dict extracted from `pal_info_display.py:27-28` | — |

Usage rules:

- One accent. Blue gradients (`#7DD3FC → #A78BFA` in `darkmode.qss:148, 474, 837-841, 1098` and `LoadingOverlay`) are replaced by the `ACCENT_BG` family; only rarity/element semantics may use non-accent hues.
- Grays `#444444`/`#555555` (QSS `QComboBox`, `QStackedWidget QPushButton`) and the legacy blue in `base_inventory_tab._update_theme` are replaced by the token vocabulary.
- Status colors never appear as large fills; tinted backgrounds use the same hue at low alpha (existing idiom, formalized per token).

### 4.3 Spacing

The codebase already clusters at 4/6/8/10/12/16/24. A **4 px base scale** fits with minimal churn: `4 / 8 / 12 / 16 / 24 / 32` (`SPACE_*` constants). Migration: 10→12, 15→16, 5→4, 6→8 at control edges, 18→16.

| Token | Value | Usage |
|---|---|---|
| `SPACE_XS` | 4 | Icon-to-label gaps, badge insets, tight list rows |
| `SPACE_SM` | 8 | Control padding (vertical), intra-group gaps, slot grids |
| `SPACE_MD` | 12 | Control padding (horizontal), card padding, **standard tab root margin** |
| `SPACE_LG` | 16 | Between sections/panels within a screen |
| `SPACE_XL` | 24 | Screen section groups, dialog padding |
| `SPACE_XXL` | 32 | Dashboard hero areas only |

### 4.4 Sizing

| Element | Value | Notes |
|---|---|---|
| Control heights | 24 (sm) / 28 (md) / 36 (lg) | Replaces observed 20/22/24/28/30/32/36/42. sm = in-row/dense grid buttons; md = default buttons, inputs, selects, header buttons; lg = primary CTAs (load save, apply bulk op) |
| Header height | 52 px | Logo 44 px + 4 px margins; all header icon buttons 32×32 (replaces 40×36) |
| Sidebar | 48 collapsed / 168 expanded; item height 44 | Expanded width grows so 12 px labels fit at x-offset 44 |
| Tree/list rows | 28 px | `TREE_ROW_HEIGHT` 22 → 28 for 12 px text; JSON tree may stay 24 with mono 11 px |
| Slots (canonical) | grid card 64, palbox 56, party row 72, equipment 56×70, tech tile 76 | Existing geometry documented, not resized in this pass |
| Results panel | min 320 / max 480, resizable | Unlocks the splitter; 350 becomes the default size |
| Map split | QSplitter, min map 400 / min sidebar 340 | Replaces fixed 3:2 |
| Dialogs | min 400×300 base class; per-dialog minimums documented | Existing large dialogs keep their sizes (900×650 etc.) |

### 4.5 Borders and Radius

- Border width: **1 px** everywhere. Selection states use 1 px border + background change (no 2 px switch → no jitter; fix in `slot_selected`/`slot_multi_selected`).
- Radius: 4 (inputs, small chips) / 6 (buttons, slots, list rows) / 8 (cards, panels) / 10 (dialogs, popups, menus). Existing values already cluster here; formalize in tokens.

### 4.6 Icons

- New `src/palworld_aio/ui/chrome/icons.py`: one registry `NAME → glyph` with documented codepoints, loaded once, consumed by header, sidebar, menus, slots, overlays, dialogs. Replaces the five per-file fallback dicts (`header_widget.py:9`, `sidebar_widget.py:9-12`, `menu_popup.py:5`, `stats_panel.py:24-26`, slot widgets).
- Fallback for a missing key is a documented placeholder glyph (`'?'`), never emoji.
- Remove all emoji from chrome: menu popup (`menu_popup.py:5`), lock/awake/DNA/predator badges, `📁` in tools tab/drop overlay, `⚠` in dialog notes, `✕` closes → Nerd glyph `\uf00d` already used elsewhere.
- Glyph sizes: 14 / 16 / 20 / 24 (map overlays, nav, buttons, empty states respectively).
- Element/boss/lucky badges keep using their webp assets via `editor/pal_editor/icons.py`; only UI chrome moves to the registry.

### 4.7 Interaction States

| State | Specification |
|---|---|
| Hover | `SURFACE_HOVER` fill; buttons also brighten border to `rgba(125,211,252,0.35)` |
| Pressed | `ACCENT_BG_STRONG` fill |
| Checked/active (pills, nav) | `ACCENT_BG_STRONG` + 1 px `ACCENT` border + `ACCENT` text (matches existing pill idiom, made single-source) |
| **Focus (keyboard)** | 2 px `FOCUS_RING` border via QSS `:focus` on all focusable controls; currently absent app-wide — this is the single biggest accessibility gap |
| Disabled | `TEXT_DISABLED` on `SURFACE`, border `BORDER_STRONG`, no hover |
| Selected (single) | 1 px `ACCENT` border + `ACCENT_BG_STRONG` background (no layout shift) |
| Selected (multi) | 1 px `ACCENT` border + `ACCENT_BG_STRONG` **plus** a leading check glyph — must be distinguishable from single-select everywhere (fixes `styles.py:71-72` identity) |
| Loading | unified `LoadingOverlay` (Section 7.6) |
| Empty | shared `EmptyState` widget (Section 7.7) |
| Error | inline labels in `DANGER`; dialog-level errors use a banner row; no `print()` |
| Inactive selection | `:selected:!active` muted variant (already present in tree QSS — keep, generalize) |

## 5. Application Shell

### 5.1 Header

- Group left→right: logo + version chips (contextual metadata) | flexible spacer | save, warning, toolbox, about, discord (actions) | window controls. Today actions and chips interleave.
- Buttons: 32×32, uniform `md` height; remove the per-widget `padding: 0` overrides (line 105) in favor of an `iconBtn` objectName class in QSS.
- Save button gets the only emphasized treatment (`ACCENT_BG` fill, brighter on dirty state via `ShellState`), so the primary action reads first.
- Keep the text spinner until a unified loading treatment lands (Phase 3), then route through it.

### 5.2 Sidebar

- Fix `LABEL_FONT_SIZE` to 11 px on all platforms (`sidebar_widget.py:16`); expanded width 150→168 so labels don't clip.
- Unify `NavItem`/`BottomBtn` painting (extract shared paint helper; kills the duplicated active-bar code and the 4 px label misalignment).
- Keep collapse persistence; keep 12 nav items and their order (functionality preserved).
- Replace the `'⭕'` egg fallback with the correct breeding glyph from the registry.

### 5.3 Results panel

- Replace min=max 350 with `QSizePolicy.Expanding` + min 320; splitter default sizes `[1000, 350]`; persist splitter state in `user.cfg` alongside the existing sidebar setting.
- Keep the three value cards + stats layout; restyle with tokens; title font moves to the 13 px section title (from `QFont(..., 14, Bold)` + inline margin QSS).

### 5.4 Window behavior

- Keep frameless window, min 1200×750, drag handling, and detachable console as-is (behavior preservation).
- Restore a 24 px status bar (currently height 0) only if the console is closed; otherwise keep current mechanism. (Needs verification of console open/close flows at implementation time.)

## 6. Screen-by-Screen Improvements

Each entry: Issues → Changes (layout / typography / color / spacing / components / accessibility) → Priority.

### 6.1 Tools (dashboard) — `ui/tabs/tools_tab.py`

Issues: 18 px margins unaligned with the 12 px standard; load buttons 42 px tall vs everything else; `📁` emoji at 36 pt and 52 pt in the drop overlay; tool cards use point-size fonts (11/9) breaking the px scale; loading overlay (850×500) unrelated to `LoadingPopup`; dialog fade hack mutates `QuitOnLastWindowClosed`.
Changes: margins 16; load buttons → `lg` (36) `primary` variant; save card keeps 340 width but token styling; tool cards → shared `Card` style with 13 px/600 titles, 11 px muted descriptions; drop overlay painted with `SUCCESS` token and Nerd glyph; stat mini-cards 20 px display values confirmed. Dialog lifecycle hack is tracked in Phase 6 cleanup (needs a behavior-neutral refactor plan; out of visual scope).
Priority: **P1**.

### 6.2 Base inventory — `ui/tabs/base_inventory_tab.py`

Issues: 8 header buttons with 6+ copies of near-identical QSS; red `×` clears styled ad hoc; `_update_theme` (line 3050) applies a legacy blue theme over the whole page; container list uses 300×80 fixed item widgets with hidden header; two picker dialogs (1200×650) duplicate inventory's picker; duplicated `RarityBorderDelegate`.
Changes: header buttons → shared `pill`/`iconBtn` variants; f-string restyle loop → `checked` property + QSS pseudo-state (same pattern as map); delete `_update_theme` legacy values; container list keeps card layout but uses slot tokens and 28 px rows; adopt shared picker dialog base (Phase 3) with rarity delegate imported from one module.
Priority: **P1**.

### 6.3 Player inventory — `ui/tabs/inventory_tab.py`

Issues: 156 inline styles; duplicated `_make_tech_button` (L1197/L1287) and `sort_btn` (L2025/L2051) — two Sort buttons rendered; 8 px slot text; four semantic header-button colors (`#a855f7/#fbbf24/#818cf8/#FB7185`) each re-inlined; stat panel uses a gray `#333/#555` button family; EXP chunk `#43b581` off-palette; 6 sub-tabs inherit the gray `QStackedWidget QPushButton` override.
Changes: remove duplicate definitions; slot text → 11 px captions; header actions → `sm` semantic variants (`info`/`warning`/`danger`) from the button component; stat +/- buttons → neutral sm variant; EXP bar → `SUCCESS`; kill the QSS gray override in `darkmode.qss` so accent buttons survive inside stacked pages; tech tiles keep 76 geometry, names 11 px, cost `WARNING`.
Priority: **P1** (highest inline-style count).

### 6.4 Pal editor — `editor/pal_editor/*`, `ui/tabs/pal_editor_tab.py`

Issues: densest surface — 10 toggle chips with individually hardcoded colors; 15 tooltip QSS copies; 18×18 icon-only chips; 6–8 px text (level overlays, `[C][A][L]` chips, bar text, partner-skill HTML); `RotatingCircleWidget` 33 ms timer runs forever; multi-select invisible (`SLOT_MULTI == SLOT_SELECTED`); selection jitter; emoji badge fallbacks; legacy `legacy_frame.py` light theme; HP shown as `value // 1000` without a unit hint.
Changes: slot/card/level badge geometry unchanged; text floors to 11 px (level badge 11 px/700, bar overlays 11 px, hint chips 11 px — chips grow 22×16→24×18); chips recolored from `SPECIAL`/`WARNING`/`DANGER`/`SUCCESS` tokens (gender `SPECIAL`, predator `DANGER`, boss `WARNING`, lucky `SPECIAL`, awake `WARNING`, cheat `DANGER`, max-stats `SUCCESS`, DNA `INFO`, fav `WARNING`); tooltips via one `TOOLTIP_STYLE` helper function returning the QSS string; multi-select gets check-glyph treatment; fix 1 px jitter; replace emoji fallbacks via registry; `RotatingCircleWidget` starts only while the info panel is visible (lifecycle fix, no visual change); retire `legacy_frame.py` (verify no callers first); HP label gains `k` suffix convention (`12.4k`).
Priority: **P1**.

### 6.5 Players / Guilds / Bases / Exclusions — `ui/main_window.py` inline tabs

Issues: hand-built in the window class; four bulk buttons share one copy-pasted QSS ×4 (lines 391–403); trees use default headers `#3a3a3a` (`tree_widgets.py:20`) vs styled headers elsewhere; alternating rows on (`SortableTreeWidget`) vs off (SearchPanel/map).
Changes: extract the four tabs into `ui/tabs/` modules using the shared `ScreenScaffold` (title + player-select + content frame) so they match 6.3/6.4 structure; bulk buttons → `sm` variants; adopt the single tree QSS + 28 px rows + alternating rows on; context menus (built inline, duplicating dead `menus.py`) → one builder path (Phase 3 menu consolidation).
Priority: **P2**.

### 6.6 Map — `ui/tabs/map_tab.py`, `ui/map_view/*`

Issues: 3:2 fixed split, no resize; floating overlay buttons with per-button concatenated QSS; calibration labels in raw `rgba(0,0,0,180)`; tree QSS duplicated from `search_panel.py`; `PlayerMarker` hardcodes what `BaseMarker` reads from config; effects use raw RGB tuples; purple `#7c3aed` gradient in markers/effects off-palette; polygon preview dots `#FFFF00`.
Changes: wrap sidebar in `CollapsibleSplitter` (widget exists, unused — `widgets/collapsible_splitter.py`), min sidebar 340; overlay buttons → `iconBtn` + `checked` states; labels/colors → tokens (`rgba(0,0,0,150)` → `SURFACE_ELEVATED` at 90%); unify marker config so player markers consume it; map effect palettes → token RGB tuples defined in `tokens.py`; preview dots → `WARNING`.
Priority: **P2**.

### 6.7 Exclusions — covered by 6.5. Priority: **P2**.

### 6.8 JSON editor — `ui/tabs/json_editor_tab.py`

Issues: the only alternating-row tree (good) but `#1A1D23` background off-token; monospace 10 pt → 11 px; **Import JSON replaces the entire GVAS file with no preview, diff, or confirmation** (`_import_json`, lines 365–391) — violates the "destructive actions require a preview and a separate commit step" invariant.
Changes: restyle to tokens; keep lazy-load/search UX; **add a confirm dialog showing source path, target path, file size, and a "this replaces the loaded save in memory" warning, requiring explicit confirmation before `save_applied`** — the one approved behavior change. (Full diff/schema validation remains a separate feature proposal, not in this plan's scope.)
Priority: **P1** (guard) / **P2** (styling).

### 6.9 Docs — `ui/tabs/docs_tab.py`, `ui/tabs/docs/wiki_tab.py`

Issues: single-button sub-tab bar adds chrome without function; `_SUB_TAB_STYLE` duplicates breeding's `_BTN_STYLE`.
Changes: keep the bar only if a second sub-tab is planned (needs product input; default: hide the bar when one tab); share the sub-tab style constant via `styles.py`; wiki pane 160→180 px for 12 px text.
Priority: **P3**.

### 6.10 Breeding — `ui/tabs/breeding_tab.py`

Issues: margins `(10,4,10,10)`; third search-field background family; result names in inline HTML (`<b style="color:#7DD3FC;font-size:15px">`); `_SelectPalDialog` string-matches `"Create" in txt` on a foreign dialog — fragile coupling; pagination disabled `#475569` on dark is near-invisible.
Changes: margins → standard; search field → shared component; name emphasis via `ACCENT` label styling, not HTML; replace string-matching with a proper `selection_mode` parameter on the create dialog (small, contained API change to `create_dialogs.py`); disabled states → `TEXT_DISABLED` token.
Priority: **P2**.

### 6.11 Dialogs (all)

Issues: mixed base classes; button order/role drift; fix-dialog Close is danger while others are default; `TabGuideDialog` ships its own palette (`#4a90e2` family); per-guild-button stylesheet rebuilt in a loop (`dialogs.py:1106`); duplicate tree QSS in `guild_assign_dialog._TREE_STYLE`; food picker sets its size twice; learn-skills dialog duplicates its slot block verbatim.
Changes: all dialogs subclass `ThemedDialog`; footer order standardized `[secondary actions left] — [Cancel] [Primary]` right-aligned; primary = `lg` accent, destructive = `danger`; Close is never danger (only Cancel/Apply-style actions carry semantics); retire `TabGuideDialog`'s palette; dedupe tree QSS; fix the double `setMinimumSize`.
Priority: **P1**.

## 7. Component Improvements

### 7.1 Buttons (`ui/chrome/` — extend `styles.py`)

Variants: `primary` (accent fill), `neutral` (accent-tinted, current default look), `semantic` (success/warning/danger/info/special tints), `ghost` (transparent, for row actions), `iconBtn` (32×32 md / 24×24 sm). Heights sm/md/lg per 4.4. All via objectName classes in `darkmode.qss`; no inline QSS.

### 7.2 Inputs

One `QLineEdit`/`QSpinBox` family: `SURFACE` fill, `BORDER_STRONG` border, `ACCENT` border on focus, 28 px height (24 in dense panels). Replaces the four background families.

### 7.3 Trees and lists

Single tree QSS (extracted from `map_tab.py:345-384`): 28 px rows, alternating rows **on**, centered 12 px headers on `SURFACE_ELEVATED`, selection = `ACCENT_BG_STRONG` + `ACCENT` text + 3 px left accent bar, `:selected:!active` muted variant. Applied to SearchPanel, map trees, JSON tree, players/guilds/bases trees, `SortableTreeWidget`. Container list keeps its card presentation but with slot tokens.

### 7.4 Slots and cards

`slot_empty/selected/multi_selected` builders stay the API; values fixed (1 px borders, distinct multi-select). `PalIcon`/`TribeIcon` share one QSS source; `PalCardWidget` and `PartySlotWidget` bar widths unify (200→same constant).

### 7.5 Menus and context menus

Consolidate six style variants (`MENU_STYLE`, `menu_popup` container + `QMenu` string ×3 in map, `ScrollableContextMenu._SUBMENU_STYLE`, `guild_assign` copy) into one popup-menu style. Decide `menus.py`: **delete** the dead `MenuFactory`/context builders and keep the single inline path in `main_window.py` for now (extraction into a real builder is a separate refactor). Emoji icons in `MenuPopup` → registry glyphs.

### 7.6 Loading

One overlay component (`LoadingOverlay`) with size-from-parent behavior (bounded, not fixed 850×500), indeterminate accent bar, phrase + elapsed label kept. `LoadingPopup` is retired; `run_with_loading` remains the single entry point.

### 7.7 Empty states

Shared `EmptyState` widget (glyph 24 px + title 13 px/600 + hint 11 px muted + optional action button), replacing the 3 duplicated placeholder labels; added to Mission and Technology panels.

### 7.8 Tooltips

One style source: `TOOLTIP_STYLE` becomes the app-level stylesheet (applied once in `main.py`, replacing the competing literal); the 15+ inline copies become `tooltip_qss()` helper calls or plain `setToolTip` (rich-text content is fine, wrapper style is global). Custom frameless tooltip in `pal_info_widget.py:198-203` joins the standard style.

### 7.9 Hover overlays

Merge `base_hover_overlay.py` + `player_hover_overlay.py` (~90% clones) into one overlay with an accent-color parameter.

## 8. Accessibility and Readability

- Contrast: all text tokens ≥ 4.5:1 on their surfaces (computed, Section 4.2); `TEXT_DISABLED` 2.6:1 is the only exception (WCAG-exempt, but must never carry required information).
- Minimum font 11 px; no shrink-to-fit below floor; elide instead.
- Keyboard: QSS `:focus` ring on every focusable control; tab order set per dialog (accept → primary); `QShortcut` hints already used in the pal editor stay and gain visible chips (already exist, resized to 11 px).
- Hit targets: minimum 24×24 for icon buttons (current 18×18 chips grow to 24×18 or gain padding).
- Color independence: status text always pairs color with a glyph or word (success `✓`, warning `!`, error `✗` prefixes on status labels); rarity keeps border+text color (border is a second cue already).
- Screen-reader surface: `setAccessibleName` on icon-only buttons (header, chips, slots). Full screen-reader verification is out of scope; naming is cheap and additive.

## 9. Desktop UX Considerations

- Resizing: splitter state persisted (results panel, map sidebar); min window size unchanged; verify no overlap at 1200×750 and at 100% / 125% / 150% DPI (Needs verification at runtime).
- Density: data screens stay dense (this is a workbench); the fixes remove *accidental* density (6–9 px text, 20 px buttons) rather than adding airiness.
- Scroll: keep overlay scrollbars; unify the one-off 6 px scrollbar (breeding) to the app scrollbar QSS.
- Drag-and-drop: pal slot DnD stays; add Ctrl+arrow move as a keyboard alternative where slots have focus (small, contained).
- Dialogs: parent-centered positioning via `ThemedDialog` everywhere (already implemented there); Escape closes; Enter applies.
- No new animations: keep existing fades where present; remove the perpetually rotating decoration timer.

## 10. Implementation Roadmap

| Phase | Scope | Key items | Verification |
|---|---|---|---|
| **1 — Foundation** | tokens + QSS dedup | Extend `constants.py` + new `ui/chrome/tokens.py`; repoint `ACCENT`; rewrite `darkmode.qss` (kill duplicates, dead selectors, gray overrides); scanner whitelist updated; `icons.py` registry | `check_theme_violations.py` baseline re-measured; `uv run pytest -c tests/pytest.ini`; `uv run pyright src`; visual smoke via `uv run start.py` |
| **2 — Shell** | header, sidebar, results, splitter | 5.1–5.4 | Focused GUI tests; manual resize pass |
| **3 — Shared components** | buttons, inputs, trees, slots, menus, tooltips, loading, empty | 7.1–7.9; `EmptyState`; screen scaffold used by 6.5 extraction | Same as Phase 1; component-level pytest where headless-checkable |
| **4a — Screens wave 1** | pal editor, player inventory, base inventory, dialogs | 6.2–6.4, 6.11 | Per-screen manual pass + existing tests |
| **4b — Screens wave 2** | tools, map, breeding, JSON, docs, extracted player/guild/base/exclusion tabs | 6.1, 6.5–6.10 | Same |
| **5 — States & a11y** | focus ring sweep, empty/loading/error coverage, tab order, accessible names | 8 | Keyboard-only walkthrough checklist |
| **6 — Cleanup** | dead code removal | `legacy_frame.py`, `menus.py`, dead QSS, `is_dark` plumbing, timer lifecycle, UX anti-pattern fixes (processEvents loops, dialog hack — each needs its own small refactor) | Scanner near-zero on UI dirs; full pytest suite |

Phases map to the superseded milestones: Phase 1 = UI-005, Phase 2 = UI-003, Phase 3 = UI-004, Phase 4 = UI-006, Phase 5 = UI-007, Phase 6 + the screen inventory in Section 2 = UI-001/UI-008.

Each phase ships as one or more independent feature branches (`feat/ui-tokens`, `feat/ui-shell`, …) with buildable commits.

## 11. Priority Matrix

| Priority | Items |
|---|---|
| **P0** | Token foundation + scanner gate; sidebar 7 pt labels; focus styles; multi-select distinct + jitter fix; min-font rule (kill 6–9 px); QSS self-duplicates and dead selectors; gray/legacy-blue override removal |
| **P1** | Button/input/tree/slot components; header + results panel; pal editor, inventory, base inventory screens; dialog standardization; loading unification; emoji removal; JSON import guard |
| **P2** | Tools, map, breeding, docs, players/guilds/bases/exclusions extraction; hover-overlay merge; empty-state completeness; menu consolidation; JSON styling |
| **P3** | `legacy_frame` removal, `is_dark` plumbing removal, scrollbar unification, wiki pane width, sub-tab bar decision |

## 12. Acceptance Criteria

1. `check_theme_violations.py` reports **0 errors** in `palworld_aio/ui/`, `palworld_aio/widgets/`, `palworld_aio/editor/` (whitelisted token files excluded); warning count ratchets down per phase and is re-baselined at each merge.
2. Exactly one accent color value (`#7DD3FC`) and one value per text role in non-whitelisted UI code.
3. No font size below 11 px and no point-size font usage in UI code outside the documented table (Section 4.1).
4. Exactly three control heights (24/28/36) and one header height (52).
5. All screen root layouts use `SPACE_*` margin constants; no literal 0/4/10/18 root margins outside documented exceptions (map canvas, docs).
6. Every focusable control shows a visible focus indicator (`:focus` QSS present in the app stylesheet; manual keyboard walkthrough of all 12 screens).
7. Multi-selection is visually distinguishable from single selection in palbox, party, and all list views.
8. No emoji in chrome (menus, badges, overlays); icon registry is the only glyph source.
9. Resizing from 1200×750 upward produces no clipped/overlapping layouts; results panel and map sidebar are user-resizable and persist.
10. All dialogs share `ThemedDialog` chrome, standard button order, and consistent button roles (Close never danger-styled).
11. Loading, empty, and error states exist for every screen (including Mission/Technology panels); errors never go to `print()`.
12. JSON import requires explicit confirmation before replacing the in-memory save.
13. Existing functionality unchanged: all 12 screens, context menus, DnD, shortcuts (F5, pal editor Q/E/F/C/L/A), drag-and-drop save loading, detached console, localization refresh all pass the existing test suite and a manual workflow checklist.
14. `uv run pytest -c tests/pytest.ini`, `uv run python -m compileall -q src tests`, and `uv run pyright src` pass at every phase boundary.

## 13. Files/Components Likely to Require Changes

**Modify (tokens/styles core):** `src/palworld_aio/constants.py`, `src/palworld_aio/ui/chrome/styles.py`, `src/palworld_aio/ui/chrome/tokens.py` (new), `resources/ui/themes/darkmode.qss`, `src/palworld_aio/main.py` (tooltip application).

**Modify (shell):** `ui/main_window.py` (also the screen extractions of 6.5), `ui/chrome/header_widget.py`, `ui/chrome/sidebar_widget.py`, `ui/chrome/results_widget.py`, `ui/chrome/styled_combo.py` (also fixes its import-order bug at line 30/143).

**New:** `ui/chrome/icons.py` (registry), `widgets/empty_state.py`, `widgets/screen_scaffold.py` (shared title+content frame).

**Modify (components):** `widgets/tree_widgets.py`, `widgets/search_panel.py`, `widgets/menu_popup.py`, `widgets/toggle_check.py`, `widgets/loading_popup.py` (retired), `widgets/base_hover_overlay.py` + `widgets/player_hover_overlay.py` (merged), `widgets/scrollable_context_menu.py`.

**Modify (screens):** `ui/tabs/tools_tab.py`, `ui/tabs/inventory_tab.py`, `ui/tabs/base_inventory_tab.py`, `ui/tabs/map_tab.py`, `ui/tabs/breeding_tab.py`, `ui/tabs/json_editor_tab.py`, `ui/tabs/docs_tab.py` + `ui/tabs/docs/wiki_tab.py`, `ui/tabs/pal_editor_tab.py`; new `ui/tabs/players_tab.py`, `guilds_tab.py`, `bases_tab.py`, `exclusions_tab.py` (extracted from `main_window.py`).

**Modify (editor/dialogs):** `editor/dialogs.py`, `editor/pal_editor/*` (cards, slots, info widget/display, bulk ops, create dialogs), `ui/dialogs/*`, `editor/pal_editor/icons.py` (emoji fallback removal).

**Delete candidates:** `editor/pal_editor/legacy_frame.py` (verify no callers), `ui/chrome/menus.py` (dead), `widgets/loading_popup.py` (after unification), dead QSS blocks in `darkmode.qss`, `is_dark` attributes in `main_window.py`/`results_widget.py`/`menu_popup.py`.

**Tooling:** `scripts/scrs/check_theme_violations.py` whitelist updates; optionally wire it into `tests/` (registry import, per `tests/test_registry.py` conventions).

## 14. Risks and Considerations

- **QSS specificity fights.** Inline styles override the global QSS; screens must migrate file-by-file or old inline values keep winning. Mitigation: per-phase file checklist + scanner as the gate; migrate a screen only when its inline styles are removed in the same commit.
- **Behavior parity.** 12 screens, drag-and-drop, shortcuts, and the detached console must survive. Mitigation: manual workflow checklist per phase (Section 12.13); no screen restyled and behavior-changed in the same commit.
- **i18n coupling.** Labels come from the translation layer (`src/i18n/`); restyling must not re-order or re-key translatable strings. Mitigation: run the language-switch flow (`main_window._change_language`) after shell changes.
- **No visual-regression infrastructure.** There is no screenshot-testing setup; verification is manual plus structural. Optional improvement (out of scope): offscreen `QWidget.grab()` smoke captures for the shell and one screen per wave.
- **Test-importer sensitivity.** Moving `players/guilds/bases/exclusions` tabs into new modules requires updating `tests/test_registry.py` (explicit AGENTS.md requirement).
- **Nerd Font availability.** The registry needs a defined no-font fallback; today missing glyphs silently render tofu or emoji. Registry fallback policy (4.6) addresses it; verify on a clean machine (Needs verification).
- **Frameless window quirks.** Header changes touch window-drag hit areas; test maximize/restore/drag after Phase 2.
- **JSON import guard is a behavior change** (the only approved one): it adds a confirmation dialog. Users relying on fast import lose one keystroke; accepted per decision in this plan's approval.
- **Performance.** Removing the always-on 33 ms decoration timer and consolidating effect timers should reduce idle CPU; any new state styling must avoid per-frame `style().polish()` calls (the header pulse already uses dynamic properties correctly — keep that pattern).
- **Private-skill/fixture conflicts.** If implementation contradicts a private skill (e.g., pal editor bounds), document the uncertainty before changing behavior, per AGENTS.md.
