/**
 * 🦊 Zephyr Configuration System
 *
 * Usage in your project:
 *
 *   // zephyr.config.ts
 *   import { defineZephyrConfig } from '@zephyr/ui/config';
 *
 *   export default defineZephyrConfig({
 *     server: 'https://your-zephyr-server.com',
 *     logo: 'zephyr-default',
 *     persona: 'friendly',
 *     theme: 'dark',
 *     openAnimation: 'slide-up',
 *   });
 */

// ─── Logo ────────────────────────────────────────────────────

/** Built-in logo preset. Pass a URL string or object for custom logos. */
export type ZephyrLogoPreset = "zephyr-default";

export interface ZephyrCustomLogo {
  /** URL or imported asset for the trigger button icon */
  trigger: string;
  /** URL or imported asset for the chat header avatar (optional, defaults to trigger) */
  header?: string;
  /** Alt text */
  alt?: string;
}

export type ZephyrLogo = ZephyrLogoPreset | ZephyrCustomLogo | string;

// ─── Persona ─────────────────────────────────────────────────

/** Built-in persona presets for the chat avatar animations */
export type ZephyrPersonaPreset =
  | "friendly"
  | "professional"
  | "playful"
  | "futuristic";

export interface ZephyrCustomPersona {
  /** Display name */
  name: string;
  /** Avatar (Lottie URL, GIF URL, SVG string, or image URL) */
  avatar: string;
  /** Avatar format */
  avatarType?: "lottie" | "gif" | "svg" | "image";
  /** Idle animation (Lottie/GIF for when the bot is waiting) */
  idle?: string;
  /** Thinking animation */
  thinking?: string;
  /** Speaking animation */
  speaking?: string;
}

export type ZephyrPersona = ZephyrPersonaPreset | ZephyrCustomPersona;

// ─── Animations ──────────────────────────────────────────────

export type ZephyrOpenAnimation =
  | "slide-up"
  | "slide-down"
  | "slide-left"
  | "slide-right"
  | "fade"
  | "scale"
  | "bounce"
  | "none";

export type ZephyrTriggerAnimation =
  | "float"
  | "pulse"
  | "bounce"
  | "glow"
  | "none";

// ─── Theme ───────────────────────────────────────────────────

export type ZephyrThemePreset = "dark" | "light" | "auto";

export interface ZephyrCustomTheme {
  /** Background color of the panel */
  background: string;
  /** Surface color (header, input area) */
  surface: string;
  /** Primary text color */
  text: string;
  /** Muted/secondary text */
  muted: string;
  /** Border color */
  border: string;
  /** User message bubble color (defaults to accentColor) */
  userBubble?: string;
  /** User message text color */
  userText?: string;
  /** Bot message bubble color */
  botBubble?: string;
  /** Bot message text color */
  botText?: string;
}

export type ZephyrTheme = ZephyrThemePreset | ZephyrCustomTheme;

// ─── Panel ───────────────────────────────────────────────────

export type ZephyrPosition =
  | "bottom-right"
  | "bottom-left"
  | "top-right"
  | "top-left";

export type ZephyrSize = "sm" | "md" | "lg";

export interface ZephyrPanelConfig {
  /** Position of the widget trigger + panel */
  position?: ZephyrPosition;
  /** Panel size preset */
  size?: ZephyrSize;
  /** Custom width in px (overrides size) */
  width?: number;
  /** Custom height in px (overrides size) */
  height?: number;
  /** Border radius in px */
  borderRadius?: number;
  /** Show backdrop overlay when open */
  backdrop?: boolean;
  /** Custom z-index */
  zIndex?: number;
  /** Draggable trigger */
  draggable?: boolean;
}

// ─── Features ────────────────────────────────────────────────

export type ZephyrFeature = "chat" | "guide" | "search" | "onboarding";

// ─── Full Config ─────────────────────────────────────────────

export interface ZephyrConfig {
  // ── Connection ──────────────────────────────────────────
  /** Zephyr backend server URL */
  server: string;
  /** API key for authentication */
  apiKey?: string;

  // ── Appearance ──────────────────────────────────────────
  /** Logo for the trigger button + header */
  logo?: ZephyrLogo;
  /** Animated persona in the chat */
  persona?: ZephyrPersona;
  /** Theme (dark/light/auto or custom) */
  theme?: ZephyrTheme;
  /** Accent color (hex) */
  accentColor?: string;

  // ── Animations ──────────────────────────────────────────
  /** Animation when the chat panel opens */
  openAnimation?: ZephyrOpenAnimation;
  /** Animation of the trigger button when idle */
  triggerAnimation?: ZephyrTriggerAnimation;

  // ── Panel ───────────────────────────────────────────────
  /** Panel layout & positioning */
  panel?: ZephyrPanelConfig;

  // ── Content ─────────────────────────────────────────────
  /** Language ('fr', 'en', etc.) */
  language?: string;
  /** Custom greeting message */
  greeting?: string;
  /** Input placeholder text */
  placeholder?: string;

  // ── Features ────────────────────────────────────────────
  /** Enabled features */
  features?: ZephyrFeature[];
  /** Start with panel open */
  startOpen?: boolean;
  /** Show unread badge on trigger */
  showBadge?: boolean;

  // ── Advanced ────────────────────────────────────────────
  /** Custom CSS to inject */
  customCSS?: string;
  /** Mount inside a specific container selector (null = body) */
  container?: string | null;
}

// ─── Defaults ────────────────────────────────────────────────

export const ZEPHYR_DEFAULTS: Required<
  Pick<
    ZephyrConfig,
    | "logo"
    | "persona"
    | "theme"
    | "accentColor"
    | "openAnimation"
    | "triggerAnimation"
    | "language"
    | "features"
    | "startOpen"
    | "showBadge"
  >
> & { panel: Required<ZephyrPanelConfig> } = {
  logo: "zephyr-default",
  persona: "friendly",
  theme: "dark",
  accentColor: "#ff6b35",
  openAnimation: "slide-up",
  triggerAnimation: "float",
  language: "fr",
  features: ["chat", "guide", "search"],
  startOpen: false,
  showBadge: true,
  panel: {
    position: "bottom-right",
    size: "md",
    width: 380,
    height: 520,
    borderRadius: 16,
    backdrop: false,
    zIndex: 99999,
    draggable: false,
  },
};

// ─── Helper ──────────────────────────────────────────────────

/**
 * Define your Zephyr config with full type-safety & autocompletion.
 *
 * @example
 * ```ts
 * // zephyr.config.ts
 * import { defineZephyrConfig } from '@zephyr/ui/config';
 *
 * export default defineZephyrConfig({
 *   server: 'http://localhost:8000',
 *   logo: 'zephyr-minimal',
 *   persona: 'professional',
 *   theme: 'dark',
 *   accentColor: '#6c63ff',
 *   openAnimation: 'scale',
 *   panel: {
 *     position: 'bottom-right',
 *     size: 'lg',
 *     backdrop: true,
 *   },
 * });
 * ```
 */
export function defineZephyrConfig(config: ZephyrConfig): ZephyrConfig {
  return config;
}

/** Merge user config with defaults */
export function resolveConfig(
  userConfig: ZephyrConfig
): ZephyrConfig & typeof ZEPHYR_DEFAULTS {
  return {
    ...ZEPHYR_DEFAULTS,
    ...userConfig,
    panel: {
      ...ZEPHYR_DEFAULTS.panel,
      ...userConfig.panel,
    },
  };
}
