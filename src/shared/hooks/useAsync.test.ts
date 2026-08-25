import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useAsync } from "./useAsync";

describe("useAsync", () => {
  it("tracks loading and successful results", async () => {
    let resolve!: (value: number) => void;
    const fn = vi.fn(
      () =>
        new Promise<number>((promiseResolve) => {
          resolve = promiseResolve;
        }),
    );
    const { result } = renderHook(() => useAsync(fn, []));

    expect(result.current).toEqual({ status: "loading" });

    await act(async () => resolve(42));

    await waitFor(() => expect(result.current).toEqual({ status: "ok", data: 42 }));
    expect(fn).toHaveBeenCalledOnce();
  });

  it("exposes Error messages and handles unknown rejection values", async () => {
    const error = renderHook(() =>
      useAsync(() => Promise.reject(new Error("failed")), []),
    );
    await waitFor(() =>
      expect(error.result.current).toEqual({ status: "error", message: "failed" }),
    );

    const unknown = renderHook(() => useAsync(() => Promise.reject("bad"), []));
    await waitFor(() =>
      expect(unknown.result.current).toEqual({
        status: "error",
        message: "Unknown error",
      }),
    );
  });

  it("ignores a result after the hook is unmounted", async () => {
    let resolve!: (value: string) => void;
    const promise = new Promise<string>((promiseResolve) => {
      resolve = promiseResolve;
    });
    const { result, unmount } = renderHook(() => useAsync(() => promise, []));

    unmount();
    await act(async () => resolve("late"));

    expect(result.current).toEqual({ status: "loading" });
  });
});
