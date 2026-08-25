import { useCallback } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type { DiagnosticReportDto } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

const SEVERITY_STYLES: Record<string, string> = {
  info: "border-l-2 border-shell-accent bg-[#f4faf7] text-shell-ink",
  warning: "border-l-2 border-amber-400 bg-amber-50 text-amber-900",
  error: "border-l-2 border-red-400 bg-red-50 text-red-900",
};

export function DiagnosticsView() {
  const state = useAsync(
    useCallback(
      () => invokeCommand<DiagnosticReportDto>("run_save_diagnostics"),
      [],
    ),
    [],
  );

  const report = state.status === "ok" ? state.data : null;

  return (
    <ViewShell
      title="Save Diagnostics"
      subtitle="Structural integrity checks on the loaded save file."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      {report && (
        <div className="flex flex-col gap-4">
          {/* Summary bar */}
          <div className="flex flex-wrap gap-3">
            {(["error", "warning", "info"] as const).map((sev) => {
              const count = report.issues.filter((i) => i.severity === sev).length;
              return (
                <div
                  key={sev}
                  className="border border-shell-line bg-white px-4 py-3"
                >
                  <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                    {sev}
                  </p>
                  <p className="mt-1 font-mono text-xl font-semibold text-shell-ink">
                    {count}
                  </p>
                </div>
              );
            })}
            <div className="border border-shell-line bg-white px-4 py-3">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                Scan Duration
              </p>
              <p className="mt-1 font-mono text-xs text-shell-ink">
                {report.scanMeta.scanDurationMs}ms
              </p>
            </div>
            <div className="border border-shell-line bg-white px-4 py-3">
              <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
                Entities Scanned
              </p>
              <p className="mt-1 font-mono text-xs text-shell-ink">
                {report.scanMeta.playerCount}P / {report.scanMeta.guildCount}G / {report.scanMeta.baseCount}B / {report.scanMeta.palCount}Pal / {report.scanMeta.containerCount}C
              </p>
            </div>
          </div>

          {/* Issue list */}
          {report.issues.length === 0 ? (
            <p className="border border-dashed border-shell-line p-6 text-center text-sm text-shell-muted">
              No issues detected. The save looks structurally sound.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {report.issues.map((issue, idx) => (
                // eslint-disable-next-line react/no-array-index-key
                <li
                  key={`${issue.code}-${idx}`}
                  className={[
                    "px-4 py-3",
                    SEVERITY_STYLES[issue.severity] ?? "",
                  ].join(" ")}
                >
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-[10px] uppercase tracking-wide opacity-70">
                      {issue.severity}
                    </span>
                    <span className="font-mono text-xs font-semibold">
                      {issue.code}
                    </span>
                    <span className="font-mono text-[10px] text-shell-muted">
                      {issue.category}
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-6">{issue.message}</p>
                  {issue.context && (
                    <p className="mt-1 font-mono text-[11px] opacity-60">
                      {issue.context}
                    </p>
                  )}
                  {issue.canAutoRepair && issue.repairAction && (
                    <p className="mt-1 font-mono text-[11px] text-emerald-700">
                      Auto-repair: {issue.repairAction.label} ({issue.repairAction.affectedEntityCount} entities)
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </ViewShell>
  );
}
