from __future__ import annotations
import pytest
from tests.dynamic_importer import import_from

tokens = import_from('palworld_aio.ui.chrome.tokens')
qss_builder = import_from('palworld_aio.ui.chrome.qss_builder')


def test_dark_palette_resolves():
    p = tokens.resolve('dark')
    assert p['canvas']
    assert p['accent']
    assert p['text']
    assert p['border']


def test_dark_palette_is_deck_operations_v2():
    # Plan 019: warm dark canvas, amber accent, teal success; cyan retired.
    p = tokens.resolve('dark')
    assert p['canvas'] == '#141312'
    assert p['accent'] == '#F59E0B'
    assert p['success'] == '#2DD4BF'
    assert '#7DD3FC' not in str(p).upper().replace('#7DD3FC', '#7DD3FC')
    for value in p.values():
        assert '#7DD3FC' not in value, 'retired cyan leaked into palette'


def test_unknown_theme_raises():
    with pytest.raises(KeyError):
        tokens.resolve('nope')


def test_all_palettes_have_same_keys():
    keys = None
    for name, palette in tokens.PALETTES.items():
        if keys is None:
            keys = set(palette)
        else:
            assert set(palette) == keys, f'{name} palette keys drifted'


def test_spacing_is_4px_grid():
    assert set(tokens.SPACING.values()) == {4, 8, 12, 16, 20, 24, 32, 40}
    for value in tokens.SPACING.values():
        assert value % 4 == 0


def test_type_scale_shape():
    for name, spec in tokens.TYPE.items():
        px, weight = spec
        assert px > 0
        assert weight in (400, 500, 600, 700)
    assert tokens.TYPE['page_title'] == (24, 600)
    assert tokens.TYPE['section_title'] == (17, 600)
    assert tokens.TYPE['body'] == (14, 400)
    assert tokens.TYPE['table'] == (13, 400)
    assert tokens.TYPE['metadata'] == (12, 400)
    assert tokens.TYPE['caption'] == (11, 400)


def test_no_text_role_is_undersized():
    for name, (px, _weight) in tokens.TYPE.items():
        assert px >= 11, f'{name} is smaller than the audit minimum'


def test_audit_radii_and_shell_dimensions():
    assert tokens.RADIUS == {'sm': 6, 'md': 8, 'lg': 10, 'xl': 12, 'pill': 9999}
    assert tokens.LAYOUT['minimum_width'] == 1024
    assert tokens.LAYOUT['minimum_height'] == 700
    assert tokens.LAYOUT['sidebar_expanded'] == 240
    assert tokens.LAYOUT['sidebar_collapsed'] == 64
    assert tokens.LAYOUT['inspector_width'] == 340
    assert tokens.LAYOUT['content_padding'] == 24


def test_density_presets_stay_on_the_spacing_grid():
    assert set(tokens.DENSITY) == {'compact', 'standard', 'comfortable'}
    for preset in tokens.DENSITY.values():
        assert set(preset) == {'row', 'control', 'gap'}
        assert all(value % 4 == 0 for value in preset.values())


def test_focus_and_motion_contracts():
    palette = tokens.resolve('dark')
    assert palette['focus_ring'] != palette['border']
    assert tokens.FOCUS['width'] >= 2
    assert 160 <= tokens.motion_duration('drawer') <= 220
    assert 180 <= tokens.motion_duration('sidebar') <= 220
    assert tokens.motion_duration('dialog', reduced_motion=True) == 0
    with pytest.raises(KeyError):
        tokens.motion_duration('unknown')


def test_generated_theme_rejects_retired_shell_colors():
    qss = qss_builder.build_qss('dark').lower()
    for legacy in tokens.RETIRED_COLORS:
        assert legacy.lower() not in qss
    assert tokens.RETIRED_RGBA_PREFIX.lower() not in qss


def test_rgba_helper():
    assert tokens.rgba('#7DD3FC', 0.2) == 'rgba(125,211,252,0.2)'


def test_build_qss_contains_core_selectors():
    qss = qss_builder.build_qss('dark')
    for selector in ('QPushButton', 'QLineEdit', 'QTreeWidget', 'QMenu',
                     'QToolTip', 'QScrollBar', 'QTabBar', 'QHeaderView::section'):
        assert selector in qss, f'missing {selector}'


def test_build_qss_no_unknown_theme():
    with pytest.raises(KeyError):
        qss_builder.build_qss('nope')


def test_build_qss_hover_and_disabled_states():
    qss = qss_builder.build_qss('dark')
    for state in (':hover', ':pressed', ':focus', ':disabled'):
        assert state in qss, f'missing {state} state'
