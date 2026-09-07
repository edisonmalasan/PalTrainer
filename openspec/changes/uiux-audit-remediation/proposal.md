# UI/UX Audit Remediation

## Why

A full UI/UX audit of the running application found structural and interaction defects that undermine an otherwise coherent visual foundation: the zone-grouped navigation reads as one undifferentiated 16-item row, a taxonomy break tags Base Inventory "WORLD DATA" while it lives under Edit, raw technical strings (HTTP errors, byte counts, full save paths) surface in primary chrome, a warning icon stays lit permanently, critical actions are hidden behind right-click-only interactions, and data-heavy pages leave half the canvas empty while the nav is overcrowded.

## What Changes

- Split the nav strip into two tiers: 5 primary destinations (Start, Tools, World, Edit, Reference) plus a contextual secondary row showing only the active zone's children. Navigation contracts (page IDs, `nav_changed` signal, keyboard shortcuts, i18n) are preserved.
- Fix the Bases / Base Inventory icon collision by giving Base Inventory a distinct open-container icon.
- Restrict "WORLD DATA" zone captions to read-oriented pages; Base Inventory and all Edit children caption "EDITING".
- Move raw technical strings out of the status strip: human-readable messages only; errors/byte counts route to the existing log/console. Update-check failures render as a resolved/unresolved icon state, never raw HTTP text.
- Give the app-bar warning button three states (none / unread-highlighted / acknowledged-dimmed) with click-to-reveal.
- Truncate the save path with monospace font, copy affordance, and full-value tooltip.
- Add monospace + tooltip + click-to-copy on truncated identifier cells (Player UID, Guild ID, Base ID).
- Convert Steam/GamePass load buttons into one segmented platform toggle.
- Add a live log panel to the Tools page lower area (bounded height, follows status-stream messages).
- Cap table containers to content height on Bases/Players/Guilds and add a right-hand inspector/detail panel (Docs list+detail pattern) that fills the freed space.
- Re-position Players bulk actions into the table footer toolbar directly under the table (preserving ui-tables frame order and all handlers).
- Label the single-page indicator as "Page 1 of N" (hide entirely when only one page).
- Add an explicit "+ Add Exclusion" button on the Exclusions page alongside the existing right-click flow.
- Split Base Inventory chips: context breadcrumbs become dropdown selector chips; Inventory/Base Pals become underlined view tabs. Group the container list: meaningful storage (Guild Chest etc.) first, dropped-item debris separated below with a muted section label.
- Apply the same chip/tab distinction and container grouping to Player Inventory for parity.
- Pal Editor: group the 8-button toolbar into safe / bulk / destructive tiers with a visual separator before Bulk Delete; add editable-vs-computed visual affordance in the inspector (editable fields get focusable styling; computed stats are read-only flat text); show units on skill values via tooltip.
- JSON Editor: add a persistent clickable path breadcrumb above the tree.
- Map Viewer: tooltips (and accessible names) on all overlay toggle buttons; add visible +/− zoom controls beside the zoom readout; flex browser columns to content before truncating.
- Breeding: fix CTA copy mismatch so the hint matches the button's actual position.
- Rename Guilds member empty-state copy to row-level wording ("Click a guild row to view its members") to avoid clashing with the global context selection.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `ui-nav`: nav restructured into primary + contextual secondary tiers; zone captions become tier headings; icon collision fix; collapse/overflow behavior re-expressed per tier.
- `ui-shell`: status strip message policy, warning button tri-state, save path truncation, monospace data typography, platform segmented toggle, context indicator behavior preserved.
- `ui-pages`: Tools (log panel, segmented toggle), Base Inventory (chips/tabs, container grouping, EDITING caption), Player Inventory parity, Pal Editor (toolbar tiers, editable affordance, units), JSON Editor (breadcrumb), Map (tooltips, zoom), Breeding (CTA copy), Exclusions (+ Add button), Guilds (copy).
- `ui-tables`: capped content-height tables, inspector panel pairing, identifier copy/tooltip/monospace, pagination label, bulk-actions adjacency on Players.
- `ui-states`: Tools empty/loading states absorb the log panel without violating the no-dead-region rule; empty-state copy updates (Guilds row-level wording).

## Impact

- **Code:** `src/palworld_aio/ui/chrome/nav_strip.py`, `app_bar.py`, `components.py`, `qss_builder.py`, `tokens.py`, `icons.py`, `styled_combo.py`; `src/palworld_aio/ui/main_window.py` (page setup, status stream wiring); `src/palworld_aio/ui/tabs/tools_tab.py`, `inventory_tab.py`, `base_inventory_tab.py`, `pal_editor_tab.py`, `json_editor_tab.py`, `map_tab.py`, `breeding_tab.py`; world table pages.
- **Preserved:** all save/load/data logic, save engine calls, menu action handlers, dialog operations, `nav_changed` page-ID contract, keyboard shortcuts, i18n key infrastructure (new keys added, none removed), bundled SVG icon set under `resources/assets/icons/svg`.
- **New assets:** at most one new `base_inventory`-distinct SVG icon (e.g. open-container glyph) following the existing icon factory pattern.
- **i18n:** new user-facing strings added via `src/i18n` with en_US fallbacks; existing keys unchanged.
