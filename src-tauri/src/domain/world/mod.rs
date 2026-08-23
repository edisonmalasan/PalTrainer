//! WorldOption and WorldMetadata domain models.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct WorldOptionsDto {
    pub exp_rate: f32,
    pub pal_capture_rate: f32,
    pub pal_spawn_num_rate: f32,
    pub pal_damage_rate_attack: f32,
    pub pal_damage_rate_defense: f32,
    pub player_damage_rate_attack: f32,
    pub player_damage_rate_defense: f32,
    pub player_stamina_decreace_rate: f32,
    pub player_stomach_decreace_rate: f32,
    pub player_auto_hp_regen_rate: f32,
    pub build_object_damage_rate: f32,
    pub build_object_deterioration_damage_rate: f32,
    pub collection_drop_rate: f32,
    pub collection_object_hp_rate: f32,
    pub collection_object_respawn_speed_rate: f32,
    pub enemy_drop_item_rate: f32,
    pub death_penalty: String, // "None", "Item", "ItemAndEquipment", "All"
    pub guild_player_max_num: i32,
    pub pal_egg_default_hatching_time: f32,
    pub enable_aim_assist_pad: bool,
    pub enable_aim_assist_keyboard: bool,
}

impl Default for WorldOptionsDto {
    fn default() -> Self {
        Self {
            exp_rate: 1.0,
            pal_capture_rate: 1.0,
            pal_spawn_num_rate: 1.0,
            pal_damage_rate_attack: 1.0,
            pal_damage_rate_defense: 1.0,
            player_damage_rate_attack: 1.0,
            player_damage_rate_defense: 1.0,
            player_stamina_decreace_rate: 1.0,
            player_stomach_decreace_rate: 1.0,
            player_auto_hp_regen_rate: 1.0,
            build_object_damage_rate: 1.0,
            build_object_deterioration_damage_rate: 1.0,
            collection_drop_rate: 1.0,
            collection_object_hp_rate: 1.0,
            collection_object_respawn_speed_rate: 1.0,
            enemy_drop_item_rate: 1.0,
            death_penalty: "ItemAndEquipment".to_string(),
            guild_player_max_num: 20,
            pal_egg_default_hatching_time: 2.0,
            enable_aim_assist_pad: true,
            enable_aim_assist_keyboard: false,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct WorldMetadataDto {
    pub world_name: String,
    pub game_days: i32,
    pub in_game_time_seconds: f64,
    pub is_multiplayer: bool,
}

impl Default for WorldMetadataDto {
    fn default() -> Self {
        Self {
            world_name: "Palworld".to_string(),
            game_days: 1,
            in_game_time_seconds: 0.0,
            is_multiplayer: false,
        }
    }
}
