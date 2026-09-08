# PalTrainer UI/UX Rehaul Audit

**Document:** `audit.md`  
**Scope:** Complete visual, structural, interaction, and navigation redesign of the PalTrainer desktop application  
**Status:** UI/UX redesign specification  
**Primary Goal:** Replace the current interface with a substantially different, modern desktop application experience while preserving the existing functionality and data capabilities.

---

# 1. Purpose of This Audit

This document defines a complete UI/UX rehaul for PalTrainer based on the supplied screenshots.

The screenshots are being used only to understand:

- existing features;
- existing data;
- existing workflows;
- relationships between tools;
- application states;
- editor capabilities;
- current shortcomings.

The screenshots **must not be treated as a layout template**.

The redesigned application should not look like a polished version of the existing interface. It should feel like a new product built around the same functionality.

The redesign should substantially change:

- application shell;
- navigation architecture;
- hierarchy;
- spacing;
- screen composition;
- content density;
- tables;
- cards;
- editors;
- dialogs;
- selectors;
- tool discovery;
- context management;
- loading states;
- empty states;
- destructive-action handling;
- visual consistency.

The goal is a modern desktop save-management application that feels deliberate, reliable, powerful, and easy to understand.

---

# 2. Important Scope Requirement: Missing Screens

Some PalTrainer screens and tools are not included in the supplied screenshots because they currently require a loaded save and the application is experiencing a bug that prevents certain tools from being opened.

This redesign specification therefore applies to **all existing and future PalTrainer screens**, including screens that are not represented in the screenshot set.

This requirement is mandatory:

> Every existing tool, hidden tool, currently inaccessible tool, dialog, editor, utility, and future screen must use the exact same redesigned design system, application shell, navigation model, spacing rules, component library, interaction patterns, and visual language defined in this document.

Do not preserve the old design for screens that were not included in the screenshots.

Do not create a mixture where redesigned pages coexist with old-style dialogs or utility screens.

Any currently unavailable Tool-tab functionality should be migrated into this system when the underlying bug is resolved.

---

# 3. High-Level Assessment of the Current Interface

The current interface is functional and relatively information-dense, but it behaves more like a collection of individual utility panels than one cohesive application.

The largest issue is not color choice.

The largest issue is **information architecture**.

The application currently relies heavily on:

- multiple horizontal navigation rows;
- small top-level dropdown labels;
- dense borders;
- thin tab indicators;
- tables occupying extremely wide regions;
- detached inspector panels;
- modal windows for complicated workflows;
- very small labels;
- little distinction between primary and secondary actions;
- large amounts of visually empty space;
- inconsistent control placement;
- screens with radically different density levels;
- contextual selections displayed in a tiny title-bar status widget.

This results in an application that technically exposes many features but requires the user to learn where things are rather than allowing the interface to explain itself.

---

# 4. Core Redesign Direction

PalTrainer should become a **workspace-oriented desktop application**.

The mental model should be:

> Load a save → understand its state → navigate entities → inspect or modify data → review changes → save safely.

Instead of organizing the UI around menus first, organize it around the user's current save and editing context.

The redesign should use five major layers:

1. **Application sidebar**
2. **Workspace header**
3. **Context bar**
4. **Primary content workspace**
5. **Inspector / action drawer**

This structure should remain consistent throughout the application.

---

# 5. New Application Architecture

## 5.1 Desktop Shell

Replace the current multi-row horizontal navigation with a persistent vertical application sidebar.

Recommended desktop structure:

    ┌──────────────┬─────────────────────────────────────────────────────────────┐
    │              │ Workspace Header                                            │
    │              ├─────────────────────────────────────────────────────────────┤
    │ Sidebar      │ Context / Breadcrumb Bar                                    │
    │              ├─────────────────────────────────────────────────────────────┤
    │              │                                                             │
    │              │ Main Workspace                                              │
    │              │                                                             │
    │              │                                             Inspector        │
    │              │                                             when needed      │
    └──────────────┴─────────────────────────────────────────────────────────────┘

The sidebar should become the stable navigation anchor for the entire application.

---

# 6. Primary Navigation

## 6.1 Sidebar Structure

Recommended navigation:

### Workspace

- Overview

### World

- Map
- Bases
- Players
- Guilds
- Exclusions

### Editors

- Player Inventory
- Base Inventory
- Pal Editor
- JSON Editor

### Tools

- Conversion
- Save Management
- Character Transfer
- Slot Injector
- Host Repair
- Restore Map
- Other existing tools
- Any tools currently inaccessible because of the loading bug

### Reference

- Items
- Pals
- Skills
- Technologies
- World Data
- IDs / internal data as applicable

### System

- Activity
- Backups
- Settings
- About

The exact names can be adjusted based on the existing codebase, but the overall hierarchy should remain.

---

# 7. Sidebar Design

## 7.1 Dimensions

Expanded width:

- approximately `232–248px`

Collapsed width:

- approximately `64–72px`

The sidebar should be collapsible.

When collapsed:

- icons remain;
- labels disappear;
- tooltips appear on hover;
- currently active section remains obvious.

## 7.2 Hierarchy

Sidebar sections should use muted uppercase or small section labels.

Example:

    WORKSPACE
      Overview

    WORLD
      Map
      Bases
      Players
      Guilds
      Exclusions

    EDIT
      Player Inventory
      Base Inventory
      Pal Editor
      JSON Editor

    TOOLS
      Tool Center

Do not permanently expand dozens of utility links if that creates excessive height.

"Tools" can lead into a dedicated Tool Center containing grouped utilities.

---

# 8. Brand Treatment

The existing PalTrainer icon can remain.

The redesigned brand area should contain:

- PalTrainer logo;
- `PalTrainer` label;
- optional version beneath or in tooltip;
- collapsed sidebar mode showing logo only.

Avoid visually mixing product branding and save-selection status into the same narrow title strip.

---

# 9. Native Window Controls

The native/custom desktop window controls can remain in the upper-right corner.

However:

- application alerts should not be visually mixed with minimize/maximize/close;
- warning indicators should exist inside the application header;
- information/help should be accessible from the app menu or profile/settings area.

The current cluster of tiny icons near the Windows controls is visually ambiguous.

Separate application controls from OS/window controls.

---

# 10. Workspace Header

Every page should use one consistent workspace header.

Recommended height:

- `64–72px`

Contents:

### Left

- page icon;
- page title;
- optional short description.

### Center / contextual area

Context chips such as:

- current save;
- current player;
- current guild;
- current base.

### Right

- undo;
- redo;
- pending changes;
- save;
- command palette;
- additional page actions.

Example:

    Players                           Save: Local World 01
    Browse and manage players        Player: Hathaway

                                           Undo  Redo  Save Changes

The current approach of displaying:

    Selected Player: ...
    Selected Guild: ...
    Selected Base: ...

inside a tiny box in the top frame should be removed.

---

# 11. Global Save Context

Save state is fundamental to PalTrainer and deserves stronger treatment.

Create a dedicated **Save Context Control**.

When no save is loaded:

    No save loaded
    Open or drop a save to begin

    [ Open Save ] [ Recent Saves ▾ ]

When loaded:

    Local World
    Steam
    Last modified 2 min ago

    [ Change Save ]

The save selector should be accessible from every screen.

---

# 12. Unsaved Changes

The tiny orange dot currently visible near the loaded-save status is too ambiguous.

Replace it with an explicit change-management state.

Examples:

    ● 3 unsaved changes

or:

    Unsaved changes

Clicking the indicator should open a change summary.

Recommended states:

- `Saved`
- `Unsaved changes`
- `Saving…`
- `Save failed`
- `Read only`
- `Backup recommended`

A potentially destructive save editor must make state extremely clear.

---

# 13. Save Safety

Because PalTrainer edits game saves, the UI should reinforce confidence.

Before modifying important data:

- automatically create or offer a backup;
- indicate backup status;
- display pending edits;
- clearly differentiate destructive actions.

Recommended global save action:

    Save Changes

rather than silently writing data after every modification unless autosave is intentional and reliable.

If immediate writes are required internally, still provide visible confirmation.

---

# 14. Global Command Palette

Add:

`Ctrl + K`

or

`Ctrl + P`

for a command palette.

Examples:

    Open Player Inventory
    Search players
    Open Base Inventory
    Convert Save Files
    Go to Map
    Load Save
    Export JSON
    Create Backup

This is valuable for an advanced desktop utility containing many features.

---

# 15. Search Philosophy

Search currently appears in many screens as similar plain text inputs.

Create a standard SearchField component.

Features:

- search icon;
- clear button;
- shortcut hint when useful;
- result count;
- filtering controls next to search;
- responsive width.

Example:

    🔍 Search players by name, UID, or guild...                Filters (2)

Do not repeat awkward labels such as:

    Players  [ Type to search... ] [ 1 result ]

Use:

    [ Search players...                           ]  Filter  Sort
    1 player

---

# 16. Visual Style

The application can remain dark by default, but the dark design should become layered rather than nearly-black-on-nearly-black.

Recommended conceptual layers:

### Background

Deep neutral application background.

### Sidebar

Slightly lighter or darker than content background.

### Surface 1

Main panels.

### Surface 2

Cards / fields / rows.

### Elevated Surface

Dialogs, popovers, drawers.

### Borders

Subtle and low-contrast.

### Accent

Warm amber/gold can remain as the PalTrainer identity color.

The existing orange/yellow accent is recognizable and can be retained, but it should be used more selectively.

---

# 17. Accent Usage

Accent should indicate:

- current navigation item;
- focused control;
- selected entity;
- primary action;
- active tab;
- important state.

Do not outline every card and inventory item in bright yellow/orange.

Excessive colored borders reduce the meaning of selection.

---

# 18. Semantic Colors

Introduce separate semantic colors for:

- success;
- warning;
- destructive;
- information;
- rarity/category;
- disabled;
- active selection.

Do not use the primary brand amber for every semantic purpose.

Examples:

- Save loaded → success
- Unsaved changes → warning
- Delete Pal → destructive
- Informational status → blue/neutral
- Selected item → brand accent

---

# 19. Typography

The current interface contains many labels that are too small and tightly packed.

Recommended hierarchy:

### Page title

`22–24px`, medium/semi-bold.

### Section title

`16–18px`.

### Standard body

`13–14px`.

### Table content

`12–13px`.

### Metadata

`11–12px`.

### Tiny labels

Avoid anything smaller than approximately `11px` except rare technical annotations.

Use a modern UI font such as:

- Inter;
- Geist;
- Segoe UI;
- system UI stack.

If the application uses Windows-native styling, Segoe UI remains an excellent option.

---

# 20. Spacing System

Use a consistent spacing scale.

Recommended:

- 4px
- 8px
- 12px
- 16px
- 20px
- 24px
- 32px
- 40px

Avoid arbitrary differences between adjacent sections.

Primary content padding:

- `24px` desktop;
- `20px` medium;
- `16px` narrow.

---

# 21. Border Radius

Suggested:

- Buttons: `6–8px`
- Inputs: `6–8px`
- Cards: `8–10px`
- Large panels/dialogs: `10–12px`

Avoid excessive rounding.

PalTrainer is a desktop utility, not a mobile banking app.

---

# 22. Borders and Separators

The current UI is heavily segmented using thin rectangles.

Reduce box-within-box composition.

Prefer:

- spacing;
- surface differences;
- typography;
- selective separators.

Use borders where they communicate boundaries rather than outlining everything.

---

# 23. Buttons

Define clear button levels.

## Primary

Used for one dominant action:

    Save Changes
    Apply Changes
    Assign to Guild

## Secondary

    Export JSON
    Loadout
    Sort

## Tertiary

Text/icon actions:

    Clear
    Refresh

## Destructive

    Delete Pal
    Remove Item
    Clear Inventory

Do not allow destructive actions to visually resemble normal actions.

---

# 24. Iconography

Use one icon family throughout the application.

Avoid mixing icon styles.

Good candidates:

- Lucide;
- Phosphor;
- Radix Icons;
- Fluent.

Icons should supplement text rather than replace it for important operations.

---

# 25. Tooltips

Use tooltips for:

- icon-only controls;
- truncated IDs;
- stats;
- rarity icons;
- internal fields;
- map controls.

Tooltips should appear after a short delay.

---

# 26. Global Breadcrumb / Context Bar

Complex editors should expose navigation context.

Example:

    World / Players / Hathaway / Inventory

or:

    Unnamed Guild / Base 1 / Inventory

This is more understandable than spreading selected player/guild/base information across unrelated components.

Breadcrumbs should be clickable where meaningful.

---

# 27. Overview Screen

Create a new **Overview** page as the default workspace after loading a save.

This should not be the current Tools page renamed.

The Overview page should answer:

- what save is loaded?
- is it safe?
- how many players?
- how many guilds?
- how many bases?
- when was it modified?
- are there unsaved changes?
- what can I do next?

Example structure:

    Overview

    World: Local World
    Steam Save • Last modified 4 min ago
    Backup: Available

    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Players 1  │ │ Guilds 1   │ │ Bases 1    │ │ Pals 220   │
    └────────────┘ └────────────┘ └────────────┘ └────────────┘

    Quick Actions
    Player Inventory
    Pal Editor
    Base Inventory
    Map Viewer

    Recent Activity
    ...

This provides a much better starting point than opening directly into a list of conversion utilities.

---

# 28. No-Save State

The current no-save Tools screen still exposes most of the full application structure.

Replace it with a focused onboarding state.

Suggested layout:

    Welcome to PalTrainer

    Load a Palworld save to inspect your world, players,
    bases, inventory, pals, and save data.

    [ Open Save File ]
    [ Open Save Folder ]

    Drop a save anywhere in this window

    Recent Saves
    ─────────────────────
    Local World 1
    Dedicated Server
    ...

Secondary section:

    Utilities that don't require a loaded save

This improves clarity significantly.

---

# 29. Tool Center Redesign

The existing Tools page separates Conversion Tools and Management Tools into plain rectangular rows.

Replace this with a dedicated **Tool Center**.

The Tool Center should group tasks conceptually.

Suggested categories:

### Save & Format

- Convert Save Files
- GamePass ↔ Steam
- Steam ID Conversion

### Repair & Recovery

- Fix Host Save
- Restore Map

### Transfer & Injection

- Character Transfer
- Slot Injector

### Additional Tools

- any currently inaccessible tools;
- future tools.

Each tool card should contain:

- icon;
- title;
- one-sentence explanation;
- requirement indicator;
- optional risk badge;
- launch affordance.

Example:

    Character Transfer
    Move character data between saves or servers.

    Requires loaded save                         Open →

Do not make the whole app look like a collection of border-only menu rows.

---

# 30. Tool Availability

Disabled tools should explain why.

Bad:

    [ Character Transfer ]  disabled

Better:

    Character Transfer
    Requires a loaded save.

    [ Load a Save ]

Never force users to guess why something cannot be clicked.

---

# 31. Activity System

The current Tools page contains a huge empty `Activity` rectangle.

Replace it with a useful activity system.

Activity should show real operations:

    23:41  Save loaded
    23:42  Backup created
    23:43  Added 10 Ancient Civilization Parts
    23:44  Player inventory saved

Each row can include:

- timestamp;
- operation;
- entity;
- status;
- undo if supported.

If no activity exists:

    No activity yet
    Changes and utility operations will appear here.

Do not dedicate half the screen to an empty border.

---

# 32. World Navigation

The current secondary navigation:

    Map Viewer | Bases | Players | Guilds | Exclusions

should no longer be a horizontal row under another top row.

These destinations belong permanently in the sidebar under `World`.

This dramatically reduces stacked navigation.

---

# 33. Map Viewer Rehaul

The current map screen is one of the most visually unique parts of PalTrainer and should become a first-class workspace.

The map should occupy almost the entire available workspace.

Recommended layout:

    ┌──────────────────────────────────────────────────────────────┐
    │ Search world…   Layers   Filters                   Reset View │
    ├───────────────┬──────────────────────────────┬───────────────┤
    │ Explorer      │                              │ Inspector     │
    │               │                              │               │
    │ Bases         │           MAP                │ Selected      │
    │ Players       │                              │ marker        │
    │ Guilds        │                              │ details       │
    │               │                              │               │
    └───────────────┴──────────────────────────────┴───────────────┘

The left explorer should be collapsible.

The right inspector should only open when something is selected.

The map itself should otherwise remain large and immersive.

---

# 34. Map Explorer

Replace the current floating `Map Browser` box with a docked, collapsible explorer.

Features:

- unified search;
- entity tabs or filters;
- grouped results;
- visible counts;
- keyboard navigation.

Example:

    Search world...

    Show
    ☑ Bases        1
    ☑ Players      1
    ☑ Guilds       1

    Results

    Base 1
    Unnamed Guild
    Hathaway

Clicking a result should:

- center map;
- select marker;
- open inspector.

---

# 35. Map Layer Controls

The existing icon-only buttons across the upper-right side of the map are difficult to understand.

Replace them with a clear layer control.

Example:

    Layers
    ☑ Bases
    ☑ Players
    ☑ Guilds
    ☑ Fast Travel
    ☑ Respawn
    ☑ Custom markers

Or use a popover triggered by:

    Layers

Individual high-frequency toggles can remain icon-based if tooltips are clear.

---

# 36. Map Zoom and Coordinates

Put map telemetry in a compact bottom overlay:

    X -1681   Y 1032        Zoom 100%

Controls:

    −  100%  +

Do not scatter map status between opposite corners.

---

# 37. Map Empty / No-Data States

If no save is loaded:

    Load a save to display world entities.

The background map may remain visible if useful as reference.

If world data fails:

    World data could not be loaded.
    Retry / View Error Details

---

# 38. Shared Entity Browser Pattern

The following screens should share one interaction pattern:

- Players
- Guilds
- Bases
- Exclusions where applicable
- Reference lists

Use a reusable `EntityBrowser`.

Structure:

    Page Header

    Toolbar
    [ Search ................................ ] [ Filters ] [ Sort ] [ Columns ]

    ┌───────────────────────────────────────────────┬────────────────────┐
    │ Data table                                    │ Inspector          │
    │                                               │                    │
    │                                               │                    │
    └───────────────────────────────────────────────┴────────────────────┘

The inspector should be:

- resizable;
- collapsible;
- approximately `320–380px`;
- context-aware.

This retains the benefits of the current master/detail approach but makes it structured and consistent.

---

# 39. Players Screen

Current issues:

- much empty space;
- bulk-action buttons float between table and empty area;
- row selection is not visually sophisticated;
- inspector typography is sparse;
- UUIDs dominate horizontal space;
- table columns are tightly packed.

Redesign:

### Header

    Players
    1 player in this save

### Toolbar

    Search players...       Guild: All     Level: Any       More Filters

### Table columns

Recommended defaults:

- Player
- Level
- Last Seen
- Guild
- Pals
- Role
- Actions

Hide full IDs from the default table.

Internal IDs belong in:

- inspector;
- copy action;
- optional columns.

### Row example

    Hathaway
    Level 70     Online / 0s ago     Unnamed Guild     220 Pals

Clicking opens inspector.

Double-clicking or `Enter` can open the player's editor.

---

# 40. Player Inspector

The right panel should contain grouped sections.

Example:

    Hathaway
    Level 70

    Status
    Last Seen      Just now
    Pals           220

    Guild
    Unnamed Guild
    Guild Master

    IDs
    Player UID
    00000000-...
    [ Copy ]

    Guild ID
    09a38db2-...
    [ Copy ]

    Actions
    [ Open Inventory ]
    [ Open Pal Editor ]
    [ Change Guild ]

Do not show metadata as scattered label/value pairs across a very tall empty panel.

---

# 41. Player Bulk Actions

The current buttons:

- Bulk Item Management
- Bulk Pal Management
- Bulk Technology Management
- Guild Assignments

should become a contextual bulk-action bar.

When no players are selected:

    Select players to enable bulk actions.

When rows are selected:

    3 players selected
    [ Items ] [ Pals ] [ Technology ] [ Guild ] [ More ▾ ]

The bar can appear above the table or as a bottom floating selection toolbar.

This is cleaner and scales better.

---

# 42. Bases Screen

Use the shared entity-browser pattern.

Default columns:

- Base
- Guild
- Guild Level
- Workers / Pals
- Location if available
- Actions

Avoid showing the raw Base ID as the first and most prominent column.

The user cares about `Base 1` more than:

    707e7dcc...

The ID belongs in secondary metadata.

---

# 43. Base Inspector

Suggested:

    Base 1

    Guild
    Unnamed Guild
    Level 1

    Base Pals
    0 / capacity

    Base ID
    707e7dcc-...
    [ Copy ]

    Guild ID
    09a38db2-...
    [ Copy ]

    Actions
    [ Open Inventory ]
    [ Show on Map ]
    [ View Guild ]

---

# 44. Guilds Screen

The current guild page divides the content between:

- guild table;
- guild-member table;
- right inspector.

This creates unnecessary complexity.

Use one main guild list.

Selecting a guild opens its inspector.

Inspector sections:

    Unnamed Guild
    Level 1

    Members
    1 member

    Hathaway
    Lv. 70 • Guild Master

    Base
    Base 1

    IDs
    ...

    Actions
    [ Manage Members ]
    [ View Bases ]
    [ Show on Map ]

If a user needs detailed guild membership management, open a focused guild details page or drawer.

Do not permanently dedicate half the main page to the members table.

---

# 45. Guild Assignment Rehaul

The current Guild Assignment modal contains two large tables and another table below the right side.

Replace it with a guided transfer workflow.

Suggested dialog or full-screen sheet:

    Assign Players to Guild

    Step 1
    Select players

    ☑ Hathaway
       Lv. 70 • Unnamed Guild • Guild Master

    Step 2
    Choose destination guild

    Search guilds...

    ○ Unnamed Guild
      Level 1 • 1 member

    Step 3
    Review

    Moving 1 player
    From: Unnamed Guild
    To: Example Guild

    [ Cancel ] [ Assign Player ]

If changing the Guild Master has special consequences, explicitly warn the user.

---

# 46. Exclusions Screen

The current screen has nested tabs:

- Excluded Player UIDs
- Excluded Guild IDs
- Excluded Base IDs

and a large empty region.

Reframe this as an **Exclusion Rules** page.

Header:

    Exclusions
    Manage entities ignored by PalTrainer operations.

Toolbar:

    [ Add Exclusion ]

Filter chips:

    All
    Players
    Guilds
    Bases

Table:

    Type       Entity / ID             Added           Actions
    Guild      09a38...                Today           Remove

Empty state:

    No exclusions
    Excluded players, guilds, and bases will appear here.

    [ Add Exclusion ]

The current instruction:

    Use the right-click menu on Guilds to exclude entries.

is undiscoverable.

Right-click can remain as a shortcut, but adding exclusions must also have an obvious normal UI.

---

# 47. Editor Navigation

Current editor navigation:

    Player Inventory | Base Inventory | Pal Editor | JSON Editor

is currently a horizontal sub-navigation beneath the general top navigation.

Move these into the sidebar under `Editors`.

Inside editors, use breadcrumbs and context selectors rather than another permanent horizontal nav.

---

# 48. Player Inventory Editor Rehaul

The current screen contains:

- player selector;
- multiple inventory categories;
- large inventory grid;
- equipment column;
- several toolbar buttons;
- many colors;
- very dense information.

This functionality is powerful but needs stronger hierarchy.

Recommended structure:

    Player Inventory

    Hathaway • Level 70
    [ Change Player ]

    ┌───────────────────────────────────────┬──────────────────────────┐
    │ Inventory                            │ Character Loadout        │
    │                                       │                          │
    │ Tabs                                  │ Equipment                │
    │ Items  Key Items  Technology ...      │                          │
    │                                       │ Weapon                   │
    │ Search / Sort / Filter                │ Accessories              │
    │                                       │ Armor                    │
    │ Inventory grid                        │ Food                     │
    │                                       │                          │
    └───────────────────────────────────────┴──────────────────────────┘

The equipment panel can remain on the right, but should be a purpose-built loadout panel rather than a long narrow strip of small boxes.

---

# 49. Player Selection

The current player dropdown expands into a large blank menu when only one player exists.

Use a searchable entity picker.

Collapsed:

    Hathaway
    Level 70

Click:

    Select player
    [ Search players... ]

    Hathaway
    Level 70 • Unnamed Guild

If there is only one player, the picker should remain compact.

---

# 50. Inventory Category Navigation

Use clear internal tabs:

- Inventory
- Key Items
- Technology
- Missions
- Paldeck
- other existing categories.

Tabs should be placed inside the editor content, not visually blend with the global navigation.

Active tab should use:

- stronger text;
- clear accent;
- optional subtle surface.

Avoid relying exclusively on a 2px orange underline.

---

# 51. Inventory Toolbar

Recommended:

    Search inventory...      Category: All      Rarity: All      Sort ▾

    48 / 100 slots

    [ Add Item ] [ Manage Slots ] [ Loadouts ] [ More ▾ ]

`Unlock All Fast Travel` does not naturally belong beside inventory sort controls.

Move feature-specific actions into:

- appropriate category;
- overflow menu;
- separate utility panel.

---

# 52. Inventory Grid

Inventory cards should be redesigned around readability.

Each slot:

- consistent aspect ratio;
- item icon centered;
- quantity badge top-right;
- rarity indicated using a thin edge, badge, or icon rather than a bright full border;
- item name limited to one or two lines;
- selected slot gets unmistakable highlight.

Example:

    ┌────────────────┐
    │           ×80  │
    │                │
    │      ICON      │
    │                │
    │ Lamball Mutton │
    └────────────────┘

Use virtualization for large inventories.

---

# 53. Inventory Empty Slots

Empty inventory slots should remain visible because slot count matters, but they should be understated.

Empty cells should not visually compete with occupied cells.

---

# 54. Item Selection

Selecting an item should open an item-detail drawer or side panel.

Suggested:

    Ancient Civilization Parts

    Quantity
    [ 15 ]

    Rarity
    Rare

    Internal ID
    ...

    [ Update ]
    [ Remove ]

Do not rely solely on actions at the bottom of a huge bulk-management modal.

---

# 55. Equipment Panel

The current narrow equipment panel contains:

- W1–W6;
- accessories;
- head;
- body;
- shield;
- glider;
- modules;
- food.

Replace the code-like abbreviations as the primary labels.

Use actual sections:

    Weapons
    [ slot ] [ slot ] [ slot ] [ slot ]

    Armor
    Head
    Body
    Shield

    Accessories
    [ slot ] [ slot ] [ slot ] [ slot ]

    Food
    ...

Internal abbreviations can appear in tooltips for advanced users.

---

# 56. Loadouts

Make loadouts a first-class interaction.

Suggested:

    Loadout: Default ▾

    [ Save Loadout ]
    [ Apply Loadout ]
    [ Manage ]

Do not put a generic `Loadouts` button without explaining whether it saves, loads, or manages loadouts.

---

# 57. Base Inventory Editor

The existing base inventory screen currently has:

- guild selector;
- base selector;
- tabs;
- container list;
- massive slot grid;
- loading overlay;
- structures toggle.

Redesign into a three-panel resource workspace.

Recommended:

    Base Inventory
    Unnamed Guild / Base 1

    ┌──────────────────────┬─────────────────────────────┬───────────────┐
    │ Containers           │ Inventory                   │ Item Detail   │
    │                      │                             │               │
    │ Search               │ Search / sort / filter      │ selected item │
    │                      │                             │               │
    │ Workbench            │ slot grid                   │               │
    │ Guild Chest          │                             │               │
    │ Dropped Items        │                             │               │
    └──────────────────────┴─────────────────────────────┴───────────────┘

Left panel:

`260–300px`

Right detail panel:

`300–340px`, optional/collapsible.

---

# 58. Base Container Cards

Existing container cards use large blocks and multiple orange borders.

Use compact rows:

    Workbench
    0 / 6 slots                               ›

    Guild Chest
    14 / 54 slots                             ›

    Dropped Items
    1 slot                                    ›

Unknown/missing icons should use one consistent placeholder.

Do not display large mystery-image blocks unless the image itself provides value.

---

# 59. Base Inventory Tabs

Top-level context:

    Unnamed Guild › Base 1

Then editor tabs:

    Inventory
    Base Pals

Avoid placing guild selector, base selector, and tabs in one flat row where they look equivalent.

Guild/base are context.

Inventory/Base Pals are content modes.

They should look different.

---

# 60. Replace Structures

`Replace Structures` appears as an isolated action.

This should be moved into a menu such as:

    Base Actions ▾
      Replace Structures
      Clear Containers
      Export Inventory
      ...

If it is dangerous, it must require confirmation.

---

# 61. Base Inventory Loading State

The supplied screenshot shows a full-screen dark overlay with:

    UPDATING WORKER CONTRACTS (NOW WITH 0% BREAK TIME)...

This loading treatment is playful but visually blocks the entire application.

Retain personality without sacrificing usability.

Recommended:

    Updating base inventory
    Processing worker data…

    █████████░░░░ 64%

    [ Cancel ] if cancellation is technically safe

Use a compact modal or center progress panel with a semi-transparent backdrop.

If progress percentage is unknown, use an indeterminate progress bar.

Do not fabricate percentage progress if the application does not know actual progress.

Fun rotating loading messages are fine as secondary text.

Example:

    Updating base inventory
    "Negotiating worker contracts…"

The actual task description must remain visible.

---

# 62. Base Pals

The current Base Pals screen shows a mostly empty grid and `No Pal Data`.

Use a proper empty state.

    No working Pals assigned to this base

    Working Pals will appear here when the base contains
    assigned Pal workers.

    [ Open Pal Editor ]

If no data is expected because of save parsing, distinguish that from zero Pals.

Examples:

- `No workers assigned`
- `Base Pal data unavailable`
- `Unable to parse worker data`

These are different states.

---

# 63. Pal Editor Rehaul

The Pal Editor is one of the most complex screens and should feel like a professional entity editor.

Current structure:

- party column;
- box number;
- huge Pal grid;
- many tiny actions;
- dense right stats panel;
- tooltip floating over center;
- small controls;
- large number of repeated cards.

Redesign around:

1. Pal source navigator;
2. Pal collection grid;
3. Pal detail inspector.

Recommended:

    Pal Editor
    Hathaway

    ┌─────────────────┬──────────────────────────────────┬────────────────────┐
    │ Sources         │ Pal Collection                   │ Pal Details        │
    │                 │                                  │                    │
    │ Party           │ Box 1 / 218                      │ Jetragon           │
    │ Palbox          │ Search / Filter / Sort           │ Level 80           │
    │ Base Pals       │                                  │                    │
    │                 │ [ Pal cards ... ]                │ stats              │
    │                 │                                  │ skills             │
    └─────────────────┴──────────────────────────────────┴────────────────────┘

---

# 64. Pal Sources

Left panel:

    Party
      Panthalus
      Azurobe

    Palbox
      Box 1
      Box 2
      Box 3
      ...

    Bases
      Base 1

Allow collapsing groups.

Do not fill the entire Party column with empty slots when only two party Pals exist unless party-slot positioning is functionally important.

If slot positions matter, show six fixed slots compactly.

---

# 65. Palbox Navigation

Current:

    Box 1 (218)   [1 spinner]  <  >

Replace with:

    Box 1 of 218            ‹  ›
    [ Jump to box… ]

Optional:

    Ctrl + ← / Ctrl + →

Keyboard navigation matters when 218 boxes exist.

---

# 66. Pal Grid

Each Pal card should expose essential information only:

- species portrait;
- name or optional shortened label;
- level;
- rarity/status icons;
- selected state.

Do not overload each cell with many tiny corner icons unless every icon is essential.

Secondary information belongs in tooltip or inspector.

---

# 67. Pal Hover

Hover card:

    Jetragon
    Level 80
    Legendary • Alpha

    Flying mount
    Missile launcher while mounted

This should use the redesigned tooltip/popover system.

---

# 68. Pal Detail Inspector

The right inspector is currently extremely dense.

Break it into sections with optional scrolling.

Header:

    Jetragon
    Moon Lord Mount

    Level 80
    Male
    Legendary

Primary stats:

    HP         18,979 / 18,979
    Attack     3,175
    Defense    2,793
    Stamina    100
    Work Speed 157

Condensed base stats:

    IV / talent / rank information

Then:

    Active Skills
    Meteoraine        700
    Beam Comet        700
    Holy Burst        700

    Passive Skills
    Legend
    Swift
    Eternal Engine
    Dimensional Leap

Use clear cards or sections.

Avoid dozens of tiny decorative boxes.

---

# 69. Pal Editor Actions

Current actions include:

- Restore All
- Max All
- Feed Food
- All Skills
- Sort
- Select All
- Bulk Clone Pals
- Bulk Delete Pals

Reorganize.

Toolbar:

    Search Pals...
    Species
    Level
    Passive Skill
    Sort

Then:

    [ Edit Selected ]

Overflow:

    Bulk Actions ▾
      Restore Health
      Max Stats
      Feed
      Add Skills
      Clone
      Delete

Destructive actions should not sit beside ordinary actions with nearly identical styling.

---

# 70. Bulk Selection

When multiple Pals are selected:

    12 Pals selected

    [ Modify Stats ]
    [ Add Skills ]
    [ Move ]
    [ Clone ]
    [ Delete ]

This selection toolbar should appear contextually.

---

# 71. Bulk Player Item Management

The current bulk item-management dialog tries to perform too many unrelated functions in one modal:

- inventory items;
- key items;
- player selection;
- abilities;
- add/remove.

Instead create a dedicated **Bulk Player Editor**.

It can be modal-like but should preferably be a full workspace or large sheet.

Recommended workflow:

    Bulk Player Editor

    Players: 1 selected
    Hathaway

    [ Items ] [ Abilities ] [ Technology ]

For Items:

    Search items...

    Filters
    Inventory | Key Items

    item grid

    Selected Item
    Ancient Core

    Quantity
    [ 100 ]

    Apply to
    ☑ Hathaway

    [ Add Item ]

This is clearer than placing player selection inside another tab.

---

# 72. Bulk Ability Editing

Current `Edit Abilities` UI contains Chinese/Japanese/raw source labels such as:

- 捕獲率
- 空腹率低減
- etc.

The redesigned UI should show localized user-facing names first.

Example:

    Capture Power
    Internal: CapturePower

    Hunger Reduction
    Internal: HungerReduction

Raw/internal labels may appear as secondary metadata.

If localization data is unavailable, fallback gracefully:

    Capture Power
    CapturePower

Do not expose mixed-language development labels as the primary interface unless the user selected that language.

---

# 73. Ability Editor

Suggested structure:

    Player Abilities

    Apply to:
    ☑ Hathaway (Lv. 70)

    Search abilities...

    Ability                       Current       New
    Capture Power                 101           [100]
    Hunger Reduction              10            [10]
    Swim Speed                    10            [10]
    Food Decay Reduction          10            [10]

    [ Reset Changes ]                     [ Apply Changes ]

Use a table/form rather than a tiny scroll region inside a large blank dialog.

---

# 74. Bulk Pal Management

Current screen contains:

- Delete Pal;
- Remove Skills.

These are two unrelated destructive workflows.

Split them into contextual operations.

Bulk Pal Management can provide:

    Bulk Pal Actions

    Delete Pals
    Remove Skills
    Move Pals
    Edit Attributes
    ...

Each launches an appropriately focused interface.

---

# 75. Delete Pal Workflow

Current screen presents hundreds of Pals immediately.

Recommended:

    Delete Pals

    Search...
    Type: All       Category: All

    □ Jetragon
    □ Anubis
    □ Azurobe
    ...

    0 selected

    [ Cancel ] [ Delete Selected ]

When selected:

    Delete 3 selected Pals?

    This removes the selected Pals from the save.

    [ Cancel ]
    [ Delete 3 Pals ]

If deletion applies "everywhere", explicitly state which collections are affected.

---

# 76. Remove Skills Workflow

Current interface:

- select active skill;
- select passive skill;
- check player pals/base pals/DPS pals;
- remove.

The logic is strong, but hierarchy should improve.

Recommended:

    Remove Skills in Bulk

    Skills

    Active Skill
    [ Select active skill... ]

    Passive Skill
    [ Select passive skill... ]

    Scope

    ☑ Party and Palbox
      Pals owned by players

    ☑ Base Pals
      Pals assigned to bases

    ☑ DPS Pals
      Pals stored in DPS save data

    Summary
    Remove selected skills from all matching Pals.

    [ Preview Matches ]

After preview:

    147 Pals affected

    [ Cancel ] [ Remove Skills from 147 Pals ]

Preview is strongly recommended for destructive bulk changes.

---

# 77. JSON Editor Rehaul

The JSON Editor should feel like a developer tool rather than a table dropped into the application.

Current issues:

- tree and values are visually compressed;
- search controls are ambiguous;
- types are shown but hierarchy is weak;
- bottom actions are separated from the content;
- raw keys dominate.

Recommended layout:

    JSON Editor

    [ Search JSON...                           ]     Expand   Collapse

    ┌──────────────────────────────────────────────────────────────┐
    │ Tree / Structured JSON                                      │
    │                                                              │
    │ ▾ root                                                       │
    │   ▾ header                         object                     │
    │       magic                        1396790855       number    │
    │       save_game_version            3                number    │
    │   ▸ properties                     object                     │
    │   trailer                          "AAAAAA=="       string    │
    └──────────────────────────────────────────────────────────────┘

    Source: Loaded save

                           [ Export ] [ Import ] [ Apply Changes ]

---

# 78. JSON Editor Modes

Consider two modes:

    Tree
    Raw JSON

Tree mode:

- safe browsing;
- editable cells where supported;
- type awareness;
- expand/collapse.

Raw mode:

- monospace editor;
- syntax highlighting;
- line numbers;
- validation;
- formatting.

If raw editing can corrupt saves, include warning and validation.

---

# 79. JSON Search

Search results should display matching path.

Example:

    4 matches

    properties.worldSaveData...
    header.custom_versions...

Keyboard:

- Enter → next;
- Shift+Enter → previous;
- Esc → clear.

---

# 80. Reference Area

The top menu currently contains `Reference`.

Make Reference a real workspace.

Potential sections:

- Item Database
- Pal Database
- Skill Database
- Technology
- Internal IDs
- Save Schema

Reference pages can use card/table browsers and serve as read-only data explorers.

Allow deep links from editors:

    View Jetragon in Reference

This can reduce tooltips overloaded with reference information.

---

# 81. Contextual Navigation

The redesigned app should make entities linkable.

Examples:

From Player Inspector:

    View Guild
    Open Inventory
    Open Palbox

From Guild Inspector:

    View Members
    View Base
    Show on Map

From Base Inspector:

    Open Inventory
    View Workers
    Show on Map

From Pal Inspector:

    Open Pal Reference
    Show Owner
    View Skills

This turns PalTrainer into an interconnected workspace rather than disconnected screens.

---

# 82. Dialog Philosophy

Use dialogs only for:

- confirmation;
- small forms;
- short workflows;
- irreversible actions.

Do not place entire applications inside dialogs.

The current Bulk Item Management, Bulk Pal Management, and Guild Assignment dialogs are complex enough to be workspaces or full-size sheets.

Recommended sizes:

### Small

400–480px

### Medium

560–720px

### Large

800–960px

### Complex workflow

Full workspace / full-height sheet.

---

# 83. Drawers

Use right-side drawers for context editing.

Examples:

- item details;
- player details;
- guild details;
- base details;
- selected Pal quick edits.

Drawers preserve the user's current location better than modal windows.

---

# 84. Confirmation Dialogs

Destructive actions should contain:

- exact action;
- exact affected count;
- consequences;
- irreversible warning when applicable;
- destructive button labeled with the actual action.

Bad:

    Are you sure?
    [ Yes ]

Good:

    Delete 12 Pals?

    These Pals will be removed from the current save.
    This action cannot be undone after saving.

    [ Cancel ]
    [ Delete 12 Pals ]

---

# 85. Undo

Where technically possible, implement an in-session undo stack.

Useful for:

- inventory quantity edits;
- adding/removing items;
- assignments;
- Pal modifications;
- bulk property changes.

Global header:

    Undo
    Redo

Pending changes should not be permanently committed until the user saves, if architecture permits.

---

# 86. Change Review

Strongly recommended:

    4 unsaved changes

Click:

    Pending Changes

    Hathaway
    Inventory
    + Ancient Civilization Parts ×10

    Jetragon
    Passive Skill
    Swift → Legend

    Base 1
    Inventory
    Removed item ...

    [ Discard All ] [ Save Changes ]

This is especially valuable for save editing.

---

# 87. Autosave Policy

Do not silently autosave destructive modifications unless the existing architecture requires it.

Preferred approach:

1. modify in-memory save;
2. mark state dirty;
3. allow user review;
4. explicitly save;
5. create backup;
6. report success.

If implementation limitations make this impossible, visually communicate when changes are immediately written.

---

# 88. Status Feedback

Use toast notifications for minor successful actions.

Examples:

    Item added to Hathaway
    Copied Player UID
    Backup created

Use inline errors for field-specific problems.

Use persistent banners for major save issues.

Do not use modal dialogs for routine success messages.

---

# 89. Error States

Errors should explain:

- what failed;
- which entity was affected;
- whether data was changed;
- how to recover.

Example:

    Could not update Base 1 inventory

    The save was not modified.
    Error: Container mapping could not be resolved.

    [ Retry ]
    [ Copy Error Details ]

Technical error details can be expandable.

---

# 90. Save Corruption Protection

For potentially unsafe operations:

    Backup created
    23:41 • backup_2026-09-08_2341.sav

Before large operations:

    This operation will modify 214 entities.
    A backup will be created automatically.

This significantly increases user trust.

---

# 91. Loading States

Avoid blocking the entire application unless absolutely necessary.

Use three levels.

## Local Skeleton

For tables/cards.

## Section Loading

For inventory/panel.

## Blocking Processing

Only for operations where navigation or editing would cause corruption.

Blocking screen should contain:

- exact operation;
- progress if available;
- clear status;
- cancel if safe.

---

# 92. Skeleton Design

Inventory skeleton:

    ▧ ▧ ▧ ▧ ▧
    ▧ ▧ ▧ ▧ ▧

Table skeleton:

    ─────────────────────
    ─────────────────────
    ─────────────────────

Do not use spinning indicators alone for large datasets.

---

# 93. Empty States

Every empty state should explain why the area is empty.

Examples:

### No Save

    No save loaded
    Load a save to access world data.

### No Players

    No players found in this save.

### No Search Results

    No players match "Jetragon".
    Clear filters

### Empty Container

    Workbench is empty
    0 of 6 slots used

### No Exclusions

    No exclusions configured.

### No Base Pals

    No Pals are currently assigned to this base.

---

# 94. Right-Click Menus

Right-click menus are appropriate for a desktop utility and should remain available as accelerators.

But important functionality must never exist exclusively in a context menu.

Example table context menu:

    Open
    Copy ID
    Show on Map
    Open Inventory
    ─────────────
    Add to Exclusions

Every essential action should also be accessible through normal UI.

---

# 95. Tables

Create one reusable DataTable component.

Features:

- sortable headers;
- optional resizable columns;
- keyboard navigation;
- selection;
- row context menu;
- sticky header;
- column visibility;
- truncation tooltips;
- virtualization;
- empty state;
- filter state;
- optional saved column preferences.

---

# 96. Table Density

Offer:

    Density
    Comfortable
    Compact

Default to `Comfortable`.

Advanced users can select compact mode.

Do not design the entire application permanently at maximum density.

---

# 97. Technical IDs

Long GUIDs/UIDs should not dominate the main interface.

Display:

    09a38db2…d84f94

Hover:

    09a38db2-4c43-59a1-8d8b-a99ea4d84f94

Adjacent action:

    Copy

Inspector can show the full ID.

---

# 98. Entity Names

Prioritize meaningful names.

Examples:

    Hathaway
    Unnamed Guild
    Base 1
    Jetragon

Identifiers are secondary metadata.

The current Bases screen leads with a truncated Base ID; this should be reversed.

---

# 99. Selection Behavior

Use consistent selection states.

Single selection:

- surface highlight;
- thin accent edge;
- optional check indicator.

Multi-select:

- checkbox;
- selection toolbar.

Hover should never look identical to selected.

---

# 100. Context Persistence

When the user chooses:

- Player: Hathaway
- Guild: Unnamed Guild
- Base: Base 1

the application should remember these selections while navigating related pages when appropriate.

Example:

    Players → Hathaway → Player Inventory

should automatically open Hathaway.

Similarly:

    Bases → Base 1 → Base Inventory

should automatically open Base 1.

This significantly reduces repeated selector usage.

---

# 101. Navigation History

Back/forward navigation should work.

Examples:

    Player → Guild → Base → Inventory

User should be able to go back through the entity chain.

If the desktop framework permits:

- `Alt + Left`
- `Alt + Right`

---

# 102. Keyboard Accessibility

Recommended shortcuts:

    Ctrl + O        Open save
    Ctrl + S        Save changes
    Ctrl + Shift+S  Save As / alternate export if applicable
    Ctrl + K        Command palette
    Ctrl + F        Search current page
    Ctrl + Z        Undo
    Ctrl + Y        Redo
    Esc             Close drawer/dialog
    Enter           Open selected entity
    Delete          Context-aware delete with confirmation

Shortcuts should appear in menus and tooltips.

---

# 103. Focus States

Every interactive control must have a visible keyboard focus indicator.

Do not rely solely on subtle border-color changes.

---

# 104. Accessibility

Minimum requirements:

- WCAG AA text contrast where practical;
- visible focus;
- accessible names for icon buttons;
- keyboard navigation;
- screen-reader labels;
- semantic headings;
- dialogs trap focus;
- tooltip information available without hover;
- rarity/status not represented by color alone.

---

# 105. Rarity and Category Colors

The inventory and Pal interfaces currently use many border colors.

Retain rarity colors where they communicate game data, but pair them with:

- rarity icon;
- rarity label;
- patterned indicator;
- tooltip.

Selected state should remain independent from rarity.

Example:

    Epic
    purple rarity dot

while a selected Epic item gets the standard PalTrainer selection ring.

---

# 106. Responsive Desktop Behavior

PalTrainer appears primarily intended for desktop.

Recommended breakpoints:

### ≥ 1440px

Full sidebar + inspector.

### 1100–1439px

Sidebar can collapse;
inspector narrower.

### 900–1099px

Inspector becomes overlay drawer.

### <900px

Support is optional, but layouts should not catastrophically break.

Avoid designing for only the exact screenshot dimensions.

---

# 107. Resizable Panels

Recommended resizable regions:

- map explorer;
- entity inspector;
- Base Inventory container list;
- Pal Editor source panel;
- JSON tree/value columns.

Persist user sizes locally.

---

# 108. Scroll Behavior

Each major workspace should have deliberate scroll ownership.

Avoid pages where:

- body scroll;
- nested panel scroll;
- modal scroll;
- table scroll

all happen simultaneously without clarity.

Preferred:

- app shell fixed;
- workspace owns primary scroll;
- large data grids scroll internally;
- inspector can scroll independently.

---

# 109. Sticky Toolbars

For large editors:

- search/filter toolbar should remain visible;
- save state should remain visible;
- bulk selection toolbar should remain visible.

Inventory users should not have to scroll back to the top to apply actions.

---

# 110. Information Density

Use progressive disclosure.

First layer:

- important user-facing information.

Second layer:

- advanced properties.

Third layer:

- IDs/internal data.

For example:

    Hathaway
    Level 70
    Guild Master

Then expandable:

    Technical Details
      Player UID
      Save container ID
      internal mappings

The current interface puts technical IDs next to normal player information too aggressively.

---

# 111. Advanced Mode

Consider an optional:

    Settings → Interface → Show advanced save data

When disabled:

- raw IDs reduced;
- internal names hidden;
- experimental fields hidden.

When enabled:

- internal identifiers;
- engine names;
- property keys;
- additional diagnostics.

This serves both normal players and power users.

---

# 112. Menus

Replace the current:

    Tools
    World ▼
    Edit ▼
    Reference ▼

navigation-dependent menu structure.

Navigation belongs in the sidebar.

A traditional desktop menubar may remain for commands:

    File
    Edit
    View
    Tools
    Help

Example:

### File

- Open Save
- Recent Saves
- Create Backup
- Export
- Exit

### Edit

- Undo
- Redo
- Find

### View

- Toggle Sidebar
- Toggle Inspector
- Density
- Reset Layout

### Tools

- Command Palette
- Tool Center

### Help

- Documentation
- Report Issue
- About

This separates commands from navigation.

---

# 113. Recent Saves

Add a Recent Saves experience.

Example:

    Recent Saves

    Local World 1
    Steam
    Modified 18 min ago

    Dedicated Server
    Steam
    Modified yesterday

Actions:

- Open;
- Reveal in Explorer;
- Remove from recent list.

---

# 114. Steam / GamePass Selector

The current Tools page includes a large:

    Steam | GamePass

toggle near the save status.

This is ambiguous.

If it represents the source platform of the loaded save, it should be part of Save Context.

Example:

    Platform
    Steam

If it configures a conversion operation, it belongs inside the conversion tool.

Do not show a platform toggle globally unless changing it globally has a clear effect.

---

# 115. Home / Overview Before Save

When no save exists, Overview should still be useful.

Suggested:

    PalTrainer

    Open a Palworld save

    [ Open Save ]
    [ Open Folder ]

    Recent Saves

    Standalone Tools
    Convert Save
    Steam ↔ GamePass
    Steam ID Converter

This allows conversion tools that do not require a loaded save to remain accessible.

---

# 116. Player Inventory Workflow Example

Target workflow:

1. Load save.
2. Click `Players`.
3. Select Hathaway.
4. Click `Open Inventory`.
5. Player Inventory automatically loads Hathaway.
6. Search for an item.
7. Select item.
8. Change quantity.
9. UI displays `1 unsaved change`.
10. Save.
11. Backup is created.
12. Toast confirms success.

The redesigned interface should optimize this type of sequence.

---

# 117. Base Workflow Example

1. Open `Bases`.
2. Select Base 1.
3. Inspector shows base summary.
4. Click `Open Inventory`.
5. Base Inventory opens in context of:
   `Unnamed Guild / Base 1`.
6. Select `Guild Chest`.
7. Edit items.
8. Save changes.
9. Return to Base 1 using breadcrumb/back navigation.

No repeated guild/base selection should be required.

---

# 118. Pal Workflow Example

1. Open Player `Hathaway`.
2. Click `Open Pal Editor`.
3. Pal Editor opens with Hathaway selected.
4. Choose Jetragon.
5. Pal details open in inspector.
6. Modify passive skill.
7. Pending change appears.
8. Select additional Pals if bulk editing.
9. Review changes.
10. Save.

---

# 119. JSON Workflow Example

1. Open JSON Editor.
2. Search `save_game_version`.
3. Matching node auto-expands.
4. User can copy JSON path.
5. Edit supported value.
6. Validation runs.
7. Pending changes shown.
8. Save or export JSON.

---

# 120. Tool Workflow Example

For Convert Save Files:

    Convert Save

    Source
    [ Choose file ]

    Detected
    Steam Save

    Convert to
    ○ JSON
    ○ SAV

    Destination
    ...

    [ Convert ]

    Conversion complete
    [ Open Folder ]

Each utility should have a focused UI instead of a generic card opening another generic dialog.

---

# 121. Component Library

Implement a shared UI component system.

Minimum reusable components:

- `AppShell`
- `Sidebar`
- `SidebarItem`
- `WorkspaceHeader`
- `SaveContext`
- `Breadcrumbs`
- `CommandPalette`
- `SearchField`
- `FilterMenu`
- `DataTable`
- `EntityInspector`
- `Drawer`
- `Dialog`
- `ConfirmationDialog`
- `Button`
- `IconButton`
- `SegmentedControl`
- `Tabs`
- `Input`
- `NumberInput`
- `Select`
- `EntityPicker`
- `Badge`
- `StatusBadge`
- `Card`
- `StatCard`
- `EmptyState`
- `LoadingState`
- `ProgressPanel`
- `Toast`
- `Tooltip`
- `ContextMenu`
- `InventoryGrid`
- `InventorySlot`
- `PalCard`
- `EntityID`
- `BulkActionBar`
- `ChangeIndicator`

No page should invent its own visual version of these controls.

---

# 122. Design Tokens

Use centralized design tokens.

Example token categories:

    colors.background
    colors.surface
    colors.surfaceRaised
    colors.border
    colors.textPrimary
    colors.textSecondary
    colors.textMuted
    colors.accent
    colors.success
    colors.warning
    colors.danger
    colors.info

    spacing.1
    spacing.2
    spacing.3
    ...

    radius.sm
    radius.md
    radius.lg

    typography.body
    typography.caption
    typography.heading

    shadow.popover
    shadow.dialog

Do not define arbitrary hex colors per component.

---

# 123. Example Dark Theme Structure

Conceptual values only:

    App Background          #0f1012
    Sidebar                 #121316
    Surface                 #17181c
    Elevated Surface        #1d1f23
    Hover                   #24262b
    Border                  #2c2f35

    Primary Text            #f4f4f5
    Secondary Text          #b7b8bd
    Muted Text              #7f828a

    PalTrainer Accent       warm amber/gold
    Success                 muted emerald
    Warning                 amber
    Danger                  red
    Info                    blue

Exact values should be verified for contrast.

---

# 124. Light Theme

Architect the design tokens so a light theme can eventually exist even if dark mode remains the initial default.

Do not hard-code components around dark-mode assumptions.

---

# 125. Motion

Use subtle motion only.

Recommended:

- drawer: `160–220ms`;
- tooltip: quick fade;
- sidebar collapse: `180–220ms`;
- selection: short color transition;
- dialogs: subtle scale/fade.

Avoid ornamental animation during save editing.

---

# 126. Loading Personality

The humorous loading message shown in the supplied screenshot can remain as a PalTrainer personality element.

However:

Primary:

    Updating Base Inventory

Secondary/fun:

    Negotiating worker contracts…

Progress:

    Processing 12 / 18 containers

The joke must never replace meaningful status.

---

# 127. Tool-Specific Consistency Requirement

Every tool currently inaccessible due to the user's loaded-save bug must be implemented using:

- same sidebar;
- same header;
- same save context;
- same dialogs;
- same button hierarchy;
- same inputs;
- same typography;
- same spacing;
- same warning system;
- same activity reporting;
- same pending-change system.

No exceptions should be made merely because a tool was absent from the screenshots.

---

# 128. Current Screenshot Coverage

The supplied screenshots reveal at least the following existing UI areas:

- Tools with no save loaded;
- Tools with save loaded;
- Map Viewer;
- Bases;
- Players;
- Bulk Player Item Management;
- Bulk Player Ability editing;
- Bulk Pal deletion;
- Bulk Pal skill removal;
- Guild Assignment;
- Guilds;
- Exclusions;
- Player Inventory Editor;
- Base Inventory loading state;
- Base Inventory Editor;
- Base Pals;
- Pal Editor;
- JSON Editor.

The redesign must also cover every screen not listed here.

---

# 129. Current UI Strengths Worth Preserving

Although the visual structure should be replaced, several functional ideas are worth retaining.

### Dense power-user capability

PalTrainer exposes many advanced operations without unnecessary wizard flows.

Keep this power.

### Dark theme

Appropriate for a game utility and long editing sessions.

Keep dark mode as default.

### Amber identity

The yellow/orange highlight is recognizable.

Keep it as the brand accent.

### Master/detail workflows

Tables paired with inspectors make sense for Players, Bases, and Guilds.

Keep the pattern, but standardize and modernize it.

### Grid-based inventory

Inventory naturally maps to slot grids.

Keep the concept.

### Pal grid

A visual Pal collection is appropriate.

Keep it.

### Map-centric world browser

Keep the map as an immersive workspace.

### Technical JSON access

Power users benefit from this.

Keep JSON editing, but improve safety and ergonomics.

---

# 130. Current UI Patterns That Should Not Be Preserved

Do not preserve:

- two or three stacked horizontal navigation rows;
- tiny top navigation dropdowns;
- giant empty bordered boxes;
- nearly every area being outlined;
- widespread use of very small uppercase text;
- IDs as primary labels;
- unclear icon-only controls;
- full application workflows inside modal windows;
- primary and destructive buttons sharing styling;
- bulk-action buttons floating in otherwise empty layouts;
- overly narrow inspector panels;
- tiny status boxes in the title bar;
- inconsistent tab placement;
- toolbar actions unrelated to the current context;
- deeply nested scroll regions;
- large blank table areas without meaningful empty states;
- invisible functionality dependent on right-click;
- loading screens without clear task information.

---

# 131. Proposed Page Hierarchy

Recommended route hierarchy:

    /overview

    /world/map
    /world/bases
    /world/bases/:baseId
    /world/players
    /world/players/:playerId
    /world/guilds
    /world/guilds/:guildId
    /world/exclusions

    /edit/player-inventory
    /edit/base-inventory
    /edit/pals
    /edit/json

    /tools
    /tools/convert-save
    /tools/platform-conversion
    /tools/steam-id
    /tools/slot-injector
    /tools/character-transfer
    /tools/fix-host
    /tools/restore-map
    /tools/...

    /reference/items
    /reference/pals
    /reference/skills
    /reference/technology

    /activity
    /backups
    /settings

The exact routing technology can differ.

The conceptual hierarchy should remain.

---

# 132. Sidebar Example

    PalTrainer

    WORKSPACE
    ◉ Overview

    WORLD
    ◈ Map
    ▣ Bases
    ◉ Players
    ◇ Guilds
    ⊘ Exclusions

    EDITORS
    ▤ Player Inventory
    ▥ Base Inventory
    ◌ Pal Editor
    { } JSON Editor

    TOOLS
    ◇ Tool Center

    REFERENCE
    ⌕ Reference

    ─────────────────────

    Save
    ● Local World
      Steam

    ⚙ Settings

This is only a structural illustration, not a literal visual requirement.

---

# 133. Workspace Header Example

    Players
    Browse and manage players in this save.

    Local World  /  1 Player

                                  2 unsaved changes
                                  Undo   Redo   Save Changes

When there are no changes:

    Saved

Do not permanently display disabled Save buttons without explanation.

---

# 134. Overview Wireframe

    ┌──────────────────────────────────────────────────────────────┐
    │ Overview                                                     │
    │ Local World • Steam                                          │
    ├──────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Players        Guilds          Bases          Pals           │
    │  1              1               1              220            │
    │                                                              │
    │  Quick Actions                                               │
    │  ┌────────────────────┐ ┌────────────────────┐                │
    │  │ Player Inventory   │ │ Pal Editor         │                │
    │  └────────────────────┘ └────────────────────┘                │
    │  ┌────────────────────┐ ┌────────────────────┐                │
    │  │ Base Inventory     │ │ Map               │                │
    │  └────────────────────┘ └────────────────────┘                │
    │                                                              │
    │  Recent Activity                                              │
    │  Save loaded                                                  │
    │  Backup created                                               │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

---

# 135. Players Wireframe

    ┌──────────────────────────────────────────────────────────────────────┐
    │ Players                                                              │
    │ 1 player                                                             │
    ├──────────────────────────────────────────────────────────────────────┤
    │ Search players...             Filters        Columns                 │
    ├──────────────────────────────────────────────┬───────────────────────┤
    │ Player       Level     Guild       Pals      │ Hathaway              │
    │                                              │ Level 70              │
    │ Hathaway     70        Unnamed     220       │                       │
    │                                              │ Unnamed Guild         │
    │                                              │ Guild Master          │
    │                                              │                       │
    │                                              │ [Open Inventory]      │
    │                                              │ [Open Pal Editor]     │
    │                                              │ [Change Guild]        │
    └──────────────────────────────────────────────┴───────────────────────┘

---

# 136. Base Inventory Wireframe

    ┌──────────────────────────────────────────────────────────────────────┐
    │ Base Inventory                                                       │
    │ Unnamed Guild / Base 1                                               │
    ├──────────────────────────────────────────────────────────────────────┤
    │ Inventory       Base Pals                                            │
    ├────────────────────┬─────────────────────────────────────────────────┤
    │ Containers         │ Search items...       Sort      Filter          │
    │                    │                                                 │
    │ Workbench          │ [ ][ ][ ][ ][ ][ ]                              │
    │ 0 / 6              │ [ ][ ][ ][ ][ ][ ]                              │
    │                    │ [ ][ ][ ][ ][ ][ ]                              │
    │ Guild Chest        │                                                 │
    │ 0 / 54             │                                                 │
    │                    │                                                 │
    │ Dropped Items      │                                                 │
    └────────────────────┴─────────────────────────────────────────────────┘

---

# 137. Pal Editor Wireframe

    ┌─────────────────────────────────────────────────────────────────────────┐
    │ Pal Editor • Hathaway                                                   │
    ├───────────────┬────────────────────────────────────┬────────────────────┤
    │ Sources       │ Search Pals...      Filter         │ Jetragon           │
    │               │                                    │ Level 80           │
    │ Party         │ Box 1 of 218       ‹  ›            │                    │
    │ Panthalus     │                                    │ HP 18,979          │
    │ Azurobe       │ [Pal][Pal][Pal][Pal][Pal]          │ ATK 3,175          │
    │               │ [Pal][Pal][Pal][Pal][Pal]          │ DEF 2,793          │
    │ Palbox        │ [Pal][Pal][Pal][Pal][Pal]          │                    │
    │ Box 1         │                                    │ Active Skills      │
    │ Box 2         │                                    │ Meteoraine         │
    │ ...           │                                    │ Beam Comet         │
    │               │                                    │ Holy Burst         │
    │               │                                    │                    │
    │               │                                    │ Passive Skills     │
    │               │                                    │ Legend             │
    │               │                                    │ Swift              │
    └───────────────┴────────────────────────────────────┴────────────────────┘

---

# 138. Map Wireframe

    ┌─────────────────────────────────────────────────────────────────────────┐
    │ Map                                      Layers   Filters   Reset        │
    ├───────────────────┬─────────────────────────────────────────┬───────────┤
    │ Search world...   │                                         │ Selected  │
    │                   │                                         │ Entity    │
    │ ☑ Bases           │                                         │           │
    │ ☑ Players         │                 WORLD MAP               │ Base 1    │
    │ ☑ Guilds          │                                         │           │
    │                   │                                         │ Guild     │
    │ Base 1            │                                         │ Unnamed   │
    │ Hathaway          │                                         │           │
    │ Unnamed Guild     │                                         │ Open →    │
    ├───────────────────┴─────────────────────────────────────────┴───────────┤
    │ X -1681  Y 1032                                         Zoom 100%       │
    └─────────────────────────────────────────────────────────────────────────┘

---

# 139. Density and Empty Space

The redesign should not attempt to fill every pixel.

However, empty space should be intentional.

Good empty space:

- between sections;
- around headers;
- around inspectors;
- inside empty states.

Bad empty space:

- half a page occupied by an empty table body while important actions float randomly above it;
- huge blank activity boxes;
- tall side panels containing only four metadata values.

Use responsive sizing so content adapts to available data.

---

# 140. Inspector Width

Recommended default:

- `340px`

Minimum:

- `300px`

Maximum:

- `480px`

Allow manual resizing.

Collapse:

- keyboard shortcut;
- inspector icon.

---

# 141. Sidebar State Persistence

Remember:

- expanded/collapsed;
- expanded section groups;
- width if resizable;
- last destination.

---

# 142. Editor State Persistence

Remember locally where useful:

- table sort;
- column widths;
- active inventory category;
- last Pal box;
- panel sizes;
- grid density;
- map zoom/layer preferences.

Do not persist dangerous unsaved edits across application restarts unless explicitly supported.

---

# 143. Search Persistence

Do not permanently preserve transient search queries when navigating unrelated pages.

Do preserve:

- filters on return during the same session;
- selected entity where contextually appropriate.

---

# 144. Context Chips

If context is displayed in the header, use readable chips.

Example:

    Save
    Local World

    Player
    Hathaway

Do not show:

    Selected Player: [L]Hatha...
    Selected Guild: Unname...
    Selected Base: 707e7dcc...

That is too technical and compressed.

---

# 145. IDs and Copying

Use a consistent ID component.

Example:

    Player UID
    00000000…0001      Copy

Clicking the shortened ID can expand.

Copy gives toast:

    Player UID copied

---

# 146. Platform Information

Represent save platform with a small badge:

    STEAM

or:

    GAME PASS

Do not visually treat platform as the most important global control unless it truly changes behavior globally.

---

# 147. Data Counts

Counts should use natural labels:

    1 Player
    1 Guild
    1 Base
    220 Pals

Pluralize properly.

---

# 148. Last Seen

Use human-friendly relative time.

Example:

    Just now
    14 min ago
    Yesterday

Tooltip:

    Sep 8, 2026, 11:32 PM

---

# 149. Filter System

For large datasets use chips.

Example:

    Filters:
    Guild: Unnamed Guild ×
    Level: 70+ ×

    Clear all

Filters should not require opening multiple hidden dropdowns to understand active state.

---

# 150. Sorting

Sorting should work through:

- table headers;
- explicit Sort menu in grids.

Pal grid sort options could include:

- level;
- name;
- species;
- rarity;
- recently modified.

---

# 151. Bulk Actions Across the App

Use one shared pattern.

When items/entities are selected:

    7 selected

    [ Edit ]
    [ Move ]
    [ Export ]
    [ More ▾ ]

    [ Clear selection ]

Destructive actions go under `More` or remain clearly separated in red.

---

# 152. Context Menus

Use context menus consistently.

Inventory item:

    Edit Quantity
    Move
    Duplicate
    View Reference
    ─────────
    Remove Item

Pal:

    Edit
    Move
    Clone
    View Reference
    ─────────
    Delete

Player:

    Open
    Inventory
    Pal Editor
    Copy UID
    ─────────
    Add to Exclusions

---

# 153. Tooltip Timing

Recommended:

- simple icon tooltip: 300–500 ms;
- complex item preview: 500–700 ms.

Avoid immediately opening large hover cards while users move across grids.

---

# 154. Item Preview

Large inventory grids benefit from hover previews.

Example:

    Ancient Civilization Parts
    Rare Material

    Quantity: 15

    Used to craft advanced technology.

    Internal ID
    AncientParts

This should not obscure large portions of the inventory unnecessarily.

---

# 155. Pal Preview

Pal preview should summarize:

- Pal;
- level;
- rank;
- main traits;
- selected passive skills.

Detailed editing remains in the inspector.

---

# 156. Performance

Large grids and tables should use virtualization.

Especially:

- inventory;
- Palbox;
- reference databases;
- JSON tree;
- large save entities.

The rehaul must not regress performance in exchange for visual polish.

---

# 157. Lazy Loading

Load expensive data only when needed.

Examples:

- detailed Pal metadata when inspector opens;
- reference images on visible grid cards;
- large JSON children when expanded where technically possible.

---

# 158. Image Handling

Pal and item images should:

- maintain consistent bounds;
- use object-fit;
- reserve space before loading;
- show skeleton;
- gracefully fallback to an icon.

Do not show broken images.

---

# 159. Unknown Assets

Current Base Inventory uses question-mark imagery for unknown containers.

Use a standardized placeholder:

    Unknown Container

    Container type could not be identified.

rather than presenting a mysterious icon without explanation.

---

# 160. Destructive Mode

For tools involving widespread deletion or skill removal, consider a clearly differentiated destructive workspace.

Use a subtle red semantic accent but do not turn the entire screen red.

Example:

    Delete Pals

    This tool permanently removes selected Pal records.

This immediately communicates risk.

---

# 161. Preview Before Bulk Modification

Bulk operations should provide:

    Preview Changes

where technically feasible.

Examples:

- Remove skill from 147 Pals;
- Assign 8 players to another guild;
- delete 20 Pals;
- inject save slot;
- replace structures;
- fix host UID.

Preview substantially improves trust.

---

# 162. Backup Integration

For dangerous tools:

    Backup
    ☑ Create backup before applying

Default checked.

If a backup cannot be created:

    Backup failed.
    Continue without backup?

This should require explicit confirmation.

---

# 163. Tool Risk Levels

Tool cards can optionally display:

    Safe
    Modifies Save
    Advanced
    Destructive

Examples:

    Convert SteamID
    Utility

    Fix Host Save
    Advanced • Modifies Save

    Bulk Delete Pals
    Destructive

This helps users understand consequences.

---

# 164. Activity Logging

Every save mutation should ideally produce an activity event.

Suggested schema:

    time
    tool
    action
    target
    summary
    result
    backup
    reversible

Example:

    23:44
    Player Inventory
    Updated Hathaway
    Ancient Civilization Parts: 5 → 15
    Saved successfully

---

# 165. Activity Detail

Clicking an activity entry could reveal:

    Operation
    Player Inventory Update

    Target
    Hathaway

    Changes
    Ancient Civilization Parts
    5 → 15

    Save
    Local World

    Backup
    backup_2026...

This would make PalTrainer much easier to trust.

---

# 166. Settings

Create a real Settings screen.

Potential categories:

### General

- startup behavior;
- recent-save behavior;
- confirmation preferences.

### Appearance

- theme;
- UI density;
- sidebar behavior.

### Save Safety

- automatic backup;
- backup retention;
- save confirmation.

### Advanced

- show internal IDs;
- JSON editing;
- diagnostic logging.

---

# 167. About / Diagnostics

Because PalTrainer manipulates save formats, diagnostics are valuable.

Include:

- app version;
- detected Palworld save version;
- parser version;
- current platform;
- save location;
- log location;
- copy diagnostic info.

---

# 168. Reference to Save Path

The current Tools page displays the full file path directly.

Instead:

    Save Location
    C:\Users\ediso\...\SaveGames\...

    [ Copy Path ] [ Open Folder ]

Truncate visually while retaining full tooltip.

---

# 169. Warning Indicator

The current yellow warning icon near the window controls is unexplained.

Replace with an application-level Issues indicator.

Example:

    ⚠ 1 issue

Click:

    Save Issue
    Base container mapping could not be resolved.

Or if no issue:

do not display a warning icon.

---

# 170. Information Icon

Move general app information/help into:

- Help menu;
- Settings;
- context help.

Do not use unlabeled icons in the title bar for critical navigation.

---

# 171. Feedback on Current Visual Density

Current PalTrainer frequently combines:

- 11px text;
- thin borders;
- dark surfaces;
- tiny buttons;
- truncated strings;
- many horizontal lines.

The redesign should increase perceived clarity without wasting space.

The target should resemble a modern development/database desktop tool rather than a web dashboard squeezed into a desktop window.

Appropriate references in spirit include:

- modern IDE sidebars;
- database administration tools;
- game mod managers;
- professional asset editors;
- modern Electron desktop software.

Do not directly clone any particular product.

---

# 172. Desired Product Personality

PalTrainer should feel:

- technical;
- capable;
- safe;
- fast;
- game-aware;
- slightly playful;
- not childish;
- not enterprise-corporate;
- not overly decorative.

The game content and Pal imagery already provide personality.

The application chrome should remain restrained.

---

# 173. Avoid Excessive Glassmorphism

Do not redesign the application around:

- blurred translucent panels;
- glowing gradients;
- neon borders;
- glass cards everywhere.

These effects would interfere with dense save-management workflows.

Use clear surfaces and strong hierarchy.

---

# 174. Avoid Dashboard Card Overuse

Cards are useful for:

- Overview;
- Tool Center;
- summaries.

Cards should not replace tables, grids, or editors where those patterns are more efficient.

---

# 175. Avoid Over-Rounding

Do not turn everything into pill-shaped UI.

Small/medium radii are enough.

Pills are appropriate for:

- status;
- filters;
- tags.

---

# 176. Avoid Excessive Uppercase

The current interface frequently uses small uppercase labels.

Use title case for most visible labels.

Uppercase can remain for tiny section headers if contrast and tracking are appropriate.

---

# 177. Menu Naming

Prefer clear names:

    Tools
    World
    Editors
    Reference

Within pages:

    Player Inventory
    Base Inventory
    Pal Editor

Do not abbreviate unless terminology is widely understood.

---

# 178. Terminology Consistency

Choose one term and use it everywhere.

Examples:

Use either:

    Base Pals

or:

    Working Pals

with one canonical concept and optional description.

Use either:

    Guild Assignment

or:

    Change Guild

depending on operation.

Avoid different names for identical workflows across screens.

---

# 179. Tooltip Terminology

Technical values may include internal names:

    Capture Power
    Internal property: CapturePower

This maintains debugging utility without harming readability.

---

# 180. Localization

The supplied ability screen shows mixed-language names.

All user-facing labels should go through localization.

Fallback order:

1. current locale;
2. English user-facing name;
3. cleaned internal identifier;
4. raw identifier as last resort.

Never mix Chinese/Japanese/English labels arbitrarily because translation entries are missing.

---

# 181. Text Truncation

Use ellipsis only when unavoidable.

Provide full value through:

- tooltip;
- inspector;
- expand;
- copy.

Primary entity names should receive sufficient width.

---

# 182. Progressive Disclosure for IDs

Example Player Inspector:

    Technical Details ▾

When expanded:

    Player UID
    Guild UID
    Character container ID
    Save object path

This is much cleaner for normal usage.

---

# 183. World Entity Linking

Every relevant World entity should be cross-linked.

Player:

    Guild → Unnamed Guild

Guild:

    Base → Base 1

Base:

    Show on Map

Map marker:

    Open Base

This provides an internal "graph" of save entities.

---

# 184. Reference Linking

Inventory item:

    Open in Item Reference

Pal:

    Open in Pal Reference

Skill:

    Open in Skill Reference

Technology:

    Open in Technology Reference

---

# 185. History Preservation

When opening linked entities, retain list state.

Example:

1. Player list filter `Level 70+`.
2. Open Hathaway.
3. Open Guild.
4. Press Back.
5. Return to Hathaway/player list with filter intact.

---

# 186. Deep Linking Internally

If the framework supports routes, allow internal route targets such as:

    paltrainer://players/<uid>
    paltrainer://bases/<id>

Even if not externally exposed, route-based architecture improves navigation consistency.

---

# 187. Window Size Minimum

Set a sensible minimum app size.

Approximately:

- 1024×700 minimum.

Below this:

- sidebar collapses;
- inspector becomes drawer;
- tables adapt.

Do not allow the UI to compress into unreadable columns.

---

# 188. Default Desktop Layout

At 1450×800 similar to supplied screenshots:

- sidebar: ~240px;
- main workspace: remaining width;
- inspector where present: ~340px;
- page padding: 24px;
- toolbars: 48px;
- tables comfortably spaced.

This is substantially different from the existing full-width content with stacked top navigation.

---

# 189. Save Context When Sidebar Collapsed

If sidebar is collapsed, save status can appear in the workspace header.

Do not hide whether a save is loaded.

---

# 190. Global Drop Zone

The user should be able to drag a compatible save file into the application from any page.

When dragging:

    Drop save to load

Show an application-wide drop overlay.

Before replacing a currently loaded save with unsaved changes:

    You have unsaved changes.
    Save before opening another save?

    [ Cancel ]
    [ Discard and Open ]
    [ Save and Open ]

---

# 191. Recent Save Errors

If recent save path no longer exists:

    Local World
    File not found

    Locate...
    Remove from Recent

---

# 192. Save Reload

Provide a visible `Reload from Disk` action.

If there are unsaved changes:

warn before reload.

---

# 193. External File Changes

If technically possible, detect external changes.

    Save changed on disk

    The loaded save was modified by another program.

    [ Reload ]
    [ Ignore ]

This is especially relevant for active game saves.

---

# 194. Game Running Warning

If Palworld is running and save editing is unsafe:

    Palworld appears to be running.

    Editing an active save may cause your changes to be overwritten.

    [ Continue Anyway ]

Only implement if reliable process detection exists.

---

# 195. Save Backups Screen

Recommended new workspace:

    Backups

    Sep 8, 23:41
    Before Player Inventory Edit
    Local World
    8.4 MB

    [ Restore ]
    [ Open Folder ]

This reinforces safety.

---

# 196. Restore Backup

Restoring backup should require confirmation:

    Restore this backup?

    Current save will be backed up before restoration.

    Backup date:
    Sep 8, 2026 11:41 PM

    [ Cancel ] [ Restore Backup ]

---

# 197. Tool Center Search

As the tool collection grows:

    Search tools...

Examples:

    "steam"
    "host"
    "transfer"

Tool cards can also be filtered:

    All
    Conversion
    Repair
    Transfer
    Advanced

---

# 198. Favorites / Recent Tools

Optional future enhancement:

    Recent Tools
    Player Inventory
    Pal Editor
    Convert Save

Do not add favorites unless tools become numerous enough to justify it.

---

# 199. First-Run Experience

Optional onboarding:

    Welcome to PalTrainer

    PalTrainer lets you inspect and modify Palworld saves.

    1. Open a save
    2. PalTrainer creates a backup
    3. Make changes
    4. Save safely

    [ Open Save ]

Do not force a long tutorial.

---

# 200. Contextual Help

Complex pages can expose:

    ?

Example Pal Editor help:

    Party
    Pals currently assigned to the player's active party.

    Palbox
    Stored Pals contained in Palbox boxes.

Avoid permanent instructional paragraphs cluttering the interface.

---

# 201. No-Save Tool Rules

Tools should declare requirements programmatically.

Example metadata:

    requiresSave: true
    requiresPlayer: false
    requiresBase: false
    destructive: true

The UI can then consistently show:

    Requires loaded save

instead of implementing ad hoc disabled behavior per page.

---

# 202. Context Requirements

Likewise editors can declare:

    Player Inventory
    Requires:
    - loaded save
    - player

If no player selected:

    Select a player to begin.

    [ Choose Player ]

If exactly one player exists, auto-select it.

---

# 203. Smart Defaults

Examples:

- one player → auto-select;
- one guild → auto-select;
- one base → auto-select;
- most recently selected player → restore selection;
- only one save candidate → offer quick open.

Avoid making users repeat obvious selections.

---

# 204. Base Inventory Smart Context

If one guild and one base exist, go directly to:

    Unnamed Guild / Base 1

instead of forcing dropdown selection.

Context selectors remain available to change target.

---

# 205. Pal Editor Smart Context

If one player exists, open automatically.

If multiple players exist, use the last selected player when valid.

---

# 206. Search Across Entities

Potential command palette/global search:

    Search PalTrainer

    Hathaway                Player
    Base 1                  Base
    Unnamed Guild           Guild
    Jetragon                Pal
    Ancient Civilization... Item

This can become a major usability improvement.

---

# 207. Performance Budget

Suggested interaction expectations:

- sidebar navigation: effectively instant;
- opening inspector: <100ms after data available;
- search feedback: <100ms;
- switching inventory container: <150ms where possible;
- Palbox pagination: smooth;
- large operations: background processing with progress.

---

# 208. Visual Regression Requirement

Every redesigned page should be visually tested against the new component system.

Do not accept pages that:

- fall back to the old tab bar;
- use old button styling;
- use old dialogs;
- use arbitrary spacing;
- use old table styling.

---

# 209. Migration Strategy

Recommended implementation order:

## Phase 1 — Foundation

- design tokens;
- typography;
- buttons;
- inputs;
- sidebar;
- header;
- save context;
- toast system;
- dialogs;
- DataTable;
- inspector.

## Phase 2 — App Shell

- new navigation;
- Overview;
- Tool Center;
- no-save state;
- activity.

## Phase 3 — World

- Players;
- Bases;
- Guilds;
- Exclusions;
- Map.

## Phase 4 — Editors

- Player Inventory;
- Base Inventory;
- Pal Editor;
- JSON Editor.

## Phase 5 — Bulk Workflows

- bulk item;
- bulk abilities;
- bulk Pal actions;
- guild assignment.

## Phase 6 — Remaining Tools

- every Tool-tab screen not supplied;
- conversion utilities;
- transfer;
- repair;
- injection;
- restore;
- currently inaccessible screens.

## Phase 7 — Safety / Polish

- backups;
- change review;
- keyboard shortcuts;
- accessibility;
- performance;
- responsive layout.

---

# 210. Migration Rule

Do not migrate only the page content while leaving the old navigation shell intact.

The shell should be migrated early.

Otherwise the application will temporarily establish a hybrid design that is likely to become permanent.

---

# 211. Component Ownership

Avoid implementing multiple near-identical components such as:

    PlayerTable
    GuildTable
    BaseTable

if a configurable EntityTable/DataTable can handle the shared behavior.

Likewise:

    PlayerInspector
    GuildInspector
    BaseInspector

can share primitives even if final content differs.

---

# 212. Page-Level Consistency Checklist

Every page should answer:

1. Where am I?
2. What save am I editing?
3. What entity is selected?
4. What can I do here?
5. Is anything unsaved?
6. What is the primary action?
7. What happens if I leave?
8. How do I recover if something fails?

If a page cannot answer these visually, it is incomplete.

---

# 213. Editor-Level Consistency Checklist

Every editor should provide:

- context;
- search;
- filtering if useful;
- selected entity;
- modification controls;
- clear pending-change state;
- save behavior;
- reset/undo where appropriate;
- loading state;
- empty state;
- error state.

---

# 214. Tool-Level Consistency Checklist

Every tool should show:

- purpose;
- prerequisites;
- source;
- destination/target;
- risk;
- operation;
- progress;
- result;
- backup state when applicable.

---

# 215. Dialog-Level Consistency Checklist

Every dialog should provide:

- meaningful title;
- short explanation if necessary;
- content;
- secondary action left;
- primary action right;
- close behavior;
- Escape handling;
- focus trap;
- correct destructive styling.

---

# 216. Inventory-Level Consistency Checklist

Every inventory grid should share:

- slot sizing rules;
- quantity badge;
- item image behavior;
- rarity representation;
- selected state;
- hover behavior;
- context menu;
- keyboard navigation;
- empty slot appearance.

Player and Base inventories should not look like separate products.

---

# 217. Pal-Level Consistency Checklist

Every Pal presentation should use the same:

- Pal portrait;
- species name;
- level treatment;
- gender marker;
- rarity/status markers;
- skill terminology;
- context menu;
- selected state.

---

# 218. Loading-Level Consistency Checklist

Every asynchronous feature should define:

- initial state;
- loading state;
- success state;
- zero-result state;
- failure state;
- retry behavior.

Do not leave blank panels during loading.

---

# 219. Exact Consistency Mandate for Unseen Screens

This point is important enough to repeat:

The screenshots do not represent the complete application.

Any screen omitted because:

- a save is required;
- the current loaded-save bug prevents opening it;
- the tool was not captured;
- the feature is hidden;
- the feature is experimental;
- the feature is reached through a context menu;
- the feature opens only under certain save conditions;

must still receive the same redesign.

The redesign system is application-wide.

There should be **zero legacy UI islands**.

---

# 220. New Visual Identity Summary

The redesigned PalTrainer should visually communicate:

### Sidebar

Persistent orientation.

### Header

Current task and save status.

### Context

Current Player / Guild / Base.

### Workspace

Focused data manipulation.

### Inspector

Details and context-sensitive actions.

### Accent

Selection and priority.

### Semantic colors

Status and risk.

### Activity

Trust and traceability.

### Backups

Safety.

This is a substantially different visual and interaction model from the current UI.

---

# 221. Final Target Experience

A user should be able to open PalTrainer and immediately understand:

    PalTrainer
    Local World
    Steam
    Saved

    1 Player
    1 Guild
    1 Base
    220 Pals

From there, the interface should feel like navigating one coherent save-management workspace rather than switching between unrelated utility screens.

The main application should prioritize:

- entities over IDs;
- context over menus;
- workflows over dialogs;
- hierarchy over borders;
- clarity over density;
- safe editing over immediate mutation;
- consistency over one-off page designs.

---

# 222. Redesign Acceptance Criteria

The redesign should not be considered complete until all of the following are true.

## Application Shell

- [ ] Primary navigation has moved away from the current stacked horizontal layout.
- [ ] A persistent sidebar or equivalently strong new navigation structure exists.
- [ ] Save context is visible and understandable.
- [ ] Selected entity context is readable.
- [ ] Native window controls are visually separate from app-level actions.
- [ ] Unsaved state is explicit.
- [ ] Global search/command navigation is available or architecture allows it.

## Visual System

- [ ] Typography scale is standardized.
- [ ] Spacing uses centralized tokens.
- [ ] Buttons have clear hierarchy.
- [ ] Destructive actions are semantically different.
- [ ] Borders are reduced.
- [ ] Accent usage is intentional.
- [ ] Components use consistent radii.
- [ ] Tooltips use a shared system.

## Navigation

- [ ] World screens follow one navigation model.
- [ ] Editor screens follow one navigation model.
- [ ] Tool screens follow one navigation model.
- [ ] Context persists between related pages.
- [ ] Back navigation preserves relevant state.
- [ ] Important actions are not exclusively hidden in context menus.

## Players

- [ ] Human-readable player information is prioritized.
- [ ] UUIDs are secondary.
- [ ] Inspector is structured.
- [ ] Bulk actions appear contextually.
- [ ] Player → Inventory is direct.
- [ ] Player → Pal Editor is direct.
- [ ] Player → Guild is direct.

## Bases

- [ ] Base names are primary.
- [ ] IDs are secondary.
- [ ] Base → Inventory is direct.
- [ ] Base → Map is direct.
- [ ] Base → Guild is direct.

## Guilds

- [ ] Guild list is simplified.
- [ ] Member list does not permanently consume unnecessary space.
- [ ] Guild assignment workflow is redesigned.
- [ ] Guild → Players is direct.
- [ ] Guild → Bases is direct.

## Exclusions

- [ ] Adding an exclusion is discoverable.
- [ ] Right-click is optional rather than mandatory.
- [ ] Player/Guild/Base exclusions use one coherent list.
- [ ] Empty state is useful.

## Map

- [ ] Map occupies the majority of the workspace.
- [ ] Browser becomes a structured explorer.
- [ ] Layers are understandable.
- [ ] Marker selection opens structured details.
- [ ] Coordinates/zoom are consolidated.
- [ ] Map controls have tooltips or labels.

## Player Inventory

- [ ] Player context is obvious.
- [ ] Inventory categories are visually distinct from global navigation.
- [ ] Grid styling is standardized.
- [ ] Equipment is structured by category.
- [ ] Rarity and selection are visually different.
- [ ] Search/filter/sort are consistent.
- [ ] Item details are easy to access.

## Base Inventory

- [ ] Guild/Base context is hierarchical.
- [ ] Containers use a clear navigator.
- [ ] Inventory grid shares Player Inventory primitives.
- [ ] Unknown structures have useful placeholders.
- [ ] Loading state communicates real work.
- [ ] Base Pals has a proper empty state.

## Pal Editor

- [ ] Sources, collection, and details are separated clearly.
- [ ] Palbox navigation is easy with hundreds of boxes.
- [ ] Pal grid is readable.
- [ ] Inspector is reorganized.
- [ ] Bulk actions appear only when relevant.
- [ ] Destructive actions are clearly distinguished.

## Bulk Workflows

- [ ] Bulk Item Management is reorganized.
- [ ] Bulk Ability editing uses readable labels.
- [ ] Bulk Pal deletion provides affected count.
- [ ] Skill removal supports preview where possible.
- [ ] Guild assignment has clear source/target/review structure.

## JSON Editor

- [ ] Tree structure is clearly readable.
- [ ] Search behavior is explicit.
- [ ] Paths can be identified.
- [ ] Import/export actions are clear.
- [ ] Validation exists for editable JSON.
- [ ] Raw JSON mode is considered or implemented if appropriate.

## Safety

- [ ] Dangerous operations provide confirmation.
- [ ] Backup behavior is visible.
- [ ] Unsaved changes are visible.
- [ ] Errors explain whether the save changed.
- [ ] Save success is communicated.
- [ ] Bulk destructive actions state affected counts.

## Accessibility

- [ ] Keyboard navigation works.
- [ ] Focus states are visible.
- [ ] Icon controls have accessible names.
- [ ] Color is not the sole state indicator.
- [ ] Text contrast is acceptable.
- [ ] Dialog focus behavior is correct.

## Missing / Inaccessible Screens

- [ ] Every existing screen not supplied in the screenshots is migrated.
- [ ] Currently broken Tool-tab screens use the new system when accessible.
- [ ] No legacy tabs remain.
- [ ] No legacy dialogs remain.
- [ ] No legacy table styling remains.
- [ ] No legacy button styling remains.
- [ ] No legacy navigation remains.

---

# 223. Non-Goals

The UI overhaul should not unnecessarily change:

- save format behavior;
- parsing logic;
- game data semantics;
- existing tool capabilities;
- entity relationships;
- supported platforms;
- internal editor functionality.

This is primarily an application architecture and interface rehaul.

Backend refactoring should occur only where required to support the redesigned UX cleanly.

---

# 224. Final Design Principle

The central rule for the redesign is:

> Do not ask how the existing PalTrainer layout can be improved. Ask how PalTrainer would be designed today if the same functionality were being built as a new desktop product.

The screenshots define **what PalTrainer can do**.

They do **not** define what PalTrainer should look like.

The new interface should preserve the power of the existing application while replacing its navigation, hierarchy, density, editing workflows, and component organization with a coherent modern desktop workspace.

Every visible and currently invisible tool should ultimately look and behave like it belongs to the same application.