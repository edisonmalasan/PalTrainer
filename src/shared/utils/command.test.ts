import { describe, expect, it } from "vitest";
import { normalizeCommandError } from "./command";

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
});
