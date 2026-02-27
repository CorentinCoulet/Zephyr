/**
 * 🎨 Astrafox CSS Styles
 *
 * All styles use CSS custom properties (--astrafox-*) set by the theme system.
 * No external CSS dependencies.
 */

/** Core widget styles — injected once per page */
export const ASTRAFOX_STYLES = `
/* ─── Root ──────────────────────────────────────────────────── */
.astrafox-root {
  --astrafox-accent: #ff6b35;
  --astrafox-bg: #0f0f1a;
  --astrafox-surface: #1a1a2e;
  --astrafox-text: #e8e8f0;
  --astrafox-muted: #6b6b80;
  --astrafox-border: #2a2a40;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
  color: var(--astrafox-text);
}
.astrafox-root *, .astrafox-root *::before, .astrafox-root *::after {
  box-sizing: inherit;
}

/* ─── Trigger button ────────────────────────────────────────── */
.astrafox-trigger {
  position: fixed;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 2px solid var(--astrafox-accent);
  background: var(--astrafox-surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  outline: none;
}
.astrafox-trigger:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
}
.astrafox-trigger:focus-visible {
  outline: 2px solid var(--astrafox-accent);
  outline-offset: 3px;
}
.astrafox-trigger.astrafox-sm { width: 44px; height: 44px; }
.astrafox-trigger.astrafox-lg { width: 68px; height: 68px; }
.astrafox-trigger.astrafox-open { animation: none !important; }

.astrafox-trigger-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.astrafox-trigger-avatar svg { width: 100%; height: 100%; }
.astrafox-trigger-avatar img { width: 100%; height: 100%; object-fit: contain; border-radius: 50%; }

/* ─── Positions ─────────────────────────────────────────────── */
.astrafox-pos-br .astrafox-trigger { bottom: 24px; right: 24px; }
.astrafox-pos-bl .astrafox-trigger { bottom: 24px; left: 24px; }
.astrafox-pos-tr .astrafox-trigger { top: 24px; right: 24px; }
.astrafox-pos-tl .astrafox-trigger { top: 24px; left: 24px; }

.astrafox-pos-br .astrafox-panel { bottom: 92px; right: 24px; }
.astrafox-pos-bl .astrafox-panel { bottom: 92px; left: 24px; }
.astrafox-pos-tr .astrafox-panel { top: 92px; right: 24px; }
.astrafox-pos-tl .astrafox-panel { top: 92px; left: 24px; }

/* ─── Badge ─────────────────────────────────────────────────── */
.astrafox-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ff4757;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
.astrafox-badge.astrafox-has-count { display: flex; }

/* ─── Backdrop ──────────────────────────────────────────────── */
.astrafox-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}
.astrafox-backdrop.astrafox-visible {
  opacity: 1;
  pointer-events: auto;
}

/* ─── Panel ─────────────────────────────────────────────────── */
.astrafox-panel {
  position: fixed;
  width: var(--astrafox-panel-width, 380px);
  height: var(--astrafox-panel-height, 520px);
  max-height: calc(100vh - 140px);
  max-width: calc(100vw - 48px);
  background: var(--astrafox-bg);
  border: 1px solid var(--astrafox-border);
  border-radius: var(--astrafox-panel-radius, 16px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.35);
  opacity: 0;
  pointer-events: none;
  transform-origin: bottom right;
}
.astrafox-panel.astrafox-visible {
  opacity: 1;
  pointer-events: auto;
}

/* ─── Header ────────────────────────────────────────────────── */
.astrafox-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--astrafox-surface);
  border-bottom: 1px solid var(--astrafox-border);
  min-height: 56px;
}
.astrafox-header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.astrafox-header-avatar svg { width: 100%; height: 100%; }
.astrafox-header-avatar img { width: 100%; height: 100%; object-fit: contain; }
.astrafox-header-info { flex: 1; min-width: 0; }
.astrafox-header-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--astrafox-text);
}
.astrafox-header-sub {
  font-size: 0.75rem;
  color: var(--astrafox-muted);
}
.astrafox-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--astrafox-muted);
  cursor: pointer;
  border-radius: 8px;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.astrafox-close:hover {
  background: var(--astrafox-border);
  color: var(--astrafox-text);
}

/* ─── Messages ──────────────────────────────────────────────── */
.astrafox-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-behavior: smooth;
}
.astrafox-messages::-webkit-scrollbar { width: 4px; }
.astrafox-messages::-webkit-scrollbar-track { background: transparent; }
.astrafox-messages::-webkit-scrollbar-thumb { background: var(--astrafox-border); border-radius: 2px; }

.astrafox-msg {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.88rem;
  line-height: 1.55;
  word-break: break-word;
}
.astrafox-msg a { color: var(--astrafox-accent); text-decoration: underline; }
.astrafox-msg code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
}
.astrafox-msg pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 6px 0;
}
.astrafox-msg pre code { background: none; padding: 0; }

.astrafox-msg.astrafox-user {
  align-self: flex-end;
  background: var(--astrafox-user-bubble);
  color: var(--astrafox-user-text);
  border-bottom-right-radius: 4px;
}
.astrafox-msg.astrafox-bot {
  align-self: flex-start;
  background: var(--astrafox-bot-bubble, var(--astrafox-surface));
  color: var(--astrafox-bot-text, var(--astrafox-text));
  border-bottom-left-radius: 4px;
}
.astrafox-msg.astrafox-system {
  align-self: center;
  background: transparent;
  color: var(--astrafox-muted);
  font-size: 0.8rem;
  font-style: italic;
}

/* ─── Typing indicator ──────────────────────────────────────── */
.astrafox-typing {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  align-self: flex-start;
}
.astrafox-typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--astrafox-muted);
  animation: astrafox-typing-dot 1.4s infinite ease-in-out;
}
.astrafox-typing span:nth-child(2) { animation-delay: 0.2s; }
.astrafox-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes astrafox-typing-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ─── Suggestions ───────────────────────────────────────────── */
.astrafox-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 8px;
}
.astrafox-suggestion {
  background: var(--astrafox-surface);
  border: 1px solid var(--astrafox-border);
  color: var(--astrafox-accent);
  padding: 5px 12px;
  border-radius: 16px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1.3;
}
.astrafox-suggestion:hover {
  background: var(--astrafox-accent);
  color: #fff;
  border-color: var(--astrafox-accent);
}

/* ─── Input ─────────────────────────────────────────────────── */
.astrafox-input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--astrafox-border);
  background: var(--astrafox-surface);
}
.astrafox-input {
  flex: 1;
  background: var(--astrafox-bg);
  border: 1px solid var(--astrafox-border);
  color: var(--astrafox-text);
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-family: inherit;
  resize: none;
  max-height: 80px;
  outline: none;
  transition: border-color 0.2s;
}
.astrafox-input::placeholder { color: var(--astrafox-muted); }
.astrafox-input:focus { border-color: var(--astrafox-accent); }

.astrafox-send {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: var(--astrafox-accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.15s;
}
.astrafox-send:hover { filter: brightness(1.1); transform: scale(1.05); }
.astrafox-send:active { transform: scale(0.95); }

/* ─── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .astrafox-panel {
    width: calc(100vw - 16px) !important;
    height: calc(100vh - 80px) !important;
    max-height: none;
    bottom: 8px !important;
    right: 8px !important;
    left: 8px !important;
    border-radius: 12px !important;
  }
}
`;

let injected = false;

/** Inject the core styles into the document head (idempotent) */
export function injectStyles(
  extraCSS?: string,
  animationCSS?: string
): void {
  if (typeof document === "undefined") return;
  if (injected) return;

  const style = document.createElement("style");
  style.id = "astrafox-styles";
  style.textContent = ASTRAFOX_STYLES + (animationCSS || "") + (extraCSS || "");
  document.head.appendChild(style);
  injected = true;
}

/** Update or append extra CSS (for runtime changes) */
export function updateExtraCSS(css: string): void {
  if (typeof document === "undefined") return;

  let el = document.getElementById("astrafox-extra-styles") as HTMLStyleElement;
  if (!el) {
    el = document.createElement("style");
    el.id = "astrafox-extra-styles";
    document.head.appendChild(el);
  }
  el.textContent = css;
}
