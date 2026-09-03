# UI Overhaul — Plan Index & Coverage Map

Branch: `feat/ui-overhaul` · Created: 2026-09-03 · Status tracking: `PROGRESS.md`

## Reading order

1. `000-design-context.md` — thesis, tokens, typography, theme strategy, invariants (read first)
2. `001-plan.md` — audit: screen-to-code map, component inventory, stylesheet audit
3. `002-plan.md` — design system foundation (tokens, fonts, QSS builder, ThemeManager)
4. `003-plan.md` — shared component library
5. `004-plan.md` — shell & navigation
6. `005-plan.md` … `015-plan.md` — screen migrations (one plan per screen group)
7. `016-plan.md` — dialogs & pickers (system-wide)
8. `017-plan.md` — a11y / states / resize / DPI / localization
9. `018-plan.md` — regression, cleanup, documentation, close-out

Implementation order = plan number order (matches the required migration order:
shell → dashboard → results/stats → search → inventories → editor → map → breeding
→ JSON → exclusions → docs → dialogs → consistency pass).

## Coverage checklist

Required area → owning plan(s):

| UI area / subsystem | Plan(s) | Done |
|---------------------|---------|------|
| Repository & UI architecture audit, screen-to-code map | 001 | ☐ |
| Current widget/component inventory | 001 | ☐ |
| Stylesheet & theme audit | 001 | ☐ |
| Design direction & visual language (thesis) | 000-context, 002 | ☐ |
| Typography & font selection (installed-font reality) | 002 |  [x] |
| Color tokens | 002 |  [x] |
| Spacing tokens (4px grid) | 002 |  [x] |
| Radius tokens | 002 |  [x] |
| Elevation & border tokens | 002 |  [x] |
| Icon strategy (Nerd Font registry) | 002 |  [x] |
| Light/dark theme strategy (dark-first, theme-ready) | 002 |  [x] |
| Application shell (window, header, splitters, overlay, console) | 004 |  [x] |
| Sidebar navigation (grouped, keyboard) | 004 |  [x] |
| Top bar (save-state chip, window controls) | 004 |  [x] |
| Dashboard (Tools tab) & save-loaded state | 005 |  [x] |
| Results Panel | 006 |  [x] |
| Statistics Panel | 006 |  [x] |
| Map Viewer (canvas chrome, markers/zones/effects tokens, overlays) | 008 | ☐ |
| Base Inventory | 009 | ☐ |
| Player Inventory | 011 | ☐ |
| Pal Editor (tab + editor package) | 010 | ☐ |
| Search Players / Guilds / Bases | 007 |  [x] |
| Exclusions | 014 | ☐ |
| JSON Editor | 013 | ☐ |
| Breeding | 012 | ☐ |
| Wiki / Docs + Tab Guide dialog | 015 | ☐ |
| Item-selection dialogs | 016 (+009/011) | ☐ |
| Pal-selection dialogs & SkillPicker | 016 (+010) | ☐ |
| Conversion dialogs (tools/options) | 005, 016 | ☐ |
| Transfer / bulk-action dialogs (item, pal, tech, guild, fix) | 016 | ☐ |
| Confirmation dialogs (shared confirm system) | 003, 016 | ☐ |
| Tables (shared DataTable + tree styling) | 003 |  [x] |
| Filters & search inputs | 003, 007 |  [x] |
| Dropdowns (styled combo) | 003 |  [x] |
| Forms (field helpers, validation states) | 003, 016 | ☐ |
| Empty states | 003 (+every screen plan) |  [x] |
| Loading states (popup, header spinner, overlays) | 003, 005 |  [x] |
| Error states (chips, banners, dialogs) | 003, 005, 016 | ☐ |
| Success states / feedback (toasts, badges) | 003 |  [x] |
| Hover / pressed / focus / selected / disabled / checked states | 002 QSS + 017 audit | ☐ |
| Scrollbars | 002 |  [x] |
| Modal behavior & dialog lifecycle safety | 003, 016, 017 | ☐ |
| Statistics/results presentation | 006 |  [x] |
| Page headers | 004, per-screen plans |  [x] |
| Interaction feedback (toasts, pulses, transitions) | 003, 004 |  [x] |
| Accessibility & keyboard navigation | 017 | ☐ |
| Window resizing & min-size correctness | 017 | ☐ |
| High-DPI behavior | 017 | ☐ |
| Long text & localization safety (9 languages) | 017 | ☐ |
| Background workers (off GUI thread) | 016, 017, 018 | ☐ |
| Regression testing (unit + integration + slow) | 018 | ☐ |
| Screenshot-based visual QA | per-plan + 018 | ☐ |
| Documentation (ui-system reference) | 018 | ☐ |
| Cleanup of obsolete styles & components | 018 | ☐ |
| tests/test_registry.py updates for moved/new modules | 002, 018 | ☐ |

## Screens (sidebar) → plan

| Sidebar entry | Page id | Tab index | Plan |
|---------------|---------|-----------|------|
| Tools | tools | 0 | 005 |
| Map | map | 7 | 008 |
| Base Inventory | base_inventory | 1 | 009 |
| Player Inventory | player_inventory | 2 | 011 |
| Pal Editor | pal_editor | 3 | 010 |
| Search Players | players | 4 | 007 |
| Search Guilds | guilds | 5 | 007 |
| Search Bases | bases | 6 | 007 |
| Exclusions | exclusions | 8 | 014 |
| JSON Editor | json_editor | 9 | 013 |
| Breeding | breeding | 11 | 012 |
| Docs | docs | 10 | 015 |

## Dialogs → plan

| Dialog | File | Plan |
|--------|------|------|
| Player item actions | ui/dialogs/player_item_dialog.py | 016 |
| Player pal actions | ui/dialogs/player_pal_dialog.py | 016 |
| Player technology | ui/dialogs/player_technology_dialog.py | 016 |
| Guild assign | ui/dialogs/guild_assign_dialog.py | 007 |
| Fix illegal pals | ui/dialogs/fix_illegal_pal_dialog.py | 016 |
| Fix illegal players | ui/dialogs/fix_illegal_player_dialog.py | 016 |
| Skill picker | ui/dialogs/skill_picker.py | 016 |
| Tab guide | ui/dialogs/tab_guide_dialog.py | 015 |
| Editor input dialogs | editor/dialogs.py | 016 |
| Pal create dialogs | editor/pal_editor/create_dialogs.py | 016 (+010) |
| GPS editor | editor/gps_editor.py | 016 (+010) |
| World options | editor/worldoption_editor.py | 016 |
| Conversion options | ui/tabs/tools_tab.py | 005 |
| Item picker / quantity / slots / loadouts | ui/tabs/inventory_tab.py | 011 |
| Guild pickers / structure / economy | ui/tabs/base_inventory_tab.py | 009 |
| Confirmations (all) | shared confirm() | 003/016 |

## Non-negotiable invariants (see 000-design-context.md §9)

Save I/O & backups untouched · JSON editor read-only-by-default · destructive actions
previewed+confirmed · UI never mutates widget trees during `exec()` · long work off
GUI thread · game-data colors (rarity/element/rank) preserved · all strings via `t()`.
