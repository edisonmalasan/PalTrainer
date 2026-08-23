import { useCallback } from "react";
import { DataTable, useSearchFilter } from "../../shared/components/DataTable";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { GuildProjection } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function GuildsView() {
  const state = useAsync(
    useCallback(() => invokeCommand<readonly GuildProjection[]>("get_guilds"), []),
    [],
  );

  const rows = state.status === "ok" ? state.data : [];
  const { query, setQuery, filtered } = useSearchFilter(
    rows,
    (r, q) =>
      r.guildName.toLowerCase().includes(q) || r.guildId.toLowerCase().includes(q),
  );

  return (
    <ViewShell
      title="Guilds"
      subtitle="Guild memberships and leadership extracted from the loaded save."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <DataTable
        columns={[
          { key: "id", header: "Guild ID", render: (r) => <span className="text-shell-muted">{r.guildId.slice(0, 16)}…</span>, width: "200px" },
          { key: "name", header: "Name", render: (r) => <span className="font-semibold text-shell-ink">{r.guildName || "—"}</span> },
          { key: "admin", header: "Admin UID", render: (r) => <span className="text-shell-muted">{r.adminUid.slice(0, 12)}…</span>, width: "160px" },
          { key: "members", header: "Members", render: (r) => r.members.length, width: "90px" },
        ]}
        rows={filtered}
        rowKey={(r) => r.guildId}
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder="Filter by guild name or ID…"
        emptyMessage="No guilds found. Load a save file first."
      />
    </ViewShell>
  );
}
