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
            return { loaded: true };
          case "close_save_session":
            return { closed: true };
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
  const pathInput = page.getByLabel("Save path");

  await pathInput.fill("C:\\fixtures\\World");
  await page.getByRole("button", { name: "Load save" }).click();
  await expect(page.getByText("Save loaded successfully.")).toBeVisible();

  await page.getByRole("button", { name: "Close session" }).click();
  await expect(page.getByText("Save session closed.")).toBeVisible();
});
