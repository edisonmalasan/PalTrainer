import re
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['uv', 'pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHANGELOG_FILE = PROJECT_ROOT / 'changelogs.md'
OUTPUT_FILE = PROJECT_ROOT / 'CHANGELOG.multilang.md'

LANGUAGES = [
    ('en_US', 'English', 'en', '🇺🇸', True),
    ('zh_CN', '中文', 'zh-CN', '🇨🇳', False),
    ('de_DE', 'Deutsch', 'de', '🇩🇪', False),
    ('es_ES', 'Español', 'es', '🇪🇸', False),
    ('fr_FR', 'Français', 'fr', '🇫🇷', False),
    ('ru_RU', 'Русский', 'ru', '🇷🇺', False),
    ('ja_JP', '日本語', 'ja', '🇯🇵', False),
    ('ko_KR', '한국어', 'ko', '🇰🇷', False),
    ('pt_BR', 'Português', 'pt_BR', '🇧🇷', False),
    ('pt_PT', 'Português', 'pt_PT', '🇵🇹', False),
]

def extract_latest_version(text: str) -> tuple[str, str]:
    m = re.match(r'^#(\d+\.\d+\.\d+)\n(.*?)(?=\n#\d+\.\d+\.\d+|\Z)', text, re.DOTALL | re.MULTILINE)
    if not m:
        raise ValueError('No version section found')
    return m.group(1), m.group(2).strip()

def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    placeholders = re.findall(r'\{[^}]+\}', text)
    tokens = {}
    for i, ph in enumerate(placeholders):
        tok = f'__PH{i}__'
        tokens[tok] = ph
        text = text.replace(ph, tok, 1)
    return text, tokens

def restore_placeholders(text: str, tokens: dict[str, str]) -> str:
    for tok, ph in tokens.items():
        text = text.replace(tok, ph)
    return text

def translate_text(text: str, target_lang: str) -> str:
    if not text.strip():
        return text
    protected, tokens = protect_placeholders(text)
    translator = GoogleTranslator(source='en', target=target_lang)
    try:
        translated = translator.translate(protected)
        translated = restore_placeholders(translated, tokens)
        return translated
    except Exception as e:
        print(f'\n  [WARN] translate failed: {e}')
        return text

def main():
    print('=' * 60)
    print('  TRANSLATE CHANGELOG')
    print('=' * 60)

    with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    version, body = extract_latest_version(content)
    print(f'\n  Latest version: {version}')
    print(f'  Lines: {len(body.splitlines())}')

    sections = []
    for code, name, google_code, flag, is_default in LANGUAGES:
        try:
            print(f'  Translating {name}...', end=' ')
        except UnicodeEncodeError:
            print(f'  Translating {code}...', end=' ')
        if is_default:
            translated = body
        else:
            translated = translate_text(body, google_code)
        open_attr = ' open' if is_default else ''
        section = (
            f'<details{open_attr}>\n'
            f'<summary>{flag} {name}</summary>\n\n'
            f'{translated}\n\n'
            f'</details>'
        )
        sections.append(section)
        print('OK')

    output = '# 🗒️ Changelog\n\n' + '\n\n'.join(sections) + '\n'

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f'\n  Saved to {OUTPUT_FILE}')
    print('  Done')

if __name__ == '__main__':
    main()
