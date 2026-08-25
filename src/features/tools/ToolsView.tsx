import { useState } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { ConverterPanel } from "./ConverterPanel";
import { ModifiersPanel } from "./ModifiersPanel";
import { TransferPanel } from "./TransferPanel";
import { XgpPanel } from "./XgpPanel";

type ToolsTab = "converter" | "modifiers" | "transfer" | "xgp";

const TABS: readonly { readonly id: ToolsTab; readonly label: string; readonly description: string }[] = [
  {
    id: "converter",
    label: "ID & Save Converter",
    description: "SteamID/UID calculator and SAV-JSON format conversion",
  },
  {
    id: "modifiers",
    label: "Save Modifiers",
    description: "Map fog restore and Palbox slot injection",
  },
  {
    id: "transfer",
    label: "Character Transfer",
    description: "Cross-world migration and host save fix",
  },
  {
    id: "xgp",
    label: "Xbox / GamePass",
    description: "XGP container discovery, extraction, and packaging",
  },
];

export function ToolsView() {
  const [activeTab, setActiveTab] = useState<ToolsTab>("converter");

  return (
    <ViewShell
      title="Tools Workbench"
      description="Advanced save utilities, platform adapters, and conversion tools for Palworld save files."
    >
      {/* ── Tab Navigation ────────────────────────────────────────────── */}
      <div className="flex gap-0.5 border-b border-shell-line">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            id={`tools-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "group border-b-2 px-4 py-3 text-left transition",
              activeTab === tab.id
                ? "border-shell-accent bg-white"
                : "border-transparent hover:border-shell-line hover:bg-shell-panel",
            ].join(" ")}
          >
            <span
              className={[
                "block text-xs font-semibold uppercase tracking-wider",
                activeTab === tab.id
                  ? "text-shell-accent"
                  : "text-shell-muted group-hover:text-shell-ink",
              ].join(" ")}
            >
              {tab.label}
            </span>
            <span className="mt-0.5 block text-[11px] text-shell-muted">
              {tab.description}
            </span>
          </button>
        ))}
      </div>

      {/* ── Tab Content ────────────────────────────────────────────── */}
      <div className="mt-6">
        {activeTab === "converter" && <ConverterPanel />}
        {activeTab === "modifiers" && <ModifiersPanel />}
        {activeTab === "transfer" && <TransferPanel />}
        {activeTab === "xgp" && <XgpPanel />}
      </div>
    </ViewShell>
  );
}
