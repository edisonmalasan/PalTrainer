import { useCallback } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { PalProjection } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function PalsView() {
  const state = useAsync(
    useCallback(() => invokeCommand<readonly PalProjection[]>("get_pals"), []),
    [],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      (r.nickname || r.palId).toLowerCase().includes(q) ||
      r.palId.toLowerCase().includes(q),
  );

  return (
    <ViewShell
      title="Pals"
      subtitle="All Pal instances from the loaded save. Read-only view."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <DataTable
        columns={[
          { key: "palId", header: "Pal ID", render: (r) => <span className="text-shell-muted">{r.palId}</span>, width: "160px" },
          { key: "nickname", header: "Nickname", render: (r) => <span className="font-semibold text-shell-ink">{r.nickname || "—"}</span> },
          { key: "level", header: "Lv", render: (r) => r.level, width: "50px" },
          { key: "gender", header: "Gender", render: (r) => r.gender, width: "80px" },
          { key: "rank", header: "Rank", render: (r) => r.rank, width: "60px" },
          { key: "hp", header: "HP", render: (r) => `${r.hp}/${r.maxHp}`, width: "110px" },
          { key: "passives", header: "Passives", render: (r) => r.passive_skills.join(", ") || "—" },
        ]}
        rows={filtered}
        rowKey={(r) => r.instanceId}
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder="Filter by Pal ID or nickname…"
        emptyMessage="No Pals found. Load a save file first."
      />
    </ViewShell>
  );
}
