/**
 * 🦊 @zephyr/ui — Main entry point
 *
 * Exports:
 *   - defineZephyrConfig  — config helper
 *   - ZephyrWidget        — core widget class
 *   - Zephyr (React)      — <Zephyr /> React component
 *   - Zephyr (Vue)        — <Zephyr /> Vue component (via '@zephyr/ui/vue')
 *   - init()               — vanilla JS initializer
 *
 * Subpath exports:
 *   '@zephyr/ui'         — React component + core
 *   '@zephyr/ui/react'   — React component + Provider + hook
 *   '@zephyr/ui/vue'     — Vue component
 *   '@zephyr/ui/config'  — Config types + defineZephyrConfig
 *   '@zephyr/ui/themes'  — Theme utilities
 */

// ── Config ────────────────────────────────────────────────────
export { defineZephyrConfig, resolveConfig, ZEPHYR_DEFAULTS } from "./core/config";
export type {
  ZephyrConfig,
  ZephyrLogo,
  ZephyrLogoPreset,
  ZephyrCustomLogo,
  ZephyrPersona,
  ZephyrPersonaPreset,
  ZephyrCustomPersona,
  ZephyrTheme,
  ZephyrThemePreset,
  ZephyrCustomTheme,
  ZephyrOpenAnimation,
  ZephyrTriggerAnimation,
  ZephyrPosition,
  ZephyrSize,
  ZephyrPanelConfig,
  ZephyrFeature,
} from "./core/config";

// ── Core Widget ───────────────────────────────────────────────
export { ZephyrWidget } from "./core/widget";
export type { ZephyrMessage, ZephyrWidgetEvents } from "./core/widget";

// ── Themes ────────────────────────────────────────────────────
export { resolveTheme, themeToCSSVars, THEME_DARK, THEME_LIGHT } from "./core/themes";

// ── Animations ────────────────────────────────────────────────
export {
  getOpenAnimationCSS,
  getOpenAnimationName,
  getTriggerAnimationCSS,
  getTriggerAnimationName,
} from "./core/animations";

// ── Logos ──────────────────────────────────────────────────────
export { resolveLogo } from "./core/logos";

// ── Personas ──────────────────────────────────────────────────
export { resolvePersona, generatePersonaSVG, EXPRESSIONS } from "./core/personas";
export type { ZephyrExpression, ResolvedPersona } from "./core/personas";

// ── Vanilla JS ────────────────────────────────────────────────
export { init, getInstance, destroy } from "./vanilla/init";

// ── React (re-export for convenience) ─────────────────────────
export { Zephyr, ZephyrProvider, useZephyr } from "./react/Zephyr";
export type { ZephyrProps } from "./react/Zephyr";
