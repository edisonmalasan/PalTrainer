from __future__ import annotations

from PyQt6.QtGui import QFont

from tests.dynamic_importer import import_from


fonts = import_from('palworld_aio.ui.chrome.fonts')
qss_builder = import_from('palworld_aio.ui.chrome.qss_builder')


def test_bundled_font_manifest_contains_every_real_weight():
    assert fonts.BUNDLED_FONT_FILES == (
        'HankenGrotesk-Regular.ttf',
        'HankenGrotesk-Medium.ttf',
        'HankenGrotesk-SemiBold.ttf',
        'Inter_28pt-Regular.ttf',
        'Inter_28pt-Medium.ttf',
        'Inter_28pt-SemiBold.ttf',
    )
    assert all(path.is_file() for path in fonts.bundled_font_paths())


def test_font_factories_use_bundled_family_stacks_and_real_weights():
    body = fonts.body_font(px=14, weight=400)
    heading = fonts.heading_font(px=24, weight=700)

    assert body.families()[0] == 'Inter 28pt'
    assert body.pixelSize() == 14
    assert body.weight() == QFont.Weight.Normal
    assert heading.families()[0] == 'Hanken Grotesk'
    assert heading.pixelSize() == 24
    assert heading.weight() == QFont.Weight.DemiBold


def test_generated_qss_never_requests_synthetic_bold():
    qss = qss_builder.build_qss('dark').lower()
    assert 'font-weight: 700' not in qss
    assert 'font-weight: bold' not in qss
