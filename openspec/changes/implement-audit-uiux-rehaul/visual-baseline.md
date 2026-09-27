# Synthetic Visual Baseline

Task 1.4 records five representative pre-rehaul states through `scripts/scrs/render_uiux_baseline.py`:

| State | Size | Data source |
|---|---:|---|
| No-save shell and Tools page | 1024×700 | Empty application state |
| Loaded shell and Tools page | 1024×700 | Synthetic labels/counts/path only |
| Selected player table and inspector | 1024×700 | Synthetic player/guild/UID |
| JSON editor prerequisite state | 1024×700 | No save loaded |
| Shared confirmation dialog | 620×360 | Synthetic explanatory copy |

The harness requires an explicit output directory, writes PNGs plus `manifest.json` there, and never discovers or reads `.sav` files. Generated artifacts are verification output and are intentionally not committed. Reproduce with:

```powershell
$output = Join-Path ([System.IO.Path]::GetTempPath()) 'paltrainer-uiux-baseline'
uv run python scripts/scrs/render_uiux_baseline.py --output-dir $output
```

The paired unit test renders into pytest's temporary directory and verifies all five non-empty images, their dimensions, the synthetic-data declaration, and absence of save files.

## Visual inspection record

The five generated images were inspected on 2026-09-09. Each image was non-blank,
used the expected dimensions, and exposed the intended current-state controls. The
JSON editor capture intentionally preserves the current light header-strip mismatch;
it is a baseline defect for the rehaul rather than a harness failure. No real save
data, save path discovery, or committed image artifact was used.

## Phase 3 shell render

After the workspace-shell cutover, the same harness was updated to render the
registry-driven sidebar, dedicated title/drag region, workspace header/context,
responsive page host, and the migrated selected-entity composition. The five
temporary images were inspected again on 2026-09-09 at their declared dimensions.
The shell, JSON editor, entity browser, and dialog all used the generated dark token
theme; the earlier light header/canvas mismatch was no longer present. At 1024×700,
the sidebar remained scrollable, the active destination stayed visible, primary
save/context state stayed in the header, and content did not overlap the distinct
window controls. The manifest again declared synthetic-only data and no save files.

## Phase 8 tools, dialogs, and System render

`scripts/scrs/render_phase8_surfaces.py` renders ten deterministic states without
executing a tool operation or discovering a save: Tool Center with no save,
save-gated Players, conversion choice, repair review/result, transfer
review/failure, Settings, About with an available update, and Diagnostics. The
paired test verifies the manifest, non-empty dimensions, no operation execution,
and absence of `.sav` files.

The ten temporary images were inspected on 2026-09-11 at 1024×700 for workspace
surfaces and 520×340 through 740×540 for dialogs. The first result-state pass
exposed insufficient workflow-dialog height: the title could be clipped after
result copy appeared. Repair and transfer minimum heights were increased, the
renderer was made lazy so only one top-level surface exists per capture, and
completed run buttons are now removed in favor of one clear Close action. The
second pass confirmed visible titles, fully wrapped review/risk/recovery/result
copy, reachable footers, distinct failure/success color plus text labels, no
blank or overlapping regions, and readable System pages at the minimum window.
All data and paths shown in the images are synthetic, and generated PNGs remain
outside the repository.

## Phase 9 semantic-state and motion review

On 2026-09-27, the ten Phase 8 synthetic states were rendered again at their
declared sizes and inspected. The transfer failure capture exposed dim review
field labels and an amber completed progress bar that implied success while its
text said "Operation failed." The shared review now uses readable secondary
text for field names, a red completed failure bar, and an explicit failure
label; the repaired capture was inspected at 740×540. The success result keeps
its distinct teal state and explicit text. No real save was read or operation
executed by the renderer.

The dark palette's primary and secondary text meet a 4.5:1 contrast target
against canvas, surface, raised, and input backgrounds; focus rings meet 3:1
on those surfaces. Disabled text is intentionally exempt from the active-text
target. The smallest type token is 11 px, and workflow labels now use the
readable secondary role. Reduced-motion preference now removes console/tool
dialog fades, animated map travel, pulsing map markers, and decorative map
effects while retaining the final zoom, selection glow, operation result, and
calibration marker. Token, workflow, and reduced-motion tests cover these
contracts.

## Phase 9 responsive and interaction measurements

The offscreen workspace contract was exercised at 1450×800, 1200×750, and
1024×700 on Windows. At 1024 pixels the sidebar collapses to icons and the
inspector uses a drawer; at 1200 pixels the sidebar remains expanded while the
inspector is a drawer; at 1450 pixels both use their wide layout. The
responsive collapse does not overwrite the user's persisted sidebar choice.
Screenshots of the 1024×700 Settings and Tool Center states were inspected
after the change, with visible headings, actions, scrollbars, and no footer
overlap. The existing map bounds and splitter-persistence tests remain part of
the focused verification set.

A user-provided 1450×800 About capture exposed a separate responsive failure:
the seven optional global header actions were squeezed into the 1210 px page
header and their labels clipped. The header now measures the expanded title,
save state, pending state, and action widths before deciding whether to show
the actions or their overflow menu. The 1450×800 shell render with the full
global action set was inspected after the fix: Save Changes, save context,
pending state, and More actions fit on one row, while all seven optional
commands remain in the overflow menu. A width-specific regression test covers
that real action count.

The final world-render pass also caught a one-frame breadcrumb remnant and a
temporarily narrow brand label after responsive layout changes. Retired chips
now hide immediately when routes replace them, and the world capture waits
for Qt to activate the resized layout. The re-rendered 1450×800 Player
Inventory and Base Inventory and 1024×700 Map images show the full brand,
clean breadcrumbs, populated editor controls, and map explorer without a
blank or hybrid shell.

The user performed the required foreground keyboard smoke pass on 2026-09-27
and reported that all steps passed: visible Tab focus through About, Ctrl+K
route selection, Escape focus restoration, Shift+F10 on a selected Map explorer
row after loading the dummy save, and readable Save/More actions at about
1024×700. The desktop control bridge exposed no native app target, so this
manual observation is explicitly user-reported; the route, dialog, context
menu, and size contracts are independently covered by automated tests.

An offscreen synthetic benchmark on 2026-09-27 used 72 route navigations,
30 inspector openings, 30 searches over 250 rows, 30 empty inventory tab
switches, and 30 empty Palbox page changes. Median / p95 times on this host:

| Interaction | Median | p95 | Audit target |
|---|---:|---:|---|
| Sidebar route navigation | 5.72 ms | 7.99 ms | Effectively instant |
| Inspector open/close | 0.18 ms | 0.29 ms | Under 100 ms |
| Search over 250 synthetic rows | 3.00 ms | 4.08 ms | Under 100 ms |
| Empty inventory tab switch | 0.21 ms | 0.81 ms | Under 150 ms where possible |
| Empty Palbox page change | 14.55 ms | 18.75 ms | Smooth |

The user's disposable save was copied into a unique temporary folder before
the populated measurements; the original dummy remained read-only. Its one
player and 218 Palbox entries loaded successfully. A first inventory load took
556 ms, initial Pal editor population took 137 ms, and 15 populated Palbox
page changes measured 13.99 ms median / 107.12 ms p95. Twenty-four inventory
tab switches measured 5.99 ms median / 34.86 ms p95 after lazy loading, with
one 4.1 s first-use outlier. A separate first/warm pass located that cost in
Technology: 3156.63 ms first use, 42.96 ms warm; Missions took 400.94 ms
first use and 26.26 ms warm. The first-use Technology exception is the
creation and styling of the complete technology widget grid on the GUI thread;
Qt widgets must be built there, and the existing page builds it once on demand.
The warm interaction budget is met. Virtualizing this one-time editor grid is
a separate behavior and architecture change, so the measured first-use delay
is retained as an explicit exception to the 150 ms target.

The same temporary copy completed a `SaveManager` automatic-backup save in
914 ms with the normal worker wrapper replaced by a synchronous test adapter
to measure total work. The default application path uses its loading worker
and progress surface. The saved file parsed afterward, a recovery snapshot
was present in the temporary folder, and its SHA-256 remained unchanged. This
profiles one representative larger operation without modifying the original
dummy save.
