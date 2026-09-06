# Tasks — UI/UX Audit Remediation

## 1. Shell chrome: two-tier nav + icon collision

- [x] 1.1 Refactor `chrome/nav_strip.py` into two tiers per design D1: primary row (Tools, World, Edit, Reference zone tabs) + contextual secondary row (active zone's children); preserve `nav_changed(str)`, page IDs, `set_active`, shortcuts, i18n keys, and overflow/compact behavior per tier.
- [x] 1.2 Add last-visited-per-zone navigation with first-child fallback; Tools primary tab navigates directly.
- [x] 1.3 Add primary-tier active-zone treatment and keep active-page amber treatment on secondary tabs; extend QSS builder for the new classes.
- [x] 1.4 Differentiate the Base Inventory nav icon from Bases (reuse `container.svg` if it reads distinctly, else add one new bundled SVG per design D2).
- [x] 1.5 Add/extend unit tests covering: all 12 destinations reachable, signal contract unchanged, zone switching swaps secondary tier, overflow keeps everything reachable.
- [x] 1.6 Verify: focused pytest run, `uv run python -m compileall -q src tests`.

## 2. Shell chrome: status strip, warning states, path, monospace, context

- [x] 2.1 Add presentation-layer status message policy per design D3: human-readable strip messages; raw errors/stats demoted to log/console; update-check failure feeds the warning affordance instead of strip text.
- [x] 2.2 Implement warning button tri-state (none/unread/acknowledged) with click-to-reveal per design D4.
- [x] 2.3 Save path: truncate + monospace + tooltip + copy affordance per design D6 (Tools masthead).
- [x] 2.4 Add monospace token class per design D5; apply to technical values in shell surfaces.
- [x] 2.5 Hide the app-bar context indicator when no save is loaded (restore on load).
- [x] 2.6 Verify: focused pytest run, compileall; manual smoke: no raw HTTP/byte strings visible in strip.

## 3. Tools page

- [ ] 3.1 Convert Steam/GamePass buttons into one segmented platform control with bundled artwork per design D8; preserve both load flows.
- [ ] 3.2 Add live activity log panel below tool groups per design D9 (bounded height, auto-scroll, clear button).
- [ ] 3.3 Verify: focused pytest run, compileall; confirm metric chips and tool rows still navigate/trigger.

## 4. Table pages: Bases, Players, Guilds

- [ ] 4.1 Add shared inspector panel component (Docs detail pattern) per design D7; wire Bases, Players, Guilds to table-column + inspector layouts with capped content-height tables.
- [ ] 4.2 Identifier cells (Player UID, Guild ID, Base ID): monospace + shortened display + full-value tooltip + click-to-copy.
- [ ] 4.3 Move Players bulk action bar into the footer directly under the table; handlers unchanged.
- [ ] 4.4 Pagination indicator: "Page N of M" label; hide on single page (Bases/Players/Guilds).
- [ ] 4.5 Guilds member pane empty-state copy → row-level wording (i18n key add/update).
- [ ] 4.6 Verify: focused pytest run, compileall; confirm selection signals still drive member/detail data.

## 5. Exclusions

- [ ] 5.1 Add persistent visible "Add Exclusion" affordance per panel reusing the existing right-click add flow; empty state keeps guidance copy.
- [ ] 5.2 Verify: focused pytest run, compileall; confirm right-click menu and new button produce identical entries.

## 6. Base Inventory + Player Inventory

- [ ] 6.1 Base Inventory ribbon caption → `sidebar.section.editing` ("EDITING").
- [ ] 6.2 Split context selector chips (guild/base; player on Player Inventory) from view tabs (Inventory / Base Pals) per design D10.
- [ ] 6.3 Group container list: storage first, dropped-items debris in a muted separated group; all containers remain selectable.
- [ ] 6.4 Player Inventory: apply the same chip/tab distinction; verify zone caption already "EDITING".
- [ ] 6.5 Verify: focused pytest run, compileall; confirm container operations (move/delete) unchanged.

## 7. Pal Editor + JSON Editor

- [ ] 7.1 Pal Editor toolbar: group safe / bulk / destructive tiers with explicit separator before Bulk Delete; single row at min width.
- [ ] 7.2 Pal Editor inspector: editable fields vs computed stats visual affordance; unit tooltips on skill power values.
- [ ] 7.3 JSON Editor: persistent clickable path breadcrumb above the table.
- [ ] 7.4 Verify: focused pytest run, compileall; confirm all toolbar handlers fire and editor mutations unchanged.

## 8. Map Viewer + Breeding

- [ ] 8.1 Map overlay toggles: tooltips + accessible names; add +/− zoom controls beside the readout wired to existing zoom handlers.
- [ ] 8.2 Map browser columns: content-first sizing with full-value tooltips; headers untruncated at 1200px.
- [ ] 8.3 Breeding: fix CTA copy/position mismatch (i18n wording; no dangling "above" reference).
- [ ] 8.4 Verify: focused pytest run, compileall; confirm map toggles/zoom and breeding selection flows unchanged.

## 9. Full verification

- [ ] 9.1 Run full test suite: `uv run pytest -c tests/pytest.ini`.
- [ ] 9.2 Run `uv run python -m compileall -q src tests` and `uv run pyright src`.
- [ ] 9.3 Cross-check every audit Phase 1–3 item against shipped behavior; record any deliberate deviations.
