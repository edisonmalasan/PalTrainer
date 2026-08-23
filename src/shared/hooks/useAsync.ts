import { useEffect, useRef, useState } from "react";

type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

export function useAsync<T>(
  fn: () => Promise<T>,
  deps: readonly unknown[],
): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });
  const cancelRef = useRef(false);

  useEffect(() => {
    cancelRef.current = false;
    setState({ status: "loading" });

    fn()
      .then((data) => {
        if (!cancelRef.current) setState({ status: "ok", data });
      })
      .catch((err: unknown) => {
        if (!cancelRef.current) {
          const msg =
            err instanceof Error
              ? err.message
              : typeof err === "object" && err !== null && "message" in err
                ? String((err as { message: unknown }).message)
                : "Unknown error";
          setState({ status: "error", message: msg });
        }
      });

    return () => {
      cancelRef.current = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
