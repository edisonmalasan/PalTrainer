import { useCallback } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { MapMarkerProjection } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function MapView() {
  const state = useAsync(
    useCallback(
      () => invokeCommand<readonly MapMarkerProjection[]>("get_map_markers"),
      [],
    ),
    [],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.label.toLowerCase().includes(q) || r.markerType.toLowerCase().includes(q),
  );

  return (
    <ViewShell
      title="Map Markers"
      subtitle="World-space positions of players, bases, and interest points (Sakurajima coordinate translation applied)."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <DataTable
        columns={[
          { key: "label", header: "Label", render: (r) => <span className="font-semibold text-shell-ink">{r.label || "—"}</span> },
          { key: "type", header: "Type", render: (r) => <span className="text-shell-muted">{r.markerType}</span>, width: "120px" },
          { key: "mapX", header: "Map X", render: (r) => r.mapX.toFixed(3), width: "100px" },
          { key: "mapY", header: "Map Y", render: (r) => r.mapY.toFixed(3), width: "100px" },
          { key: "worldX", header: "World X", render: (r) => r.worldX.toFixed(0), width: "100px" },
          { key: "worldY", header: "World Y", render: (r) => r.worldY.toFixed(0), width: "100px" },
        ]}
        rows={filtered}
        rowKey={(r) => `${r.markerType}:${r.label}:${r.worldX}`}
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder="Filter by label or type…"
        emptyMessage="No map markers found. Load a save file first."
      />
    </ViewShell>
  );
}
