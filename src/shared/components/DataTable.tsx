import { useState } from "react";

interface Column<T> {
  readonly key: string;
  readonly header: string;
  readonly render: (row: T) => React.ReactNode;
  readonly width?: string;
}

interface DataTableProps<T> {
  readonly columns: readonly Column<T>[];
  readonly rows: readonly T[];
  readonly rowKey: (row: T) => string;
  readonly searchValue?: string;
  readonly onSearchChange?: (value: string) => void;
  readonly searchPlaceholder?: string;
  readonly emptyMessage?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search…",
  emptyMessage = "No records found.",
}: DataTableProps<T>) {
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
            <line x1="10.5" y1="10.5" x2="14.5" y2="14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="search"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-shell-muted"
            placeholder={searchPlaceholder}
            value={searchValue ?? ""}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
      )}

      {rows.length === 0 ? (
        <p className="border border-dashed border-shell-line p-6 text-center text-sm text-shell-muted">
          {emptyMessage}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-shell-line bg-shell-panel">
                {columns.map((col) => (
                  <th
                    key={col.key}
                    style={{ width: col.width }}
                    className="px-3 py-2 text-left font-mono text-[11px] uppercase tracking-wide text-shell-muted"
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr
                  key={rowKey(row)}
                  className={[
                    "border-b border-shell-line transition-colors",
                    idx % 2 === 0 ? "bg-white" : "bg-shell-panel/40",
                    "hover:bg-[#edf5f2]",
                  ].join(" ")}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-3 py-2 font-mono text-xs">
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-right font-mono text-[10px] text-shell-muted">
            {rows.length} record{rows.length !== 1 ? "s" : ""}
          </p>
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
