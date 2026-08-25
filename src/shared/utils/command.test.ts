import { describe, expect, it, vi } from "vitest";
import { invokeCommand, normalizeCommandError } from "./command";

const invokeMock = vi.hoisted(() => vi.fn());

vi.mock("@tauri-apps/api/core", () => ({
  invoke: invokeMock,
}));

describe("normalizeCommandError", () => {
  it("keeps typed command errors intact", () => {
    expect(
      normalizeCommandError({
        code: "settings_write_failed",
        message: "Could not save settings.",
        details: "disk full",
      }),
    ).toEqual({
      code: "settings_write_failed",
      message: "Could not save settings.",
      details: "disk full",
    });
  });

  it("turns untyped errors into user-safe command errors", () => {
    expect(normalizeCommandError(new Error("boom"))).toEqual({
      code: "unknown",
      message: "boom",
    });
  });

  it("passes typed arguments through to Tauri and returns its result", async () => {
    invokeMock.mockResolvedValueOnce({ loaded: true });

    await expect(
      invokeCommand<{ loaded: boolean }>("load_save", { path: "save.sav" }),
    ).resolves.toEqual({
      loaded: true,
    });
    expect(invokeMock).toHaveBeenCalledWith("load_save", { path: "save.sav" });
  });

  it("normalizes an IPC rejection before it reaches the UI", async () => {
    invokeMock.mockRejectedValueOnce({
      code: "stale_save",
      message: "Save changed externally.",
    });

    await expect(invokeCommand("commit_save")).rejects.toEqual({
      code: "stale_save",
      message: "Save changed externally.",
      details: undefined,
    });
  });
});
