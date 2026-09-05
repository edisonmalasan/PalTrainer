# UI Overhaul — Visual QA Ledger

> **Limitation (recorded 2026-09-04, see 000-design-context.md §2):** this
> environment cannot view images (`ib/image` screenshots and rendered captures
> alike). Verification below is therefore split into the four vocabulary
> categories from 000-design-context.md §12. **Screenshot-based visual
> verification is PENDING manual review** — the PNG captures listed here are
> saved for a capable reviewer (or the user) to inspect.

## Ledger

| Screen | Reference Folder | New Screenshot | Layout Changed | States Checked | Result |
|---|---|---|---|---|---|
| Shell v2 (band/tray/drawer) | ib/image (tools-tab header) | Logs/shell_v2_shot.png | Yes — structural (no sidebar, no right dock) | code-based: populated, empty, dirty, loading, drawer open/closed, Esc | Implementation+functional+structural PASS; visual PENDING |
| Start page v2 | ib/image/tools-tab | Logs/start_v2_shot.png, Logs/page_tools.png | Yes — structural (masthead/ledger/columns, no cards) | code-based: no-save, loaded metrics, hover/focus QSS defined | Implementation+functional+structural PASS; visual PENDING |
| Search Players | ib/image/search-players | Logs/page_players.png | Yes — ribbon search + full-bleed table + footer | code-based: filter counts, selection signal, bulk bar | PASS structural; visual PENDING |
| Exclusions | ib/image/exclusions | Logs/page_exclusions.png | Yes — segmented single-table (was 3 panels) | code-based: segment switch, context menus wired | PASS structural; visual PENDING |
| Map Viewer | ib/image/map-viewer | Logs/page_map.png | Yes — canvas-first + floating legend card | code-based: build, refresh, zoom emit | PASS structural; visual PENDING |
| Pal Editor | ib/image/pal-editor | Logs/page_pal_editor.png | Yes — ribbon + tokenized (geometry shell done) | code-based: build + slot select | PASS structural; visual PENDING |
| JSON Editor | ib/image/json-editor | Logs/page_json_editor.png | Yes — ribbon + footer toolbar, tokenized tree | code-based: refresh, search, read-only | PASS structural; visual PENDING |
| Breeding | ib/image/breeding | Logs/page_breeding.png | Yes — ribbon + tokenized switch/selectors | code-based: build, mode switch | PASS structural; visual PENDING |
| Base Inventory | ib/image/base-inventory | pending | Yes — ribbon + segmented switch (168 literals) | code-based: build via pages_ok | PASS structural; visual PENDING |
| Player Inventory | ib/image/player-inventory | pending | Yes — ribbon + tokenized actions (213 literals) | code-based: build via pages_ok | PASS structural; visual PENDING |
| Search Guilds / Bases | ib/image/search-* | pending | Yes — via 023 (same as players) | code-based: build via pages_ok | PASS structural; visual PENDING |
| Docs | ib/image/docs-tab | pending | Yes — ribbon + switch (inline cyan removed) | code-based: build via pages_ok | PASS structural; visual PENDING |

## Manual-review checklist (for whoever inspects the PNGs)

1. Confirm no left sidebar and no right dock are present (rail on the right).
2. Confirm warm dark canvas + amber accent + teal loaded-state (not cyan glass).
3. Confirm Hanken Grotesk renders headings and Inter renders body text.
4. Confirm the Start page shows masthead / field report / campaign strip /
   mission columns with no rounded glass cards.
5. Check long-text and localization overflow at ≥1200px width.
6. Check high-DPI rendering (capture at 100% and 200%).
