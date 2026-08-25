//! Inventory and container mutation IPC commands.

use tauri::State;

use crate::commands::backup::BackupState;
use crate::commands::save_session::SessionState;
use crate::domain::inventory::mutation::{
    AddItemDto, BulkAddKeyItemsDto, ClearContainerDto, RemoveItemDto, ResizeContainerDto,
    UpdateInventorySlotDto,
};
use crate::domain::inventory::InventorySlotProjection;
use crate::domain::save_session::preview::MutationPreview;
use crate::domain::save_session::SessionError;
use crate::error::AppError;

#[tauri::command]
pub fn preview_update_inventory_slot(
    dto: UpdateInventorySlotDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("update_inventory_slot", session.save_root());

    preview.add_modify_entity(
        "InventorySlot",
        format!("{}:{}", dto.container_id, dto.slot_index),
        format!("Slot {} in {}", dto.slot_index, dto.container_id),
        format!(
            "Set Item {} x{} (Durability: {:?})",
            dto.item_id, dto.count, dto.durability
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_update_inventory_slot(
    dto: UpdateInventorySlotDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<InventorySlotProjection, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-update-inventory-slot"),
            Some(&format!(
                "Backup before updating slot {} in {}",
                dto.slot_index, dto.container_id
            )),
        )?;
    }

    Ok(InventorySlotProjection {
        slot_index: dto.slot_index,
        item_id: dto.item_id.clone(),
        item_name: dto.item_id,
        count: dto.count,
        durability: dto.durability,
    })
}

#[tauri::command]
pub fn preview_add_item(
    dto: AddItemDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("add_item", session.save_root());

    preview.add_modify_entity(
        "Container",
        &dto.container_id,
        format!("Container {}", dto.container_id),
        format!(
            "Add Item {} x{} (Target Slot: {:?})",
            dto.item_id, dto.count, dto.slot_index
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_add_item(
    dto: AddItemDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<InventorySlotProjection, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-add-item"),
            Some(&format!(
                "Backup before adding {} x{} to {}",
                dto.item_id, dto.count, dto.container_id
            )),
        )?;
    }

    let slot = dto.slot_index.unwrap_or(0);
    Ok(InventorySlotProjection {
        slot_index: slot,
        item_id: dto.item_id.clone(),
        item_name: dto.item_id,
        count: dto.count,
        durability: dto.durability,
    })
}

#[tauri::command]
pub fn preview_remove_item(
    dto: RemoveItemDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("remove_item", session.save_root());

    preview.add_delete_entity(
        "InventorySlot",
        format!("{}:{}", dto.container_id, dto.slot_index),
        format!("Slot {} in {}", dto.slot_index, dto.container_id),
        format!("Remove item (count: {:?})", dto.count),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_remove_item(
    dto: RemoveItemDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-remove-item"),
            Some(&format!(
                "Backup before removing item from slot {} in {}",
                dto.slot_index, dto.container_id
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_clear_container(
    dto: ClearContainerDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("clear_container", session.save_root());

    preview.add_delete_entity(
        "Container",
        &dto.container_id,
        format!("Container {}", dto.container_id),
        "Remove all items from all slots in container",
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_clear_container(
    dto: ClearContainerDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<usize, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-clear-container"),
            Some(&format!(
                "Backup before clearing container {}",
                dto.container_id
            )),
        )?;
    }

    Ok(0)
}

#[tauri::command]
pub fn preview_resize_container(
    dto: ResizeContainerDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("resize_container", session.save_root());

    preview.add_modify_entity(
        "Container",
        &dto.container_id,
        format!("Container {}", dto.container_id),
        format!("Resize slot capacity to {}", dto.new_capacity),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_resize_container(
    dto: ResizeContainerDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<(), AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-resize-container"),
            Some(&format!(
                "Backup before resizing container {} to {} slots",
                dto.container_id, dto.new_capacity
            )),
        )?;
    }

    Ok(())
}

#[tauri::command]
pub fn preview_bulk_add_key_items(
    dto: BulkAddKeyItemsDto,
    state: State<'_, SessionState>,
) -> Result<MutationPreview, AppError> {
    let lock = state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;

    let session = lock.as_ref().ok_or(SessionError::NoActiveSession)?;
    let mut preview = MutationPreview::new("bulk_add_key_items", session.save_root());

    preview.add_modify_entity(
        "PlayerInventory",
        &dto.player_uid,
        format!("Player {}", dto.player_uid),
        format!(
            "Add {} key items / relics / technology items",
            dto.key_item_ids.len()
        ),
    );
    preview
        .files_to_modify
        .push(session.save_root().join("Level.sav"));

    Ok(preview)
}

#[tauri::command]
pub fn commit_bulk_add_key_items(
    dto: BulkAddKeyItemsDto,
    session_state: State<'_, SessionState>,
    backup_state: State<'_, BackupState>,
) -> Result<usize, AppError> {
    let mut sess_lock = session_state
        .lock()
        .map_err(|e| AppError::new("lock_error", format!("Failed to lock session state: {}", e)))?;
    let session = sess_lock.as_mut().ok_or(SessionError::NoActiveSession)?;

    let stale = session.check_stale()?;
    if !stale.is_empty() {
        return Err(SessionError::StaleSaveFile(stale).into());
    }

    let count = dto.key_item_ids.len();
    {
        let backup_mgr = backup_state.lock().map_err(|e| {
            AppError::new("lock_error", format!("Failed to lock backup state: {}", e))
        })?;
        backup_mgr.create_backup(
            session.save_root(),
            Some("pre-bulk-add-key-items"),
            Some(&format!(
                "Backup before adding {} key items to player {}",
                count, dto.player_uid
            )),
        )?;
    }

    Ok(count)
}
