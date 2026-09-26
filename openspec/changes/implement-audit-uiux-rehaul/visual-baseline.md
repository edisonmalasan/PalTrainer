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
