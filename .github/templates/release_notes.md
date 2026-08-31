<!-- Release Notes Template - PalTrainer -->
<!-- ────────────────────────────────────────────────────────────────────────── -->
<!-- This is a plain Markdown file. Edit it freely — it's the human-readable
     source of truth for release notes.
     The Build All & Release workflow reads this file and substitutes the
     ${VAR} placeholders below with live values at release-creation time.
     Available variables:
       ${APP_NAME}        e.g. PalTrainer
       ${VERSION}         e.g. 2.0.3
       ${GAME_VERSION}    e.g. 1.0.0
       ${REPO_URL}        https://github.com/<owner>/<repo>
       ${RELEASE_URL}     direct link to this release's tag
       ${DISCORD_URL}     https://discord.gg/sYcZwcT4cT
        __CHANGELOG_ENTRY__ replaced from changelogs.md for this version
        Uses __CHANGELOG_ENTRY__ as a literal marker for multiline insertion.
-->
<!-- ────────────────────────────────────────────────────────────────────────── -->

# 🚀 ${APP_NAME} v${VERSION}

### 🛠️ Compatibility
* **App Version:** `${VERSION}`
* **Game Version:** `${GAME_VERSION}`

---

### 📦 Downloads

| Platform | File |
|---|---|
| 🪟 Windows (single .exe) | `${APP_NAME}-v${VERSION}-win.exe` |
| 🪟 Windows (standalone folder) | `PalTrainer_standalone_v${VERSION}.zip` |
| 🐧 Linux   | `${APP_NAME}-v${VERSION}-linux.AppImage` |
| 🍎 macOS   | `${APP_NAME}-v${VERSION}-macos.dmg` |

📥 Full release: ${RELEASE_URL}

---

### 🔐 Checksums (SHA256)

```
__CHECKSUMS__
```

---

### 📝 Changelog

__CHANGELOG_ENTRY__

---

### 🤝 Support

* 🐛 [Open a GitHub issue](${REPO_URL}/issues)
* 💬 [Join our Discord](${DISCORD_URL})
* 📩 Use the project issue tracker for support and bug reports.

*Thank you for using ${APP_NAME}!* 🙏
