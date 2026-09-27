# ui-pages Specification

## Purpose

Defines the per-page layout, hierarchy, density, and interaction contracts for PalTrainer's modernized content pages, so each page communicates its primary goal first, presents actions with clear affordances, uses screen space intentionally, and behaves coherently in both precondition (no save / no selection) and populated working states.

## Requirements

### Requirement: Plain section labels without dev jargon

Content-page section labels SHALL present user-facing wording (translated where the page is translated); internal operation codenames (e.g. "OPS.SAVE_LEDGER", "OPS.FIELD REPORT", "OPS.CAMPAIGN") SHALL NOT appear as visible UI text on modernized pages.

#### Scenario: Tools section labels read as UI copy

- **WHEN** Tool Center renders its section labels
- **THEN** no label shows an internal codename pattern such as "OPS.*" and each label reads as user-facing copy consistent with the en_US locale

### Requirement: Page content uses available width without dead regions
Modernized pages SHALL size their content regions to use the available workspace at supported window sizes without reserved dead columns. Populated content SHALL not leave a dominant empty band, while maps and data-heavy editors SHALL prioritize their primary workspace rather than dashboard-card decoration.

#### Scenario: Populated Tool Center fills the workspace
- **WHEN** the Tool Center is shown at the default desktop size
- **THEN** categorized tool cards use a responsive layout, search and filters remain visible, and no empty region dominates the populated content

#### Scenario: Populated Tools page fills the canvas
- **WHEN** the Tool Center replaces the former populated Tools page at the default desktop size
- **THEN** tool discovery uses the available workspace without a reserved dead column or an empty band taller than the categorized tool content

### Requirement: Platform assets use correct bundled artwork

Platform-specific UI (Steam and GamePass load buttons and any platform badges) SHALL use the existing bundled SVG assets (steam.svg, gamepass.svg, gamepass_alt.svg) via the token-colored icon factory; no substitute platform logos and no Nerd Font glyph rendering MAY be introduced.

#### Scenario: Steam and GamePass buttons render bundled artwork

- **WHEN** Overview renders its Steam and GamePass load buttons
- **THEN** both buttons show artwork from the bundled steam/gamepass SVG assets through the icon factory with token-appropriate colors, and no text renders in a Nerd Font family

### Requirement: Base Inventory page uses human-readable selection labels

The Base Inventory page SHALL present selection controls with user-facing labels: base selections display as "Base N" (1-based within the selected guild) rather than raw identifiers, container list rows display human-readable container names (derived from internal asset names, with a 1-based index when several containers share a name) rather than raw asset names, and raw identifiers remain accessible via tooltips. Selection information for the active container SHALL appear exactly once in the left column.

#### Scenario: Populated base selection

- **WHEN** a guild and base are selected and the container list is populated
- **THEN** the base picker shows a "Base N" label, container rows show human-readable names (e.g. "Storage Chest 2"), raw ids appear only in tooltips, and the selected container's summary is not rendered twice in the left column

#### Scenario: No selection

- **WHEN** no guild/base is selected
- **THEN** the empty state names both prerequisite steps (select guild, then select base) instead of a generic message

### Requirement: Base Inventory toolbar separates filters from actions

The Base Inventory page SHALL group its secondary controls: filter pickers (item filter, structure filter, with their clear affordances) grouped apart from the Replace Structures action, and picker buttons SHALL show a visually distinct selected state while a selection is active. All control styling SHALL come from the shared theme builder with no hardcoded inline color stylesheets.

#### Scenario: Filters and actions are distinguishable

- **WHEN** the Base Inventory page renders its context row with a base selected
- **THEN** filter pickers and the Replace Structures action are visually grouped and spaced as separate controls, pickers with an active selection show the selected-state styling, and no control carries an inline hardcoded color stylesheet outside the theme builder

### Requirement: Player Inventory toolbar separates filters from bulk actions and renders readable item names

The Player Inventory page SHALL group its toolbar controls by weight: filters and clears left, utility actions (Modify Slots, Loadouts, Sort) grouped right, and the bulk Unlock All Fast Travel action visually distinguished (warning-tier treatment) behind a separator from routine actions, with all handlers preserved. Item and equipment card names SHALL be elided with the full name available via tooltip rather than clipped mid-word. The inventory grid SHALL NOT render a stretched trailing placeholder for incomplete rows. Game-data rarity color semantics on item cards are preserved.

#### Scenario: Populated player inventory toolbar

- **WHEN** a player is selected and the inventory grid is populated
- **THEN** the toolbar shows filters left and utility actions right with the Unlock All Fast Travel action visually distinguished, no toolbar control carries a hardcoded inline color stylesheet outside the theme builder, every item and equipment name is elided with a full-name tooltip, and no stretched trailing empty slot renders after the last item

#### Scenario: Player picker selected state

- **WHEN** a player is selected on the Player Inventory page
- **THEN** the player picker button shows the shared accent-border selected state, matching the Base Inventory picker behavior

### Requirement: Pal Editor renders a readable dense workspace from the token palette

The Pal Editor SHALL render its populated workspace (party panel, pal box grid, toolbar, selected-pal inspector) with: no mojibake or retired-font glyph text (any icon comes from the bundled SVG set or clean text labels), no cyan and no hardcoded hex colors outside token-derived values in its chrome styling, passive skill chips on flat token surfaces with tier borders (no gradients), the selected pal's raw identifier available via tooltip rather than printed in the identity header, party-card HP text never overlapping the HP fill, and the bulk toolbar tiered into neutral utility, warning-tier bulk actions, and a distinct destructive action without orphan wrapping at minimum window width.

#### Scenario: Populated inspector is legible

- **WHEN** a player and a pal are selected in the Pal Editor
- **THEN** the inspector shows the pal identity (name, level, stars), labeled stat bars with readable values, active and passive skill sections, no corrupted glyph text, no cyan surfaces, and no raw GUID text in the identity header

#### Scenario: Toolbar tiers

- **WHEN** the Pal Editor bulk toolbar renders at 1200px window width
- **THEN** utility actions, bulk mutating actions, and the destructive bulk delete are visually distinct tiers on a single row without a wrapped orphan button

#### Scenario: Party HP readability

- **WHEN** the party panel shows a pal with HP values
- **THEN** the HP numbers are fully readable and do not overlap the HP bar fill

### Requirement: Standard table pages use noun titles, hygienic identifier columns, and differentiated member-precondition states

The Players, Guilds, and Bases pages SHALL present noun page titles (Players, Guilds, Bases — no "Search …" command phrasing in titles), SHALL render identifier columns (Player UID, Guild ID, Base ID) in a shortened display form with the full identifier available via tooltip, and the Guilds member detail pane SHALL differentiate its no-save state (load-save message) from its no-selection state (shared empty-state presentation naming the select-guild prerequisite). No raw full identifiers remain as visible column text.

#### Scenario: Players page with populated table

- **WHEN** a save is loaded and the Players page shows its table
- **THEN** the page title reads "Players", the UID column shows a shortened identifier with the full UID in the tooltip, and the search field label does not duplicate the title phrasing

#### Scenario: Guild members without selection

- **WHEN** a save is loaded but no guild is selected on the Guilds page
- **THEN** the member pane shows the shared empty-state presentation ("Select a guild…" with a hint) rather than a no-save message or plain text

#### Scenario: Bases identifiers

- **WHEN** the Bases page table is populated
- **THEN** Base ID and Guild ID columns show shortened identifiers with full values in tooltips

### Requirement: Pal Editor animation and painter colors derive from the token palette

All painter-drawn decorations in the Pal Editor (passive-skill overlay animations, badge borders, pens) SHALL derive their colors from the token palette (info tier replacing cyan, special tier for purple families); no hardcoded cyan-family RGB values MAY remain in editor painter code.

#### Scenario: Legendary passive overlay

- **WHEN** a passive skill card renders its legendary-tier overlay animation
- **THEN** the animated sweep and borders use token-derived colors with no cyan-family RGB values hardcoded in the painter

### Requirement: Map overlay chrome is token-styled and browser columns stay readable

The Map page overlay toolbar SHALL style its toggle buttons through the shared theme builder with an accent-based active state (no cyan, no hardcoded inline color stylesheets), the workspace header SHALL identify the page's World zone, and the map browser sidebar SHALL size its tree columns so no column header label truncates at the minimum window width.

#### Scenario: Active map toggle

- **WHEN** a map overlay toggle (bases, players, rings, zones, map type) is active
- **THEN** the button shows the accent-based checked styling from the theme builder with no cyan ring or hardcoded inline stylesheet

#### Scenario: Browser headers at minimum width

- **WHEN** the Map page renders at 1200px window width
- **THEN** the map browser tree column headers (Guild, Leader, Last Seen, Bases, Base Pals) display without truncation

### Requirement: Exclusions pages differentiate configured-empty from no-save states

The Exclusions page panels SHALL distinguish between the no-save condition (load-save message retained) and the loaded-but-empty condition (shared empty-state presentation: "No exclusions configured" with a hint directing users to the right-click exclusion menus on Players, Guilds, and Bases). The page SHALL NOT display "Load a save first" messaging while a save is loaded. All remaining hardcoded cyan in Map page chrome (calibration label, sidebar tab buttons, context menu borders) SHALL be token-derived.

#### Scenario: Save loaded, no exclusions

- **WHEN** a save is loaded and the selected exclusions list has no entries
- **THEN** the panel shows the shared empty-state presentation explaining the list is empty and where exclusions are added, not a load-save message

#### Scenario: No save loaded

- **WHEN** no save is loaded
- **THEN** the exclusions panels show the load-save guidance state

### Requirement: Breeding presents a single call-to-action and Docs uses the token palette

The Breeding page SHALL present exactly one "Select a Pal" call-to-action while no pal is selected (the shared empty-state's action); the standalone select button and hint label reappear only after a pal is selected (as the re-select affordance). The Docs page SHALL style its category/list/filter/sort/badge/card chrome entirely from the token palette with no cyan-family hardcoded values, and its filter group labels SHALL NOT truncate (multi-value groups render the label on its own row above the filter chips).

#### Scenario: Breeding pre-selection

- **WHEN** the Breeding page is shown with no pal selected
- **THEN** exactly one visible "Select a Pal" action exists (inside the empty state), with the standalone button and hint label hidden

#### Scenario: Docs filter group with many values

- **WHEN** the Docs page renders the Elements filter group
- **THEN** the "Element:" label is fully visible (own row above the chips) and no filter chip row clips the label

#### Scenario: Docs token compliance

- **WHEN** the Docs page renders lists, filters, sorts, badges, and detail cards
- **THEN** no cyan-family hardcoded color values remain in the wiki styling

### Requirement: Overview explains the loaded save and next actions
The system SHALL use Overview as the default workspace after loading a save and SHALL summarize save identity, platform, modification time, backup/safety state, unsaved state, key entity counts, recent activity, and direct quick actions. With no save, it SHALL instead present focused open/drop guidance, recent saves, and utilities that genuinely require no loaded save.

#### Scenario: Save loads successfully
- **WHEN** a save finishes loading
- **THEN** Overview answers what is loaded, whether it is safe, what it contains, whether it has pending changes, and which primary workflows can be opened next

### Requirement: Tool Center declares purpose, prerequisites, and risk
The system SHALL group all conversion, repair, recovery, transfer, injection, restore, and additional utilities by purpose. Each tool SHALL show a title, concise explanation, prerequisite state, risk level where relevant, and visible launch or prerequisite action, and SHALL report operation progress and result.

#### Scenario: Tool requires a loaded save
- **WHEN** a user views a tool whose declared requirements are not met
- **THEN** the card explains the missing requirement and offers a relevant action instead of appearing mysteriously disabled

### Requirement: World pages share entity browser and inspector behavior
Players, Bases, Guilds, and Exclusions SHALL prioritize names and meaningful metadata, use common search/filter/sort/table behavior, open structured detail inspectors, expose direct links to related entities and editors, and show bulk actions only when selection makes them applicable. Exclusions SHALL provide a persistent Add Exclusion action in addition to context-menu entry points.

#### Scenario: Player is selected
- **WHEN** the user selects a player row
- **THEN** the inspector shows structured identity, guild, activity, platform, technical details on demand, and direct Inventory, Pal Editor, and Guild actions

#### Scenario: Empty exclusions list
- **WHEN** a loaded save has no exclusions of the selected type
- **THEN** the page explains the empty state and offers Add Exclusion without requiring right-click discovery

### Requirement: Map is a first-class explorer workspace
The Map page SHALL devote the majority of the workspace to the map, provide a structured explorer and contextual inspector, offer understandable layers and filters, consolidate zoom and coordinate controls, and keep selected markers linked to their World entities. Controls SHALL be labeled or have tooltips and accessible names.

#### Scenario: User selects a map marker
- **WHEN** the user selects a player, base, or other supported marker
- **THEN** structured details and relevant entity actions appear without obscuring the primary map workspace

### Requirement: Inventory editors share context and grid primitives
Player Inventory and Base Inventory SHALL show explicit player or guild/base/container context, distinguish context selectors from inventory-category tabs, share inventory slot, quantity, rarity, selection, hover, preview, menu, search, filter, sort, and keyboard behavior, and provide meaningful empty/loading/unknown-structure states. Base containers SHALL be grouped with storage before dropped-item debris.

#### Scenario: User opens Base Inventory with one valid guild and base
- **WHEN** exactly one valid guild and base exist
- **THEN** the editor selects them automatically, exposes change-context controls, and presents available storage containers before debris containers

### Requirement: Pal Editor separates sources, collection, and details
The Pal Editor SHALL clearly separate player/source context, party and Palbox collection, and the selected-Pal inspector; support efficient box navigation at large counts; distinguish editable values from computed statistics; use consistent Pal presentation; and separate safe, bulk, and destructive actions. Bulk actions SHALL appear only with applicable selection and destructive flows SHALL provide affected counts and preview.

#### Scenario: User selects multiple Pals
- **WHEN** multi-selection becomes active
- **THEN** a contextual bulk action surface shows the selection count, applicable operations, preview where supported, and a clearly isolated destructive action

### Requirement: JSON Editor supports understandable tree and raw workflows
The JSON Editor SHALL provide a persistent clickable path breadcrumb, explicit search and match navigation, readable Key/Value/Type tree presentation, clear import/export/refresh actions, validation for edited content, and a raw JSON mode when safe editing support is available.

#### Scenario: User navigates a nested JSON value
- **WHEN** a nested row is selected
- **THEN** its full path is visible, ancestor segments are navigable, and editable content is validated before application

### Requirement: Reference and system workspaces use the same product model
Items, Pals, Skills, Technologies, breeding, world/internal data, Activity, Backups, Settings, About, and Diagnostics SHALL use the same shell, search, cards/tables, inspectors, states, and linking conventions as save-editing pages.

#### Scenario: User opens a referenced item
- **WHEN** an inventory item links to its reference record
- **THEN** the Reference workspace opens that item with related context and navigation history preserved

### Requirement: Every existing and future screen adopts the shared workspace system
No existing, hidden, experimental, save-gated, context-menu-only, or currently inaccessible screen SHALL retain legacy navigation, dialog, table, button, spacing, or state styling. New screens SHALL declare navigation placement, prerequisites, context, risk, loading, empty, error, and result behavior using the shared system.

#### Scenario: Previously inaccessible tool becomes available
- **WHEN** an underlying loading bug is resolved and the tool can open
- **THEN** it appears within the Tool Center and renders entirely with the new shell and shared components
