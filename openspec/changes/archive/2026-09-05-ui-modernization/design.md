## Context

See `proposal.md` for motivation. Current state (from read-only exploration): `MainWindow` frameless + `QStackedWidget` (12 pages) + right 76px `NexusBand` with custom-painted `BandItem`s; per-page `create_page_ribbon()`; token system in `chrome/tokens.py` (dark-only warm palette) generating `resources/ui/themes/darkmode.qss` via `chrome/qss_builder.py`; shared factories in `chrome/components.py` (`make_panel/card/button/badge/searchField/DataTable/BaseDialog`) plus `chrome/icons.py`, `chrome/fonts.py`, `widgets/empty_state.py`, `widgets/search_panel.py`. Three styling generations coexist (builder vs. legacy `styles.DIALOG_STYLE/PICKER_*/SLOT_*` gradients vs. per-widget hardcoded hex including retired cyan `#7DD3FC` and blue `#4a90e2`); every table page reserves a `170px` right margin for the floating `WindowControls` overlay; `inventory_tab`/`base_inventory_tab`/`map_tab`/`wiki_tab` are 1500–4200-line monoliths with business logic (`backup_manager`, `.sav` reads, auto-save timers, calibration file rewrites) embedded in UI code.

## Goals / Non-Goals

**Goals:**
- Establish one token-driven visual language across shell, tables, states, and (incrementally) dialogs while keeping the dark Deck-Ops direction.
- Fix rail legibility, ribbon/overlay collisions, table-frame consistency, and empty-state guidance in Phases 0–3.
- Make Phase 4 shippable per-dialog and Phase 5 cleanly separable.

**Non-Goals:**
- No save/manager/business-logic changes; no monolith-internal rewrites (Phase 5); no new light theme; no navigation-ID, shortcut, i18n-key, timer, or threading-model changes; no literal application of the `pyqt6-ui-designer` reference layout (left 240px sidebar + 64px topbar + corporate blue) — only its token/state discipline.

## Decisions

- **Adapt, don't adopt, the pyqt6-ui-designer skill.** Rationale: the skill's value is token-first colors, 4px grid, complete interactive states, and `class`-property QSS; its reference shell (left sidebar, top bar, light+dark blue) contradicts the settled Deck-Ops decision (right rail, frameless, dark-only amber/teal from plans 019–025). Alternative (rebuild shell per skill) rejected: would churn navigation contracts and user muscle memory for no functional gain.
- **Reuse, don't parallelize: `tokens.py` + `qss_builder.py` + `components.py`.** All new QSS enters the builder as `objectName/property` rules; per-widget `setStyleSheet` with hex is a violation caught by `scripts/scrs/check_theme_violations.py`. `StyledCombo` is replaced by `QComboBox` + builder rules rather than themed in place. Alternative (local QSS fixes per screen) rejected: recreates the three-generation fork.
- **Overlay-aware ribbon constant instead of `170px` magic.** Introduce one layout constant for the `WindowControls` reserve and a ribbon helper wrapping the private `_ribbon_actions_slot`, so Phases 1–3 pages share the fix. Alternative (per-page margin tweaks) rejected: proven to drift.
- **Property-driven state everywhere.** Selection/active/checked via `setProperty()` + `unpolish/polish` (as tray/band/guild-assign already do); stylesheet-string swaps (tech frames, player cards) migrate in Phase 4. Rationale: only properties respond to theme changes.
- **Phase order 0→3 → 4 (per-dialog) → 5 (deferred).** Shell/tables/states are outer-chrome-only and low-risk; dialogs each own blocking loops and direct `.sav` access so they ship one at a time starting with the already-migrated `guild_assign_dialog`; monolith internals are excluded because they mix virtualization, delegates, timers, and file rewrites. Alternative (monoliths first) rejected: highest blast radius, lowest visual return.
- **Per-phase visual gates.** Before/after screenshots at fixed size per touched page plus `compileall` and `pytest -c tests/pytest.ini` (focused then full) before advancing. Rationale: QSS regressions are invisible to unit tests.

## Risks / Trade-offs

- [Risk] Custom `paintEvent` widgets (BandItem, NerdBtn, CatBtn, delegates) ignore QSS → Mitigation: keep paint for glyphs only; move all color/padding/state into properties + builder rules; verify HiDPI/i18n label lengths.
- [Risk] Frameless drag vs. overlay geometry regresses (ribbon clicks start moves, controls unclickable) → Mitigation: hit-test excludes interactive children (existing `_hit_window_drag_zone` contract); test at min/max sizes.
- [Risk] Lazy-tab `_ensure_tab` + `_refresh_tab` coupling breaks when pages reframe → Mitigation: preserve page indices/IDs and `refresh()` signatures; reframe containers only.
- [Risk] Blocking `processEvents` popups (`player_select_popup`, `skill_picker`) freeze under restyle → Mitigation: do not touch their event loops in this change; only outer dialog chrome in Phase 4.
- [Risk] `apply_to_widget` per-dialog QSS copies diverge from global theme → Mitigation: migrated dialogs rely on global QSS + builder rules; remove per-widget copies as each dialog migrates.
- [Risk] Retired cyan/blue remnants survive in rarely opened screens → Mitigation: scanner + screenshot checklist per phase; `wiki_tab`, `pal_editor`, `fix_illegal_*`, `PICKER_*/SLOT_*` explicitly listed in tasks.
- Trade-off: dark-only (no light theme) keeps scope shippable but diverges from the skill's two-theme ideal — accepted and recorded.

## Migration Plan

- Land Phase 0 (tokens/builder/ribbon constant, no visuals) → Phase 1 (rail/tray) → Phase 2 (five table pages on one frame) → Phase 3 (empty states/Tools/Map) → Phase 4 (one dialog per commit/PR, guild-assign first) → stop. Phase 5 is a separate future change with its own proposal.
- Rollback per phase: revert the phase's builder + page-frame commits; tokens file stays frozen so earlier phases remain coherent. No data migration involved.

## Open Questions

- None blocking. Deferrable detail: exact rail micro-label wording per locale (validated against `t()` keys during Phase 1 implementation); tray-drawer default expanded state (keeps current `user.cfg` behavior unless specs say otherwise).
