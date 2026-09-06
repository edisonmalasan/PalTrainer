## Context

Per-tab modernization program under `feat/tools-save-management-ui`. Each tab batch follows: orchestrator UX review → concrete spec/design/task updates → worker implementation → orchestrator review gate (diff + checks + populated screenshot). Tools is batch 1.

Current-state evidence for Tools (populated capture via `scripts/scrs/shot_populated.py`, backup Level.sav read-only fixture):

- Start page v2 renders masthead (kicker "OPS.SAVE_LEDGER", status + dot, Steam/GamePass buttons, path button, drag hint), a "OPS.FIELD REPORT" strip with 4 metric chips, an "OPS.CAMPAIGN" strip repeating 4 of the 7 tools, and a 3-column mission grid where "WORLD TOOLS" holds one row. Content ends ~60% down the canvas.
- Mission rows are `QPushButton#missionRow` — borderless, no icons, descriptions only in tooltips → weak affordance.
- Handler map (must be preserved): converting tool indices 0=convert saves (options dialog), 1=gamepass fix, 2=steamid, 3=restore map; management 0=slot injector, 1=character transfer, 2=fix host save. `_reset_save_session()` runs before every tool launch.
- Metrics chips have `_make_nav_release` wiring to players/guilds/bases/pal_editor — preserve.
- `refresh_labels()` retranslates masthead, rows, campaign buttons, overlay text — must be updated to the new structure; campaign button refs retire.
- QSS: `#fieldReport`, `#campaignStrip`, `#campaignStep`, `#missionZone`, `#missionRow` exist in qss_builder.py (~1153-1268); `#opsMasthead`, `#opsLoadBtn`, `#opsSavePath`, `#opsDropHint`, `#fieldMetric` retained/reused.

## Design decisions (orchestrator authority)

1. **One tool system.** Campaign strip is deleted. Mission columns become two balanced groups: Conversion (4 rows: Convert Save Files, Convert GamePass ↔ Steam, Convert SteamID, Restore Map — restoring map into conversion matches its `_run_converting_tool` index-3 handler grouping) and Management (3 rows). Group headers become plain labels ("Conversion Tools" / "Management Tools" — existing i18n `tools.section.converting` / `tools.section.management` reused; World Tools header retires).
2. **Real tool rows.** Each row = fixed icon tile (28px, bundled SVG via `app_icons.get_qicon`/pixmap factory), title (medium weight, primary text), one-line description (secondary text, always visible). Existing icon mapping: convert saves→`export`, gamepass fix→`gamepass`, steamid→`copy`, restore map→`map`, slot injector→`container`, character transfer→`player_select`, fix host save→`check_circle` (all present in `resources/assets/icons/svg/`). Rows keep `missionRow` objectName with upgraded QSS (surface background, 1px border, radius, 44px min height, hover accent border) so they read as buttons, not text.
3. **Masthead absorbs metrics.** Field-report strip retires; the four metric chips move into the masthead card's lower band as a metric row separated by a hairline. Chips keep navigation behavior and placeholder styling when empty (`—`). Masthead keeps status + dot + Steam/GamePass buttons + path reveal. "OPS.SAVE_LEDGER" kicker retires; status text itself is the masthead headline.
4. **State-dependent hint.** Drag hint label hidden in loaded state (shown only when `state == 'no_save'`); path button remains the reveal affordance (existing explorer behavior preserved).
5. **Density/width.** Canvas margins stay 24px; two tool columns split width with `stretch=1` each; `addStretch(1)` after columns is replaced by a compact footer guidance strip (translated hint pointing to status strip/logs) so the populated page doesn't leave a large dead band; no third column.
6. **Typography roles.** Group headers: small caps-style kicker treatment (existing `missionZone` style, weight 600). Tool titles: 11px medium→semibold; descriptions: `TYPE['micro']` secondary. No size inflation elsewhere.
7. **i18n.** Keys preserved; en_US values updated only where codenames retire (`ops.save_ledger`, `ops.field_report`, `ops.campaign` become unused — do not delete keys, stop referencing them). No other locale files touched.

## Constraints / non-goals

- No manager/business logic changes; handlers, save-session reset, dialog animation (`_animate_dialog_slide_in`), and ConversionOptionsDialog preserved.
- No parallel styling system; all new styles go through qss_builder tokens.
- No changes to other tabs in this batch; shared component extraction only if it falls out naturally (avoid speculative abstraction).
- Preserve `DropOverlay` drag-drop behavior and overlay text refresh path.

## Verification plan

- `uv run python -m compileall -q src tests`
- Focused pytest: tests covering tools tab / operations if present (`uv run pytest -c tests/pytest.ini tests/test_operations.py` exists per rg hit) plus any tools-related tests.
- `SHOT_PAGES=tools uv run python scripts/scrs/shot_populated.py` for populated capture; orchestrator reviews empty state by launching app without save.

## Batch 2: Base Inventory (orchestrator decisions, populated review done)

Evidence: settled no-selection capture + populated capture (guild selected via `_on_guild_changed` → auto base select; drive helper in `scripts/scrs/shot_populated.py`). Findings:

- Base selector label is raw GUID prefix ("707e7dcc"); container rows all read "CommonDropItem3D" with "?" icon; container info widget duplicates the selected container card; Loadouts button has hardcoded purple inline QSS (line ~2989); filters and structure actions share one undifferentiated row; selection state not visually distinct on picker buttons.

Decisions (chrome-level only; monolith internals stay out of scope per archived Phase 5 deferral):

1. **Human labels for selections.** Base picker rows/label show "Base N" (1-based index within guild) with the GUID kept in the tooltip. Container rows show a friendly display name derived from the internal asset name: strip `3D`/`Common`/`Drop`/`Item` casing artifacts and map known container assets to "Storage Chest"/"Feed Box"/etc.; when N containers share a display name, append a 1-based index ("Storage Chest 2"). Raw id stays available via tooltip.
2. **Dedupe selection info.** The left column shows the container summary exactly once: keep the list selection card; the bottom `ContainerInfoWidget` renders only when it carries information not already on the selection card (otherwise hidden for the current selection).
3. **Token-only styling.** Loadouts button restyled through qss_builder (standard ghost/secondary treatment, no hardcoded purple inline stylesheet).
4. **Toolbar grouping.** Row 1: guild picker, base picker, view switch (Inventory/Base Pals). Row 2 becomes filters + actions grouped with spacing and small icons: filter pickers (All Items, All Structures + clear buttons) left; Replace Structures action right-aligned. Pickers show selected state (accent border) when a selection is active.
5. **Empty-state hierarchy.** No-selection empty state keeps EmptyState component; precondition hint names both steps (choose guild → choose base).

## Batch 3: Player Inventory (orchestrator decisions, populated review done)

Evidence: populated capture (player "Hathaway" selected via drive helper). Findings: item names clip mid-word without ellipsis or tooltip; Sort button hardcoded purple (`inventory_tab.py:2044`, shared `InventoryGridWidget` header); toolbar mixes filters and heavy bulk actions at one visual weight; trailing grid row renders a wide empty slot artifact; player picker has no selected-state distinction.

Decisions (chrome-level; `InventoryGridWidget` is shared by Player and Base Inventory so its header fixes benefit both):

1. **Token-only toolbar.** Retire the hardcoded purple inline stylesheets on toolbar controls in `inventory_tab.py` (Sort at minimum; purple occurrences at lines ~1185/1284/1292 are internal panel decorations — retire where they style toolbar-class controls, leave semantic rarity colors `rarity_colors` untouched).
2. **Elided names.** Item/equipment card names elide via `QFontMetrics.elidedText` (single line) with the full name in the tooltip; no mid-word clipping.
3. **Toolbar grouping.** Filters/clears left; utility actions grouped right: [Modify Slots] [Loadouts] [Sort], then a separator before [Unlock All Fast Travel] styled with the warning-tier border (bulk mutation affordance) — preserving all handlers.
4. **Grid row artifact.** Fix the trailing wide-empty-slot rendering so incomplete rows show normal empty slots (no stretched placeholder).
5. **Picker selected state.** Reuse the batch-2 `_set_picker_selected` property pattern for the player picker button (extract to a shared helper if it avoids duplication; otherwise duplicate the 8-line static method — do not over-abstract).
6. **Non-goals.** Rarity color semantics (green/blue/purple borders on rarity tiers) are game data semantics and stay; grid column count and card sizes stay; no monolith internal rewrite.

## Batch 4: Pal Editor (orchestrator decisions, populated review done)

Evidence: populated capture (player selected, first box pal clicked → inspector filled). Findings: mojibake stat icons (`'âš”'`-style corrupted emoji in `pal_info_widget.py` ~712/725/738); 4 inspector buttons still `setFont(QFont(constants.FONT_FAMILY_NERD))` (~286/329/337/345) against the retired Nerd Font; SAN bar cyan gradient (`#38BDF8→#7DD3FC`, ~704) violates the frozen no-cyan rule; passive skill chips render cyan/blue gradient; raw GUID printed in the inspector identity header; party card HP text overlaps the HP bar; bulk toolbar uses 6+ competing accent colors with "Bulk Delete Pals" wrapping to its own row.

Decisions (chrome-level; the `editor/pal_editor/` module keeps its existing `_PAL_STYLESHEET` + per-widget mechanism — values are token-derived, recurring patterns move to qss_builder; no full internal rewrite):

1. **Encoding/icon repair.** Replace mojibake glyph QLabels (Attack/Defense/Work Speed icons) with clean text labels only — no new icon assets required. Remove the 4 `FONT_FAMILY_NERD` setFont calls; buttons keep/obtain readable text (existing text if any, else translated short labels) with optional SVG icons from the bundled set.
2. **Token-derive all hardcoded hexes in the Pal Editor chrome.** `data.py` `_PAL_STYLESHEET` and the inspector widget styles swap literal hexes for `chrome.tokens.resolve()` values. Bar treatments (hp/hunger/san/trust/exp/max) become named qss_builder rules; semantic mapping: HP=success, Hunger=warning, SAN=info, Trust/EXP/MAX=special — gradients flattened to solid token fills (or two-stop token gradients), cyan eliminated.
3. **Passive skill chips.** Flat token surface + `special_border` tier border (strong passives) / neutral border (regular); no gradients; readable contrast for the chip text.
4. **Inspector identity.** GUID demoted to tooltip (path button click-copy behavior if one exists is preserved); identity header = name, level badge, stars, gender/type icons; "NEXT MAX" row stays but must render readable (no garbled glyphs).
5. **Party cards.** HP value text moves to a dark pill/below-bar position so it never overlaps the fill; text uses primary text color.
6. **Toolbar tiers.** Neutral utility (Box/DPS toggle, Sort, Select All) = `ghostBtn`; bulk mutating actions (Restore All, Max All, Feed Food, All Skills, Bulk Clone Pals) = `warnActionBtn`; destructive (Bulk Delete Pals) = danger treatment (`make_danger_button` equivalent objectName); one row, no orphan wrap at 1200px.
7. **Non-goals.** Editor business logic, skill data mapping, bulk op handlers, DPS mode internals, grid card structure (beyond HP pill) unchanged; i18n keys preserved.

### Batch 4 review verdict (orchestrator)

APPROVED with one corrective follow-up folded into batch 5: painter-level hardcoded colors remain in `editor/pal_editor/widgets.py` — cyan `QColor(125,211,252,…)` at ~201 (badge border) and ~681 (pen), the 'legend' sweep gradient at ~863-867, and hardcoded purple rain at ~841/855. QSS is fully tokenized; these painter paths must derive from token values (info/special tiers).

## Batch 5: Players / Guilds / Bases (orchestrator decisions, populated reviews done)

Evidence: populated captures of all three SearchPanel table pages. Findings: page titles read as commands ("Search Players:" / "Search Guilds:" / "Search Bases:") and the same key feeds both the ribbon title and the search-field label (duplicated wording); Guild ID / Base ID / UID columns render full or truncated raw GUIDs; the Guilds member detail pane shows "No data — Load a save first." while a save IS loaded (conflates no-save with no-selection, plain text rather than shared EmptyState).

Decisions:

1. **Noun titles.** en_US values: `deletion.search_players` → "Players", `deletion.search_guilds` → "Guilds", `deletion.search_bases` → "Bases" (keys unchanged; ribbon title and search label both read correctly from the same key; other locales untouched).
2. **GUID hygiene.** Add a minimal tooltip capability to `SearchPanel.add_item` (per-column tooltip via QTreeWidget item.setToolTip); Players UID, Guilds Guild ID, Bases Base ID/Guild ID columns display the short form (first 8 chars + "…") with the full GUID in the tooltip. Keep all data passed through `data`/`sort_keys` unchanged — display-only.
3. **Guild members precondition.** No-selection state of the members pane uses the shared EmptyState component: "Select a guild to view its members" (hint: pick a guild above). The genuine no-save condition keeps a load-save message. Differentiated states, no plain text placeholder.
4. **4.8 painter correction** (from batch 4 review): token-derive `widgets.py` painter colors — cyan family → info tier, purple family → special tier.
5. **Non-goals.** Table columns/order/widths preserved except display-text shortening with tooltips; context menus, selection wiring, footer pattern unchanged.

## Batch 6: Map (orchestrator decisions, populated review done)

Evidence: populated capture (map renders, browser panel, overlay toolbar). Findings: 10 hardcoded cyan occurrences in `map_tab.py` toolbar styles (`rgba(125,211,252,…)` + `#7dd3fc` checked borders) — the toolbar's active toggle shows a cyan ring; ribbon zone caption uses `sidebar.section.inspect` ("LOAD & INSPECT") while Map lives in the World nav zone (other world pages use `sidebar.section.world`); browser tree's 5th column header truncates ("Bas…") inside the 340px sidebar.

Decisions:

1. **Toolbar tokens.** `btn_css`/`btn_wide_css` inline styles retire into a named qss_builder rule (`mapToggleBtn`); checked state uses accent tokens (accent border, accent-tinted background), not cyan. Icon buttons keep their existing local .webp assets and tooltips.
2. **Zone caption.** Map ribbon zone → `sidebar.section.world` (key exists; value-only reference change).
3. **Browser columns.** Sidebar min width 340 → 360; explicit per-column widths for the base/player trees so no header label truncates at minimum window size (Bases/Base Pals columns sized to fit); headers remain Interactive with last-section stretch.
4. **Non-goals.** Map rendering, markers, calibration flows, coordinate chips, browser search untouched.

### Batch 6 review verdict (orchestrator)

APPROVED. Active toggles show amber accent, zone caption WORLD DATA, browser headers untruncated (verified in capture + worker's pixel scan). Correction folded into batch 7: remaining map cyan — calibration label (~289), bases/players sidebar tab buttons (~856/857), and 4 context-menu border styles (~1282/1334/1448/2462).

## Batch 7: Exclusions (orchestrator decisions, populated review done)

Evidence: populated capture (save loaded, exclusions lists empty). Findings: all three exclusion panels show "No data — Load a save first." while a save IS loaded — an empty exclusions list is a valid configured state, conflated with the no-save condition (same class of bug as batch 5's guilds members pane). Exclusions are managed via right-click context menus (add flows live on Players/Guilds/Bases context menus).

Decisions:

1. **Differentiated empty states.** When no save is loaded, panels keep the load-save message. When a save is loaded but the list is empty, each panel shows the shared EmptyState presentation: "No exclusions configured" with hint "Use the right-click menu on Players, Guilds, or Bases to exclude entries" (players/guilds/bases variants where wording differs naturally). Wired via the existing `set_empty_state`/`set_empty_state_widget` plumbing and refresh_labels.
2. **Map cyan correction** (from batch 6 review): calibration label color, bases/players sidebar tab buttons, and the 4 context-menu border styles in map_tab.py → token-derived (accent/info tiers, builder-consistent menus).
3. **Non-goals.** Context menu behavior, exclusion storage, switching buttons (pageSwitchBtn already correct), table columns unchanged.

### Batch 7 review verdict (orchestrator)

APPROVED. Loaded-but-empty EmptyState verified in capture with per-type hints; no-save state keeps load-save message; map_tab cyan fully tokenized (only a code comment remains); 481 tests green.

### JSON Editor review verdict (orchestrator)

PASSES with no changes needed: standard page frame (search toolbar, Key/Value/Type tree, footer status + actions), tooltips on search steppers, no hardcoded color violations found. No batch dispatched.

## Batch 8: Breeding + Docs (orchestrator decisions, populated reviews done)

Evidence: populated captures of both pages; wiki_tab.py contains 26 cyan-family occurrences (`#7DD3FC`/`rgba(125,211,252,…)` in `_BASE` active states, `_LIST_S`, `_SORT_BTN_S`/`_FILTER_BTN_S`, `_card`/`_badge` defaults, painter at ~355); Breeding duplicates its CTA — a standalone "Select a Pal…" button + hint label above the results AND the EmptyState's own CTA + hint below (both visible pre-selection).

Decisions:

1. **Breeding single CTA.** While no pal is selected: hide the standalone select button and hint label (the EmptyState owns the CTA); show them again once a pal is selected (button becomes the re-select affordance). `_selected_label` behavior unchanged.
2. **Docs tokens.** All cyan-family values in wiki_tab.py → token-derived (accent for active/filter states, builder-consistent list styles, info/special for badges per semantic); painter QColor included. No layout rewrite of the wiki (sidebar/list/detail structure is sound).
3. **Docs filter label truncation.** The "Element:" filter label truncates ("Elemé:") when icon chips share the first row; render the group label on its own row above the chips whenever the group has more than a few values (use the existing multi-row branch for the element groups) so the label never clips.
4. **Non-goals.** Wiki content, search behavior, sort logic, breeding computation, Parents/Children toggle unchanged.
