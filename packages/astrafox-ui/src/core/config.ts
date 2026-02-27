/**
 * 🦊 Astrafox Configuration System
 *
 * Usage in your project:
 *
 *   // astrafox.config.ts
 *   import { defineAstrafoxConfig } from '@astrafox/ui/config';
 *
 *   export default defineAstrafoxConfig({
 *     server: 'https://your-astrafox-server.com',
 *     logo: 'astrafox-default',
 *     persona: 'friendly',
 *     theme: 'dark',
 *     openAnimation: 'slide-up',
 *   });
 */

// ─── Logo ────────────────────────────────────────────────────

/** Built-in logo preset. Pass a URL string or object for custom logos. */
export type AstrafoxLogoPreset = "astrafox-default";

export interface AstrafoxCustomLogo {
  /** URL or imported asset for the trigger button icon */
  trigger: string;
  /** URL or imported asset for the chat header avatar (optional, defaults to trigger) */
  header?: string;
  /** Alt text */
  alt?: string;
}

export type AstrafoxLogo = AstrafoxLogoPreset | AstrafoxCustomLogo | string;

// ─── Persona ─────────────────────────────────────────────────

/** Built-in persona presets for the chat avatar animations */
export type AstrafoxPersonaPreset =
  | "friendly"
  | "professional"
  | "playful"
  | "futuristic";

export interface AstrafoxCustomPersona {
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

export type AstrafoxPersona = AstrafoxPersonaPreset | AstrafoxCustomPersona;

// ─── Animations ──────────────────────────────────────────────

export type AstrafoxOpenAnimation =
  | "slide-up"
  | "slide-down"
  | "slide-left"
  | "slide-right"
  | "fade"
  | "scale"
  | "bounce"
  | "none";

export type AstrafoxTriggerAnimation =
  | "float"
  | "pulse"
  | "bounce"
  | "glow"
  | "none";

// ─── Theme ───────────────────────────────────────────────────

export type AstrafoxThemePreset = "dark" | "light" | "auto";

export interface AstrafoxCustomTheme {
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

export type AstrafoxTheme = AstrafoxThemePreset | AstrafoxCustomTheme;

// ─── Panel ───────────────────────────────────────────────────

export type AstrafoxPosition =
  | "bottom-right"
  | "bottom-left"
  | "top-right"
  | "top-left";

export type AstrafoxSize = "sm" | "md" | "lg";

export interface AstrafoxPanelConfig {
  /** Position of the widget trigger + panel */
  position?: AstrafoxPosition;
  /** Panel size preset */
  size?: AstrafoxSize;
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

export type AstrafoxFeature = "chat" | "guide" | "search" | "onboarding";

// ─── Full Config ─────────────────────────────────────────────

export interface AstrafoxConfig {
  // ── Connection ──────────────────────────────────────────
  /** Astrafox backend server URL */
  server: string;
  /** API key for authentication */
  apiKey?: string;

  // ── Appearance ──────────────────────────────────────────
  /** Logo for the trigger button + header */
  logo?: AstrafoxLogo;
  /** Animated persona in the chat */
  persona?: AstrafoxPersona;
  /** Theme (dark/light/auto or custom) */
  theme?: AstrafoxTheme;
  /** Accent color (hex) */
  accentColor?: string;

  // ── Animations ──────────────────────────────────────────
  /** Animation when the chat panel opens */
  openAnimation?: AstrafoxOpenAnimation;
  /** Animation of the trigger button when idle */
  triggerAnimation?: AstrafoxTriggerAnimation;

  // ── Panel ───────────────────────────────────────────────
  /** Panel layout & positioning */
  panel?: AstrafoxPanelConfig;

  // ── Content ─────────────────────────────────────────────
  /** Language ('fr', 'en', etc.) */
  language?: string;
  /** Custom greeting message */
  greeting?: string;
  /** Input placeholder text */
  placeholder?: string;

  // ── Features ────────────────────────────────────────────
  /** Enabled features */
  features?: AstrafoxFeature[];
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

export const ASTRAFOX_DEFAULTS: Required<
  Pick<
    AstrafoxConfig,
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
> & { panel: Required<AstrafoxPanelConfig> } = {
  logo: "astrafox-default",
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
 * Define your Astrafox config with full type-safety & autocompletion.
 *
 * @example
 * ```ts
 * // astrafox.config.ts
 * import { defineAstrafoxConfig } from '@astrafox/ui/config';
 *
 * export default defineAstrafoxConfig({
 *   server: 'http://localhost:8000',
 *   logo: 'astrafox-minimal',
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
export function defineAstrafoxConfig(config: AstrafoxConfig): AstrafoxConfig {
  return config;
}

/** Merge user config with defaults */
export function resolveConfig(
  userConfig: AstrafoxConfig
): AstrafoxConfig & typeof ASTRAFOX_DEFAULTS {
  return {
    ...ASTRAFOX_DEFAULTS,
    ...userConfig,
    panel: {
      ...ASTRAFOX_DEFAULTS.panel,
      ...userConfig.panel,
    },
  };
}
