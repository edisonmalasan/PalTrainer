import { useCallback, useState } from "react";
import { useAsync } from "../../shared/hooks/useAsync";
import type { PalDefenderCommand } from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

export function PalDefenderPanel() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const state = useAsync(
    useCallback(
      () => invokeCommand<PalDefenderCommand[]>("generate_paldefender_commands"),
      [],
    ),
    [],
  );

  const commands = state.status === "ok" ? state.data : [];

  const handleCopy = (cmd: string, index: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(index);
    setTimeout(() => {
      setCopiedIndex(null);
    }, 2000);
  };

  const categories = Array.from(new Set(commands.map((c) => c.category)));

  const filteredCommands = commands.filter((c) => {
    if (selectedCategory !== "all" && c.category !== selectedCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        c.command.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Alert banner */}
      <div className="rounded-xl border border-shell-line bg-shell-card p-4 text-xs leading-relaxed text-shell-ink">
        <p className="font-semibold uppercase tracking-wider text-shell-accent">
          PalDefender & Server RCON Toolset
        </p>
        <p className="mt-1 text-shell-muted">
          Quickly generate and export administration, anti-cheat audit, moderation, and broadcast console commands for PalDefender / Dedicated Server RCON console execution.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-shell-line bg-shell-card/50 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setSelectedCategory("all")}
            className={`rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wide transition ${
              selectedCategory === "all"
                ? "bg-shell-ink text-shell-bg shadow-sm"
                : "border border-shell-line bg-shell-card text-shell-muted hover:text-shell-ink"
            }`}
          >
            All Categories ({commands.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wide transition ${
                selectedCategory === cat
                  ? "bg-shell-ink text-shell-bg shadow-sm"
                  : "border border-shell-line bg-shell-card text-shell-muted hover:text-shell-ink"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative min-w-[220px]">
          <input
            type="text"
            placeholder="Search commands..."
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

      {/* Commands List */}
      <div className="overflow-hidden rounded-xl border border-shell-line bg-shell-card">
        <div className="divide-y divide-shell-line">
          {filteredCommands.map((cmd, idx) => {
            const isCopied = copiedIndex === idx;
            return (
              <div
                key={`${cmd.command}-${idx}`}
                className="flex flex-col justify-between gap-3 p-4 transition hover:bg-shell-bg/50 md:flex-row md:items-center"
              >
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-shell-bg px-2 py-0.5 font-mono text-[10px] font-semibold text-shell-muted">
                      {cmd.category}
                    </span>
                    <code className="rounded bg-shell-panel px-2.5 py-1 font-mono text-xs font-bold text-shell-accent">
                      {cmd.command}
                    </code>
                  </div>
                  <p className="text-xs text-shell-muted">{cmd.description}</p>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopy(cmd.command, idx)}
                  className={`flex shrink-0 items-center gap-1.5 rounded-lg border px-3 py-1.5 font-mono text-xs font-semibold transition active:scale-[0.98] ${
                    isCopied
                      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                      : "border-shell-line bg-shell-bg text-shell-ink hover:border-shell-accent hover:text-shell-accent"
                  }`}
                >
                  {isCopied ? (
                    <>
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
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      Copied!
                    </>
                  ) : (
                    <>
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
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                      </svg>
                      Copy Command
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
