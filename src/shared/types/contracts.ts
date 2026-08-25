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

export interface EntityDiffSummary {
  readonly entityType: string;
  readonly entityId: string;
  readonly label: string;
  readonly changeDescription: string;
}

export interface MutationPreview {
  readonly operation: string;
  readonly targetSaveRoot: string;
  readonly entitiesToModify: readonly EntityDiffSummary[];
  readonly entitiesToDelete: readonly EntityDiffSummary[];
  readonly filesToModify: readonly string[];
  readonly filesToDelete: readonly string[];
  readonly backupTarget: string | null;
  readonly warnings: readonly string[];
  readonly isSafe: boolean;
}

export interface UpdatePlayerDto {
  readonly uid: string;
  readonly nickname?: string;
  readonly level?: number;
  readonly exp?: number;
  readonly hp?: number;
  readonly maxHp?: number;
  readonly status?: string;
}

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

export interface UpdateGuildDto {
  readonly guildId: string;
  readonly name?: string;
  readonly level?: number;
}

export interface TransferGuildAdminDto {
  readonly guildId: string;
  readonly newAdminUid: string;
}

export interface MoveGuildMemberDto {
  readonly playerUid: string;
  readonly sourceGuildId: string;
  readonly targetGuildId: string;
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

export interface UpdateBaseDto {
  readonly baseId: string;
  readonly level?: number;
  readonly radius?: number;
}

export interface NudgeBaseCoordinatesDto {
  readonly baseId: string;
  readonly deltaX: number;
  readonly deltaY: number;
  readonly deltaZ: number;
}

export interface ImportBaseBundleDto {
  readonly bundlePath: string;
  readonly targetGuildId: string;
  readonly offsetX?: number;
  readonly offsetY?: number;
  readonly offsetZ?: number;
}

export interface CloneBaseDto {
  readonly baseId: string;
  readonly targetGuildId: string;
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
  readonly ownerUid: string;
  readonly speciesId: string;
  readonly nickname?: string | null;
  readonly gender: string;
  readonly level: number;
  readonly exp: number;
  readonly hp: number;
  readonly maxHp: number;
  readonly attack: number;
  readonly defense: number;
  readonly workSpeed: number;
  readonly ivHp: number;
  readonly ivAttack: number;
  readonly ivDefense: number;
  readonly rank: number;
  readonly souls: number;
  readonly isLucky: boolean;
  readonly isBoss: boolean;
  readonly passiveSkills: readonly string[];
  readonly activeSkills: readonly string[];
  readonly location: string;
}

// --- Pal Mutation DTOs ---

export interface UpdatePalDto {
  readonly instanceId: string;
  readonly nickname?: string;
  readonly level?: number;
  readonly exp?: number;
  readonly gender?: string;
  readonly ivHp?: number;
  readonly ivAttack?: number;
  readonly ivDefense?: number;
  readonly souls?: number;
  readonly condenserRank?: number;
  readonly passiveSkills?: readonly string[];
  readonly activeSkills?: readonly string[];
  readonly isBoss?: boolean;
  readonly isLucky?: boolean;
  readonly cheatMode: boolean;
}

export interface CreatePalDto {
  readonly speciesId: string;
  readonly nickname?: string;
  readonly level: number;
  readonly gender: string;
  /** "palbox" | "party" | "base" | "dps" | "gps" */
  readonly containerType: string;
  readonly ownerUid?: string;
  readonly cheatMode: boolean;
}

export interface ImportPalDto {
  readonly bundlePath: string;
  readonly targetContainerType: string;
  readonly targetOwnerUid?: string;
  readonly cheatMode: boolean;
}

export interface ClonePalDto {
  readonly instanceId: string;
  readonly targetContainerType: string;
  readonly targetOwnerUid?: string;
}

export interface DeletePalDto {
  readonly instanceIds: readonly string[];
}

export interface BulkMaxPalsDto {
  /** Empty = all Pals in the loaded save. */
  readonly instanceIds: readonly string[];
  readonly cheatMode: boolean;
}

export interface BulkSyncPalSkillsDto {
  readonly sourceInstanceId: string;
  readonly targetInstanceIds: readonly string[];
  readonly syncPassives: boolean;
  readonly syncActiveSkills: boolean;
}

export interface ExportPalBundleDto {
  readonly instanceId: string;
  readonly exportPath: string;
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

export interface WorldOptionsDto {
  readonly expRate: number;
  readonly palCaptureRate: number;
  readonly palSpawnNumRate: number;
  readonly palDamageRateAttack: number;
  readonly palDamageRateDefense: number;
  readonly playerDamageRateAttack: number;
  readonly playerDamageRateDefense: number;
  readonly playerStaminaDecreaceRate: number;
  readonly playerStomachDecreaceRate: number;
  readonly playerAutoHpRegenRate: number;
  readonly buildObjectDamageRate: number;
  readonly buildObjectDeteriorationDamageRate: number;
  readonly collectionDropRate: number;
  readonly collectionObjectHpRate: number;
  readonly collectionObjectRespawnSpeedRate: number;
  readonly enemyDropItemRate: number;
  readonly deathPenalty: string;
  readonly guildPlayerMaxNum: number;
  readonly palEggDefaultHatchingTime: number;
  readonly enableAimAssistPad: boolean;
  readonly enableAimAssistKeyboard: boolean;
}

export interface WorldMetadataDto {
  readonly worldName: string;
  readonly gameDays: number;
  readonly inGameTimeSeconds: number;
  readonly isMultiplayer: boolean;
}

export interface Point2D {
  readonly x: number;
  readonly y: number;
}

export interface ZoneExclusion {
  readonly id: string;
  readonly name: string;
  readonly zoneType: string;
  readonly points: readonly Point2D[];
  readonly protectBases: boolean;
  readonly protectPlayers: boolean;
  readonly protectStructures: boolean;
}

export interface ExclusionConfig {
  readonly excludedPlayerUids: readonly string[];
  readonly excludedGuildIds: readonly string[];
  readonly excludedBaseIds: readonly string[];
  readonly zones: readonly ZoneExclusion[];
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

