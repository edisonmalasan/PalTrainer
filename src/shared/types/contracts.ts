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
  readonly recentSavePaths: readonly string[];
  readonly scanSaveLogger: boolean;
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

export interface SaveSummary {
  readonly saveRoot: string;
  readonly worldName: string;
  readonly saveType: string;
  readonly playerCount: number;
  readonly levelSavSize: number;
  readonly isDirty: boolean;
  readonly loadedAt: number;
}

export interface GpsSummary {
  readonly path: string;
  readonly fileSize: number;
  readonly loadedAt: number;
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
  readonly playerUid: string;
  readonly playerName: string;
  readonly isAdmin: boolean;
}

export interface GuildProjection {
  readonly guildId: string;
  readonly name: string;
  readonly adminPlayerUid: string;
  readonly adminPlayerName: string;
  readonly level: number;
  readonly baseCount: number;
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
  readonly containerId: string;
  readonly containerType: string;
  readonly ownerId: string;
  readonly slotCapacity: number;
  readonly slots: readonly InventorySlotProjection[];
  /** Optional legacy alias for ownerId */
  readonly ownerUid?: string;
}

// --- Inventory Mutation DTOs ---

export interface UpdateInventorySlotDto {
  readonly ownerUid: string;
  readonly containerId: string;
  readonly slotIndex: number;
  readonly itemId: string;
  readonly count: number;
  readonly durability?: number;
}

export interface AddItemDto {
  readonly ownerUid: string;
  readonly containerId: string;
  readonly itemId: string;
  readonly count: number;
  readonly durability?: number;
  readonly slotIndex?: number;
}

export interface RemoveItemDto {
  readonly ownerUid: string;
  readonly containerId: string;
  readonly slotIndex: number;
  readonly count?: number;
}

export interface ClearContainerDto {
  readonly ownerUid: string;
  readonly containerId: string;
}

export interface ResizeContainerDto {
  readonly ownerUid: string;
  readonly containerId: string;
  readonly newCapacity: number;
}

export interface BulkAddKeyItemsDto {
  readonly playerUid: string;
  readonly keyItemIds: readonly string[];
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

/** Draft for a zone drawn on the map canvas; points are post-Sakurajima map-grid units. */
export interface ZoneExclusionFromMapDto {
  readonly name: string;
  readonly zoneType: string;
  readonly points: readonly Point2D[];
  readonly protectBases: boolean;
  readonly protectPlayers: boolean;
  readonly protectStructures: boolean;
}

export interface MapMarkerProjection {
  readonly id: string;
  readonly markerType: string;
  readonly label: string;
  readonly worldX: number;
  readonly worldY: number;
  readonly worldZ: number;
  /** "PreSakurajima" | "PostSakurajima" */
  readonly mapVersion: string;
  readonly mapX: number;
  readonly mapY: number;
  readonly treemapX: number;
  readonly treemapY: number;
  /** Base camp area multiplier (0.5-10.0); null for non-base markers. */
  readonly areaRange?: number | null;
}

export interface MapDataProjection {
  readonly mapVersion: string;
  readonly markers: readonly MapMarkerProjection[];
}

export interface MapAssetPayload {
  readonly name: string;
  readonly mimeType: string;
  readonly base64Data: string;
}

export interface MoveBaseToMapDto {
  readonly baseId: string;
  readonly mapX: number;
  readonly mapY: number;
}

export interface MovePlayerToMapDto {
  readonly uid: string;
  readonly mapX: number;
  readonly mapY: number;
}

export interface UpdateBaseAreaRangeDto {
  readonly baseId: string;
  /** Base camp area multiplier; validated in 50-1000% (0.5-10.0). */
  readonly areaRange: number;
}

export type DiagnosticSeverity = "info" | "warning" | "error";

export type DiagnosticCategory =
  | "stale_file"
  | "integrity"
  | "orphaned_player"
  | "duplicate_player"
  | "broken_guild"
  | "empty_guild"
  | "illegal_pal"
  | "invalid_pal_species"
  | "invalid_passives"
  | "invalid_active_skills"
  | "unassigned_pal"
  | "overfilled_container"
  | "invalid_item"
  | "unreferenced_data"
  | "invalid_structure"
  | "stale_timestamp"
  | "dynamic_container_link"
  | "private_chest_lock"
  | "death_bag"
  | "imported_dna_pal"
  | "non_base_map_object"
  | "skin";

export interface RepairActionDescriptor {
  readonly label: string;
  readonly description: string;
  readonly affectedEntityCount: number;
}

export interface CleanupActionDescriptor {
  readonly label: string;
  readonly description: string;
  readonly entitiesToRemove: number;
}

export interface DiagnosticIssue {
  readonly severity: DiagnosticSeverity;
  readonly category: DiagnosticCategory;
  readonly code: string;
  readonly message: string;
  readonly targetId: string;
  readonly context: string | null;
  readonly canAutoRepair: boolean;
  readonly repairAction: RepairActionDescriptor | null;
  readonly cleanupAction: CleanupActionDescriptor | null;
}

export interface DiagnosticScanMeta {
  readonly scanDurationMs: number;
  readonly playerCount: number;
  readonly guildCount: number;
  readonly baseCount: number;
  readonly palCount: number;
  readonly containerCount: number;
  readonly saveRoot: string;
}

export interface DiagnosticReportDto {
  readonly totalIssues: number;
  readonly errors: number;
  readonly warnings: number;
  readonly infos: number;
  readonly issues: readonly DiagnosticIssue[];
  readonly scanMeta: DiagnosticScanMeta;
  readonly scannedAt: string;
}

export type CleanupTarget =
  | "empty_guilds"
  | "inactive_players"
  | "duplicate_players"
  | "unreferenced_data"
  | "non_base_map_objects"
  | "invalid_structure_objects"
  | "all_skins"
  | "imported_dna_pals"
  | "invalid_items"
  | "invalid_pals"
  | "invalid_passives";

export interface CleanupParams {
  readonly target: CleanupTarget;
  readonly inactivityDaysThreshold?: number;
  readonly protectDeathBags: boolean;
  readonly scopePlayerUid?: string;
}

export type RepairTarget =
  | "structures"
  | "items"
  | "pals"
  | "illegal_pals"
  | "illegal_players"
  | "invalid_active_skills"
  | "overfilled_inventories"
  | "guilds"
  | "timestamps"
  | "unassigned_pals"
  | "dynamic_containers"
  | "private_chests";

export interface RepairParams {
  readonly target: RepairTarget;
  readonly scopeEntityId?: string;
  readonly autoHeal: boolean;
  readonly clampStats: boolean;
}

export type ResetTarget =
  | "missions"
  | "dungeons"
  | "oil_rig"
  | "invaders"
  | "supply_drops"
  | "anti_air_turrets"
  | "lock_gimmicks";

export interface ResetParams {
  readonly targets: readonly ResetTarget[];
  readonly scopePlayerUid?: string;
}

export interface PalDefenderCommand {
  readonly command: string;
  readonly description: string;
  readonly category: string;
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

// ── Phase 8: Conversion, Transfer, and Platform Tool Contracts ──────────────────

export interface IdConversionResult {
  readonly steamId: string;
  readonly palworldUid: string;
  readonly nosteamUid: string;
  readonly inputType: string;
}

export interface ConvertSavToJsonDto {
  readonly inputPath: string;
  readonly outputPath?: string;
  readonly minify: boolean;
}

export interface ConvertJsonToSavDto {
  readonly inputPath: string;
  readonly outputPath?: string;
  readonly saveType?: string;
}

export interface ConversionResult {
  readonly sourcePath: string;
  readonly targetPath: string;
  readonly bytesWritten: number;
  readonly message: string;
}

export interface RawJsonSummary {
  readonly savePath: string;
  readonly propertyCount: number;
  readonly topLevelKeys: readonly string[];
  readonly saveType: string;
  readonly isReadOnly: boolean;
}

export interface RestoreMapOptions {
  readonly customLocalDataPath?: string;
  readonly clearUiFog: boolean;
  readonly clearHiddenLocations: boolean;
  readonly disableSkyCloudOverlay: boolean;
}

export interface RestoreMapReport {
  readonly filesUpdated: readonly string[];
  readonly backupPath?: string;
  readonly masksCleared: number;
  readonly hiddenLocationsReset: number;
  readonly message: string;
}

export interface PalboxCapacityDto {
  readonly playerUid: string;
  readonly containerId: string;
  readonly currentSlotCount: number;
  readonly currentPageCount: number;
  readonly occupiedSlotCount: number;
  readonly maxRecommendedPages: number;
}

export interface SlotInjectionParams {
  readonly playerUid: string;
  readonly targetPageCount: number;
}

export interface SlotInjectionAuditResult {
  readonly playerUid: string;
  readonly containerId: string;
  readonly previousSlotCount: number;
  readonly newSlotCount: number;
  readonly newPageCount: number;
  readonly backupPath?: string;
  readonly message: string;
}

export interface TransferPlayerSummaryDto {
  readonly uid: string;
  readonly nickname: string;
  readonly level: number;
  readonly palCount: number;
  readonly itemCount: number;
  readonly hasDpsFile: boolean;
}

export interface CharacterTransferOptions {
  readonly sourceSavePath: string;
  readonly targetSavePath: string;
  readonly playerUid: string;
  readonly transferPals: boolean;
  readonly transferInventory: boolean;
  readonly transferTech: boolean;
  readonly transferAllPlayers: boolean;
  readonly targetGuildId?: string;
}

export interface CharacterTransferAuditResult {
  readonly transferredPlayers: readonly string[];
  readonly sourceSave: string;
  readonly targetSave: string;
  readonly palsTransferred: number;
  readonly itemsTransferred: number;
  readonly backupPath?: string;
  readonly message: string;
}

export interface HostSwapOptions {
  readonly sourceUid: string;
  readonly targetUid: string;
  readonly swapMode: boolean;
}

export interface HostSwapInspectionDto {
  readonly sourceUid: string;
  readonly targetUid: string;
  readonly sourcePlayerFound: boolean;
  readonly targetPlayerFound: boolean;
  readonly sourceNickname: string;
  readonly targetNickname: string;
  readonly sourcePalCount: number;
  readonly targetPalCount: number;
  readonly affectedGuilds: readonly string[];
  readonly affectedBases: readonly string[];
}

export interface HostSwapAuditResult {
  readonly sourceUid: string;
  readonly targetUid: string;
  readonly mode: string;
  readonly filesRenamed: readonly string[];
  readonly backupPath?: string;
  readonly message: string;
}

export interface XgpSaveEntry {
  readonly wgsDir: string;
  readonly userId: string;
  readonly packageName: string;
  readonly lastModified: number;
  readonly containerCount: number;
  readonly hasLevelSav: boolean;
  readonly hasPlayers: boolean;
}

export interface XgpExtractOptions {
  readonly wgsUserDir: string;
  readonly destinationPath: string;
}

export interface XgpImportOptions {
  readonly sourceSteamPath: string;
  readonly targetWgsUserDir: string;
  readonly packageName?: string;
}

export interface XgpExtractResult {
  readonly destinationPath: string;
  readonly filesExtracted: readonly string[];
  readonly message: string;
}

export interface XgpImportAuditResult {
  readonly targetWgsUserDir: string;
  readonly containersCreated: number;
  readonly backupPath?: string;
  readonly message: string;
}
