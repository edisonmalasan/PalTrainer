"""Guard tests for Breeding hint copy and single-CTA empty state
(uiux-audit-remediation 8.3): instructional copy must not reference a
control in the wrong position, and the empty state keeps exactly one
"Select a Pal" action while no pal is selected.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from

tab_mod = import_from('palworld_aio.ui.tabs.breeding_tab')
empty_state_mod = import_from('palworld_aio.widgets.empty_state')
i18n_mod = import_from('i18n')

_app = None

POSITIONAL_WORDS = ('above', 'below', 'beside')


def _app_instance():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


@pytest.fixture(scope='session', autouse=True)
def _i18n_en_us():
    i18n_mod.load_resources('en_US')
    yield


@pytest.fixture(scope='session')
def app():
    return _app_instance()


@pytest.fixture(scope='session')
def tab(app):
    return tab_mod.BreedingTab(None)


# --------------------------------------------- 8.3 hint copy

def test_breeding_hint_key_is_position_neutral():
    hint = i18n_mod.t('breeding.hint')
    lowered = hint.lower()
    for word in POSITIONAL_WORDS:
        assert word not in lowered, f'hint references position: {word!r}'
    assert 'breeding combination' in lowered


def test_breeding_hint_fallback_is_position_neutral(tab):
    lowered = tab._hint_label.text().lower()
    for word in POSITIONAL_WORDS:
        assert word not in lowered, f'hint references position: {word!r}'


def test_no_positional_breeding_strings_in_en_us():
    import json
    from tests.test_registry import PROJECT_ROOT
    data = json.loads(
        (PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json').read_text(encoding='utf-8-sig'))
    for key, text in data.items():
        if key.startswith('breeding.'):
            lowered = str(text).lower()
            for word in POSITIONAL_WORDS:
                assert word not in lowered, f'{key} references position: {word!r}'


# ------------------------------------- single-CTA empty state (unchanged)

def test_empty_state_hides_standalone_cta_and_shows_one_action(tab):
    tab._selected_tribe = None
    tab._breeding_data = None
    tab._do_update_results()
    assert not tab._select_btn.isVisibleTo(tab._select_btn.parentWidget())
    assert not tab._hint_label.isVisibleTo(tab._hint_label.parentWidget())
    empties = list(tab.findChildren(empty_state_mod.EmptyState))
    assert len(empties) == 1
    empty = empties[0]
    # the EmptyState owns the single visible "Select a Pal" affordance
    buttons = [b for b in empty.findChildren(type(tab._select_btn))
               if b.text() == 'Select a Pal...']
    assert len(buttons) == 1
    assert buttons[0].isVisibleTo(buttons[0].parentWidget())
    # the standalone twin stays hidden (no duplicate CTA)
    assert not tab._select_btn.isVisibleTo(tab._select_btn.parentWidget())


def test_post_selection_restores_reselect_affordance(tab):
    tab._selected_tribe = None
    tab._breeding_data = None
    tab._do_update_results()
    # simulate a selection: results rebuild shows the standalone button again
    tab._selected_tribe = 'sheepball'
    tab._selected_name = 'Lamball'
    tab._selected_icon = None
    tab._breeding_data = {'pal_info': {}, 'children': [], 'parents': []}
    tab._do_update_results()
    assert tab._select_btn.isVisibleTo(tab._select_btn.parentWidget())
    assert tab._hint_label.isVisibleTo(tab._hint_label.parentWidget())
    assert tab._hint_label.text() == i18n_mod.t('breeding.hint')
