import { useCallback } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { BaseProjection } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function BasesView() {
  const state = useAsync(
    useCallback(() => invokeCommand<readonly BaseProjection[]>("get_bases"), []),
    [],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.baseName.toLowerCase().includes(q) || r.baseId.toLowerCase().includes(q),
  );

  return (
    <ViewShell
      title="Bases"
      subtitle="Base camp locations and levels found in the loaded save."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <DataTable
        columns={[
          { key: "name", header: "Base Name", render: (r) => <span className="font-semibold text-shell-ink">{r.baseName || "—"}</span> },
          { key: "level", header: "Level", render: (r) => r.currentLevel, width: "70px" },
          { key: "workers", header: "Workers", render: (r) => r.workerCount, width: "80px" },
          { key: "pos", header: "World Position", render: (r) => `${r.worldX.toFixed(0)}, ${r.worldY.toFixed(0)}` },
          { key: "guild", header: "Owner Guild", render: (r) => <span className="text-shell-muted">{r.ownerGuildId.slice(0, 12)}…</span> },
        ]}
        rows={filtered}
        rowKey={(r) => r.baseId}
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder="Filter by base name or ID…"
        emptyMessage="No bases found. Load a save file first."
      />
    </ViewShell>
  );
}
