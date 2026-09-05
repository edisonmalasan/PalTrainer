# ui-nav Specification

## Purpose

Defines the top navigation behavior of PalTrainer's shell v3: the app bar (brand, save chip, context indicator, utilities, window controls, drag zone) and the nav strip (zone-grouped page destinations with full interaction states and keyboard reachability).

## Requirements

### Requirement: App bar presents brand, save state, context, and utilities

The system SHALL render a top app bar containing, in reading order: the application brand (circular logo mark plus "PalTrainer" wordmark), a save-state chip, a compact current-context indicator, utility buttons (console, tab guide, warnings, about), and the window minimize/maximize/close cluster. The app bar SHALL act as the frameless window's drag strip; interactive children within it SHALL never initiate a window drag.

#### Scenario: Brand is visible and consistent

- **WHEN** the main window is shown at minimum size (1200x750) or maximized
- **THEN** the logo mark and wordmark are fully visible at the app bar's left, and the brand is not clipped, overlapped, or scaled inconsistently

#### Scenario: Save chip reflects shell state

- **WHEN** the application transitions between no-save, loading, loaded, dirty, saving, and error shell states
- **THEN** the save chip shows the corresponding state text and icon (spinner while loading/saving), and clicking the chip triggers the existing save flow when a save is loaded

#### Scenario: Window controls live in the app bar

- **WHEN** the user clicks minimize, maximize/restore, or close in the app bar
- **THEN** the corresponding window action occurs without any page content being occluded by floating window controls

#### Scenario: App bar drags the frameless window

- **WHEN** the user presses and drags on the app bar's empty area
- **THEN** the window moves; **WHEN** the user presses on any interactive app-bar child
- **THEN** the child handles the press and no window move occurs

### Requirement: Context indicator summarizes current selection

The system SHALL display a compact current-context indicator (player, guild, or base selection and its save state summary) in the app bar, with full selection detail available on demand (popover or page headers) rather than in a permanently docked tray.

#### Scenario: Selection updates propagate

- **WHEN** the user selects a player, guild, or base on any page
- **THEN** the context indicator updates to show that selection, and no permanent right-side tray remains visible

#### Scenario: No selection placeholder

- **WHEN** no selection has been made or no save is loaded
- **THEN** the context indicator shows an explicit placeholder rather than stale text

### Requirement: Nav strip groups all 12 destinations into four zones

The system SHALL present all 12 page destinations in a top nav strip grouped into four labeled zones — Start (Tools), World (Map, Bases, Players, Guilds, Exclusions), Edit (Player Inventory, Base Inventory, Pal Editor, JSON Editor), Reference (Breeding, Docs) — with Exclusions directly visible as a first-class World destination and exactly one active destination at any time.

#### Scenario: All destinations reachable and distinct

- **WHEN** the user looks at the nav strip with no save loaded
- **THEN** all 12 destinations are visible (directly or via a documented overflow affordance at narrow widths), each with a distinct label, and Exclusions is directly visible under World

#### Scenario: Zone labels are user-facing

- **WHEN** any destination is shown
- **THEN** its zone group (Start / World / Edit / Reference) is identifiable from the nav strip, and the labels localize with the application language

### Requirement: Nav strip interaction states

The system SHALL provide distinct visual treatments for nav destinations: active (amber accent per the token palette), hover, pressed, keyboard focus, and no disabled destination state under normal operation (pages render empty states instead of disabling).

#### Scenario: Active destination indicated

- **WHEN** the user activates any destination via click or keyboard shortcut
- **THEN** the canvas shows the corresponding page and that destination alone shows the active treatment

#### Scenario: Narrow window overflow

- **WHEN** the window width cannot display all destination labels
- **THEN** the nav strip compacts labels first and then collapses least-recently-relevant zone groups into an overflow menu; every destination remains reachable

### Requirement: Keyboard shortcuts reach every destination

The system SHALL provide keyboard shortcuts for all 12 destinations, including Breeding and Docs, without conflicting with existing dialog shortcuts.

#### Scenario: Shortcut navigation

- **WHEN** the user presses the shortcut for any destination (existing Ctrl+1..0 retained for the current ten; new shortcuts for Breeding and Docs)
- **THEN** the shell activates that destination exactly as if clicked
