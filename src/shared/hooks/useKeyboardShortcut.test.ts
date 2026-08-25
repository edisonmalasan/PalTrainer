import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useKeyboardShortcut } from "./useKeyboardShortcut";

describe("useKeyboardShortcut", () => {
  it("runs for the requested key and prevents the browser default", () => {
    const callback = vi.fn();
    renderHook(() => useKeyboardShortcut("s", callback, { ctrl: true }));
    const event = new KeyboardEvent("keydown", {
      key: "S",
      ctrlKey: true,
      cancelable: true,
    });

    window.dispatchEvent(event);

    expect(callback).toHaveBeenCalledOnce();
    expect(event.defaultPrevented).toBe(true);
  });

  it("accepts the platform meta key when ctrl is requested and ignores input fields", () => {
    const callback = vi.fn();
    renderHook(() => useKeyboardShortcut("k", callback, { ctrl: true }));
    const input = document.createElement("input");
    document.body.appendChild(input);

    input.dispatchEvent(
      new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true }),
    );
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }));

    expect(callback).toHaveBeenCalledOnce();
    input.remove();
  });

  it("removes the listener on unmount and supports shortcuts inside inputs when enabled", () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() =>
      useKeyboardShortcut("x", callback, {
        allowInInputs: true,
        preventDefault: false,
      }),
    );
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "x", bubbles: true }));
    expect(callback).toHaveBeenCalledOnce();

    unmount();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "x" }));
    expect(callback).toHaveBeenCalledOnce();
    input.remove();
  });
});
