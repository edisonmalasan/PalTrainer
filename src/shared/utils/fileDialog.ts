//! Native file-picking helpers for the tools workbench. Every privileged path
//! flows through the Tauri dialog plugin (`dialog:allow-open`) — no free-text
//! path entry. All helpers are no-op safe outside the Tauri runtime so tests
//! can render the UI without a desktop shell.

import { open } from "@tauri-apps/plugin-dialog";

export type PickFilter = "sav" | "json" | "savOrJson" | "directory";

const FILTERS: Record<
  Exclude<PickFilter, "directory">,
  { name: string; extensions: string[] }
> = {
  sav: { name: "Palworld save files (*.sav)", extensions: ["sav"] },
  json: { name: "JSON files (*.json)", extensions: ["json"] },
  savOrJson: {
    name: "Palworld save / JSON files (*.sav, *.json)",
    extensions: ["sav", "json"],
  },
};

export function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function pick(
  filter: PickFilter,
  title: string,
  defaultPath?: string,
): Promise<string | null> {
  if (!isTauriRuntime()) return null;

  const selection = await open({
    directory: filter === "directory",
    multiple: false,
    title,
    defaultPath: defaultPath || undefined,
    ...(filter === "directory" ? {} : { filters: [FILTERS[filter]] }),
  });
  return typeof selection === "string" && selection.length > 0 ? selection : null;
}

export function pickSavFile(
  title: string,
  defaultPath?: string,
): Promise<string | null> {
  return pick("sav", title, defaultPath);
}

export function pickJsonFile(
  title: string,
  defaultPath?: string,
): Promise<string | null> {
  return pick("json", title, defaultPath);
}

export function pickSaveOrJsonFile(
  title: string,
  defaultPath?: string,
): Promise<string | null> {
  return pick("savOrJson", title, defaultPath);
}

export function pickDirectory(
  title: string,
  defaultPath?: string,
): Promise<string | null> {
  return pick("directory", title, defaultPath);
}

export function fileExtension(path: string): string {
  const clean = path.replace(/[\\/]+$/, "");
  const dot = clean.lastIndexOf(".");
  return dot > clean.lastIndexOf("/") && dot > clean.lastIndexOf("\\") && dot >= 0
    ? clean.slice(dot + 1).toLowerCase()
    : "";
}

export function fileStem(path: string): string {
  const clean = path.replace(/[\\/]+$/, "");
  const base = clean.split(/[\\/]/).pop() ?? clean;
  const dot = base.lastIndexOf(".");
  return dot > 0 ? base.slice(0, dot) : base;
}

export function fileBaseName(path: string): string {
  return (
    path
      .replace(/[\\/]+$/, "")
      .split(/[\\/]/)
      .pop() ?? path
  );
}

/// Derives the conversion output path next to the input file: same folder,
/// same stem, new extension. Returns null when the input has no directory.
export function deriveOutputPath(
  inputPath: string,
  newExtension: string,
): string | null {
  const trimmed = inputPath.trim();
  if (!trimmed) return null;
  const separator = trimmed.includes("\\") ? "\\" : "/";
  const cut = trimmed.lastIndexOf(separator);
  if (cut < 0) return null;
  return `${trimmed.slice(0, cut + 1)}${fileStem(trimmed)}.${newExtension.replace(/^\./, "")}`;
}
