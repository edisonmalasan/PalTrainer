"""Restore map visibility with explicit backup and recovery state."""
from __future__ import annotations

import os
import shutil
import tempfile
import time

from PyQt6.QtWidgets import QApplication

from i18n import t
from loading_manager import run_with_loading, show_critical, show_question
from palsav.gvas import GvasFile
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palworld_aio import constants
from palworld_aio.ui.chrome.components import BaseDialog, BulkWorkflowReview, make_button
from common import get_steam_save_path
from resource_resolver import get_data_base


savegames_path = get_steam_save_path()
restore_map_path = os.path.join(get_data_base(), 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)


def backup_local_data(subfolder_path: str) -> str | None:
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(
        restore_map_path, timestamp, os.path.basename(subfolder_path))
    original_local_data = os.path.join(subfolder_path, 'LocalData.sav')
    if not os.path.exists(original_local_data):
        return None
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    shutil.copy2(original_local_data, backup_file)
    print(t('Backup created at: {backup_file}', backup_file=backup_file))
    return backup_file


def clear_fog_in_local_data(path: str) -> None:
    from palsav.io import load_sav, save_sav

    gvas = load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    data = gvas.dump()
    save_data = data['properties']['SaveData']['value']
    if 'WorldMapUISaveDataMap' in save_data:
        for entry in save_data['WorldMapUISaveDataMap']['value']:
            mask = entry['value']['MaskTextureData']['value']
            mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapUISaveDataMap fog cleared')
    elif 'WorldMapMaskTextureV4' in save_data:
        mask = save_data['WorldMapMaskTextureV4']['value']
        mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapMaskTextureV4 fog cleared')
    hidden_locations = save_data.get(
        'Local_HiddenLocationFlagMap', {}).get('value', [])
    for entry in hidden_locations:
        entry['value'] = False
    print(f'  Hidden locations set: {len(hidden_locations)} entries')
    save_data['Local_ShowSkyIslandCloudOnWorldMapUI'] = {
        'value': False, 'id': None, 'type': 'BoolProperty'}
    print('  Sky island cloud overlay disabled')
    save_sav(
        GvasFile.load(data), path,
        custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)


def discover_local_data_folders() -> list[str]:
    """Return folders containing Steam/local LocalData.sav files."""

    folders: list[str] = []
    direct = os.path.join(savegames_path, 'LocalData.sav')
    if os.path.isfile(direct):
        folders.append(savegames_path)
    elif os.path.isdir(savegames_path):
        for owner in os.listdir(savegames_path):
            owner_path = os.path.join(savegames_path, owner)
            if not os.path.isdir(owner_path):
                continue
            for world in os.listdir(owner_path):
                world_path = os.path.join(owner_path, world)
                if os.path.isfile(os.path.join(world_path, 'LocalData.sav')):
                    folders.append(world_path)
    if constants.loaded_level_json and constants.current_save_path:
        loaded = os.path.normcase(os.path.abspath(constants.current_save_path))
        discovered = {
            os.path.normcase(os.path.abspath(folder)) for folder in folders}
        if (os.path.isfile(os.path.join(loaded, 'LocalData.sav'))
                and loaded not in discovered):
            folders.append(constants.current_save_path)
    return folders


def clear_fog_in_all_subfolders() -> int:
    folders = discover_local_data_folders()
    for folder in folders:
        backup_local_data(folder)
        print(t('Clearing fog in: {path}', path=folder))
        clear_fog_in_local_data(os.path.join(folder, 'LocalData.sav'))
    print('=' * 80)
    print(t('Total worlds/servers updated: {copied_count}', copied_count=len(folders)))
    print('=' * 80)
    return len(folders)


class RestoreMapDialog(BaseDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(
            t('tool.restore_map'), parent, min_size=(720, 390),
            kicker=t('repair.workflow.kicker', default='Repair and recovery'))
        folders = discover_local_data_folders()
        self.workflow_review = BulkWorkflowReview(
            source=t(
                'restore_map.detected',
                default='{count} local world(s) detected', count=len(folders)),
            target=t(
                'restore_map.target',
                default='Map visibility in each LocalData.sav'),
            review=t(
                'restore_map.review',
                default=(
                    'Clear fog and hidden-location flags while preserving map '
                    'markers, icons, and other local map data.')),
            parent=self,
        )
        self.workflow_review.set_risk(
            t(
                'restore_map.risk',
                default='This writes directly to each discovered LocalData.sav.'),
            t(
                'restore_map.backup',
                default=(
                    'A separate copy of every LocalData.sav is created under '
                    'Backups/Restore Map before that file is changed.')),
        )
        self.content_layout.addWidget(self.workflow_review)

        self.xgp_btn = make_button(
            t('restore_map.xgp_action', default='Clear Game Pass fog'),
            'secondary', parent=self)
        self.xgp_btn.clicked.connect(self.on_xgp_clear_fog)
        self.footer.insertWidget(self.footer.count() - 1, self.xgp_btn)
        self.run_btn = make_button(
            t('restore_map.local_action', default='Clear local fog'),
            'primary', parent=self)
        self.run_btn.setEnabled(bool(folders))
        self.run_btn.clicked.connect(self.on_local_clear_fog)
        self.footer.insertWidget(self.footer.count() - 1, self.run_btn)
        self._primary_button = self.run_btn if folders else self.xgp_btn

    def _begin(self, label: str) -> None:
        self.run_btn.setEnabled(False)
        self.xgp_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.workflow_review.progress.setRange(0, 0)
        self.workflow_review.progress.setFormat(label)
        self.workflow_review.progress.show()

    def _finish(self, message: str, success: bool = True) -> None:
        self.workflow_review.set_progress(
            1, 1,
            t('repair.workflow.complete', default='Repair complete') if success
            else t('repair.workflow.failed_short', default='Repair failed'))
        self.workflow_review.set_result(message, success=success)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText(t('button.close', default='Close'))
        self.close_btn.setEnabled(True)
        self._primary_button = self.cancel_btn

    def _fail(self, error) -> None:
        self._finish(t(
            'restore_map.failed',
            default=(
                'Map restore did not complete. Restore affected LocalData.sav '
                'files from Backups/Restore Map. Details: {detail}'),
            detail=str(error).strip()), success=False)

    def on_local_clear_fog(self) -> None:
        self._begin(t('restore_map.running', default='Clearing local map fog…'))
        run_with_loading(
            lambda count: self._finish(t(
                'restore_map.complete',
                default='Map visibility restored in {count} local world(s).',
                count=count)),
            clear_fog_in_all_subfolders,
            parent=self,
            on_error=self._fail,
            local_state=True,
        )

    def on_xgp_clear_fog(self) -> None:
        from palworld_xgp_import.gamepass_manager import (
            _is_elevated,
            _read_container_data,
            block_gamingservices_network,
            find_container_paths,
            read_container_index,
            relaunch_elevated,
        )
        from palworld_xgp_import.container_types import ContainerFileList, FILETIME

        if not _is_elevated():
            if show_question(
                self,
                t('xgp.admin.title', default='Administrator Required'),
                t(
                    'xgp.admin.msg',
                    default=(
                        'Clearing fog on an Xbox/Game Pass save requires '
                        'administrator rights so cloud sync can be blocked.\n\n'
                        'Relaunch PalTrainer as administrator now?')),
            ):
                if relaunch_elevated():
                    QApplication.quit()
                    return
                show_critical(self, t('error.title'), t(
                    'xgp.admin.relaunch_failed',
                    default='Could not relaunch as administrator.'))
            else:
                self.workflow_review.set_result(t(
                    'repair.workflow.cancelled',
                    default='Cancelled. No save data was changed.'), success=True)
            return

        containers = find_container_paths()
        if not containers:
            self._finish(t(
                'restore_map.no_xgp', default='No Game Pass saves were found.'),
                success=False)
            return
        container_path = containers[0]
        index = read_container_index(container_path)
        local_containers = [
            item for item in index.containers
            if 'LocalData' in item.container_name]
        if not local_containers:
            self._finish(t(
                'restore_map.no_local_data',
                default='No LocalData containers were found.'), success=False)
            return

        self.workflow_review.set_context(
            source=t(
                'restore_map.xgp_detected',
                default='{count} Game Pass world(s) detected',
                count=len(local_containers)),
            target=t('restore_map.target', default='Map visibility in each LocalData.sav'),
            review=t(
                'restore_map.xgp_review',
                default=(
                    'Block cloud sync, back up each container, clear fog, and '
                    'restore network access.')),
        )
        self._begin(t('restore_map.running_xgp', default='Clearing Game Pass map fog…'))
        network_state: dict[str, list[str]] = {'adapters': []}

        def task() -> tuple[list[str], int]:
            adapter = block_gamingservices_network()
            if not adapter:
                raise RuntimeError(
                    'Could not block Game Pass cloud sync; no containers were changed.')
            network_state['adapters'] = [adapter]
            updated = 0
            for container in local_containers:
                raw = _read_container_data(container_path, container)
                if not raw:
                    continue
                with tempfile.NamedTemporaryFile(
                    suffix='.sav', delete=False) as temp_file:
                    temp_file.write(raw)
                    temp_path = temp_file.name
                try:
                    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
                    backup_dir = os.path.join(
                        restore_map_path, timestamp,
                        container.container_name.replace('-', '_'))
                    os.makedirs(backup_dir, exist_ok=True)
                    shutil.copy2(
                        temp_path, os.path.join(backup_dir, 'LocalData.sav'))
                    clear_fog_in_local_data(temp_path)
                    with open(temp_path, 'rb') as modified_file:
                        modified = modified_file.read()
                    container_dir = os.path.join(
                        container_path,
                        container.container_uuid.bytes_le.hex().upper())
                    lists = sorted(
                        name for name in os.listdir(container_dir)
                        if name.startswith('container.'))
                    if not lists:
                        continue
                    with open(os.path.join(container_dir, lists[0]), 'rb') as manifest:
                        file_list = ContainerFileList.from_stream(manifest)
                    if not file_list.files:
                        continue
                    data_path = os.path.join(
                        container_dir,
                        file_list.files[0].uuid.bytes_le.hex().upper())
                    with open(data_path, 'wb') as output:
                        output.write(modified)
                    container.mtime = FILETIME.far_future()
                    container.size = len(modified)
                    updated += 1
                finally:
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
            index.write_file(container_path)
            return [adapter], updated

        def done(result: tuple[list[str], int]) -> None:
            adapters, count = result
            if adapters:
                from palworld_xgp_import.gamepass_manager import restore_network
                restore_network(adapters, self)
            self._finish(t(
                'restore_map.xgp_complete',
                default='Map visibility restored in {count} Game Pass world(s).',
                count=count))

        def failed(error) -> None:
            adapters = network_state['adapters']
            if adapters:
                from palworld_xgp_import.gamepass_manager import restore_network
                restore_network(adapters, self)
                network_state['adapters'] = []
            self._fail(error)

        run_with_loading(
            done, task, parent=self, on_error=failed, local_state=True)


def restore_map(parent=None) -> RestoreMapDialog:
    return RestoreMapDialog(parent or QApplication.activeWindow())


def main() -> None:
    _app = QApplication.instance() or QApplication([])
    dialog = restore_map()
    dialog.exec()


if __name__ == '__main__':
    main()
