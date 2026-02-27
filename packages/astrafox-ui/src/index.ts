/**
 * 🦊 @astrafox/ui — Main entry point
 *
 * Exports:
 *   - defineAstrafoxConfig  — config helper
 *   - AstrafoxWidget        — core widget class
 *   - Astrafox (React)      — <Astrafox /> React component
 *   - Astrafox (Vue)        — <Astrafox /> Vue component (via '@astrafox/ui/vue')
 *   - init()               — vanilla JS initializer
 *
 * Subpath exports:
 *   '@astrafox/ui'         — React component + core
 *   '@astrafox/ui/react'   — React component + Provider + hook
 *   '@astrafox/ui/vue'     — Vue component
 *   '@astrafox/ui/config'  — Config types + defineAstrafoxConfig
 *   '@astrafox/ui/themes'  — Theme utilities
 */

// ── Config ────────────────────────────────────────────────────
export { defineAstrafoxConfig, resolveConfig, ASTRAFOX_DEFAULTS } from "./core/config";
export type {
  AstrafoxConfig,
  AstrafoxLogo,
  AstrafoxLogoPreset,
  AstrafoxCustomLogo,
  AstrafoxPersona,
  AstrafoxPersonaPreset,
  AstrafoxCustomPersona,
  AstrafoxTheme,
  AstrafoxThemePreset,
  AstrafoxCustomTheme,
  AstrafoxOpenAnimation,
  AstrafoxTriggerAnimation,
  AstrafoxPosition,
  AstrafoxSize,
  AstrafoxPanelConfig,
  AstrafoxFeature,
} from "./core/config";

// ── Core Widget ───────────────────────────────────────────────
export { AstrafoxWidget } from "./core/widget";
export type { AstrafoxMessage, AstrafoxWidgetEvents } from "./core/widget";

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
export type { AstrafoxExpression, ResolvedPersona } from "./core/personas";

// ── Vanilla JS ────────────────────────────────────────────────
export { init, getInstance, destroy } from "./vanilla/init";

// ── React (re-export for convenience) ─────────────────────────
export { Astrafox, AstrafoxProvider, useAstrafox } from "./react/Astrafox";
export type { AstrafoxProps } from "./react/Astrafox";
