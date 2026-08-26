export type RouteGroup = "session" | "entities" | "exploration" | "advanced";

export interface AppRoute {
  readonly id: string;
  readonly label: string;
  readonly group: RouteGroup;
  readonly enabled: boolean;
  readonly shortcutIndex?: number;
}

export interface RouteGroupMeta {
  readonly id: RouteGroup;
  readonly title: string;
}

export const routeGroups: readonly RouteGroupMeta[] = [
  { id: "session", title: "Save & World" },
  { id: "entities", title: "World Entities" },
  { id: "exploration", title: "Map & Genetics" },
  { id: "advanced", title: "Tools & Config" },
];

export const appRoutes: readonly AppRoute[] = [
  // Session & World Group
  { id: "save-session", label: "Save Session", group: "session", enabled: true, shortcutIndex: 1 },
  { id: "world-options", label: "World Options", group: "session", enabled: true, shortcutIndex: 2 },

  // World Entities Group
  { id: "players", label: "Players", group: "entities", enabled: true, shortcutIndex: 3 },
  { id: "guilds", label: "Guilds", group: "entities", enabled: true, shortcutIndex: 4 },
  { id: "bases", label: "Bases", group: "entities", enabled: true, shortcutIndex: 5 },
  { id: "pals", label: "Pals", group: "entities", enabled: true, shortcutIndex: 6 },
  { id: "inventory", label: "Inventory", group: "entities", enabled: true, shortcutIndex: 7 },

  // Exploration Group
  { id: "map", label: "Map", group: "exploration", enabled: true, shortcutIndex: 8 },
  { id: "breeding", label: "Breeding", group: "exploration", enabled: true, shortcutIndex: 9 },

  // Tools & Config Group
  { id: "diagnostics", label: "Diagnostics", group: "advanced", enabled: true },
  { id: "tools", label: "Tools", group: "advanced", enabled: true, shortcutIndex: 0 },
  { id: "settings", label: "Settings", group: "advanced", enabled: true },
];
