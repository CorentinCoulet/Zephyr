/**
 * 🎨 Zephyr Theme System
 *
 * Built-in dark/light themes + custom theme support.
 * Themes map to CSS custom properties injected on the widget root.
 */

import type { ZephyrTheme, ZephyrCustomTheme } from "./config";

// ─── Built-in themes ─────────────────────────────────────────

export const THEME_DARK: ZephyrCustomTheme = {
  background: "#0f0f1a",
  surface: "#1a1a2e",
  text: "#e8e8f0",
  muted: "#6b6b80",
  border: "#2a2a40",
  userBubble: "var(--zephyr-accent, #ff6b35)",
  userText: "#ffffff",
  botBubble: "#1e1e35",
  botText: "#e8e8f0",
};

export const THEME_LIGHT: ZephyrCustomTheme = {
  background: "#f5f5fa",
  surface: "#ffffff",
  text: "#1a1a2e",
  muted: "#8888a0",
  border: "#e0e0ee",
  userBubble: "var(--zephyr-accent, #ff6b35)",
  userText: "#ffffff",
  botBubble: "#f0f0f8",
  botText: "#1a1a2e",
};

export const BUILT_IN_THEMES: Record<string, ZephyrCustomTheme> = {
  dark: THEME_DARK,
  light: THEME_LIGHT,
};

// ─── Theme resolution ────────────────────────────────────────

export function resolveTheme(theme: ZephyrTheme): ZephyrCustomTheme {
  if (typeof theme === "object") return theme;
  if (theme === "auto") {
    const prefersDark =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    return prefersDark ? THEME_DARK : THEME_LIGHT;
  }
  return BUILT_IN_THEMES[theme] || THEME_DARK;
}

/** Convert theme to CSS custom properties */
export function themeToCSSVars(
  theme: ZephyrCustomTheme,
  accentColor: string
): Record<string, string> {
  return {
    "--zephyr-accent": accentColor,
    "--zephyr-bg": theme.background,
    "--zephyr-surface": theme.surface,
    "--zephyr-text": theme.text,
    "--zephyr-muted": theme.muted,
    "--zephyr-border": theme.border,
    "--zephyr-user-bubble": theme.userBubble || accentColor,
    "--zephyr-user-text": theme.userText || "#ffffff",
    "--zephyr-bot-bubble": theme.botBubble || theme.surface,
    "--zephyr-bot-text": theme.botText || theme.text,
  };
}
