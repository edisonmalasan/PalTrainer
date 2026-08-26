import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const settings = { theme: "system", language: "en", showAdvancedTools: false };
    const internals = {
      invoke: async (command: string) => {
        switch (command) {
          case "get_app_info":
            return { name: "PalTrainer", version: "0.1.0", tauriVersion: "2" };
          case "get_settings":
            return settings;
          case "get_feature_flags":
            return [];
          case "load_save_session":
            return {
              saveRoot: "C:\\fixtures\\World",
              worldName: "Test World",
              saveType: "PLZ",
              playerCount: 1,
              levelSavSize: 1024,
              isDirty: false,
              loadedAt: 1756160000,
            };
          case "close_save_session":
            return null;
          // Tauri dialog plugin mocked to hand back a Level.sav path
          case "plugin:dialog|open":
            return "C:\\fixtures\\World\\Level.sav";
          case "get_players":
            return [];
          default:
            return null;
        }
      },
    };

    Object.defineProperty(window, "__TAURI_INTERNALS__", {
      configurable: true,
      value: internals,
    });
  });
});

test("launches the workbench and navigates to the session view", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Save Workbench" })).toBeVisible();
  await expect(
    page.locator("header").getByRole("heading", { name: "Save Session" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Players" }).click();
  await expect(
    page.locator("header").getByRole("heading", { name: "Players" }),
  ).toBeVisible();
});

test("opens and closes a save session through the IPC boundary", async ({ page }) => {
  await page.goto("/");

  // Single-step flow: picking Level.sav in the dialog loads the session
  await page.getByRole("button", { name: "Load Save…" }).click();
  await expect(page.getByText("Save loaded successfully.")).toBeVisible();
  await expect(page.getByLabel("Loaded save summary")).toContainText("Test World");

  await page.getByRole("button", { name: "Close Session" }).click();
  await expect(page.getByText("Save session closed.")).toBeVisible();
});
