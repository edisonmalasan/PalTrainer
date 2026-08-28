import { describe, expect, it } from "vitest";
import {
  deriveOutputPath,
  fileBaseName,
  fileExtension,
  fileStem,
  isTauriRuntime,
} from "./fileDialog";

describe("file dialog path helpers", () => {
  it("detects non-Tauri test runtime so pickers stay inert", () => {
    expect(isTauriRuntime()).toBe(false);
  });

  it("extracts the extension and stem from mixed separators", () => {
    expect(fileExtension("C:\\Saves\\World\\Level.sav")).toBe("sav");
    expect(fileExtension("/saves/world/Level.JSON")).toBe("json");
    expect(fileExtension("C:\\Saves\\World")).toBe("");
    expect(fileStem("C:\\Saves\\World\\Level.sav")).toBe("Level");
    expect(fileBaseName("/saves/world/Level.sav")).toBe("Level.sav");
  });

  it("derives output JSON next to an input SAV", () => {
    expect(deriveOutputPath("C:\\Saves\\World\\Level.sav", "json")).toBe(
      "C:\\Saves\\World\\Level.json",
    );
    expect(deriveOutputPath("/saves/world/Level.sav", "sav")).toBe(
      "/saves/world/Level.sav",
    );
  });

  it("returns null output derivation for a path with no parent", () => {
    expect(deriveOutputPath("Level.sav", "json")).toBeNull();
  });
});
