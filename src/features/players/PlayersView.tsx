import { useCallback } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { PlayerProjection } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function PlayersView() {
  const state = useAsync(
    useCallback(() => invokeCommand<readonly PlayerProjection[]>("get_players"), []),
    [],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.displayName.toLowerCase().includes(q) || r.uid.toLowerCase().includes(q),
  );

  return (
    <ViewShell
      title="Players"
      subtitle="All player characters found in the loaded save."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <DataTable
        columns={[
          { key: "uid", header: "UID", render: (r) => <span className="text-shell-muted">{r.uid.slice(0, 16)}…</span>, width: "200px" },
          { key: "name", header: "Name", render: (r) => <span className="font-semibold text-shell-ink">{r.displayName || "—"}</span> },
          { key: "level", header: "Lv", render: (r) => r.level, width: "60px" },
          { key: "hp", header: "HP", render: (r) => `${r.hp} / ${r.maxHp}`, width: "120px" },
          { key: "host", header: "Host", render: (r) => r.isHost ? <Badge color="accent">Host</Badge> : null, width: "80px" },
        ]}
        rows={filtered}
        rowKey={(r) => r.uid}
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder="Filter by name or UID…"
        emptyMessage="No players found. Load a save file first."
      />
    </ViewShell>
  );
}

function Badge({ color, children }: { color: "accent" | "muted"; children: React.ReactNode }) {
  return (
    <span
      className={[
        "rounded-sm px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide",
        color === "accent"
          ? "bg-[#edf5f2] text-shell-accent"
          : "bg-shell-panel text-shell-muted",
      ].join(" ")}
    >
      {children}
    </span>
  );
}
