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
    for value in tokens.SPACING.values():
        assert value % 4 == 0


def test_type_scale_shape():
    for name, spec in tokens.TYPE.items():
        px, weight = spec
        assert px > 0
        assert weight in (400, 500, 600, 700)
    # Plan 019 type scale, top-nav-shell: display 19/700, title 14/600
    # (real bundled SemiBold, no synthetic bold).
    assert tokens.TYPE['display'] == (19, 700)
    assert tokens.TYPE['title'] == (14, 600)


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
