# ui-shell Specification

## Purpose

Defines the observable behavior of PalTrainer's right-rail application shell: navigation across the 12 pages, the per-page ribbon, the frameless window-controls overlay, the save/selection instrument tray, and application of the dark Deck-Ops theme.

## Requirements

### Requirement: Rail navigation reaches every page with a distinct identity

The system SHALL expose all 12 page destinations (tools, base_inventory, player_inventory, pal_editor, players, guilds, bases, map, exclusions, json_editor, breeding, docs) in the right rail, each with a visually distinct label and icon, grouped by mission zone, with exactly one active destination indicated at a time.

#### Scenario: User identifies each destination

- **WHEN** the user looks at the rail with no save loaded
- **THEN** Players, Guilds, and Bases are distinguishable from each other (no two nav items share the same visible label), Exclusions is fully legible, and the active page shows an active indicator

#### Scenario: Navigation preserves page identity

- **WHEN** the user activates any rail destination via click or its `Ctrl+1..0` shortcut
- **THEN** the canvas shows the corresponding page, the rail marks that destination active, and the same navigation ID is emitted that existing refresh/setup coupling expects

### Requirement: Page ribbon presents title, zone, and actions without overlay collision

The system SHALL render each page's ribbon with a display title, a zone caption, and an action slot, such that ribbon content never underlaps the floating window-controls cluster and drag-to-move still works on the ribbon's empty area but never on interactive controls.

#### Scenario: Ribbon stays clear of window controls

- **WHEN** the main window is shown at minimum size (1200x750) or maximized
- **THEN** ribbon titles, zone captions, and action buttons are fully visible and clickable, with no text clipped under the minimize/maximize/close cluster

### Requirement: Instrument tray reports save, selection, and metrics at a glance

The system SHALL show save state (no-save/loading/loaded/saving/error, dirty indicator), current PLAYER/GUILD/BASE selection, and players/guilds/bases/pals counts in the rail tray, with detailed statistics available in the tray drawer overlay.

#### Scenario: Tray reflects empty and loaded states

- **WHEN** no save is loaded
- **THEN** the tray reports "No save" state with zeroed metrics rather than blank or truncated micro-text
- **WHEN** a save finishes loading
- **THEN** the tray updates state, selection placeholders, and all four metrics without requiring a page switch

### Requirement: Dark Deck-Ops theme applies consistently from one source

The system SHALL render all shell surfaces (canvas, rail, ribbon, tray, tooltips, menus, scrollbars) from the frozen token palette (warm dark surfaces, amber `#F59E0B` accent, teal success) with no residual cyan (`#7DD3FC`) or blue (`#4a90e2`) shell chrome, and theme changes SHALL propagate without per-widget stylesheets overriding the global theme.

#### Scenario: No parallel shell styling

- **WHEN** the application starts and any page is visited
- **THEN** rail, ribbon, tray, menus, and tooltips share the same accent/surface treatment, and no shell widget carries an inline color stylesheet that diverges from the token palette
