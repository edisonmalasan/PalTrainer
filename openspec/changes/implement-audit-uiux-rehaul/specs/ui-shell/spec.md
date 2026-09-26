## MODIFIED Requirements

### Requirement: Page header presents title, zone, and actions without overlay collision
The system SHALL render each workspace with a consistent header containing page identity and description, current save and entity context, and page/global actions. Context SHALL remain understandable when the sidebar is collapsed, and page content SHALL never collide with window controls or participate in window dragging.

#### Scenario: Header remains usable at supported sizes
- **WHEN** the main window is shown at its 1024 by 700 minimum or maximized
- **THEN** the page title, save context, selected-entity context, pending-change state, and primary actions remain visible or available through an explicit overflow without clipping under window controls

#### Scenario: Ribbon stays clear of window controls
- **WHEN** the former ribbon is replaced by the workspace header at minimum size or maximized
- **THEN** header content spans its available region without a reserved dead gutter and remains clear of the dedicated window-control cluster

#### Scenario: Page content does not drag the window
- **WHEN** the user presses and drags on a workspace header, context bar, inspector, or page content
- **THEN** no window move occurs; dragging is restricted to a dedicated shell drag region

### Requirement: Dark Deck-Ops theme applies consistently from one source
The system SHALL render sidebar, workspace headers, context bars, content surfaces, inspectors, drawers, dialogs, menus, tooltips, scrollbars, inventory grids, and transient states from the centralized token palette. No page or hidden workflow MAY retain an inline legacy theme or glyph-font icon system.

#### Scenario: No parallel shell styling
- **WHEN** the application starts and every reachable page or workflow is visited
- **THEN** all surfaces share the same tokenized hierarchy and icon system without residual legacy navigation, tables, buttons, dialogs, or light fallback viewports

#### Scenario: Scroll containers never fall back to a light palette
- **WHEN** any page renders scrollable content
- **THEN** its viewport and inner containers use the active theme rather than the platform default palette

## ADDED Requirements

### Requirement: Workspace shell uses a persistent collapsible sidebar
The system SHALL compose the desktop around a persistent sidebar, workspace header, context or breadcrumb bar, primary content workspace, and contextual inspector or action drawer. Expanded and collapsed sidebar state SHALL persist, and the sidebar SHALL remain the stable navigation anchor on every page.

#### Scenario: User collapses the sidebar
- **WHEN** the user collapses the sidebar
- **THEN** destination icons, active location, tooltips, and save context remain available while labels are hidden and the preference is restored on restart

### Requirement: Native controls and application status remain distinct
The system SHALL visually and interactively separate minimize, maximize, and close controls from application warnings, help, save state, and page actions.

#### Scenario: Warning is present near window controls
- **WHEN** an application warning is active
- **THEN** it appears in the application header or status system and cannot be mistaken for an operating-system window action

## REMOVED Requirements

### Requirement: Typography uses bundled real weights
**Reason**: Typography is now governed application-wide by `ui-design-system` rather than as a shell-only contract.
**Migration**: Preserve bundled real weights while moving their normative ownership to the shared design-system capability.
