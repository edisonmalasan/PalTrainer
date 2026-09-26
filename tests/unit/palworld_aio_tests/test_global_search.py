from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tests.dynamic_importer import import_from


search_mod = import_from('palworld_aio.ui.global_search')
context_mod = import_from('palworld_aio.ui.workspace_context')
router_mod = import_from('palworld_aio.ui.router')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def records():
    return search_mod.build_search_records(
        players=[{'uid': 'p1', 'name': 'Ada', 'guild_name': 'Builders'}],
        guilds=[{'id': 'g1', 'name': 'Builders', 'member_count': 3}],
        bases=[{'id': 'b1', 'name': 'North Base', 'guild_id': 'g1',
                'guild_name': 'Builders'}],
        pals=[{'instance_id': 'pal1', 'name': 'Lamball', 'owner_uid': 'p1',
               'owner_name': 'Ada'}],
        items=[{'asset': 'item1', 'name': 'Pal Sphere'}],
        skills=[{'asset': 'skill1', 'name': 'Power Shot'}],
        technologies=[{'asset': 'tech1', 'name': 'Egg Incubator'}],
        world_data=[{'id': 'fast1', 'name': 'Plateau of Beginnings'}],
    )


def _router():
    context = context_mod.WorkspaceContext()
    context.finish_load(context_mod.SaveIdentity('world', 'Island', 'C:/Level.sav'))
    return context, router_mod.WorkspaceRouter(context)


def test_fixture_read_models_cover_every_required_result_type(records):
    assert {record.entity_type for record in records} == set(search_mod.SearchEntityType)
    assert all(record.type_label for record in records)
    assert all(record.identifier and record.label for record in records)


def test_search_matches_names_ids_details_and_multiple_terms(records):
    index = search_mod.GlobalSearchIndex(records)
    assert index.search('ada')[0].entity_type is search_mod.SearchEntityType.PLAYER
    assert index.search('g1')[0].entity_type is search_mod.SearchEntityType.GUILD
    assert index.search('north builders')[0].identifier == 'b1'
    assert index.search('egg incubator')[0].identifier == 'tech1'
    assert not index.search('missing record')


def test_player_and_base_results_navigate_with_identifier_context(records):
    context, router = _router()
    index = search_mod.GlobalSearchIndex(records)
    player = next(record for record in records if record.identifier == 'p1')
    result = index.activate(player, router)
    assert result.route.route_id == 'players'
    assert context.snapshot.player.identifier == 'p1'
    assert result.restored_view_state['selected'] == ['p1']

    base = next(record for record in records if record.identifier == 'b1')
    result = index.activate(base, router)
    assert result.route.route_id == 'bases'
    assert context.snapshot.guild.identifier == 'g1'
    assert context.snapshot.base.identifier == 'b1'


def test_reference_results_open_correct_section_and_identifier(records):
    _context, router = _router()
    index = search_mod.GlobalSearchIndex(records)
    item = next(record for record in records if record.identifier == 'item1')
    result = index.activate(item, router)
    assert result.route.route_id == 'docs'
    assert result.restored_view_state == {'section': 'items', 'selected_id': 'item1'}


def test_dialog_shows_type_labels_and_activates_contextual_result(app, records):
    context, router = _router()
    dialog = search_mod.GlobalSearchDialog(search_mod.GlobalSearchIndex(records), router)
    dialog.refresh_results('Lamball')
    assert dialog.result_list.count() == 1
    assert 'Pal' in dialog.result_list.item(0).text()
    dialog._activate_item(dialog.result_list.item(0))
    assert router.current_route_id == 'pal_editor'
    assert context.snapshot.player.identifier == 'p1'


def test_duplicate_identifiers_are_rejected_per_entity_type(records):
    with pytest.raises(ValueError, match='unique per type'):
        search_mod.GlobalSearchIndex((records[0], records[0]))
    # The same raw ID in a different type remains unambiguous.
    changed = search_mod.GlobalSearchRecord(
        search_mod.SearchEntityType.ITEM, records[0].identifier, 'Ada item', '',
        'docs', {}, {'section': 'items'},
    )
    search_mod.GlobalSearchIndex((records[0], changed))
