from __future__ import annotations

import json

from tests.dynamic_importer import import_from
from tests.test_registry import PROJECT_ROOT


i18n = import_from('i18n')
localization = import_from('palworld_aio.ui.chrome.localization')


FOUNDATION_KEYS = {
    'ui.action.cancel',
    'ui.action.close',
    'ui.action.generic',
    'ui.action.more',
    'ui.context.item_accessible',
    'ui.context.separator',
    'ui.drawer.close',
    'ui.icon.accessible',
    'ui.inventory.empty_slot',
    'ui.inventory.empty_slot_accessible',
    'ui.inventory.slot_accessible',
    'ui.notification.accessible',
    'ui.notification.dismiss',
    'ui.page.accessible',
    'ui.pal.card_accessible',
    'ui.pending.many',
    'ui.pending.none',
    'ui.pending.one',
    'ui.pending.review',
    'ui.save.context_accessible',
    'ui.save.no_save_detail',
    'ui.save.no_save_title',
    'ui.search.accessible_name',
    'ui.segmented.options',
    'ui.state.clear_filters',
    'ui.state.loading',
    'ui.state.retry',
}


def test_every_foundation_key_has_english_copy():
    path = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    resources = json.loads(path.read_text(encoding='utf-8-sig'))
    assert not (FOUNDATION_KEYS - resources.keys())
    assert all(resources[key].strip() for key in FOUNDATION_KEYS)


def test_non_english_locale_falls_back_to_english_foundation_copy():
    i18n.load_resources('fr_FR')
    assert localization.tr('ui.pending.none', 'fallback') == 'No pending changes'
    assert localization.tr('ui.pending.many', 'fallback {count}', count=3) == '3 pending changes'
    i18n.load_resources('en_US')


def test_component_translation_helper_has_prebootstrap_default():
    assert localization.tr('ui.does.not.exist', 'Readable fallback') == 'Readable fallback'
    assert localization.tr('ui.does.not.exist', '{count} records', count=2) == '2 records'
