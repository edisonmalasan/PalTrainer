# Supported Save Versions

This document describes the compatibility boundary of the current PalTrainer
build. It is intentionally conservative: a file that can be opened is not
automatically safe to rewrite.

## Container formats

The Rust save engine recognizes the Palworld container headers used by:

- `PLZ` saves, including decompression and the current write path.
- `CNK` saves, including nested-header parsing and decompression where the
  payload is supported. CNK writing is currently rejected as unsupported.
- `PLM` headers. PLM writing is currently rejected as unsupported because its
  Oodle path is not bundled.

The engine validates lengths, magic values, compression streams, and GVAS
structure before exposing data to editing workflows. Unsupported or malformed
input must be treated as read-only and must never be rewritten as a best guess.

## Game versions

PalTrainer does not yet publish a complete game-build allowlist. GVAS metadata
such as save-game version, package version, engine version, branch, and custom
version entries is read from the file and carried through conversion results.
Compatibility for a particular Palworld release is established only after
fixtures pass parser, mutation, and sacred-roundtrip tests for that release.

When a save reports an unknown or future version, PalTrainer must:

1. show a clear compatibility warning;
2. default to read-only behavior;
3. preserve unknown bytes and fields during any supported roundtrip; and
4. require an explicit, validated preview before a mutation is allowed.

Do not remove the original save to work around a compatibility warning.

## Xbox / Game Pass

The current XGP tooling understands the `containers.index` v14 layout and
recognized save blobs in WGS user directories. Cloud synchronization can
replace local files after import, so the application warns before write-back
and creates a backup of the target directory.

## Updating this document

Add a game build to the published compatibility list only with representative
fixtures, successful parse and write tests, and a verified in-game load. Record
known limitations in the release notes and keep unsupported formats visibly
read-only.
