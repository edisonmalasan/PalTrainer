import { useEffect } from "react";

interface ShortcutOptions {
  readonly ctrl?: boolean;
  readonly meta?: boolean;
  readonly shift?: boolean;
  readonly alt?: boolean;
  readonly allowInInputs?: boolean;
  readonly preventDefault?: boolean;
}

export function useKeyboardShortcut(
  key: string,
  callback: (e: KeyboardEvent) => void,
  options: ShortcutOptions = {},
) {
  const {
    ctrl = false,
    meta = false,
    shift = false,
    alt = false,
    allowInInputs = false,
    preventDefault = true,
  } = options;

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Check target element to avoid capturing typing in input fields
      const target = e.target as HTMLElement | null;
      const isInput =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);

      if (isInput && !allowInInputs) {
        return;
      }

      // Modifier matching
      const matchesCtrl = !ctrl || e.ctrlKey || e.metaKey;
      const matchesShift = shift ? e.shiftKey : !e.shiftKey;
      const matchesAlt = alt ? e.altKey : !e.altKey;
      const matchesKey = e.key.toLowerCase() === key.toLowerCase();

      if (matchesKey && matchesCtrl && matchesShift && matchesAlt) {
        if (preventDefault) {
          e.preventDefault();
        }
        callback(e);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [key, callback, ctrl, meta, shift, alt, allowInInputs, preventDefault]);
}
