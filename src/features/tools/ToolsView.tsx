import { useState } from "react";
import { ViewShell } from "../../shared/components/ViewShell";
import { ConverterPanel } from "./ConverterPanel";
import { ModifiersPanel } from "./ModifiersPanel";
import { TransferPanel } from "./TransferPanel";
import { XgpPanel } from "./XgpPanel";

// The phase-18 Bento outcome: two 2×2 grids. Conversion Tools hold the
// top-level converter workflows; Management Tools hold slot / transfer /
// host-save workflows. Selecting a card scrolls to the matching tab+section.
type ToolsTab = "converter" | "modifiers" | "transfer" | "xgp";
type ToolsSectionId =
  "converter-formats" | "converter-restore-map" | "converter-xgp" | "converter-steamid";

interface ToolCard {
  readonly id: ToolsSectionId;
  readonly label: string;
  readonly description: string;
  readonly kicks: readonly string[];
}

const CONVERSION_TOOLS: readonly ToolCard[] = [
  {
    id: "converter-formats",
    label: "Convert Save Files",
    description: "SAV to JSON and back, with PLZ / CNK compression",
    kicks: ["SAV to JSON", "JSON to SAV"],
  },
  {
    id: "converter-xgp",
    label: "GamePass ↔ Steam",
    description: "Extract WGS blobs or package Steam saves for Xbox",
    kicks: ["Extract", "Package"],
  },
  {
    id: "converter-steamid",
    label: "SteamID Convert",
    description: "SteamID64, Palworld UID, and No-Steam UID in one step",
    kicks: ["CityHash64", "UID"],
  },
  {
    id: "converter-restore-map",
    label: "Restore Map",
    description: "Reveal world fog and hidden locations in LocalData.sav",
    kicks: ["LocalData.sav", "Non-Destructive"],
  },
];

const MANAGEMENT_TOOLS: readonly ToolCard[] = [
  {
    id: "converter-formats",
    label: "Slot Injector",
    description: "Expand Palbox capacity and inject extra slots",
    kicks: ["Palbox Slots", "Capacity"],
  },
  {
    id: "converter-xgp",
    label: "Character Transfer",
    description: "Cross-world pal and character migration",
    kicks: ["Host Swap", "Migrate"],
  },
  {
    id: "converter-steamid",
    label: "Fix Host Save",
    description: "Repair host save identity and ownership pointers",
    kicks: ["Ownership", "Repair"],
  },
];

const TAB_FOR_SECTION: Record<ToolsSectionId, ToolsTab> = {
  "converter-formats": "converter",
  "converter-restore-map": "modifiers",
  "converter-steamid": "converter",
  "converter-xgp": "xgp",
};

const SCROLL_ID_FOR_SECTION: Record<ToolsSectionId, string> = {
  "converter-formats": "converter-formats",
  "converter-restore-map": "converter-formats",
  "converter-steamid": "converter-steamid",
  "converter-xgp": "converter-formats",
};

const TOOL_TABS: readonly {
  readonly id: ToolsTab;
  readonly label: string;
  readonly description: string;
}[] = [
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

function ToolCardButton({
  card,
  onOpen,
  accent = false,
}: {
  readonly card: ToolCard;
  readonly onOpen: (id: ToolsSectionId) => void;
  readonly accent?: boolean;
}) {
  return (
    <button
      type="button"
      data-tool-card={card.label}
      data-testid={`tool-card-${card.label}`}
      onClick={() => onOpen(card.id)}
      className={[
        "group rounded-[2.5rem] border p-6 text-left transition-all duration-200 hover:-translate-y-0.5",
        "hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.08)]",
        accent
          ? "border-shell-accent/30 bg-shell-accent/5"
          : "border-shell-line bg-shell-surface",
      ].join(" ")}
    >
      <span className="block text-base font-semibold tracking-tight text-shell-ink">
        {card.label}
      </span>
      <span className="mt-1 block text-xs text-shell-muted">{card.description}</span>
      <span className="mt-3 flex flex-wrap gap-1.5">
        {card.kicks.map((kick) => (
          <span
            key={kick}
            className="rounded-lg border border-shell-line bg-shell-panel px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-shell-muted group-hover:text-shell-ink"
          >
            {kick}
          </span>
        ))}
      </span>
    </button>
  );
}

export function ToolsView() {
  const [activeTab, setActiveTab] = useState<ToolsTab>("converter");

  function openSection(id: ToolsSectionId) {
    setActiveTab(TAB_FOR_SECTION[id]);
    // Let the tab content mount before scrolling to the target anchor.
    window.setTimeout(() => {
      document
        .getElementById(SCROLL_ID_FOR_SECTION[id])
        ?.scrollIntoView({ behavior: "smooth" });
    }, 0);
  }

  return (
    <ViewShell
      title="Tools Workbench"
      description="Advanced save utilities, platform adapters, and conversion tools for Palworld save files."
    >
      {/* ── Tab Navigation ────────────────────────────────────────────── */}
      <div className="flex gap-0.5 border-b border-shell-line">
        {TOOL_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            id={`tools-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "group border-b-2 px-4 py-3 text-left transition",
              activeTab === tab.id
                ? "border-shell-accent bg-shell-surface"
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

      {/* ── Bento Tool Grids (Conversion landing) ───────────────────── */}
      {activeTab === "converter" && (
        <div className="mt-6 space-y-10">
          <section data-tool-group="conversion-tools" aria-label="Conversion Tools">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-shell-muted">
              Conversion Tools
            </h2>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {CONVERSION_TOOLS.map((card) => (
                <ToolCardButton key={card.label} card={card} onOpen={openSection} />
              ))}
            </div>
          </section>
          <section data-tool-group="management-tools" aria-label="Management Tools">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-shell-muted">
              Management Tools
            </h2>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              {MANAGEMENT_TOOLS.map((card, index) => (
                <ToolCardButton
                  key={card.label}
                  card={card}
                  onOpen={openSection}
                  accent={index === 0}
                />
              ))}
            </div>
          </section>
        </div>
      )}

      {/* ── Tab Panel Content ────────────────────────────────────────── */}
      <div className="mt-6">
        {activeTab === "converter" && <ConverterPanel />}
        {activeTab === "modifiers" && <ModifiersPanel />}
        {activeTab === "transfer" && <TransferPanel />}
        {activeTab === "xgp" && <XgpPanel />}
      </div>
    </ViewShell>
  );
}
