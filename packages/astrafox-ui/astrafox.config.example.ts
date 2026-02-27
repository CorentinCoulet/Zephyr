/**
 * 🦊 Astrafox Configuration
 *
 * Copy this file to your project root as `astrafox.config.ts`
 * and customize it. Then pass it to the <Astrafox /> component:
 *
 *   import config from './astrafox.config';
 *   <Astrafox config={config} />
 */

import { defineAstrafoxConfig } from "@astrafox/ui/config";

export default defineAstrafoxConfig({
  // ── Connection ──────────────────────────────────────────────
  server: "http://localhost:8000",
  apiKey: "", // Your Astrafox API key

  // ── Logo ────────────────────────────────────────────────────
  // Built-in: 'astrafox-default'
  // Custom URL: 'https://yourcdn.com/logo.svg'
  // Custom object: { trigger: '/logo-small.svg', header: '/logo-big.svg' }
  logo: "astrafox-default",

  // ── Persona (animated avatar in chat) ───────────────────────
  // Built-in: 'friendly' | 'professional' | 'playful' | 'futuristic'
  // Custom: { name: 'Mon Bot', avatar: '/bot.gif', avatarType: 'gif' }
  persona: "friendly",

  // ── Theme ───────────────────────────────────────────────────
  // Built-in: 'dark' | 'light' | 'auto'
  // Custom: { background: '#1a1a2e', surface: '#2a2a40', text: '#e8e8f0', ... }
  theme: "dark",

  // ── Accent color ────────────────────────────────────────────
  accentColor: "#ff6b35",

  // ── Animations ──────────────────────────────────────────────
  // Panel open: 'slide-up' | 'slide-down' | 'fade' | 'scale' | 'bounce' | 'none'
  openAnimation: "slide-up",
  // Trigger button: 'float' | 'pulse' | 'bounce' | 'glow' | 'none'
  triggerAnimation: "float",

  // ── Panel ───────────────────────────────────────────────────
  panel: {
    position: "bottom-right", // 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
    size: "md",               // 'sm' | 'md' | 'lg'
    // width: 380,            // Custom width in px (overrides size)
    // height: 520,           // Custom height in px (overrides size)
    borderRadius: 16,
    backdrop: false,           // Show overlay when chat is open
    zIndex: 99999,
    draggable: false,
  },

  // ── Content ─────────────────────────────────────────────────
  language: "fr",
  greeting: "Bonjour ! Comment puis-je vous aider ? 🦊",
  placeholder: "Posez une question...",

  // ── Features ────────────────────────────────────────────────
  features: ["chat", "guide", "search"],
  startOpen: false,
  showBadge: true,

  // ── Advanced ────────────────────────────────────────────────
  // customCSS: '.astrafox-header { background: #000; }',
  // container: '#my-widget-container', // null = body (floating)
});
