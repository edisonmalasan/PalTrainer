# ui-shell Delta

## Purpose

Placeholder — existing capability retains its purpose (application shell behavior). This delta replaces the right-rail shell with the top two-tier shell.

## RENAMED Requirements

- FROM: `### Requirement: Page ribbon presents title, zone, and actions without overlay collision`
- TO: `### Requirement: Page header presents title, zone, and actions without overlay collision`

## ADDED Requirements

### Requirement: Typography uses bundled real weights

The system SHALL render all primary UI typography (navigation, labels, headings, buttons, tables, dialogs, technical metadata) from the bundled Hanken Grotesk and Inter families using real bundled weights (Regular/Medium/SemiBold) rather than synthetic bold, and SHALL NOT reference the Hack Nerd Font family anywhere in the interface.

#### Scenario: No synthetic bold on primary text

- **WHEN** the application renders headings, navigation labels, or emphasized text
- **THEN** the rendered glyphs use bundled weight files, and no bundled font references target the Hack Nerd Font family

## MODIFIED Requirements

### Requirement: Page header presents title, zone, and actions without overlay collision

The system SHALL render each page's header row with a display title, a zone caption, and an action slot, such that header content never requires a reserved window-controls gutter (window controls live in the app bar), and page drag behavior only applies to the app bar, never to page content.

#### Scenario: Ribbon stays clear of window controls

- **WHEN** the main window is shown at minimum size (1200x750) or maximized
- **THEN** page header titles, zone captions, and action buttons span the full canvas width with no reserved dead gutter, and no content is clipped under window controls

#### Scenario: Page content does not drag the window

- **WHEN** the user presses and drags on a page header or any page content
- **THEN** no window move occurs; dragging is restricted to the app bar

### Requirement: Dark Deck-Ops theme applies consistently from one source

The system SHALL render all shell surfaces (app bar, nav strip, page headers, chips, status strip, tooltips, menus, scrollbars, and scroll-area viewports) from the frozen token palette (warm dark surfaces, amber `#F59E0B` accent, teal success) with no residual cyan (`#7DD3FC`) or blue (`#4a90e2`) shell chrome, and theme changes SHALL propagate without per-widget stylesheets overriding the global theme. Every rendered icon SHALL come from the bundled token-colored vector icon set; no glyph-font icon rendering MAY remain in shell surfaces.

#### Scenario: No parallel shell styling

- **WHEN** the application starts and any page is visited
- **THEN** app bar, nav strip, page headers, chips, status strip, menus, and tooltips share the same accent/surface treatment, and no shell widget carries an inline color stylesheet that diverges from the token palette

#### Scenario: Scroll containers never fall back to a light palette

- **WHEN** any page renders content inside a scroll area (including Breeding results)
- **THEN** the scroll viewport and inner containers use the dark token palette rather than a default light background

## REMOVED Requirements

### Requirement: Rail navigation reaches every page with a distinct identity

**Reason**: The right-edge 76px rail is replaced by the top nav strip and app bar; the rail's legibility problems (micro-labels, cramped zone captions) motivated this redesign.
**Migration**: Navigation IDs (`tools` … `docs`), signal contracts, and lazy page construction are preserved verbatim; the same destinations are now grouped in the top nav strip per the ui-nav capability's "Nav strip groups all 12 destinations" requirement.

### Requirement: Instrument tray reports save, selection, and metrics at a glance

**Reason**: The permanent right-side tray is removed; save state and the save action move to the app-bar save chip, selection moves to the context indicator and page headers, and metrics remain on the Tools field report with the statistics popover available on demand.
**Migration**: `ShellState` lifecycle, dirty signaling, save triggering, and selection update call sites keep their signatures and now feed the app bar surfaces.
