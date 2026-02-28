/**
 * 🎬 Zephyr Animation System
 *
 * Open/close animations for the panel and trigger button effects.
 * All animations are pure CSS keyframes — no JS dependencies.
 */

import type { ZephyrOpenAnimation, ZephyrTriggerAnimation } from "./config";

// ─── Panel open/close animations ─────────────────────────────

export interface AnimationKeyframes {
  open: string;
  close: string;
}

const slideUp: AnimationKeyframes = {
  open: `
    @keyframes zephyr-slide-up-in {
      from { opacity: 0; transform: translateY(20px) scale(0.95); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }`,
  close: `
    @keyframes zephyr-slide-up-out {
      from { opacity: 1; transform: translateY(0) scale(1); }
      to   { opacity: 0; transform: translateY(20px) scale(0.95); }
    }`,
};

const slideDown: AnimationKeyframes = {
  open: `
    @keyframes zephyr-slide-down-in {
      from { opacity: 0; transform: translateY(-20px) scale(0.95); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }`,
  close: `
    @keyframes zephyr-slide-down-out {
      from { opacity: 1; transform: translateY(0) scale(1); }
      to   { opacity: 0; transform: translateY(-20px) scale(0.95); }
    }`,
};

const slideLeft: AnimationKeyframes = {
  open: `
    @keyframes zephyr-slide-left-in {
      from { opacity: 0; transform: translateX(20px) scale(0.95); }
      to   { opacity: 1; transform: translateX(0) scale(1); }
    }`,
  close: `
    @keyframes zephyr-slide-left-out {
      from { opacity: 1; transform: translateX(0) scale(1); }
      to   { opacity: 0; transform: translateX(20px) scale(0.95); }
    }`,
};

const slideRight: AnimationKeyframes = {
  open: `
    @keyframes zephyr-slide-right-in {
      from { opacity: 0; transform: translateX(-20px) scale(0.95); }
      to   { opacity: 1; transform: translateX(0) scale(1); }
    }`,
  close: `
    @keyframes zephyr-slide-right-out {
      from { opacity: 1; transform: translateX(0) scale(1); }
      to   { opacity: 0; transform: translateX(-20px) scale(0.95); }
    }`,
};

const fade: AnimationKeyframes = {
  open: `
    @keyframes zephyr-fade-in {
      from { opacity: 0; }
      to   { opacity: 1; }
    }`,
  close: `
    @keyframes zephyr-fade-out {
      from { opacity: 1; }
      to   { opacity: 0; }
    }`,
};

const scale: AnimationKeyframes = {
  open: `
    @keyframes zephyr-scale-in {
      from { opacity: 0; transform: scale(0.6); }
      to   { opacity: 1; transform: scale(1); }
    }`,
  close: `
    @keyframes zephyr-scale-out {
      from { opacity: 1; transform: scale(1); }
      to   { opacity: 0; transform: scale(0.6); }
    }`,
};

const bounce: AnimationKeyframes = {
  open: `
    @keyframes zephyr-bounce-in {
      0%   { opacity: 0; transform: scale(0.3); }
      50%  { opacity: 1; transform: scale(1.08); }
      70%  { transform: scale(0.95); }
      100% { transform: scale(1); }
    }`,
  close: `
    @keyframes zephyr-bounce-out {
      0%   { opacity: 1; transform: scale(1); }
      30%  { transform: scale(1.05); }
      100% { opacity: 0; transform: scale(0.3); }
    }`,
};

const none: AnimationKeyframes = { open: "", close: "" };

export const OPEN_ANIMATIONS: Record<ZephyrOpenAnimation, AnimationKeyframes> =
  {
    "slide-up": slideUp,
    "slide-down": slideDown,
    "slide-left": slideLeft,
    "slide-right": slideRight,
    fade,
    scale,
    bounce,
    none,
  };

// ─── Trigger button animations ───────────────────────────────

export const TRIGGER_ANIMATIONS: Record<ZephyrTriggerAnimation, string> = {
  float: `
    @keyframes zephyr-float {
      0%, 100% { transform: translateY(0); }
      50%      { transform: translateY(-6px); }
    }`,
  pulse: `
    @keyframes zephyr-pulse {
      0%, 100% { box-shadow: 0 0 0 0 var(--zephyr-accent); }
      50%      { box-shadow: 0 0 0 10px transparent; }
    }`,
  bounce: `
    @keyframes zephyr-trigger-bounce {
      0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
      40%  { transform: translateY(-8px); }
      60%  { transform: translateY(-4px); }
    }`,
  glow: `
    @keyframes zephyr-glow {
      0%, 100% { box-shadow: 0 0 8px 0 var(--zephyr-accent); }
      50%      { box-shadow: 0 0 20px 4px var(--zephyr-accent); }
    }`,
  none: "",
};

// ─── Helpers ─────────────────────────────────────────────────

/** Get CSS keyframes for a given open animation preset */
export function getOpenAnimationCSS(preset: ZephyrOpenAnimation): string {
  const anim = OPEN_ANIMATIONS[preset] || OPEN_ANIMATIONS["slide-up"];
  return `${anim.open}\n${anim.close}`;
}

/** Get animation name for panel open */
export function getOpenAnimationName(preset: ZephyrOpenAnimation): string {
  if (preset === "none") return "none";
  return `zephyr-${preset}-in`;
}

/** Get animation name for panel close */
export function getCloseAnimationName(preset: ZephyrOpenAnimation): string {
  if (preset === "none") return "none";
  return `zephyr-${preset}-out`;
}

/** Get CSS keyframes for a given trigger animation preset */
export function getTriggerAnimationCSS(
  preset: ZephyrTriggerAnimation
): string {
  return TRIGGER_ANIMATIONS[preset] || "";
}

/** Get animation name for trigger */
export function getTriggerAnimationName(
  preset: ZephyrTriggerAnimation
): string {
  if (preset === "none") return "none";
  const map: Record<string, string> = {
    float: "zephyr-float",
    pulse: "zephyr-pulse",
    bounce: "zephyr-trigger-bounce",
    glow: "zephyr-glow",
  };
  return map[preset] || "none";
}
