# Release Signing Policy

PalTrainer release artifacts must be signed before publication. Signing keys and
passwords are release infrastructure secrets and must never be committed to the
repository, embedded in `tauri.conf.json`, or stored in the working tree.

## Windows artifacts

- Sign the generated executable and installer artifacts with the project-owned
  Authenticode certificate in the release environment.
- Store the certificate and password in the CI secret store or a protected local
  release machine. Use a temporary file only for the duration of signing and
  remove it immediately afterward.
- Verify the signature, certificate chain, subject, expiry, and timestamp before
  publishing artifacts.
- Publish SHA-256 checksums beside every installer and retain the exact signed
  artifacts used to calculate them.

## Tauri updater artifacts

Updater signing is a separate key from Windows Authenticode signing. Enable and
configure the Tauri updater only when its update protocol and key custody are
approved. The private updater key must remain outside Git and CI logs; only the
public verification key may be distributed with the application.

## Release gate

A release is blocked when signing fails, verification is unavailable, a key is
expired or revoked, or checksums do not match the published files.
