export interface AppRoute {
  readonly id: string;
  readonly label: string;
  readonly phase: string;
  readonly enabled: boolean;
}

export const appRoutes: readonly AppRoute[] = [
  { id: "save-session", label: "Save Session", phase: "Phase 3", enabled: false },
  { id: "players", label: "Players", phase: "Phase 4", enabled: false },
  { id: "guilds", label: "Guilds", phase: "Phase 4", enabled: false },
  { id: "bases", label: "Bases", phase: "Phase 4", enabled: false },
  { id: "pals", label: "Pals", phase: "Phase 4", enabled: false },
  { id: "inventory", label: "Inventory", phase: "Phase 4", enabled: false },
  { id: "map", label: "Map", phase: "Phase 4", enabled: false },
  { id: "breeding", label: "Breeding", phase: "Phase 4", enabled: false },
  { id: "diagnostics", label: "Diagnostics", phase: "Phase 4", enabled: false },
  { id: "tools", label: "Tools", phase: "Phase 8", enabled: false },
  { id: "settings", label: "Settings", phase: "Phase 1", enabled: true },
];
