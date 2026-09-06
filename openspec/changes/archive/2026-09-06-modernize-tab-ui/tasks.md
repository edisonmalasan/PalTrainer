# Tasks

## 1. Tools page (batch 1)

- [x] 1.1 Remove campaign strip: delete `CAMPAIGN_STEPS`, `_create_campaign_strip`, `_campaign_btns` and its `refresh_labels()` branch; retire `#campaignStrip`/`#campaignStep` QSS rules.
- [x] 1.2 Rebalance tool groups into two columns: Conversion (convert saves, gamepassâ†”steam, steamid, restore map) and Management (slot injector, character transfer, fix host save); retire World Tools header; preserve handler indices and `_reset_save_session()` behavior.
- [x] 1.3 Upgrade tool rows to action rows: icon tile (bundled SVGs per design mapping), title + always-visible one-line description, hover/cursor affordance; update `refresh_labels()` for the new row structure.
- [x] 1.4 Merge field-report metrics into masthead: metric chips row inside the save-hub card (keep nav wiring, placeholder styling); remove standalone `fieldReport` frame and QSS; retire "OPS.SAVE_LEDGER"/"OPS.FIELD REPORT" kicker references.
- [x] 1.5 State-dependent save hub: hide drag hint when loaded; keep path reveal affordance; verify no-save state still shows hint + guidance.
- [x] 1.6 Replace `body.addStretch(1)` dead band with compact translated footer guidance strip; keep page scroll behavior intact.
- [x] 1.7 Update en_US label values only where jargon retires; keys preserved; no other locales touched.
- [x] 1.8 Verification: `uv run python -m compileall -q src tests`; focused pytest for touched areas; populated screenshot via `SHOT_PAGES=tools uv run python scripts/scrs/shot_populated.py`; confirm no-save state visually.

## 2. Base Inventory (batch 2)

- [x] 2.1 Friendly base labels: base picker rows and button label show "Base N" (1-based per guild); GUID only in tooltip.
- [x] 2.2 Friendly container labels: map internal container asset names to human display names; index duplicates ("Storage Chest 2"); raw id in tooltip; list selection card unchanged otherwise.
- [x] 2.3 Dedupe container info: hide bottom ContainerInfoWidget when it repeats the selected card's information; show only when it adds detail.
- [x] 2.4 Retire hardcoded purple Loadouts stylesheet; restyle via qss_builder tokens.
- [x] 2.5 Regroup context row: filters (All Items, All Structures, clears) left, Replace Structures right; add small icons; selected pickers show accent-border selected state.
- [x] 2.6 Empty-state hint names the two-step prerequisite (guild â†’ base).
- [x] 2.7 Fix stale QSS comment at qss_builder.py:1152 ("Start page v2 ... field report + campaign" â†’ Start page v3 wording).
- [x] 2.8 Verification: compileall; focused pytest; populated screenshot `SHOT_PAGES=base_inventory` with guild/base driven; no-selection screenshot.

## 3. Player Inventory (batch 3)

- [x] 3.1 Retire hardcoded purple toolbar stylesheets in inventory_tab.py (Sort button + toolbar-class purple decorations; keep rarity color semantics).
- [x] 3.2 Elide item/equipment card names via QFontMetrics with full-name tooltips (no mid-word clipping).
- [x] 3.3 Regroup toolbar: filters/clears left; Modify Slots/Loadouts/Sort right; separator before warning-styled Unlock All Fast Travel.
- [x] 3.4 Fix trailing wide-empty-slot artifact in inventory grid rows.
- [x] 3.5 Selected-state property pattern on the player picker button (reuse batch-2 pattern).
- [x] 3.6 Verification: compileall; focused pytest; populated screenshot `SHOT_PAGES=player_inventory` (drive helper selects first player); no-selection state check.

## 4. Pal Editor (batch 4)

- [x] 4.1 Repair encoding damage: replace mojibake stat icon QLabels with clean text labels; remove the 4 `FONT_FAMILY_NERD` setFont calls in pal_info_widget.py (readable text labels or bundled SVG icons instead).
- [x] 4.2 Token-derive hardcoded hexes in pal_editor chrome (`data.py` _PAL_STYLESHEET + inspector styles) via chrome.tokens; move bar treatments (hp/hunger/san/trust/exp/max) into named qss_builder rules; eliminate cyan (SAN bar â†’ info tier).
- [x] 4.3 Passive skill chips: flat token surface + special/neutral tier borders, no gradients.
- [x] 4.4 Inspector identity header: GUID to tooltip; readable NEXT MAX row (no garbled glyphs).
- [x] 4.5 Party cards: HP text into dark pill/below-bar position, no overlap with the fill.
- [x] 4.6 Toolbar tiers: ghostBtn for Box/Sort/Select All; warnActionBtn for Restore All/Max All/Feed Food/All Skills/Bulk Clone; danger treatment for Bulk Delete; single row at 1200px.
- [x] 4.7 Verification: compileall; focused pytest + full suite; populated screenshot `SHOT_PAGES=pal_editor` (drive helper selects player + first pal) with inspector visible; confirm no mojibake glyphs and no cyan.

## 5. Players / Guilds / Bases (batch 5)

- [x] 4.8 Correction (from batch 4 review): token-derive painter colors in editor/pal_editor/widgets.py (cyan QColor(125,211,252,â€¦) at ~201/~681/'legend' sweep ~863-867 â†’ info tier; purple rain at ~841/855 â†’ special tier).
- [x] 5.1 Noun titles: en_US `deletion.search_players`â†’"Players", `deletion.search_guilds`â†’"Guilds", `deletion.search_bases`â†’"Bases" (values only; keys and other locales untouched).
- [x] 5.2 SearchPanel per-column tooltip support; Players UID, Guilds Guild ID, Bases Base ID/Guild ID columns show short form (first 8 + ellipsis) with full GUID tooltip; data/sort_keys unchanged.
- [x] 5.3 Guilds members pane: shared EmptyState for no-selection ("Select a guild to view its members" + hint); no-save condition keeps load-save message; states differentiated.
- [x] 5.4 Verification: compileall; full pytest; populated screenshots `SHOT_PAGES=players,guilds,bases`; guilds no-selection state uses EmptyState (visible in capture).

## 6. Map (batch 6)

- [x] 6.1 Retire 10 hardcoded cyan styles in map_tab.py toolbar (btn_css/btn_wide_css) into a named qss_builder `mapToggleBtn` rule with accent checked-state; regenerate darkmode.qss.
- [x] 6.2 Map ribbon zone caption â†’ `sidebar.section.world`.
- [x] 6.3 Browser sidebar min width 340â†’360 with explicit base/player tree column widths so no header truncates at 1200px.
- [x] 6.4 Verification: compileall; full pytest; populated capture `SHOT_PAGES=map`; confirm no cyan ring on active toggles and no truncated headers.

## 7. Exclusions (batch 7)

- [x] 6.5 Correction (from batch 6 review): map_tab.py remaining cyan â†’ tokens (calibration label ~289, bases/players tab buttons ~856-857, 4 context menu styles ~1282/1334/1448/2462).
- [x] 7.1 Exclusions panels differentiate no-save (keep load-save message) vs loaded-but-empty (shared EmptyState "No exclusions configured" + hint pointing to right-click menus on Players/Guilds/Bases); wired through refresh_labels.
- [x] 7.2 Verification: compileall; full pytest; populated capture `SHOT_PAGES=exclusions`; confirm loaded-but-empty shows the new EmptyState; no-save state checked offscreen.

## 8. Breeding + Docs (batch 8)

- [x] 8.0 JSON Editor: reviewed by orchestrator â€” compliant, no changes needed.
- [x] 8.1 Breeding: while no pal is selected hide the standalone select button + hint label (EmptyState owns the CTA); restore both after a pal is selected.
- [x] 8.2 Docs: tokenize all 26 cyan-family occurrences in wiki_tab.py (active/filter/list styles, card/badge defaults, painter QColor) â†’ accent/info/special tokens.
- [x] 8.3 Docs: fix "Element:" filter label truncation â€” label renders on its own row above the chips for multi-value groups.
- [x] 8.4 Verification: compileall; full pytest; populated captures `SHOT_PAGES=docs,breeding`; confirm no cyan in wiki and single CTA on breeding.

## 5. Players (batch 5 â€” pending orchestrator review)

## 6. Guilds (batch 6 â€” pending orchestrator review)

## 7. Bases (batch 7 â€” pending orchestrator review)

## 8. Map (batch 8 â€” pending orchestrator review)

## 9. Exclusions (batch 9 â€” pending orchestrator review)

## 10. JSON Editor (batch 10 â€” pending orchestrator review)

## 11. Docs / Wiki (batch 11 â€” pending orchestrator review)

## 12. Breeding (batch 12 â€” pending orchestrator review)
