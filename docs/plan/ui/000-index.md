# UI Overhaul — Plan Index & Coverage Map

Branch: `feat/ui-overhaul` · Created: 2026-09-03 · **Reset: 2026-09-04 (Mandatory Overhaul Reset executed — see 000-design-context.md §0)** · Status tracking: `PROGRESS.md`

## Reading order

1. `000-design-context.md` — **§0 reset status first**, then thesis v2, tokens, typography, invariants
2. `019-plan.md` — **design reset** (thesis v2, palette v2, typography v2, divergence matrix) — ACTIVE
3. `020-plan.md` — shell v2 (NexusBand rail, page ribbons, InstrumentTray) — ACTIVE
4. `021-plan.md` — Start page v2 (operations masthead, campaign strip, mission columns) — ACTIVE
5. `022-plan.md` — dialog strategy — ACTIVE
6. `023-plan.md` — table strategy + search/exclusions recomposition — ACTIVE
7. `024-plan.md` — a11y / states / resize / DPI / localization — ACTIVE
8. `025-plan.md` — regression, cleanup, documentation, close-out — ACTIVE
9. Screen revisions (ACTIVE): `007-r02` search · `008-r02` Map · `009-r02`
   Base Inventory · `010-r02` Pal Editor · `011-r02` Player Inventory ·
   `012-r02` Breeding · `013-r02` JSON · `014-r02` Exclusions · `015-r02` Docs
10. `008-plan.md` … `018-plan.md` — **FROZEN** original screen plans

## Plan status

| Plan | Subject | Status |
|---|---|---|
| 001 | Repository & UI audit | COMPLETE (audit still valid; conclusions superseded by 019 §3) |
| 002 | Design system foundation | INFRA ONLY (token dict/builder/scanner kept; palette+type content replaced by 019) |
| 003 | Shared component library | INFRA ONLY (components kept; visuals re-derived by 020–023) |
| 004 | Shell & navigation | REJECTED (old topology preserved) |
| 005 | Dashboard | REJECTED (old card composition preserved) |
| 006 | Results & Statistics panels | REJECTED (right dock preserved) |
| 007 | Search screens | REJECTED (sidebar-era composition; needs re-plan vs 023) |
| 008–018 | Screen migrations & passes | FROZEN — revise before execution |
| 019 | Design reset "Deck Operations" | ACTIVE |
| 020 | Shell v2 (NexusBand + ribbons + tray) | ACTIVE |
| 021 | Start page v2 | ACTIVE |
| 022 | Dialog strategy (overlay sheets) | ACTIVE |
| 023 | Table strategy + search recomposition | ACTIVE |
| 024 | A11y / states / DPI / localization | ACTIVE |
| 025 | Regression / cleanup / close-out | IMPLEMENTED |
| 007-r02 / 008-r02 … 015-r02 | Screen revisions | ACTIVE |

## Coverage checklist

Required area → owning plan(s):

| UI area / subsystem | Plan(s) | Done |
|---------------------|---------|------|
| Repository & UI architecture audit, screen-to-code map | 001, 019 §3 | [x] |
| Design direction & visual language (thesis v2 + divergence matrix) | 019 | [x] |
| Mandatory Overhaul Reset (rejection records, retained infra) | 019 §3, design-context §0 | [x] |
| Typography & fonts (bundled Hanken Grotesk + Inter, loading, packaging) | 019 §6, design-context §3 | [x] |
| Color tokens (palette v2 warm/amber/teal) | 019 §5 | [x] |
| Spacing / radius / elevation / height tokens | 019 §7 (kept from 002) | [x] |
| Icon strategy (Nerd Font registry, no emoji) | 002 (kept), design-context §1 | [x] |
| Light/dark theme strategy (dark-only, theme-ready) | 002 (kept) | [x] |
| Shell v2 (canvas + NexusBand + ribbons + window controls) | 020 | [ ] |
| Navigation model v2 (rail zones, keyboard, deep links) | 020 | [ ] |
| Results replacement (InstrumentTray + TrayDrawer overlay) | 020 | [ ] |
| Statistics presentation (rail metrics + drawer deltas) | 020 | [ ] |
| Start page v2 (masthead, campaign strip, mission columns) | 021 | [ ] |
| Map Viewer | 008-r02 | [x] |
| Base Inventory | 009-r02 | [x] |
| Player Inventory | 011-r02 | [x] |
| Pal Editor | 010-r02 | [x] |
| Search Players / Guilds / Bases | 023 + 007-r02 | [x] |
| Exclusions | 014-r02 (via 023) | [x] |
| JSON Editor | 013-r02 | [x] |
| Breeding | 012-r02 | [x] |
| Wiki / Docs + Tab Guide dialog | 015-r02 (+022) | [x] |
| Item-selection dialogs | 022 | [ ] |
| Pal-selection dialogs & SkillPicker | 022 | [ ] |
| Conversion dialogs (tools/options) | 021, 022 | [ ] |
| Transfer / bulk-action dialogs | 022 | [ ] |
| Confirmation dialogs (shared confirm, danger variant) | 003 kept, 022 | [ ] |
| Dialog strategy (overlay sheets, action columns) | 022 | [x] |
| Table strategy (dense full-bleed, no per-panel QSS) | 023 | [x] |
| Filters & search inputs | 023 | [ ] |
| Dropdowns (styled combo) | 003 kept | [x] |
| Forms (field helpers, validation states) | 022, 023 | [ ] |
| Empty states | 021 Start; per-screen plans | [ ] |
| Loading states (rail spinner, header-free, overlays) | 020, 021 | [ ] |
| Error states (chips, banners, dialogs) | 022, 023 | [ ] |
| Success states / feedback (toasts, badges, deltas) | 003 kept, 020 | [ ] |
| Hover/pressed/focus/selected/disabled/checked states | 019 QSS + 024 audit | [ ] |
| Scrollbars | 002 kept | [x] |
| Modal behavior & dialog lifecycle safety | 003 kept, 022, 024 | [ ] |
| Accessibility & keyboard navigation | 020 (band), 024 | [x] |
| Window resizing & min-size correctness | 024 | [ ] |
| High-DPI behavior | 024 | [ ] |
| Long text & localization safety (9 languages) | 024 | [ ] |
| Background workers (off GUI thread) | 022, 024, 025 | [ ] |
| Regression testing (unit + integration + slow) | 025 | [x] |
| Screenshot-based visual QA | **PENDING MANUAL** (see design-context §2) + 025 | [ ] |
| Documentation (ui-system reference) | 025 | [x] |
| Cleanup of obsolete styles & components (legacy shell deletion) | 025 | [x] |
| tests/test_registry.py updates for moved/new modules | 020, 025 | [x] (dynamic loader covers new chrome) |

## Screens (page ids) → plan

| Page id | Tab index | Plan |
|---------|-----------|------|
| tools | 0 | **021** |
| map | 7 | 008 → revise |
| base_inventory | 1 | 009 → revise |
| player_inventory | 2 | 011 → revise |
| pal_editor | 3 | 010 → revise |
| players | 4 | re-plan vs 023 |
| guilds | 5 | re-plan vs 023 |
| bases | 6 | re-plan vs 023 |
| exclusions | 8 | 014 → revise |
| json_editor | 9 | 013 → revise |
| breeding | 11 | 012 → revise |
| docs | 10 | 015 → revise (+022) |

## Dialogs → plan

| Dialog | File | Plan |
|--------|------|------|
| Player item actions | ui/dialogs/player_item_dialog.py | 022 |
| Player pal actions | ui/dialogs/player_pal_dialog.py | 022 |
| Player technology | ui/dialogs/player_technology_dialog.py | 022 |
| Guild assign | ui/dialogs/guild_assign_dialog.py | 022 |
| Fix illegal pals / players | ui/dialogs/fix_illegal_*.py | 022 |
| Skill picker | ui/dialogs/skill_picker.py | 022 |
| Tab guide | ui/dialogs/tab_guide_dialog.py | 015 → revise (+022) |
| Editor input dialogs | editor/dialogs.py | 022 |
| Pal create dialogs | editor/pal_editor/create_dialogs.py | 022 (+010 revise) |
| GPS editor | editor/gps_editor.py | 022 |
| World options | editor/worldoption_editor.py | 022 |
| Conversion options | ui/tabs/tools_tab.py | **021** |
| Item picker / quantity / slots / loadouts | ui/tabs/inventory_tab.py | 022 (+011 revise) |
| Guild pickers / structure / economy | ui/tabs/base_inventory_tab.py | 022 (+009 revise) |
| Confirmations (all) | shared confirm() | 003 kept, 022 |
| Menu popup | widgets (MenuPopup) | 020 (re-hosted), 022 (restyled) |

## Non-negotiable invariants (see 000-design-context.md §7)

Save I/O & backups untouched · JSON editor read-only-by-default · destructive actions
previewed+confirmed · UI never mutates widget trees during `exec()` · long work off
GUI thread · game-data colors (rarity/element/rank) preserved · all strings via `t()` ·
**new-shell rules: no left sidebar, no right dock, no glass/cyan in new code.**
