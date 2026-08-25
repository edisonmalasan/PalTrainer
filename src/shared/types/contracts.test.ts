import { describe, expect, it } from "vitest";
import type { AppSettings, MutationPreview, UpdatePalDto } from "./contracts";

describe("frontend contracts", () => {
  it("keeps settings and mutation payloads serializable for IPC", () => {
    const settings = {
      theme: "dark",
      language: "en",
      showAdvancedTools: false,
    } satisfies AppSettings;
    const update = {
      instanceId: "pal-001",
      level: 50,
      cheatMode: false,
    } satisfies UpdatePalDto;

    expect(JSON.parse(JSON.stringify({ settings, update }))).toEqual({
      settings,
      update,
    });
  });

  it("represents a preview as an explicit, reviewable diff", () => {
    const preview = {
      operation: "update_pal",
      targetSaveRoot: "C:\\Saves\\World",
      entitiesToModify: [
        {
          entityType: "pal",
          entityId: "pal-001",
          label: "Pal 001",
          changeDescription: "Level 50 -> 55",
        },
      ],
      entitiesToDelete: [],
      filesToModify: ["Players/Players.json"],
      filesToDelete: [],
      backupTarget: "C:\\Saves\\Backups\\backup.zip",
      warnings: [],
      isSafe: true,
    } satisfies MutationPreview;

    expect(preview.entitiesToModify).toHaveLength(1);
    expect(preview.isSafe).toBe(true);
  });
});
