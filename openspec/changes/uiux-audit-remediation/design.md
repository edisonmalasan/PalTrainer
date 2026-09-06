# Design — UI/UX Audit Remediation

## Context

Shell v3 already implements: an app bar (`chrome/app_bar.py`) with brand, save chip, context indicator, utilities (console, tab guide, warning, about), window controls; a nav strip (`chrome/nav_strip.py`) rendering four zone groups inline in one 38px row; page ribbons via `create_page_ribbon(title, zone_caption, parent)`; a status strip wired to the streamed message system; a token palette (`chrome/tokens.py`) with QSS builder (`chrome/qss_builder.py`); a bundled SVG icon factory (`chrome/icons.py`); Hanken Grotesk/Inter bundled fonts (`chrome/fonts.py`).

The audit verdict: keep the foundation, fix structure and interactions. Every decision below defers to: preserve data/save logic, the `nav_changed` page-ID contract, keyboard shortcuts, i18n keys (add-only), and the bundled SVG asset set.

## Decisions

### D1 — Two-tier nav (primary + contextual secondary)

- **Direction (from audit §5):** Primary tier = `Tools · World · Edit · Reference` (Start zone's sole child Tools is promoted to a primary destination). Secondary tier = active zone's children only.
- **Implementation shape:** Refactor `nav_strip.py` into `NavStrip` hosting two QSS-styled rows inside one widget (fixed height grows from 38px to ~72px): a primary row of zone `NavTab`s (with chevron/caret treatment for zone-type destinations) and a secondary row of child `NavTab`s. Keep `ZONES` membership data as the single source of truth; add a `zone → last visited page` map. Zone activation: Tools navigates directly; World/Edit/Reference activate the zone and navigate to the last-visited child (fallback: first child).
- **Contracts preserved:** page IDs unchanged, `nav_changed(str)` unchanged, `set_active(id)` unchanged in signature, keyboard shortcuts still map to page IDs (main_window keeps its shortcut table; shortcut activation routes through `set_active`).
- **Zone captions vs ribbons:** primary-tier zone tabs are the group labels; per-page ribbons keep their zone captions but Base Inventory's caption changes from `sidebar.section.world` to `sidebar.section.editing`. Map keeps World.
- **Overflow:** keep existing compact-then-collapse strategy per tier; secondary tier overflow uses the existing `»` menu; primary tier compacts to zone short labels before overflow. Start/Tools never collapses.
- **Active treatments:** active page = amber underline + accent icon (existing). Active zone = amber text treatment on the primary tab while any child is active.

### D2 — Base Inventory / Bases icon collision

- Reuse `container.svg` (already bundled) as the Base Inventory nav icon if it reads distinctly at nav size; otherwise add one new `base_inventory.svg` (open-container glyph) following the icon factory. Decision at implementation time by visual check at 16–20px; prefer reusing existing assets first.

### D3 — Status strip message policy

- Introduce a small presentation helper (e.g. `_present_status(message)` in main_window's stream handling) that maps known technical payloads to human summaries before display: load results → "Save loaded"; update-check failures → warning-affordance update only; decompression stats → log only. Raw messages continue to the existing log/console stream unchanged. No backend changes to the stream itself.

### D4 — Warning tri-state

- Extend `app_bar.py` warning button with state `none | unread | acknowledged`. Store acknowledgement in the existing user-settings mechanism (not persistent across restarts unless trivially supported). Clicking always reveals the condition (console open or popup) and moves unread → acknowledged. Condition resolution (successful update check) returns to none.

### D5 — Monospace data typography

- Check bundled fonts for a monospace family already shipped; if none, use the system monospace fallback via the QSS builder's font stack (no new font bundling in this change — audit scope is visual demotion, not new font assets). Apply via a QSS token class (e.g. `QLabel#monoValue`, table item font roles) rather than per-widget stylesheets.

### D6 — Save path truncation + copy

- Elide middle of path (QFontMetrics elide or manual `…` slicing), monospace font, tooltip = full path, copy button uses existing `copy.svg` with transient "Copied" feedback.

### D7 — Table pages: capped height + inspector panel

- New shared inspector panel component in `chrome/components.py` (title, stat grid rows, action slot) modeled on the Docs detail panel.
- Bases/Players/Guilds layouts change from single column to table column + inspector column (fixed side width ~320–360px, responsive at min width 1200).
- Table container: `setMaximumHeight` bounded by row count × row height + header, with internal scroll beyond cap.
- Inspector selection follows existing row-selection signals; no data-layer changes. Identifier values in inspector and ID columns use D5 monospace + tooltip + copy.
- Players bulk bar moves into the footer directly under the table card (handlers unchanged) per ui-tables delta.
- Guilds member pane: the member list itself is the detail area — inspector-style wording fixes apply; member pane keeps its position but gains the row-level copy ("Click a guild row to view its members").
- Pagination: audit's "Page 1 of 1" reading turned out to be SearchPanel's result count (`search_panel.py` count_label). Task 4.4 relabels it to a labeled count (e.g. "1 result") instead of adding pagination, which the app does not have.

### D8 — Segmented platform toggle (Tools)

- Replace the two standalone Steam/GamePass buttons with one segmented control (two exclusive segments using bundled `steam.svg` / `gamepass.svg` artwork) where exactly one platform is selected; activating the selected segment starts the existing load flow. Keep both load handlers intact.

### D9 — Tools live log panel

- Reuse the existing streamed-message plumbing: subscribe the new panel to the same signal the status strip consumes; render entries in a bounded-height dark scroll area with a clear button. Console detach behavior untouched.

### D10 — Base/Player Inventory chips vs tabs

- Context (guild/base/player) selectors: bordered dropdown chips with chevron (extend `styled_combo.py` styling or QSS classes).
- View modes (Inventory / Base Pals): underlined tab styling (new QSS class), reusing existing toggle logic.
- Container list: partition rows by slot count/name class (guild chest & multi-slot storage vs dropped items), render debris group under a muted label; all containers remain listed and selectable.

### D11 — Pal Editor toolbar tiers + editable affordance

- Toolbar grouping: safe utilities group, bulk group, then a QSS separator and warning-tier destructive button, single row at min width (existing tiering spec already mandates tiers; this enforces the separator and ordering).
- Inspector: editable fields get the standard focusable input chrome; computed/read-only stats render as flat read-only rows without input borders. Skill value tooltips gain unit context (damage/power values).

### D12 — JSON Editor breadcrumb

- Horizontal clickable breadcrumb above the table tracking the current path; clicking an ancestor jumps selection there. Simple label-chips implementation over the existing tree model.

### D13 — Map discoverability

- Tooltips + accessible names on overlay toggles; +/− zoom buttons beside the readout calling the same zoom handlers as scroll; browser tree column `setSectionResizeMode(ResizeToContents)` fallbacks with tooltip on elided values.

### D14 — i18n

- New keys added under existing namespaces (en_US + translations where feasible; en_US fallback is authoritative). Existing keys untouched. Copy fixes (Guilds wording, Breeding position wording) are key-value edits or new keys.

## Risks / Trade-offs

- **Two-tier nav height:** +34px vertical chrome. Accepted; primary tier clarity outweighs the cost, and the secondary row replaces inline captions so net height growth is small.
- **Insight panels on sparse tables:** inspector adds horizontal complexity on Bases/Players/Guilds; bounded side width and min-width 1200 keep it safe. No data logic touched — panels render from existing read models.
- **Monospace without bundling a font:** system monospace may vary across machines; acceptable for data demotion purposes. Revisit bundling only if visual QA shows breakage.
- **Warning acknowledgement persistence:** kept session-scoped to avoid new settings schema; conditions re-notify on recurrence.

## Migration Plan

1. Shell chrome (nav, app bar, status, fonts/QSS) — no page behavior changes.
2. Tools page (segmented toggle, log panel, path copy).
3. Table pages (inspector + capped height + ID copy + pagination + bulk adjacency + wording).
4. Inventory pages (chips/tabs, container grouping, caption).
5. Editor/Reference polish (Pal Editor tiers, JSON breadcrumb, Map controls, Breeding copy).
Each phase ships independently compilable and testable; tasks.md enforces per-phase verification.

## Open Questions

- None blocking. D2's reuse-vs-new-icon and D5's monospace family resolve by inspection during implementation.
