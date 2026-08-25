import { useCallback, useMemo, useState } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { useAsync } from "../../shared/hooks/useAsync";
import type {
  DiagnosticCategory,
  DiagnosticIssue,
  DiagnosticReportDto,
  DiagnosticSeverity,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";
import { CleanupPanel } from "./CleanupPanel";
import { PalDefenderPanel } from "./PalDefenderPanel";
import { RepairPanel } from "./RepairPanel";
import { ResetPanel } from "./ResetPanel";

type DiagnosticTab = "scanner" | "cleanup" | "repair" | "reset" | "paldefender";

const SEVERITY_BADGES: Record<DiagnosticSeverity, { bg: string; text: string; border: string }> = {
  error: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
  },
  warning: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/20",
  },
  info: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
  },
};

const CATEGORY_LABELS: Record<DiagnosticCategory, string> = {
  stale_file: "Stale Files",
  integrity: "Container Integrity",
  orphaned_player: "Orphaned Players",
  duplicate_player: "Duplicate Players",
  broken_guild: "Broken Guilds",
  empty_guild: "Empty Guilds",
  illegal_pal: "Illegal Pals",
  invalid_pal_species: "Invalid Pal Species",
  invalid_passives: "Invalid Passives",
  invalid_active_skills: "Invalid Active Skills",
  unassigned_pal: "Unassigned Worker Pals",
  overfilled_container: "Overfilled Containers",
  invalid_item: "Invalid Items",
  unreferenced_data: "Unreferenced Data",
  invalid_structure: "Invalid Structures",
  stale_timestamp: "Stale Timestamps",
  dynamic_container_link: "Dynamic Containers",
  private_chest_lock: "Private Chest Locks",
  death_bag: "Death Bags",
  imported_dna_pal: "Imported DNA Pals",
  non_base_map_object: "Non-Base Map Objects",
  skin: "Skins & Attachments",
};

export function DiagnosticsView() {
  const [activeTab, setActiveTab] = useState<DiagnosticTab>("scanner");
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [targetedCategory, setTargetedCategory] = useState<DiagnosticCategory | "">("");

  const fetchReport = useCallback(() => {
    if (targetedCategory) {
      return invokeCommand<DiagnosticReportDto>("run_targeted_diagnostic", {
        category: targetedCategory,
      });
    }
    return invokeCommand<DiagnosticReportDto>("run_save_diagnostics");
  }, [targetedCategory]);

  const state = useAsync(fetchReport, [refreshKey, targetedCategory]);
  const report = state.status === "ok" ? state.data : null;

  const filteredIssues = useMemo(() => {
    if (!report) return [];
    return report.issues.filter((issue) => {
      if (selectedSeverity !== "all" && issue.severity !== selectedSeverity) {
        return false;
      }
      if (selectedCategory !== "all" && issue.category !== selectedCategory) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesCode = issue.code.toLowerCase().includes(q);
        const matchesMsg = issue.message.toLowerCase().includes(q);
        const matchesTarget = issue.targetId.toLowerCase().includes(q);
        const matchesCat = (CATEGORY_LABELS[issue.category] ?? issue.category)
          .toLowerCase()
          .includes(q);
        if (!matchesCode && !matchesMsg && !matchesTarget && !matchesCat) {
          return false;
        }
      }
      return true;
    });
  }, [report, selectedSeverity, selectedCategory, searchQuery]);

  return (
    <ViewShell
      title="Save Diagnostics, Cleanup & Repair Suite"
      subtitle="Comprehensive save health auditing, automated maintenance, state recovery, and server administration tools."
      status={state.status}
      errorMessage={state.status === "error" ? state.message : undefined}
    >
      <div className="flex flex-col gap-6">
        {/* Navigation Sub-Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-shell-line pb-3">
          {(
            [
              { id: "scanner", label: "Diagnostic Scanner" },
              { id: "cleanup", label: "Save Cleanup & Deletion" },
              { id: "repair", label: "Structural & State Repair" },
              { id: "reset", label: "World Resets & Gimmicks" },
              { id: "paldefender", label: "PalDefender Console" },
            ] as const
          ).map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-lg px-4 py-2 font-mono text-xs font-semibold tracking-wide transition ${
                  isActive
                    ? "bg-shell-ink text-shell-bg shadow-sm"
                    : "border border-shell-line bg-shell-card text-shell-muted hover:text-shell-ink hover:bg-shell-bg"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Diagnostic Scanner */}
        {activeTab === "scanner" && (
          <div className="flex flex-col gap-6">
            {/* Top Control Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-shell-line bg-shell-card/50 p-4 backdrop-blur-md">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setTargetedCategory("");
                    setRefreshKey((k) => k + 1);
                  }}
                  className="flex items-center gap-2 rounded-lg bg-shell-accent px-4 py-2 text-xs font-semibold text-shell-ink shadow-sm transition hover:bg-shell-accent/90 active:scale-[0.98]"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Re-Scan Full Save
                </button>

                <div className="flex items-center gap-2">
                  <label htmlFor="targeted-scan-select" className="font-mono text-xs text-shell-muted">Targeted Scan:</label>
                  <select
                    id="targeted-scan-select"
                    aria-label="Targeted Scan"
                    value={targetedCategory}
                    onChange={(e) => {
                      setTargetedCategory(e.target.value as DiagnosticCategory | "");
                      setRefreshKey((k) => k + 1);
                    }}
                    className="rounded-lg border border-shell-line bg-shell-bg px-3 py-1.5 font-mono text-xs text-shell-ink focus:border-shell-accent focus:outline-none"
                  >
                    <option value="">All Categories (Full Scan)</option>
                    {Object.entries(CATEGORY_LABELS).map(([catKey, label]) => (
                      <option key={catKey} value={catKey}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Search filter */}
              <div className="relative min-w-[240px]">
                <input
                  type="text"
                  placeholder="Filter findings by code, target..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-shell-line bg-shell-bg py-1.5 pl-8 pr-3 text-xs text-shell-ink placeholder:text-shell-muted focus:border-shell-accent focus:outline-none"
                />
                <svg
                  className="absolute left-2.5 top-2 h-3.5 w-3.5 text-shell-muted"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>

            {report && (
              <>
                {/* Metric Overview Grid */}
                <div className="grid grid-cols-2 gap-4 md:grid-cols-6">
                  <div className="rounded-xl border border-shell-line bg-shell-card p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-shell-muted">
                      Total Findings
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold text-shell-ink">
                      {report.totalIssues}
                    </p>
                  </div>

                  <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-red-400">
                      Critical Errors
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold text-red-400">
                      {report.errors}
                    </p>
                  </div>

                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-amber-400">
                      Warnings
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold text-amber-400">
                      {report.warnings}
                    </p>
                  </div>

                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-emerald-400">
                      Valid / Healthy
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold text-emerald-400">
                      {report.infos}
                    </p>
                  </div>

                  <div className="rounded-xl border border-shell-line bg-shell-card p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-shell-muted">
                      Scan Latency
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold text-shell-ink">
                      {report.scanMeta.scanDurationMs}
                      <span className="text-xs font-normal text-shell-muted"> ms</span>
                    </p>
                  </div>

                  <div className="rounded-xl border border-shell-line bg-shell-card p-4">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-shell-muted">
                      Entity Scope
                    </p>
                    <p className="mt-1 font-mono text-xs leading-relaxed text-shell-ink">
                      {report.scanMeta.playerCount}P / {report.scanMeta.guildCount}G /{" "}
                      {report.scanMeta.baseCount}B / {report.scanMeta.palCount}Pal
                    </p>
                  </div>
                </div>

                {/* Severity Filter Chips */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-shell-muted">Severity:</span>
                  {(["all", "error", "warning", "info"] as const).map((sev) => {
                    const count =
                      sev === "all"
                        ? report.totalIssues
                        : report.issues.filter((i) => i.severity === sev).length;
                    const isSelected = selectedSeverity === sev;
                    return (
                      <button
                        key={sev}
                        type="button"
                        onClick={() => setSelectedSeverity(sev)}
                        className={`rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wide transition ${
                          isSelected
                            ? "bg-shell-ink text-shell-bg shadow-sm"
                            : "border border-shell-line bg-shell-card text-shell-muted hover:text-shell-ink"
                        }`}
                      >
                        {sev} ({count})
                      </button>
                    );
                  })}

                  <div className="mx-2 h-4 w-px bg-shell-line" />

                  <span className="font-mono text-xs text-shell-muted">Category:</span>
                  <select
                    id="scanner-category-filter"
                    aria-label="Scanner Category"
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="rounded-lg border border-shell-line bg-shell-card px-2.5 py-1 font-mono text-xs text-shell-ink focus:border-shell-accent focus:outline-none"
                  >
                    <option value="all">All Categories</option>
                    {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Findings List */}
                {filteredIssues.length === 0 ? (
                  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-shell-line bg-shell-card/30 p-12 text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400">
                      <svg
                        className="h-6 w-6"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                    <p className="mt-4 font-mono text-sm font-semibold text-shell-ink">
                      No issues matching criteria
                    </p>
                    <p className="mt-1 max-w-sm text-xs text-shell-muted">
                      The scanned save elements meet all integrity and structural constraints for the selected filters.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-xl border border-shell-line bg-shell-card">
                    <div className="divide-y divide-shell-line">
                      {filteredIssues.map((issue: DiagnosticIssue, idx: number) => {
                        const badge = SEVERITY_BADGES[issue.severity];
                        return (
                          <div
                            key={`${issue.code}-${idx}`}
                            className="flex flex-col gap-2 p-4 transition hover:bg-shell-bg/50"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`rounded border px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider ${badge.bg} ${badge.text} ${badge.border}`}
                                >
                                  {issue.severity}
                                </span>
                                <span className="font-mono text-xs font-semibold text-shell-ink">
                                  {issue.code}
                                </span>
                                <span className="rounded-full bg-shell-bg px-2 py-0.5 font-mono text-[10px] text-shell-muted">
                                  {CATEGORY_LABELS[issue.category] ?? issue.category}
                                </span>
                              </div>

                              <span className="font-mono text-[11px] text-shell-muted">
                                Target:{" "}
                                <span className="font-semibold text-shell-ink">
                                  {issue.targetId}
                                </span>
                              </span>
                            </div>

                            <p className="text-xs leading-relaxed text-shell-ink/90">
                              {issue.message}
                            </p>

                            {issue.context && (
                              <p className="rounded bg-shell-bg/70 p-2 font-mono text-[11px] text-shell-muted">
                                {issue.context}
                              </p>
                            )}

                            {issue.canAutoRepair && issue.repairAction && (
                              <div className="mt-1 flex items-center gap-2 font-mono text-[11px] text-emerald-500">
                                <svg
                                  className="h-3.5 w-3.5"
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 10V3L4 14h7v7l9-11h-7z"
                                  />
                                </svg>
                                <span>
                                  Repairable: {issue.repairAction.label} (
                                  {issue.repairAction.affectedEntityCount} entities)
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Tab 2: Save Cleanup & Deletion */}
        {activeTab === "cleanup" && <CleanupPanel />}

        {/* Tab 3: Structural & State Repair */}
        {activeTab === "repair" && <RepairPanel />}

        {/* Tab 4: World Resets & Gimmicks */}
        {activeTab === "reset" && <ResetPanel />}

        {/* Tab 5: PalDefender Console */}
        {activeTab === "paldefender" && <PalDefenderPanel />}
      </div>
    </ViewShell>
  );
}
