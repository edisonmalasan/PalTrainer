# Troubleshooting

## The save is reported as stale

Another process changed, removed, or replaced a file after PalTrainer loaded
it. Close Palworld and sync tools, reload the save, and create a fresh preview.
Do not force the old session to write over the newer file.

## The format is unsupported

The save may use a future game version, an unsupported compression path, or a
malformed container. Keep the original, use read-only inspection if available,
and include the compatibility warning and diagnostic report when filing an
issue. Do not rename the file extension or edit its bytes manually.

## The application cannot find a save

Use the file or folder picker and select the actual save root. Steam saves and
XGP WGS data have different layouts. The selected path must remain inside an
approved user-selected root; paths outside it are rejected by design.

## An edit failed

Keep the automatic backup and the original untouched copy. Read the exact
error and preview warning, then reload the save before trying again. If the
operation created a partial temporary artifact, close PalTrainer and remove
only the clearly identified temporary file, never the original save.

## XGP import or extraction failed

Confirm that the WGS user directory contains a valid `containers.index` and
recognized blobs. Pause cloud synchronization during the operation. A cloud
client can replace local files after import; restore the directory backup if
the resulting container set is incorrect.

## The game will not load an edited save

1. Close the game and sync client.
2. Restore the backup made immediately before the edit.
3. Confirm the restored save loads before attempting another change.
4. Preserve the failing save, backup, diagnostic output, and compatibility
   warning for investigation.

Never send a personal save publicly without removing private identifiers and
confirming that the recipient needs the file.

## Reporting a problem

Include the PalTrainer version, operating system, source format, reported save
metadata, exact operation, and relevant diagnostic code. Do not include raw
save data, account identifiers, or backup archives unless they have been
reviewed and intentionally redacted.
