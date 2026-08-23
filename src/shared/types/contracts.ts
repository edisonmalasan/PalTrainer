export type ThemePreference = "system" | "light" | "dark";
export type LanguagePreference = "en";

export interface AppInfo {
  readonly name: string;
  readonly version: string;
  readonly tauriVersion: string;
}

export interface AppSettings {
  readonly theme: ThemePreference;
  readonly language: LanguagePreference;
  readonly showAdvancedTools: boolean;
}

export interface FeatureFlag {
  readonly id: string;
  readonly label: string;
  readonly enabled: boolean;
  readonly description: string;
}

export interface AppLogEntry {
  readonly level: "info" | "warning" | "error";
  readonly message: string;
  readonly timestamp: string;
}

export interface CommandError {
  readonly code: string;
  readonly message: string;
  readonly details?: string;
}

// ── Phase 4 Domain DTOs ──────────────────────────────────────────────────────

export interface PlayerProjection {
  readonly uid: string;
  readonly displayName: string;
  readonly level: number;
  readonly exp: number;
  readonly hp: number;
  readonly maxHp: number;
  readonly fullStomach: number;
  readonly isHost: boolean;
}

export interface GuildMemberProjection {
  readonly uid: string;
  readonly displayName: string;
  readonly rank: number;
}

export interface GuildProjection {
  readonly guildId: string;
  readonly guildName: string;
  readonly adminUid: string;
  readonly members: readonly GuildMemberProjection[];
}

export interface BaseProjection {
  readonly baseId: string;
  readonly ownerGuildId: string;
  readonly baseName: string;
  readonly worldX: number;
  readonly worldY: number;
  readonly worldZ: number;
  readonly currentLevel: number;
  readonly workerCount: number;
}

export interface PalProjection {
  readonly instanceId: string;
  readonly palId: string;
  readonly nickname: string;
  readonly level: number;
  readonly exp: number;
  readonly gender: string;
  readonly rank: number;
  readonly condenser_rank: number;
  readonly hp: number;
  readonly maxHp: number;
  readonly workSpeed: number;
  readonly passive_skills: readonly string[];
  readonly active_skills: readonly string[];
  readonly ownerUid: string | null;
  readonly container: string | null;
}

export interface InventorySlotProjection {
  readonly slotIndex: number;
  readonly itemId: string;
  readonly count: number;
  readonly durability: number | null;
}

export interface InventoryProjection {
  readonly ownerUid: string;
  readonly slots: readonly InventorySlotProjection[];
}

export interface MapMarkerProjection {
  readonly label: string;
  readonly worldX: number;
  readonly worldY: number;
  readonly mapX: number;
  readonly mapY: number;
  readonly markerType: string;
}

export type DiagnosticSeverity = "info" | "warning" | "error";

export interface DiagnosticIssue {
  readonly code: string;
  readonly severity: DiagnosticSeverity;
  readonly message: string;
  readonly context: string | null;
}

export interface DiagnosticReportDto {
  readonly issues: readonly DiagnosticIssue[];
  readonly scannedAt: string;
}

export interface BreedingLookupResult {
  readonly parent1: string;
  readonly parent2: string;
  readonly childPalId: string;
  readonly childName: string;
  readonly isUniqueCombo: boolean;
}

export interface WorkSuitabilityInfo {
  readonly workType: string;
  readonly level: number;
}

export interface PalSpeciesInfo {
  readonly id: string;
  readonly name: string;
  readonly elementTypes: readonly string[];
  readonly rarity: number;
  readonly hpScaling: number;
  readonly attackScaling: number;
  readonly defenseScaling: number;
  readonly workSuitabilities: readonly WorkSuitabilityInfo[];
}

export interface ItemInfo {
  readonly id: string;
  readonly name: string;
  readonly itemType: string;
  readonly description: string;
  readonly maxStackCount: number;
}

export interface PassiveSkillInfo {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly tier: number;
}

export interface ActiveSkillInfo {
  readonly id: string;
  readonly name: string;
  readonly elementType: string;
  readonly power: number;
  readonly cooldownSeconds: number;
}

export interface GameCatalog {
  readonly pals: readonly PalSpeciesInfo[];
  readonly items: readonly ItemInfo[];
  readonly passives: readonly PassiveSkillInfo[];
  readonly activeSkills: readonly ActiveSkillInfo[];
}

