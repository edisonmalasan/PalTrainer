import { useCallback, useState } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  ExclusionConfig,
  MapMarkerProjection,
  ZoneExclusion,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function MapView() {
  const [reloadKey, setReloadKey] = useState(0);

  const markerState = useAsync(
    useCallback(() => invokeCommand<readonly MapMarkerProjection[]>("get_map_markers"), []),
    [reloadKey],
  );

  const configState = useAsync(
    useCallback(() => invokeCommand<ExclusionConfig>("get_exclusion_config"), []),
    [reloadKey],
  );

  const markers = markerState.status === "ok" ? markerState.data : [];
  const exclusions = configState.status === "ok" ? configState.data : null;

  const { query, setQuery, filtered } = useSearchFilter(
    markers,
    (r, q) =>
      r.label.toLowerCase().includes(q) || r.markerType.toLowerCase().includes(q),
  );

  // New Zone Drawer State
  const [showAddZone, setShowAddZone] = useState(false);
  const [newZoneName, setNewZoneName] = useState("");
  const [newZoneType, setNewZoneType] = useState<"rectangle" | "polygon">("rectangle");
  const [rectPoints, setRectPoints] = useState({ minX: 0, minY: 0, maxX: 100000, maxY: 100000 });
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
      <div className="flex flex-col gap-6">
        {/* Exclusion Zone Management Panel */}
        <div className="border border-shell-line bg-white p-5">
          <div className="flex items-center justify-between border-b border-shell-line pb-3">
            <div>
              <h3 className="text-base font-semibold">Exclusion Zones & Protection</h3>
              <p className="mt-1 text-xs text-shell-muted">
                Entities inside active exclusion zones will be skipped during automated cleanup and deletion sweeps.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowAddZone(!showAddZone)}
              className="border border-shell-line bg-white px-3 py-1.5 font-mono text-xs text-shell-ink transition hover:bg-shell-panel active:translate-y-[1px]"
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
                    onChange={(e) => setNewZoneType(e.target.value as "rectangle" | "polygon")}
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
                      onChange={(e) => setRectPoints({ ...rectPoints, minX: Number(e.target.value) })}
                      className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                    />
                    <input
                      type="number"
                      placeholder="Min Y"
                      value={rectPoints.minY}
                      onChange={(e) => setRectPoints({ ...rectPoints, minY: Number(e.target.value) })}
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
                      onChange={(e) => setRectPoints({ ...rectPoints, maxX: Number(e.target.value) })}
                      className="w-1/2 border border-shell-line px-2 py-1 font-mono text-xs"
                    />
                    <input
                      type="number"
                      placeholder="Max Y"
                      value={rectPoints.maxY}
                      onChange={(e) => setRectPoints({ ...rectPoints, maxY: Number(e.target.value) })}
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
                  className="border border-shell-accent bg-[#edf5f2] px-3 py-1 font-mono text-xs font-semibold text-shell-accent hover:bg-[#d9ede7] active:translate-y-[1px] disabled:opacity-50"
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
            {(!exclusions || exclusions.zones.length === 0) ? (
              <p className="mt-2 text-xs text-shell-muted">No exclusion zones configured.</p>
            ) : (
              <div className="mt-2 grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                {exclusions.zones.map((z) => (
                  <div key={z.id} className="flex items-center justify-between border border-shell-line bg-shell-panel p-2.5">
                    <div>
                      <p className="font-semibold text-xs text-shell-ink">{z.name}</p>
                      <p className="font-mono text-[10px] text-shell-muted">{z.zoneType} · {z.points.length} pts</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleRemoveZone(z.id)}
                      className="text-xs text-red-600 hover:text-red-800"
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
                onChange={(e) => setTestCoord({ ...testCoord, x: Number(e.target.value) })}
                className="w-32 border border-shell-line px-2.5 py-1 font-mono text-xs"
              />
              <input
                type="number"
                placeholder="World Y"
                value={testCoord.y}
                onChange={(e) => setTestCoord({ ...testCoord, y: Number(e.target.value) })}
                className="w-32 border border-shell-line px-2.5 py-1 font-mono text-xs"
              />
              <button
                type="button"
                onClick={() => void handleTestCoordinate()}
                className="border border-shell-line bg-white px-3 py-1 font-mono text-xs hover:bg-shell-panel active:translate-y-[1px]"
              >
                Check
              </button>
              {testResult !== null && (
                <span
                  className={[
                    "font-mono text-xs font-semibold uppercase px-2 py-0.5 rounded-sm",
                    testResult ? "bg-amber-100 text-amber-900" : "bg-[#edf5f2] text-shell-accent",
                  ].join(" ")}
                >
                  {testResult ? "Excluded (Protected)" : "Not Excluded"}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Map Markers Table */}
        <DataTable
          columns={[
            {
              key: "label",
              header: "Label",
              render: (r) => <span className="font-semibold text-shell-ink">{r.label || "—"}</span>,
            },
            {
              key: "type",
              header: "Type",
              render: (r) => <span className="text-shell-muted">{r.markerType}</span>,
              width: "120px",
            },
            { key: "mapX", header: "Map X", render: (r) => r.mapX.toFixed(3), width: "100px" },
            { key: "mapY", header: "Map Y", render: (r) => r.mapY.toFixed(3), width: "100px" },
            { key: "worldX", header: "World X", render: (r) => r.worldX.toFixed(0), width: "100px" },
            { key: "worldY", header: "World Y", render: (r) => r.worldY.toFixed(0), width: "100px" },
          ]}
          rows={filtered}
          rowKey={(r) => `${r.markerType}:${r.label}:${r.worldX}`}
          searchValue={query}
          onSearchChange={setQuery}
          searchPlaceholder="Filter by label or marker type…"
          emptyMessage="No map markers found. Load a save file first."
        />
      </div>
    </ViewShell>
  );
}
