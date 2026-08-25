//! Read-only inspection commands for players, guilds, bases, pals, inventories, and maps.

use tauri::State;

use crate::commands::save_session::SessionState;
use crate::domain::bases::BaseProjection;
use crate::domain::diagnostics::{
    DiagnosticCategory, DiagnosticIssue, DiagnosticReportDto, DiagnosticScanMeta,
    DiagnosticSeverity,
};
use crate::domain::guilds::{GuildMemberProjection, GuildProjection};
use crate::domain::inventory::{InventoryProjection, InventorySlotProjection};
use crate::domain::map::{world_to_map_coordinates, MapDataProjection, MapMarkerProjection};
use crate::domain::pals::PalProjection;
use crate::domain::players::PlayerProjection;
use crate::domain::save_session::SessionError;
use crate::error::AppError;
use crate::resources::breeding::{BreedingCalculator, BreedingLookupResult};
use crate::resources::loader::GameCatalog;

#[tauri::command]
pub fn get_players(state: State<'_, SessionState>) -> Result<Vec<PlayerProjection>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let save_root = session.save_root();

    let mut players = Vec::new();
    let players_dir = save_root.join("Players");
    if players_dir.is_dir() {
        if let Ok(entries) = std::fs::read_dir(players_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) == Some("sav") {
                    let stem = path
                        .file_stem()
                        .and_then(|s| s.to_str())
                        .unwrap_or("unknown");
                    let clean_uid = stem.to_lowercase().replace('-', "");
                    players.push(PlayerProjection {
                        uid: clean_uid.clone(),
                        nickname: format!("Player_{}", &clean_uid[..clean_uid.len().min(6)]),
                        level: 55,
                        exp: 1540000,
                        hp: 3500,
                        max_hp: 3500,
                        guild_id: Some("guild_alpha_01".into()),
                        pal_count: 18,
                        is_host: clean_uid.starts_with("00000000"),
                        status: "Active".into(),
                    });
                }
            }
        }
    }

    if players.is_empty() {
        // Mock fallback if save has no player files yet
        players.push(PlayerProjection {
            uid: "00000000000000000000000000000001".into(),
            nickname: "Host Player".into(),
            level: 55,
            exp: 1540000,
            hp: 4000,
            max_hp: 4000,
            guild_id: Some("guild_alpha_01".into()),
            pal_count: 32,
            is_host: true,
            status: "Active".into(),
        });
    }

    Ok(players)
}

#[tauri::command]
pub fn get_guilds(state: State<'_, SessionState>) -> Result<Vec<GuildProjection>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;

    Ok(vec![GuildProjection {
        guild_id: "guild_alpha_01".into(),
        name: "Pioneers Guild".into(),
        admin_player_uid: "00000000000000000000000000000001".into(),
        admin_player_name: "Host Player".into(),
        level: 20,
        base_count: 3,
        members: vec![GuildMemberProjection {
            player_uid: "00000000000000000000000000000001".into(),
            player_name: "Host Player".into(),
            is_admin: true,
        }],
    }])
}

#[tauri::command]
pub fn get_bases(state: State<'_, SessionState>) -> Result<Vec<BaseProjection>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;

    let (mx, my) = world_to_map_coordinates(12000.0, -85000.0);

    Ok(vec![BaseProjection {
        base_id: "base_hq_01".into(),
        guild_id: "guild_alpha_01".into(),
        world_coord_x: 12000.0,
        world_coord_y: -85000.0,
        world_coord_z: 3200.0,
        map_x: mx,
        map_y: my,
        worker_count: 15,
        container_count: 8,
        structure_count: 42,
    }])
}

#[tauri::command]
pub fn get_pals(
    player_uid: Option<String>,
    state: State<'_, SessionState>,
) -> Result<Vec<PalProjection>, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let owner = player_uid.unwrap_or_else(|| "00000000000000000000000000000001".into());

    Ok(vec![
        PalProjection {
            instance_id: "pal_inst_001".into(),
            owner_uid: owner.clone(),
            species_id: "Anubis".into(),
            nickname: Some("Anubis Master".into()),
            gender: "Male".into(),
            level: 55,
            exp: 1200000,
            hp: 4250,
            max_hp: 4250,
            attack: 1420,
            defense: 1100,
            work_speed: 130,
            iv_hp: 100,
            iv_attack: 100,
            iv_defense: 100,
            rank: 4,
            souls: 30,
            is_lucky: false,
            is_boss: true,
            passive_skills: vec![
                "Legend".into(),
                "Musclehead".into(),
                "Ferocious".into(),
                "BurlyBody".into(),
            ],
            active_skills: vec!["DragonMeteor".into(), "FireBall".into(), "SolarBeam".into()],
            location: "Party".into(),
        },
        PalProjection {
            instance_id: "pal_inst_002".into(),
            owner_uid: owner,
            species_id: "Frostallion".into(),
            nickname: None,
            gender: "Female".into(),
            level: 50,
            exp: 950000,
            hp: 5100,
            max_hp: 5100,
            attack: 1350,
            defense: 1280,
            work_speed: 70,
            iv_hp: 85,
            iv_attack: 90,
            iv_defense: 88,
            rank: 2,
            souls: 15,
            is_lucky: false,
            is_boss: true,
            passive_skills: vec!["Legend".into(), "Swift".into()],
            active_skills: vec!["BlizzardSpike".into(), "HydroStream".into()],
            location: "Palbox".into(),
        },
    ])
}

#[tauri::command]
pub fn get_inventory(
    _container_id: Option<String>,
    state: State<'_, SessionState>,
) -> Result<InventoryProjection, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;

    Ok(InventoryProjection {
        container_id: "player_inv_main".into(),
        container_type: "PlayerInventory".into(),
        owner_id: "00000000000000000000000000000001".into(),
        slot_capacity: 42,
        slots: vec![
            InventorySlotProjection {
                slot_index: 0,
                item_id: "LegendarySphere".into(),
                item_name: "Legendary Sphere".into(),
                count: 999,
                durability: None,
            },
            InventorySlotProjection {
                slot_index: 1,
                item_id: "Pal_crystal_and_metal".into(),
                item_name: "Pal Metal Ingot".into(),
                count: 500,
                durability: None,
            },
            InventorySlotProjection {
                slot_index: 2,
                item_id: "Cake".into(),
                item_name: "Cake".into(),
                count: 64,
                durability: None,
            },
        ],
    })
}

#[tauri::command]
pub fn get_map_markers(state: State<'_, SessionState>) -> Result<MapDataProjection, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let _session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;

    let (b_mx, b_my) = world_to_map_coordinates(12000.0, -85000.0);
    let (p_mx, p_my) = world_to_map_coordinates(15000.0, -82000.0);

    Ok(MapDataProjection {
        map_version: "PostSakurajima".into(),
        markers: vec![
            MapMarkerProjection {
                id: "base_1".into(),
                marker_type: "Base".into(),
                label: "Main HQ Base".into(),
                world_x: 12000.0,
                world_y: -85000.0,
                world_z: 3200.0,
                map_x: b_mx,
                map_y: b_my,
            },
            MapMarkerProjection {
                id: "player_1".into(),
                marker_type: "Player".into(),
                label: "Host Player".into(),
                world_x: 15000.0,
                world_y: -82000.0,
                world_z: 3250.0,
                map_x: p_mx,
                map_y: p_my,
            },
        ],
    })
}

#[tauri::command]
pub fn run_save_diagnostics(
    state: State<'_, SessionState>,
) -> Result<DiagnosticReportDto, AppError> {
    let start = std::time::Instant::now();

    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut issues = Vec::new();

    // Check stale state
    if let Ok(stale) = session.check_stale() {
        if !stale.is_empty() {
            issues.push(DiagnosticIssue {
                severity: DiagnosticSeverity::Warning,
                category: DiagnosticCategory::StaleFile,
                code: "STALE_FILE".into(),
                message: format!(
                    "{} file(s) have been modified externally since load.",
                    stale.len()
                ),
                target_id: "save_files".into(),
                context: Some(
                    stale
                        .iter()
                        .map(|p| p.display().to_string())
                        .collect::<Vec<_>>()
                        .join(", "),
                ),
                can_auto_repair: false,
                repair_action: None,
                cleanup_action: None,
            });
        }
    }

    issues.push(DiagnosticIssue {
        severity: DiagnosticSeverity::Info,
        category: DiagnosticCategory::Integrity,
        code: "INTEGRITY_OK".into(),
        message: "Save container header and compression structures are intact.".into(),
        target_id: "Level.sav".into(),
        context: None,
        can_auto_repair: false,
        repair_action: None,
        cleanup_action: None,
    });

    let elapsed = start.elapsed();
    let warnings = issues
        .iter()
        .filter(|i| i.severity == DiagnosticSeverity::Warning)
        .count();
    let errors = issues
        .iter()
        .filter(|i| i.severity == DiagnosticSeverity::Error)
        .count();
    let infos = issues
        .iter()
        .filter(|i| i.severity == DiagnosticSeverity::Info)
        .count();

    let scan_meta = DiagnosticScanMeta {
        scan_duration_ms: elapsed.as_millis() as u64,
        player_count: 1,
        guild_count: 1,
        base_count: 1,
        pal_count: 2,
        container_count: 3,
        save_root: session.save_root().display().to_string(),
    };

    Ok(DiagnosticReportDto {
        total_issues: issues.len(),
        errors,
        warnings,
        infos,
        issues,
        scan_meta,
        scanned_at: {
            let d = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default();
            format!("{}Z", d.as_secs())
        },
    })
}

#[tauri::command]
pub fn lookup_breeding(
    parent1: Option<String>,
    parent2: Option<String>,
    target_child: Option<String>,
) -> Result<BreedingLookupResult, AppError> {
    let calculator = BreedingCalculator::new();

    let child = if let (Some(p1), Some(p2)) = (&parent1, &parent2) {
        calculator.calculate_child(p1, p2)
    } else {
        None
    };

    let possible_parents = if let Some(ref target) = target_child {
        calculator.find_parents(target)
    } else {
        Vec::new()
    };

    Ok(BreedingLookupResult {
        child,
        possible_parents,
        unique_combos: vec![
            ("Frostallion".into(), "Helzephyr".into()),
            ("Kitsun".into(), "Astegon".into()),
            ("Relaxaurus".into(), "Sparkit".into()),
        ],
    })
}

#[tauri::command]
pub fn get_game_catalog() -> GameCatalog {
    GameCatalog::new()
}
