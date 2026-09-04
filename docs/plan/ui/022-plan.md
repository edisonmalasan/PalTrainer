# 022 — Dialog Strategy: Overlay Sheets & Action Columns

> **Status: ACTIVE.** Replaces plan 016 (frozen) as the dialog/picker design
> authority. Infra from 003/016 (BaseDialog, confirm(), safe helpers) retained.

## 1. Objective

Define and implement the v2 dialog grammar: dialogs read as **overlay sheets**
of the Deck Operations shell — canvas-local surfaces with a left rule, content
zone, and right-aligned action cluster with isolated destructive actions —
instead of floating glass cards.

## 2. Scope

**In scope:** `chrome/components.py` (BaseDialog, confirm), dialog QSS in
`qss_builder.py` (`QDialog` global + `#dialogOption`/`#dialogCancel` +
sheet grammar), conversion options dialog (tools_tab), pickers opened from
inventories/base dialogs (composition only; screens own their internals).

**Out of scope:** per-screen dialogs' content layout (screen plans), MenuPopup
restyle (tokenized already).

## 3. Design requirements

1. **Sheet anatomy** (BaseDialog v2): `#dialogSheet` frame inside the dialog:
   top kicker row (zone micro-label), title (title token), hairline rule,
   content zone, footer row = [stretch][cancel ghost][primary amber CTA],
   danger actions isolated at footer-left with `danger` class.
2. **QMessageBox-family** (confirm/info/error) keep native behavior but get
   tokenized QSS (already global) — no per-dialog inline styles.
3. **No translucency**; floating elevation = surface_raised + border_strong
   + soft shadow (level-2 token allowance).
4. Focus lands on the primary action; Esc cancels; Return activates focused.
5. All states (hover/pressed/focus/disabled) defined for sheet buttons.

## 4. Behavior preservation

- Every dialog keeps its slots, signals, exec() lifecycle, parent-centering
  (`center_on_parent`), `_RestoreOnCloseFilter`/restore flow in tools_tab.
- Blocking `processEvents` pickers (`SkillPicker.pick`,
  `show_player_select_popup`) untouched this plan (restyle only).
- No widget-tree mutation during `exec()`.

## 5. Implementation tasks

1. `components.py`: BaseDialog gains kicker/title/footer API
   (`add_confirm_button` kept); danger-variant footer placement.
2. `qss_builder.py`: `QDialog`/`QMessageBox` global rules refreshed to sheet
   grammar; `#dialogSheet`, `#dialogKicker`, `#dialogTitle` labels,
   `#dialogRule`, footer buttons (`class="primary|ghost|danger"` reuse).
3. tools_tab `ConversionOptionsDialog` migrated to sheet anatomy.
4. Scanner whitelist untouched; rebuild theme.

## 6. Tests

- Smoke: construct BaseDialog v2 — kicker/title/footer present; confirm()
  danger variant places destructive button left; Esc/Return behavior.
- Full suite + compileall + scanner ≤ 1390 + pyright delta.

## 7. Visual QA

Code-based structural assertions + offscreen capture (`Logs/dialog_v2.png`).
Screenshot-based verification PENDING manual review.

## 8. Risks & rollback

- Dialogs subclass BaseDialog widely — API changes must be additive.
- Rollback: revert components.py + qss block; dialogs still function via old
  objectNames.
