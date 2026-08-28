import { useCallback, useRef, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { PreviewModal } from "../../shared/components/PreviewModal";
import { ViewShell } from "../../shared/components/ViewShell";
import { MapCanvas } from "./MapCanvas";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  ExclusionConfig,
  MapDataProjection,
  MoveBaseToMapDto,
  MovePlayerToMapDto,
  MutationPreview,
  Point2D,
  UpdateBaseAreaRangeDto,
  ZoneExclusion,
  ZoneExclusionFromMapDto,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

type MarkerFilter = "Bases" | "Players";

export function MapView() {
  const [reloadKey, setReloadKey] = useState(0);
  const [markerFilter, setMarkerFilter] = useState<MarkerFilter>("Bases");
  const [pendingPreview, setPendingPreview] = useState<MutationPreview | null>(null);
  const [committing, setCommitting] = useState(false);
  const pendingCommitRef = useRef<(() => Promise<void>) | null>(null);

  const markerState = useAsync(
    useCallback(() => invokeCommand<MapDataProjection>("get_map_markers"), []),
    [reloadKey],
  );

  const configState = useAsync(
    useCallback(() => invokeCommand<ExclusionConfig>("get_exclusion_config"), []),
    [reloadKey],
  );

  const markers = markerState.status === "ok" ? markerState.data.markers : [];
  const visibleMarkers = markers.filter((m) =>
    markerFilter === "Bases" ? m.markerType === "Base" : m.markerType === "Player",
  );
  const exclusions = configState.status === "ok" ? configState.data : null;

  async function openMovePreview(
    marker: (typeof markers)[number],
    mapX: number,
    mapY: number,
  ) {
    try {
      if (marker.markerType === "Base") {
        const dto: MoveBaseToMapDto = { baseId: marker.id, mapX, mapY };
        const preview = await invokeCommand<MutationPreview>(
          "preview_move_base_to_map",
          {
            dto,
          },
        );
        pendingCommitRef.current = async () => {
          await invokeCommand("commit_move_base_to_map", { dto });
          setReloadKey((k) => k + 1);
        };
        setPendingPreview(preview);
      } else {
        const dto: MovePlayerToMapDto = { uid: marker.id, mapX, mapY };
        const preview = await invokeCommand<MutationPreview>(
          "preview_move_player_to_map",
          {
            dto,
          },
        );
        pendingCommitRef.current = async () => {
          await invokeCommand("commit_move_player_to_map", { dto });
          setReloadKey((k) => k + 1);
        };
        setPendingPreview(preview);
      }
    } catch (err: unknown) {
      console.error("Failed to preview marker move", err);
    }
  }

  async function openAreaRangePreview(
    marker: (typeof markers)[number],
    areaRange: number,
  ) {
    if (marker.markerType !== "Base") return;
    try {
      const dto: UpdateBaseAreaRangeDto = { baseId: marker.id, areaRange };
      const preview = await invokeCommand<MutationPreview>(
        "preview_update_base_area_range",
        {
          dto,
        },
      );
      pendingCommitRef.current = async () => {
        await invokeCommand("commit_update_base_area_range", { dto });
        setReloadKey((k) => k + 1);
      };
      setPendingPreview(preview);
    } catch (err: unknown) {
      console.error("Failed to preview area range update", err);
    }
  }

  async function handleConfirmPending() {
    setCommitting(true);
    try {
      await pendingCommitRef.current?.();
      setPendingPreview(null);
      pendingCommitRef.current = null;
    } finally {
      setCommitting(false);
    }
  }

  const { query, setQuery, filtered } = useSearchFilter(
    visibleMarkers,
    (r, q) =>
      r.label.toLowerCase().includes(q) || r.markerType.toLowerCase().includes(q),
  );

  // New Zone Drawer State
  const [showAddZone, setShowAddZone] = useState(false);
  const [newZoneName, setNewZoneName] = useState("");
  const [newZoneType, setNewZoneType] = useState<"rectangle" | "polygon">("rectangle");
  const [rectPoints, setRectPoints] = useState({
    minX: 0,
    minY: 0,
    maxX: 100000,
    maxY: 100000,
  });
  const [protectBases, setProtectBases] = useState(true);
  const [protectPlayers, setProtectPlayers] = useState(true);

  // Coordinate test tool
  const [testCoord, setTestCoord] = useState({ x: 0, y: 0 });
  const [testResult, setTestResult] = useState<boolean | null>(null);

  async function handleAddZone() {
    if (!newZoneName.trim()) return;
    const newZone: ZoneExclusion = {
      id: `zone_${Date.now()}`,
      name: newZoneName.trim(),
      zoneType: newZoneType,
      points: [
        { x: Number(rectPoints.minX), y: Number(rectPoints.minY) },
        { x: Number(rectPoints.maxX), y: Number(rectPoints.maxY) },
      ],
      protectBases,
      protectPlayers,
      protectStructures: true,
    };

    try {
      await invokeCommand("add_zone_exclusion", { zone: newZone });
      setShowAddZone(false);
      setNewZoneName("");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      console.error("Failed to add zone", err);
    }
  }

  async function handleRemoveZone(zoneId: string) {
    try {
      await invokeCommand("remove_zone_exclusion", { zoneId });
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      console.error("Failed to remove zone", err);
    }
  }

  // A zone drawn on the canvas arrives in post-Sakurajima map-grid units; the
  // backend converts the corners to world coordinates before persisting.
  async function handleZoneDrawn(
    zoneType: "rectangle" | "polygon",
    points: readonly Point2D[],
  ) {
    try {
      const draft: ZoneExclusionFromMapDto = {
        name: `Zone ${(exclusions?.zones.length ?? 0) + 1}`,
        zoneType,
        points,
        protectBases: true,
        protectPlayers: true,
        protectStructures: true,
      };
      await invokeCommand("add_zone_exclusion_from_map", { zone: draft });
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      console.error("Failed to add drawn zone", err);
    }
  }

  async function handleTestCoordinate() {
    try {
      const isExcluded = await invokeCommand<boolean>("check_coordinate_excluded", {
        worldX: Number(testCoord.x),
        worldY: Number(testCoord.y),
      });
      setTestResult(isExcluded);
    } catch (err: unknown) {
      console.error("Failed to test coordinate", err);
    }
  }

  return (
    <ViewShell
      title="Map & Exclusions"
      subtitle="World markers (Sakurajima calibrated) and persistent zone exclusions for safe world cleanup."
      status={markerState.status}
      errorMessage={markerState.status === "error" ? markerState.message : undefined}
    >
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[62fr_38fr]">
        {/* Canvas — 62% left split (phase 16 outcome) */}
        <section
          className="border border-shell-line bg-shell-surface lg:sticky lg:top-4 lg:h-[calc(100dvh-190px)]"
          aria-label="World map canvas"
        >
          <MapCanvas
            markers={visibleMarkers}
            zones={exclusions?.zones ?? []}
            onMoveMarker={(marker, mapX, mapY) =>
              void openMovePreview(marker, mapX, mapY)
            }
            onAreaRangeChange={(marker, areaRange) =>
              void openAreaRangePreview(marker, areaRange)
            }
            onZoneDrawn={(zoneType, points) => void handleZoneDrawn(zoneType, points)}
          />
        </section>

        {/* Map Browser — 38% right split */}
        <aside className="flex min-w-0 flex-col gap-6">
          {/* Exclusion Zone Management Panel */}
          <div className="border border-shell-line bg-shell-surface p-5">
            <div className="flex items-center justify-between border-b border-shell-line pb-3">
              <div>
                <h3 className="text-base font-semibold">
                  Exclusion Zones & Protection
                </h3>
                <p className="mt-1 text-xs text-shell-muted">
                  Entities inside active exclusion zones will be skipped during
                  automated cleanup and deletion sweeps.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowAddZone(!showAddZone)}
                className="border border-shell-line bg-shell-surface px-3 py-1.5 font-mono text-xs text-shell-ink transition hover:bg-shell-panel active:translate-y-[1px]"
              >
                {showAddZone ? "Cancel" : "+ Add Exclusion Zone"}
              </button>
            </div>

            {/* Add Zone Drawer */}
            {showAddZone && (
              <div className="mt-4 border-b border-shell-line pb-4">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-shell-muted">
                  Define New Exclusion Zone
                </h4>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
                  <label className="grid gap-1 text-xs font-medium">
                    <span>Zone Name</span>
                    <input
                      type="text"
                      placeholder="e.g. Spawn Sanctuary"
                      value={newZoneName}
                      onChange={(e) => setNewZoneName(e.target.value)}
                      className="border border-shell-line px-2.5 py-1.5 font-mono text-xs"
                    />
                  </label>

                  <label className="grid gap-1 text-xs font-medium">
                    <span>Zone Geometry</span>
                    <select
                      value={newZoneType}
                      onChange={(e) =>
                        setNewZoneType(e.target.value as "rectangle" | "polygon")
                      }
                      className="border border-shell-line px-2.5 py-1.5 text-xs"
                    >
                      <option value="rectangle">Rectangle (2 points)</option>
                      <option value="polygon">Polygon</option>
                    </select>
                  </label>

                  <label className="grid gap-1 text-xs font-medium">
                    <span>Min X / Min Y</span>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        placeholder="Min X"
                        value={rectPoints.minX}
                        onChange={(e) =>
                          setRectPoints({ ...rectPoints, minX: Number(e.target.value) })
                        }
                        className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                      />
                      <input
                        type="number"
                        placeholder="Min Y"
                        value={rectPoints.minY}
                        onChange={(e) =>
                          setRectPoints({ ...rectPoints, minY: Number(e.target.value) })
                        }
                        className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                      />
                    </div>
                  </label>

                  <label className="grid gap-1 text-xs font-medium">
                    <span>Max X / Max Y</span>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        placeholder="Max X"
                        value={rectPoints.maxX}
                        onChange={(e) =>
                          setRectPoints({ ...rectPoints, maxX: Number(e.target.value) })
                        }
                        className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                      />
                      <input
                        type="number"
                        placeholder="Max Y"
                        value={rectPoints.maxY}
                        onChange={(e) =>
                          setRectPoints({ ...rectPoints, maxY: Number(e.target.value) })
                        }
                        className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                      />
                    </div>
                  </label>
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <div className="flex gap-4 text-xs">
                    <label className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={protectBases}
                        onChange={(e) => setProtectBases(e.target.checked)}
                      />
                      <span>Protect Bases</span>
                    </label>
                    <label className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={protectPlayers}
                        onChange={(e) => setProtectPlayers(e.target.checked)}
                      />
                      <span>Protect Players</span>
                    </label>
                  </div>
                  <button
                    type="button"
                    disabled={!newZoneName.trim()}
                    onClick={() => void handleAddZone()}
                    className="border border-shell-accent-solid bg-shell-accent-solid-subtle px-3 py-1 font-mono text-xs font-semibold text-shell-accent hover:bg-shell-accent-subtle-hover active:translate-y-[1px] disabled:opacity-50"
                  >
                    Save Zone
                  </button>
                </div>
              </div>
            )}

            {/* Active Zones List */}
            <div className="mt-4">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                Active Zones ({exclusions?.zones.length ?? 0})
              </p>
              {!exclusions || exclusions.zones.length === 0 ? (
                <p className="mt-2 text-xs text-shell-muted">
                  No exclusion zones configured.
                </p>
              ) : (
                <div className="mt-2 grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {exclusions.zones.map((z) => (
                    <div
                      key={z.id}
                      className="flex items-center justify-between border border-shell-line bg-shell-panel p-2.5"
                    >
                      <div>
                        <p className="font-semibold text-xs text-shell-ink">{z.name}</p>
                        <p className="font-mono text-[10px] text-shell-muted">
                          {z.zoneType} · {z.points.length} pts
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleRemoveZone(z.id)}
                        className="text-xs text-shell-destructive hover:text-shell-destructive"
                        title="Delete zone"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Coordinate Exclusion Tester */}
            <div className="mt-5 border-t border-shell-line pt-4">
              <h4 className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                Test Coordinate for Exclusion
              </h4>
              <div className="mt-2 flex items-center gap-3">
                <input
                  type="number"
                  placeholder="World X"
                  value={testCoord.x}
                  onChange={(e) =>
                    setTestCoord({ ...testCoord, x: Number(e.target.value) })
                  }
                  className="w-32 border border-shell-line px-2.5 py-1 font-mono text-xs"
                />
                <input
                  type="number"
                  placeholder="World Y"
                  value={testCoord.y}
                  onChange={(e) =>
                    setTestCoord({ ...testCoord, y: Number(e.target.value) })
                  }
                  className="w-32 border border-shell-line px-2.5 py-1 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => void handleTestCoordinate()}
                  className="border border-shell-line bg-shell-surface px-3 py-1 font-mono text-xs hover:bg-shell-panel active:translate-y-[1px]"
                >
                  Check
                </button>
                {testResult !== null && (
                  <span
                    className={[
                      "font-mono text-xs font-semibold uppercase px-2 py-0.5 rounded-sm",
                      testResult
                        ? "bg-shell-warning-subtle text-shell-warning"
                        : "bg-shell-accent-subtle text-shell-accent",
                    ].join(" ")}
                  >
                    {testResult ? "Excluded (Protected)" : "Not Excluded"}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Bases | Players toggle (phase 16 outcome) */}
          <div
            className="flex border border-shell-line bg-shell-surface font-mono text-xs"
            role="tablist"
            aria-label="Marker filter"
          >
            {(["Bases", "Players"] as const).map((option) => (
              <button
                key={option}
                type="button"
                role="tab"
                aria-selected={markerFilter === option}
                onClick={() => setMarkerFilter(option)}
                className={[
                  "flex-1 px-3 py-1.5 uppercase tracking-wide transition-colors",
                  markerFilter === option
                    ? "bg-shell-accent-subtle text-shell-accent"
                    : "text-shell-muted hover:bg-shell-panel hover:text-shell-ink",
                ].join(" ")}
              >
                {option}
              </button>
            ))}
          </div>

          {/* Map Markers Table */}
          <DataTable
            columns={[
              {
                key: "label",
                header: "Label",
                render: (r) => (
                  <span className="font-semibold text-shell-ink">{r.label || "—"}</span>
                ),
              },
              {
                key: "type",
                header: "Type",
                render: (r) => <span className="text-shell-muted">{r.markerType}</span>,
                width: "120px",
              },
              {
                key: "mapX",
                header: "Map X",
                render: (r) => r.mapX.toFixed(3),
                width: "100px",
              },
              {
                key: "mapY",
                header: "Map Y",
                render: (r) => r.mapY.toFixed(3),
                width: "100px",
              },
              {
                key: "worldX",
                header: "World X",
                render: (r) => r.worldX.toFixed(0),
                width: "100px",
              },
              {
                key: "worldY",
                header: "World Y",
                render: (r) => r.worldY.toFixed(0),
                width: "100px",
              },
            ]}
            rows={filtered}
            rowKey={(r) => `${r.markerType}:${r.label}:${r.worldX}`}
            searchValue={query}
            onSearchChange={setQuery}
            searchPlaceholder="Filter by label or marker type…"
            emptyHeadline="No map markers found"
            emptyDescription="Load a save file first to view map markers."
          />
        </aside>
      </div>

      <PreviewModal
        preview={pendingPreview}
        committing={committing}
        onCancel={() => {
          setPendingPreview(null);
          pendingCommitRef.current = null;
        }}
        onConfirm={handleConfirmPending}
      />
    </ViewShell>
  );
}
