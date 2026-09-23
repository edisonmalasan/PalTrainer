from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


palette_mod = import_from('palworld_aio.ui.chrome.command_palette')
routes = import_from('palworld_aio.ui.routes')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _commands(observed):
    commands = list(palette_mod.route_commands(
        lambda route_id: observed.append(('route', route_id))))
    commands.extend((
        palette_mod.CommandDescriptor(
            'app:load', 'Load Save', 'Application',
            lambda: observed.append(('app', 'load')), ('open', 'file'), 'Ctrl+O'),
        palette_mod.CommandDescriptor(
            'app:save', 'Save Changes', 'Application',
            lambda: observed.append(('app', 'save')), ('write',), 'Ctrl+S'),
    ))
    return commands


def test_palette_contains_every_route_and_safe_load_save_commands(app):
    palette = palette_mod.CommandPalette(_commands([]))
    expected = {f'route:{route_id}' for route_id in routes.ROUTES.ids}
    assert expected <= set(palette.visible_command_ids)
    assert {'app:load', 'app:save'} <= set(palette.visible_command_ids)


def test_fuzzy_filter_matches_labels_groups_help_and_keywords(app):
    palette = palette_mod.CommandPalette(_commands([]))
    palette.set_query('pinv')
    assert palette.visible_command_ids[0] == 'route:player_inventory'
    palette.set_query('troubleshoot')
    assert palette.visible_command_ids == ('route:diagnostics',)
    palette.set_query('does-not-exist')
    assert not palette.visible_command_ids
    assert not palette.empty_label.isHidden()


def test_keyboard_selection_and_enter_execute_current_command(app):
    observed = []
    palette = palette_mod.CommandPalette(_commands(observed))
    executed = []
    palette.commandExecuted.connect(executed.append)
    palette.open_palette()
    palette.set_query('save')
    index = palette.visible_command_ids.index('app:save')
    palette.result_list.setCurrentRow(index)
    palette.search_input.setFocus()
    QTest.keyClick(palette.search_input, Qt.Key.Key_Return)
    assert observed == [('app', 'save')]
    assert executed == ['app:save']
    assert palette.result() == palette.DialogCode.Accepted


def test_duplicate_command_ids_are_rejected(app):
    command = palette_mod.CommandDescriptor('same', 'One', 'App', lambda: None)
    with pytest.raises(ValueError, match='unique'):
        palette_mod.CommandPalette((command, command))
