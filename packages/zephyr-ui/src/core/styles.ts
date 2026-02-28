/**
 * 🎨 Zephyr CSS Styles
 *
 * All styles use CSS custom properties (--zephyr-*) set by the theme system.
 * No external CSS dependencies.
 */

/** Core widget styles — injected once per page */
export const ZEPHYR_STYLES = `
/* ─── Root ──────────────────────────────────────────────────── */
.zephyr-root {
  --zephyr-accent: #ff6b35;
  --zephyr-bg: #0f0f1a;
  --zephyr-surface: #1a1a2e;
  --zephyr-text: #e8e8f0;
  --zephyr-muted: #6b6b80;
  --zephyr-border: #2a2a40;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
  color: var(--zephyr-text);
}
.zephyr-root *, .zephyr-root *::before, .zephyr-root *::after {
  box-sizing: inherit;
}

/* ─── Trigger button ────────────────────────────────────────── */
.zephyr-trigger {
  position: fixed;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 2px solid var(--zephyr-accent);
  background: var(--zephyr-surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  outline: none;
}
.zephyr-trigger:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
}
.zephyr-trigger:focus-visible {
  outline: 2px solid var(--zephyr-accent);
  outline-offset: 3px;
}
.zephyr-trigger.zephyr-sm { width: 44px; height: 44px; }
.zephyr-trigger.zephyr-lg { width: 68px; height: 68px; }
.zephyr-trigger.zephyr-open { animation: none !important; }

.zephyr-trigger-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zephyr-trigger-avatar svg { width: 100%; height: 100%; }
.zephyr-trigger-avatar img { width: 100%; height: 100%; object-fit: contain; border-radius: 50%; }

/* ─── Positions ─────────────────────────────────────────────── */
.zephyr-pos-br .zephyr-trigger { bottom: 24px; right: 24px; }
.zephyr-pos-bl .zephyr-trigger { bottom: 24px; left: 24px; }
.zephyr-pos-tr .zephyr-trigger { top: 24px; right: 24px; }
.zephyr-pos-tl .zephyr-trigger { top: 24px; left: 24px; }

.zephyr-pos-br .zephyr-panel { bottom: 92px; right: 24px; }
.zephyr-pos-bl .zephyr-panel { bottom: 92px; left: 24px; }
.zephyr-pos-tr .zephyr-panel { top: 92px; right: 24px; }
.zephyr-pos-tl .zephyr-panel { top: 92px; left: 24px; }

/* ─── Badge ─────────────────────────────────────────────────── */
.zephyr-badge {
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
.zephyr-badge.zephyr-has-count { display: flex; }

/* ─── Backdrop ──────────────────────────────────────────────── */
.zephyr-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}
.zephyr-backdrop.zephyr-visible {
  opacity: 1;
  pointer-events: auto;
}

/* ─── Panel ─────────────────────────────────────────────────── */
.zephyr-panel {
  position: fixed;
  width: var(--zephyr-panel-width, 380px);
  height: var(--zephyr-panel-height, 520px);
  max-height: calc(100vh - 140px);
  max-width: calc(100vw - 48px);
  background: var(--zephyr-bg);
  border: 1px solid var(--zephyr-border);
  border-radius: var(--zephyr-panel-radius, 16px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.35);
  opacity: 0;
  pointer-events: none;
  transform-origin: bottom right;
}
.zephyr-panel.zephyr-visible {
  opacity: 1;
  pointer-events: auto;
}

/* ─── Header ────────────────────────────────────────────────── */
.zephyr-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--zephyr-surface);
  border-bottom: 1px solid var(--zephyr-border);
  min-height: 56px;
}
.zephyr-header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.zephyr-header-avatar svg { width: 100%; height: 100%; }
.zephyr-header-avatar img { width: 100%; height: 100%; object-fit: contain; }
.zephyr-header-info { flex: 1; min-width: 0; }
.zephyr-header-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--zephyr-text);
}
.zephyr-header-sub {
  font-size: 0.75rem;
  color: var(--zephyr-muted);
}
.zephyr-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--zephyr-muted);
  cursor: pointer;
  border-radius: 8px;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.zephyr-close:hover {
  background: var(--zephyr-border);
  color: var(--zephyr-text);
}

/* ─── Messages ──────────────────────────────────────────────── */
.zephyr-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-behavior: smooth;
}
.zephyr-messages::-webkit-scrollbar { width: 4px; }
.zephyr-messages::-webkit-scrollbar-track { background: transparent; }
.zephyr-messages::-webkit-scrollbar-thumb { background: var(--zephyr-border); border-radius: 2px; }

.zephyr-msg {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.88rem;
  line-height: 1.55;
  word-break: break-word;
}
.zephyr-msg a { color: var(--zephyr-accent); text-decoration: underline; }
.zephyr-msg code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
}
.zephyr-msg pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 6px 0;
}
.zephyr-msg pre code { background: none; padding: 0; }

.zephyr-msg.zephyr-user {
  align-self: flex-end;
  background: var(--zephyr-user-bubble);
  color: var(--zephyr-user-text);
  border-bottom-right-radius: 4px;
}
.zephyr-msg.zephyr-bot {
  align-self: flex-start;
  background: var(--zephyr-bot-bubble, var(--zephyr-surface));
  color: var(--zephyr-bot-text, var(--zephyr-text));
  border-bottom-left-radius: 4px;
}
.zephyr-msg.zephyr-system {
  align-self: center;
  background: transparent;
  color: var(--zephyr-muted);
  font-size: 0.8rem;
  font-style: italic;
}

/* ─── Typing indicator ──────────────────────────────────────── */
.zephyr-typing {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  align-self: flex-start;
}
.zephyr-typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--zephyr-muted);
  animation: zephyr-typing-dot 1.4s infinite ease-in-out;
}
.zephyr-typing span:nth-child(2) { animation-delay: 0.2s; }
.zephyr-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes zephyr-typing-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ─── Suggestions ───────────────────────────────────────────── */
.zephyr-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 8px;
}
.zephyr-suggestion {
  background: var(--zephyr-surface);
  border: 1px solid var(--zephyr-border);
  color: var(--zephyr-accent);
  padding: 5px 12px;
  border-radius: 16px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1.3;
}
.zephyr-suggestion:hover {
  background: var(--zephyr-accent);
  color: #fff;
  border-color: var(--zephyr-accent);
}

/* ─── Input ─────────────────────────────────────────────────── */
.zephyr-input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--zephyr-border);
  background: var(--zephyr-surface);
}
.zephyr-input {
  flex: 1;
  background: var(--zephyr-bg);
  border: 1px solid var(--zephyr-border);
  color: var(--zephyr-text);
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-family: inherit;
  resize: none;
  max-height: 80px;
  outline: none;
  transition: border-color 0.2s;
}
.zephyr-input::placeholder { color: var(--zephyr-muted); }
.zephyr-input:focus { border-color: var(--zephyr-accent); }

.zephyr-send {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: var(--zephyr-accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.15s;
}
.zephyr-send:hover { filter: brightness(1.1); transform: scale(1.05); }
.zephyr-send:active { transform: scale(0.95); }

/* ─── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .zephyr-panel {
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
  style.id = "zephyr-styles";
  style.textContent = ZEPHYR_STYLES + (animationCSS || "") + (extraCSS || "");
  document.head.appendChild(style);
  injected = true;
}

/** Update or append extra CSS (for runtime changes) */
export function updateExtraCSS(css: string): void {
  if (typeof document === "undefined") return;

  let el = document.getElementById("zephyr-extra-styles") as HTMLStyleElement;
  if (!el) {
    el = document.createElement("style");
    el.id = "zephyr-extra-styles";
    document.head.appendChild(el);
  }
  el.textContent = css;
}
