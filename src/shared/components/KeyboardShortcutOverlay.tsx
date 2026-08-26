import { useEffect } from "react";

interface ShortcutGroup {
  readonly title: string;
  readonly shortcuts: readonly {
    readonly keys: readonly string[];
    readonly description: string;
  }[];
}

const SHORTCUT_GROUPS: readonly ShortcutGroup[] = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: ["Ctrl", "1"], description: "Jump to Save Session view" },
      { keys: ["Ctrl", "2"], description: "Jump to World Options view" },
      { keys: ["Ctrl", "3"], description: "Jump to Players view" },
      { keys: ["Ctrl", "4"], description: "Jump to Guilds view" },
      { keys: ["Ctrl", "5"], description: "Jump to Bases view" },
      { keys: ["Ctrl", "6"], description: "Jump to Pals view" },
      { keys: ["Ctrl", "7"], description: "Jump to Inventory view" },
      { keys: ["Ctrl", "8"], description: "Jump to Map view" },
      { keys: ["Ctrl", "9"], description: "Jump to Breeding / Diagnostics view" },
      { keys: ["Ctrl", "0"], description: "Jump to Tools Workbench view" },
    ],
  },
  {
    title: "Global Actions & Dialogs",
    shortcuts: [
      { keys: ["?"], description: "Toggle this keyboard shortcuts cheat sheet" },
      { keys: ["Esc"], description: "Dismiss active modal or clear selection" },
      { keys: ["Ctrl", "Enter"], description: "Confirm & commit pending mutation preview" },
      { keys: ["Tab"], description: "Navigate between interactive controls" },
    ],
  },
  {
    title: "Tables & Data Lists",
    shortcuts: [
      { keys: ["Enter", "Space"], description: "Select highlighted row or execute row action" },
      { keys: ["▲", "▼"], description: "Sort column (click header or focus)" },
    ],
  },
];

interface KeyboardShortcutOverlayProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
}

export function KeyboardShortcutOverlay({
  isOpen,
  onClose,
}: KeyboardShortcutOverlayProps) {
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-dialog-title"
    >
      <div className="flex max-h-[85vh] w-full max-w-2xl flex-col border border-shell-line bg-shell-surface shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-shell-line px-5 py-4">
          <div>
            <h3
              id="shortcuts-dialog-title"
              className="text-base font-semibold tracking-tight text-shell-ink"
            >
              Keyboard Shortcuts &amp; Accessibility
            </h3>
            <p className="text-xs text-shell-muted">
              Quick keyboard navigation and productivity commands in PalTrainer.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="border border-shell-line bg-shell-panel px-2.5 py-1 text-xs font-medium text-shell-muted hover:bg-shell-surface hover:text-shell-ink"
          >
            Close (Esc)
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title}>
              <h4 className="font-mono text-[11px] font-semibold uppercase tracking-wider text-shell-accent">
                {group.title}
              </h4>
              <div className="mt-2 divide-y divide-shell-line/60 border border-shell-line bg-shell-panel">
                {group.shortcuts.map((sc, i) => (
                  <div
                    key={`${sc.description}-${i}`}
                    className="flex items-center justify-between px-3.5 py-2 text-xs"
                  >
                    <span className="text-shell-ink">{sc.description}</span>
                    <div className="flex items-center gap-1 font-mono">
                      {sc.keys.map((k) => (
                        <kbd
                          key={k}
                          className="rounded-sm border border-shell-line bg-shell-surface px-1.5 py-0.5 text-[11px] font-semibold text-shell-ink shadow-xs"
                        >
                          {k}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-shell-line bg-shell-panel px-5 py-3 text-xs text-shell-muted">
          <span>Press <kbd className="font-mono font-semibold">?</kbd> anywhere to open this dialog</span>
          <button
            type="button"
            onClick={onClose}
            className="border border-shell-accent-solid bg-shell-accent-solid px-4 py-1 text-xs font-semibold uppercase tracking-wider text-white hover:bg-shell-accent-solid-hover active:translate-y-[1px]"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
