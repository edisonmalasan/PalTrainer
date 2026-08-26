# Phase 20 — Docs & i18n

**Goal:** In-app help + 10 locales as in PST.

**Source:** `resources/tab_guide/{en,de,es,fr,ja,ko,ru,zh}/**/*.html` 88 guides, `resources/i18n/*.json` 10 locales (`en_US`→`zh_CN`), `src/i18n/__init__.py t()` fallback `zh_CN`.

| Task | Branch | Scope | Verification |
|------|--------|-------|--------------|
| 20.1 | `feat/docs-tab` | Render `tab_guide` HTML per tab + `wiki_tab.py` search | `DocsTab` renders `intro` |
| 20.2 | `feat/i18n` | `t()` `load_resources` + native names map, `set_language` persisted `user.cfg`, 10 locales menu in header | `t()` fallback `en_US` |
| 20.3 | `feat/docs-breeding` | `BreedingTab` `_SelectPalDialog` grid ready (already `BreedingView` exists) polish per Image 14 | breeding grid search |

**Outcome:** `Docs` tab with searchable guide per section; language switch persists.
