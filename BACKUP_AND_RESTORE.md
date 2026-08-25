# Backup and Restore

PalTrainer is designed to make a recoverable copy before save-modifying work.
Backups are a safety boundary, not a substitute for the user's own archival
copies.

## Before editing

1. Close Palworld and any cloud-sync client that may rewrite the save.
2. Keep an untouched copy of the complete save root in a separate location.
3. Load the save in PalTrainer and resolve any stale-file or compatibility
   warning before previewing a mutation.
4. Review the preview. It lists affected entities, files, warnings, and the
   backup destination.

## During an edit

Every supported mutation must create an automatic backup before writing. The
backend also checks whether files changed since the save session was opened.
When a stale file is detected, stop, reload the save, and review the new state.

Writes use temporary files and atomic replacement where the operation supports
it. Do not interrupt a write, close the application, or allow a sync client to
modify the save during that window.

## Restoring a backup

1. Close Palworld and pause cloud synchronization.
2. In PalTrainer, open the backup list from the save-session workflow.
3. Select the backup whose timestamp and source path match the intended save.
4. Review the restore preview and confirm the operation.
5. Reopen the save in Palworld only after the restore completes successfully.

For a manual restore, copy the complete backup contents back to the original
save root. Preserve the directory layout and do not mix files from different
backup timestamps.

## XGP restores

XGP imports back up the target WGS directory before packaging. Restore the
complete WGS backup, not an individual blob, and resume synchronization only
after verifying the restored container set.

## What to retain

Keep at least one known-good original and the backup created immediately before
each important edit. Never commit save files, backups, archives, or logs to Git.
