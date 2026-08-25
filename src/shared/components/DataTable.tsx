import { useMemo, useState } from "react";
import { EmptyState } from "./EmptyState";

export interface Column<T> {
  readonly key: string;
  readonly header: string | React.ReactNode;
  readonly render: (row: T) => React.ReactNode;
  readonly width?: string;
  readonly sortable?: boolean;
  readonly sortValue?: (row: T) => string | number | boolean;
}

interface DataTableProps<T> {
  readonly columns: readonly Column<T>[];
  readonly rows: readonly T[];
  readonly rowKey: (row: T) => string;
  readonly onRowClick?: (row: T) => void;
  readonly searchValue?: string;
  readonly onSearchChange?: (value: string) => void;
  readonly searchPlaceholder?: string;
  readonly emptyHeadline?: string;
  readonly emptyDescription?: string;
  readonly emptyAction?: {
    readonly label: string;
    readonly onClick: () => void;
  };
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search records…",
  emptyHeadline = "No records found",
  emptyDescription = "There are no entries matching the current filter criteria.",
  emptyAction,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  function handleHeaderClick(col: Column<T>) {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      if (sortDirection === "asc") {
        setSortDirection("desc");
      } else {
        setSortKey(null);
        setSortDirection("asc");
      }
    } else {
      setSortKey(col.key);
      setSortDirection("asc");
    }
  }

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    const col = columns.find((c) => c.key === sortKey);
    if (!col || !col.sortValue) return rows;

    const sorter = col.sortValue;
    return [...rows].sort((a, b) => {
      const valA = sorter(a);
      const valB = sorter(b);
      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [rows, sortKey, sortDirection, columns]);

  return (
    <div className="flex flex-col gap-3">
      {onSearchChange !== undefined && (
        <div className="flex items-center gap-2 border border-shell-line bg-white px-3 py-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 16 16"
            fill="none"
            className="shrink-0 text-shell-muted"
            aria-hidden="true"
          >
            <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.5" />
            <line
              x1="10.5"
              y1="10.5"
              x2="14.5"
              y2="14.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <input
            type="search"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-shell-muted"
            placeholder={searchPlaceholder}
            value={searchValue ?? ""}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchValue && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="text-xs text-shell-muted hover:text-shell-ink"
              aria-label="Clear search"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {sortedRows.length === 0 ? (
        <EmptyState
          headline={emptyHeadline}
          description={emptyDescription}
          action={emptyAction}
        />
      ) : (
        <div className="overflow-x-auto border border-shell-line bg-white">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-shell-line bg-shell-panel">
                {columns.map((col) => {
                  const isSorted = sortKey === col.key;
                  return (
                    <th
                      key={col.key}
                      style={{ width: col.width }}
                      onClick={() => handleHeaderClick(col)}
                      className={[
                        "px-3 py-2.5 text-left font-mono text-[11px] uppercase tracking-wider text-shell-muted select-none",
                        col.sortable ? "cursor-pointer hover:bg-shell-line/40 hover:text-shell-ink" : "",
                      ].join(" ")}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{col.header}</span>
                        {col.sortable && (
                          <span className="text-[10px]" aria-hidden="true">
                            {isSorted ? (
                              sortDirection === "asc" ? "▲" : "▼"
                            ) : (
                              <span className="opacity-30">▲</span>
                            )}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, idx) => (
                <tr
                  key={rowKey(row)}
                  tabIndex={onRowClick ? 0 : undefined}
                  onClick={() => onRowClick?.(row)}
                  onKeyDown={(e) => {
                    if (onRowClick && (e.key === "Enter" || e.key === " ")) {
                      e.preventDefault();
                      onRowClick(row);
                    }
                  }}
                  className={[
                    "border-b border-shell-line transition-colors",
                    idx % 2 === 0 ? "bg-white" : "bg-shell-panel/30",
                    onRowClick
                      ? "cursor-pointer hover:bg-[#edf5f2] focus-visible:bg-[#edf5f2] focus-visible:outline-none"
                      : "hover:bg-shell-panel/60",
                  ].join(" ")}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-3 py-2.5 font-mono text-xs text-shell-ink">
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between border-t border-shell-line bg-shell-panel px-3 py-2">
            <span className="font-mono text-[10px] uppercase text-shell-muted">
              Records: <strong className="text-shell-ink">{sortedRows.length}</strong>
            </span>
            {sortKey && (
              <span className="font-mono text-[10px] text-shell-muted">
                Sorted by {sortKey} ({sortDirection})
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Search filter util ────────────────────────────────────────────────────────
export function useSearchFilter<T>(
  rows: readonly T[],
  predicate: (row: T, q: string) => boolean,
) {
  const [query, setQuery] = useState("");
  const filtered = query.trim()
    ? rows.filter((r) => predicate(r, query.toLowerCase()))
    : rows;
  return { query, setQuery, filtered };
}
