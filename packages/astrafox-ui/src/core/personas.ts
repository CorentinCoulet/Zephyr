/**
 * 🎭 Astrafox Persona System
 *
 * Personas define the animated avatar inside the chat panel.
 * Built-in presets are SVG-based; custom personas can use Lottie, GIF, or images.
 */

import type { AstrafoxPersona, AstrafoxPersonaPreset, AstrafoxCustomPersona } from "./config";
import { ASTRAFOX_LOGO_B64 } from "./logos";

// ─── Built-in persona definitions ────────────────────────────

const BUILT_IN_PERSONAS: Record<AstrafoxPersonaPreset, AstrafoxCustomPersona> = {
  friendly: {
    name: "Astrafox Friendly",
    avatar: "", // Will be resolved to SVG at runtime
    avatarType: "svg",
  },
  professional: {
    name: "Astrafox Pro",
    avatar: "",
    avatarType: "svg",
  },
  playful: {
    name: "Astrafox Playful",
    avatar: "",
    avatarType: "svg",
  },
  futuristic: {
    name: "Astrafox Futuristic",
    avatar: "",
    avatarType: "svg",
  },
};

// ─── Persona SVG builder (accent-aware) ──────────────────────

/** Expression states for animated personas */
export type AstrafoxExpression =
  | "neutral"
  | "happy"
  | "surprised"
  | "thinking"
  | "helping"
  | "speaking"
  | "wink";

export interface PersonaExpressionData {
  eyeRx: number;
  eyeRy: number;
  mouth: string;
  eyeArc?: boolean;
  dots?: boolean;
  winkLeft?: boolean;
}

export const EXPRESSIONS: Record<AstrafoxExpression, PersonaExpressionData> = {
  neutral: { eyeRx: 3, eyeRy: 3.5, mouth: "M28,42 Q32,44 36,42" },
  happy: { eyeRx: 0, eyeRy: 0, mouth: "M26,42 Q32,48 38,42", eyeArc: true },
  surprised: { eyeRx: 4, eyeRy: 5, mouth: "M28,43 Q32,47 36,43" },
  thinking: { eyeRx: 3, eyeRy: 2.5, mouth: "M28,42 L36,42", dots: true },
  helping: { eyeRx: 3, eyeRy: 3.5, mouth: "M26,42 Q32,46 38,42" },
  speaking: { eyeRx: 3, eyeRy: 3.5, mouth: "M28,41 Q32,46 36,41" },
  wink: { eyeRx: 3, eyeRy: 3.5, mouth: "M26,42 Q32,47 38,42", winkLeft: true },
};

/** Generate persona SVG for a given preset + accent + expression */
export function generatePersonaSVG(
  preset: AstrafoxPersonaPreset,
  accent: string,
  expression: AstrafoxExpression = "neutral"
): string {
  const LOGO = ASTRAFOX_LOGO_B64;

  const svgMap: Record<AstrafoxPersonaPreset, (c: string) => string> = {
    friendly: (c) => `
      <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="40" r="38" fill="${c}" opacity="0.12"/>
        <circle cx="40" cy="40" r="35" fill="none" stroke="${c}" stroke-width="2" opacity="0.5"/>
        <image href="${LOGO}" x="8" y="8" width="64" height="64"/>
      </svg>`,

    professional: (c) => `
      <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <rect x="8" y="8" width="64" height="64" rx="18" fill="${c}" opacity="0.08"/>
        <rect x="8" y="8" width="64" height="64" rx="18" fill="none" stroke="${c}" stroke-width="1.5" opacity="0.3"/>
        <image href="${LOGO}" x="10" y="10" width="60" height="60"/>
      </svg>`,

    playful: (c) => `
      <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="40" r="38" fill="${c}" opacity="0.1"/>
        <circle cx="40" cy="40" r="34" fill="${c}" opacity="0.06"/>
        <circle cx="40" cy="40" r="30" fill="${c}" opacity="0.03"/>
        <circle cx="40" cy="40" r="33" fill="none" stroke="${c}" stroke-width="1" opacity="0.3"/>
        <image href="${LOGO}" x="10" y="10" width="60" height="60" opacity="0.92"/>
      </svg>`,

    futuristic: (c) => `
      <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <rect x="5" y="5" width="70" height="70" rx="16" fill="none" stroke="${c}" stroke-width="1.5" opacity="0.6"/>
        <rect x="10" y="10" width="60" height="60" rx="12" fill="${c}" opacity="0.06"/>
        <circle cx="40" cy="7" r="3" fill="${c}" opacity="0.8"/>
        <circle cx="40" cy="73" r="2.5" fill="${c}" opacity="0.4"/>
        <circle cx="7" cy="40" r="2.5" fill="${c}" opacity="0.4"/>
        <circle cx="73" cy="40" r="2.5" fill="${c}" opacity="0.4"/>
        <image href="${LOGO}" x="14" y="14" width="52" height="52"/>
      </svg>`,
  };

  return (svgMap[preset] || svgMap.friendly)(accent);
}

// ─── Persona resolution ──────────────────────────────────────

export interface ResolvedPersona {
  name: string;
  /** SVG string, or URL to Lottie/GIF/image */
  avatar: string;
  /** How to render: inline SVG, or as img/lottie */
  renderType: "svg-inline" | "image" | "lottie";
}

export function resolvePersona(
  persona: AstrafoxPersona | undefined,
  accent: string
): ResolvedPersona {
  // Built-in preset name
  if (typeof persona === "string") {
    const preset = persona as AstrafoxPersonaPreset;
    if (preset in BUILT_IN_PERSONAS) {
      return {
        name: BUILT_IN_PERSONAS[preset].name,
        avatar: generatePersonaSVG(preset, accent),
        renderType: "svg-inline",
      };
    }
    // Treat as URL
    return { name: "Custom", avatar: persona, renderType: "image" };
  }

  // Custom persona object
  if (persona && typeof persona === "object") {
    const custom = persona as AstrafoxCustomPersona;
    const type = custom.avatarType === "lottie" ? "lottie" :
                 custom.avatarType === "svg" ? "svg-inline" : "image";
    return {
      name: custom.name,
      avatar: custom.avatar,
      renderType: type,
    };
  }

  // Default
  return {
    name: "Astrafox Friendly",
    avatar: generatePersonaSVG("friendly", accent),
    renderType: "svg-inline",
  };
}
