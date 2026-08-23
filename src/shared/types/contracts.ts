export type ThemePreference = "system" | "light" | "dark";
export type LanguagePreference = "en";

export interface AppInfo {
  readonly name: string;
  readonly version: string;
  readonly tauriVersion: string;
}

export interface AppSettings {
  readonly theme: ThemePreference;
  readonly language: LanguagePreference;
  readonly showAdvancedTools: boolean;
}

export interface FeatureFlag {
  readonly id: string;
  readonly label: string;
  readonly enabled: boolean;
  readonly description: string;
}

export interface AppLogEntry {
  readonly level: "info" | "warning" | "error";
  readonly message: string;
  readonly timestamp: string;
}

export interface CommandError {
  readonly code: string;
  readonly message: string;
  readonly details?: string;
}
