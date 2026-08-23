import { invoke } from "@tauri-apps/api/core";
import type { CommandError } from "../types/contracts";

export async function invokeCommand<T>(
  command: string,
  args?: Record<string, unknown>,
): Promise<T> {
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    throw normalizeCommandError(error);
  }
}

export function normalizeCommandError(error: unknown): CommandError {
  if (typeof error === "object" && error !== null) {
    const candidate = error as Partial<CommandError>;
    if (typeof candidate.code === "string" && typeof candidate.message === "string") {
      return {
        code: candidate.code,
        message: candidate.message,
        details: candidate.details,
      };
    }
  }

  return {
    code: "unknown",
    message:
      error instanceof Error ? error.message : "An unknown command error occurred.",
  };
}
