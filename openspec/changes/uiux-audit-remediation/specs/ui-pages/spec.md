# ui-pages Delta

## Purpose

Defines the per-page layout, hierarchy, density, and interaction contracts for PalTrainer's modernized content pages, so each page communicates its primary goal first, presents actions with clear affordances, uses screen space intentionally, and behaves coherently in both precondition (no save / no selection) and populated working states.

## ADDED Requirements

### Requirement: Tools page hosts a live activity log panel

The Tools page SHALL present a live log panel in the canvas area below the grouped tool system: it mirrors the application's streamed operational messages (the same stream the status strip and console consume), auto-scrolls to the newest entry, and provides a clear control. The panel occupies a bounded height rather than an unbounded fill.

#### Scenario: Populated Tools page uses the lower canvas

- **WHEN** the Tools page is shown populated at default window size
- **THEN** the area below the tool groups contains the live log panel instead of empty canvas, and log entries accumulate as operations stream

#### Scenario: Log panel clearing

- **WHEN** the user activates the log panel's clear control
- **THEN** the panel empties without affecting the detached console or the underlying log stream

### Requirement: Base Inventory distinguishes context selection from view switching

The Base Inventory page SHALL visually separate its two control kinds: guild and base selection controls render as bordered dropdown selector chips with chevrons (context breadcrumbs that switch what is being viewed), while the Inventory and Base Pals surfaces render as underlined view tabs (view modes within the selected context). The three control kinds SHALL NOT share one identical chip styling.

#### Scenario: Chips and tabs are distinguishable

- **WHEN** a guild and base are selected on the Base Inventory page
- **THEN** the guild and base controls show selector-chip styling with a chevron, the Inventory / Base Pals controls show tab styling with the active tab underlined, and activating them switches view without changing selection

### Requirement: Base Inventory groups storage containers above world debris

The Base Inventory container list SHALL present meaningful storage containers (guild chests, storage containers with multiple slots) grouped first, and near-empty world debris (dropped items) grouped below under a visually muted section, so the primary containers do not compete with incidental entries for attention. Both groups remain selectable and complete — no container is hidden or removed.

#### Scenario: Container list ordering

- **WHEN** the container list is populated for a base with both storage containers and dropped-item entries
- **THEN** storage containers appear in the primary group above a separated, muted dropped-items group, and every container remains reachable and selectable

### Requirement: Player Inventory matches the shared chip and tab pattern

The Player Inventory page SHALL use the same visual distinction between context selector chips and view tabs as the Base Inventory page, and its zone caption SHALL read "EDITING".

#### Scenario: Player Inventory control kinds

- **WHEN** the Player Inventory page renders its context and view controls
- **THEN** selector controls and view controls are visually distinguishable per the shared pattern, and the zone caption matches the Edit tier

### Requirement: JSON Editor shows a persistent path breadcrumb

The JSON Editor SHALL render a persistent breadcrumb of the current tree path above the table, updating as the selection or expansion point changes, so the user's position remains visible after scrolling deep nesting.

#### Scenario: Deep navigation keeps context

- **WHEN** the user expands several nested levels in the JSON tree
- **THEN** the breadcrumb shows the path from the root (for example "properties > worldSaveData > …") and remains visible without scrolling

### Requirement: Map overlay controls are discoverable

The Map page overlay toolbar SHALL give every toggle button a tooltip and accessible name describing what it toggles, and the map canvas SHALL provide visible zoom-in and zoom-out controls adjacent to the zoom-level readout in addition to any scroll-based zooming.

#### Scenario: Toggle tooltips

- **WHEN** the user hovers any map overlay toggle button
- **THEN** a tooltip names the overlay it toggles, and the button exposes an accessible name with the same text

#### Scenario: Visible zoom controls

- **WHEN** the map canvas is shown
- **THEN** zoom-in and zoom-out buttons sit adjacent to the zoom readout and adjusting them changes the map zoom identically to scroll zooming

## MODIFIED Requirements

### Requirement: Tools page presents a single save-hub with one grouped tool system

The Tools page SHALL present a save-hub masthead (save state, save path with reveal and copy affordances, Steam/GamePass platform selection as a single segmented control, and Players/Guilds/Bases/Pals metric chips that navigate to their pages) followed by exactly one grouped tool list system and the live activity log panel: tool entries SHALL NOT be repeated in a second quick-action/campaign surface. Tool entries SHALL be organized into labeled groups — Conversion (Convert Save Files, Convert GamePass ↔ Steam, Convert SteamID, Restore Map) and Management (Slot Injector, Character Transfer, Fix Host Save) — with every group containing at least two entries.

#### Scenario: Populated Tools page structure

- **WHEN** the Tools page is shown with a save loaded
- **THEN** the masthead card shows the loaded state with the truncated save path, the segmented platform control, and clickable metric chips; below it, exactly two tool groups (Conversion with 4 rows, Management with 3 rows) are present with no duplicate quick-action strip, and the live log panel fills the lower canvas

#### Scenario: Metric chips navigate

- **WHEN** the user clicks the Players, Guilds, Bases, or Pals metric chip on the Tools page
- **THEN** the application navigates to the corresponding page, preserving the existing navigation behavior

#### Scenario: Platform segmented control

- **WHEN** the user selects a platform in the segmented control
- **THEN** the segmented control shows exactly one platform selected at a time and activating it starts the same load flow the previous standalone buttons triggered

### Requirement: Base Inventory page uses human-readable selection labels

The Base Inventory page SHALL present selection controls with user-facing labels: base selections display as "Base N" (1-based within the selected guild) rather than raw identifiers, container list rows display human-readable container names (derived from internal asset names, with a 1-based index when several containers share a name) rather than raw asset names, and raw identifiers remain accessible via tooltips. Selection information for the active container SHALL appear exactly once in the left column. The page's zone caption SHALL read "EDITING", matching its Edit-tier nav position.

#### Scenario: Populated base selection

- **WHEN** a guild and base are selected and the container list is populated
- **THEN** the base picker shows a "Base N" label, container rows show human-readable names (e.g. "Storage Chest 2"), raw ids appear only in tooltips, and the selected container's summary is not rendered twice in the left column

#### Scenario: Zone caption matches Edit tier

- **WHEN** the Base Inventory page is shown
- **THEN** its ribbon zone caption reads "EDITING" and never "WORLD DATA"

#### Scenario: No selection

- **WHEN** no guild/base is selected
- **THEN** the empty state names both prerequisite steps (select guild, then select base) instead of a generic message

### Requirement: Exclusions pages differentiate configured-empty from no-save states

The Exclusions page panels SHALL distinguish between the no-save condition (load-save message retained) and the loaded-but-empty condition (shared empty-state presentation: "No exclusions configured" with a hint directing users to the right-click exclusion menus on Players, Guilds, and Bases). Each panel SHALL additionally provide a persistent visible "Add Exclusion" affordance that adds an entry to that panel's list directly, so the right-click menu is not the only route. The page SHALL NOT display "Load a save first" messaging while a save is loaded. All remaining hardcoded cyan in Map page chrome (calibration label, sidebar tab buttons, context menu borders) SHALL be token-derived.

#### Scenario: Save loaded, no exclusions

- **WHEN** a save is loaded and the selected exclusions list has no entries
- **THEN** the panel shows the shared empty-state presentation explaining the list is empty and where exclusions are added, not a load-save message, and a visible Add Exclusion affordance is present

#### Scenario: Add exclusion affordance

- **WHEN** the user activates the Add Exclusion affordance on a panel while a save is loaded
- **THEN** the panel opens the same add flow as the right-click exclusion menu for that list, and the resulting entry appears in the table

#### Scenario: No save loaded

- **WHEN** no save is loaded
- **THEN** the exclusions panels show the load-save guidance state

### Requirement: Standard table pages use noun titles, hygienic identifier columns, and differentiated member-precondition states

The Players, Guilds, and Bases pages SHALL present noun page titles (Players, Guilds, Bases — no "Search …" command phrasing in titles), SHALL render identifier columns (Player UID, Guild ID, Base ID) in a shortened display form with the full identifier available via tooltip and a click-to-copy affordance in a monospace font, and the Guilds member detail pane SHALL differentiate its no-save state (load-save message) from its no-selection state (shared empty-state presentation whose copy describes the row interaction — "Click a guild row to view its members" — without implying no global selection exists). No raw full identifiers remain as visible column text.

#### Scenario: Players page with populated table

- **WHEN** a save is loaded and the Players page shows its table
- **THEN** the page title reads "Players", the UID column shows a shortened monospace identifier with the full UID in the tooltip and click-to-copy, and the search field label does not duplicate the title phrasing

#### Scenario: Guild members without selection

- **WHEN** a save is loaded but no guild row is selected on the Guilds page
- **THEN** the member pane shows the shared empty-state presentation with row-level wording ("Click a guild row to view its members" plus a hint) rather than a no-save message, plain text, or wording implying no guild was chosen anywhere

#### Scenario: Bases identifiers

- **WHEN** the Bases page table is populated
- **THEN** Base ID and Guild ID columns show shortened monospace identifiers with full values in tooltips and click-to-copy

### Requirement: Map overlay chrome is token-styled and browser columns stay readable

The Map page overlay toolbar SHALL style its toggle buttons through the shared theme builder with an accent-based active state (no cyan, no hardcoded inline color stylesheets), the page ribbon zone caption SHALL match the page's navigation zone (World), and the map browser sidebar SHALL size its tree columns to content before truncating values, with full values available via tooltips, so no column header label truncates at the minimum window width.

#### Scenario: Active map toggle

- **WHEN** a map overlay toggle (bases, players, rings, zones, map type) is active
- **THEN** the button shows the accent-based checked styling from the theme builder with no cyan ring or hardcoded inline stylesheet

#### Scenario: Browser headers at minimum width

- **WHEN** the Map page renders at 1200px window width
- **THEN** the map browser tree column headers (Guild, Leader, Last Seen, Bases, Base Pals) display without truncation, and truncated cell values show full text in tooltips

### Requirement: Breeding presents a single call-to-action and Docs uses the token palette

The Breeding page SHALL present exactly one "Select a Pal" call-to-action while no pal is selected (the shared empty-state's action); the standalone select button and hint label reappear only after a pal is selected (as the re-select affordance), and any instructional copy SHALL describe the controls' actual positions (no "above"/"below" wording that contradicts the layout). The Docs page SHALL style its category/list/filter/sort/badge/card chrome entirely from the token palette with no cyan-family hardcoded values, and its filter group labels SHALL NOT truncate (multi-value groups render the label on its own row above the filter chips).

#### Scenario: Breeding pre-selection

- **WHEN** the Breeding page is shown with no pal selected
- **THEN** exactly one visible "Select a Pal" action exists (inside the empty state), with the standalone button and hint label hidden, and no instructional copy references a control in the wrong position

#### Scenario: Docs filter group with many values

- **WHEN** the Docs page renders the Elements filter group
- **THEN** the "Element:" label is fully visible (own row above the chips) and no filter chip row clips the label

#### Scenario: Docs token compliance

- **WHEN** the Docs page renders lists, filters, sorts, badges, and detail cards
- **THEN** no cyan-family hardcoded color values remain in the wiki styling

## REMOVED Requirements

(none)
