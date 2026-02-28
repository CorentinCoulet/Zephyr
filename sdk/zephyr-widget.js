/**
 * 🦊 Zephyr Widget — Embeddable AI Navigation Assistant
 *
 * Usage:
 *   <script src="https://your-zephyr-server/sdk/zephyr-widget.js"></script>
 *   <script>
 *     ZephyrWidget.init({
 *       server: 'https://your-zephyr-server',
 *       persona: 'minimal',
 *       theme: 'dark',
 *       position: 'bottom-right',
 *       language: 'fr',
 *     });
 *   </script>
 *
 * Or via npm:
 *   import { ZephyrWidget } from '@zephyr/widget';
 *   ZephyrWidget.init({ server: '...', persona: 'spirit' });
 */

(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.ZephyrWidget = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  // ─── Defaults ───────────────────────────────────────────────
  const DEFAULTS = {
    server: "",
    apiKey: "",
    persona: "minimal", // "mascot" | "spirit" | "minimal" | "futuristic" | custom URL
    theme: "dark", // "dark" | "light" | "auto"
    position: "bottom-right", // "bottom-right" | "bottom-left" | "top-right" | "top-left"
    size: "md", // "sm" | "md" | "lg"
    language: "fr", // "fr" | "en"
    greeting: null, // Custom greeting — null = use server default
    placeholder: null, // Input placeholder
    accentColor: "#ff6b35",
    zIndex: 99999,
    draggable: false,
    open: false, // Start open
    showBadge: true,
    badgeCount: 0,
    features: ["chat", "guide", "search"], // Enabled features
    onReady: null,
    onMessage: null,
    onError: null,
    onToggle: null,
    containerSelector: null, // Mount inside a specific element (null = body)
    customCSS: "", // Additional CSS to inject
  };

  // ─── Zephyr Logo (base64) ──────────────────────────────
  const ZEPHYR_LOGO = "data:image/png;base64,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";

  // ─── Persona SVG templates ─────────────────────────────────
  const PERSONAS = {
    mascot: {
      svg: (accent) => `
        <svg viewBox="0 0 64 64" width="100%" height="100%">
          <circle cx="32" cy="32" r="30" fill="${accent}" opacity="0.12"/>
          <circle cx="32" cy="32" r="28" fill="none" stroke="${accent}" stroke-width="2" opacity="0.5"/>
          <image href="${ZEPHYR_LOGO}" x="6" y="6" width="52" height="52" style="border-radius:50%"/>
        </svg>`,
    },
    spirit: {
      svg: (accent) => `
        <svg viewBox="0 0 64 64" width="100%" height="100%">
          <circle cx="32" cy="32" r="31" fill="${accent}" opacity="0.1"/>
          <circle cx="32" cy="32" r="27" fill="${accent}" opacity="0.06"/>
          <circle cx="32" cy="32" r="23" fill="${accent}" opacity="0.03"/>
          <circle cx="32" cy="32" r="26" fill="none" stroke="${accent}" stroke-width="1" opacity="0.3"/>
          <image href="${ZEPHYR_LOGO}" x="8" y="8" width="48" height="48" opacity="0.9"/>
        </svg>`,
    },
    minimal: {
      svg: (accent) => `
        <svg viewBox="0 0 64 64" width="100%" height="100%">
          <rect x="6" y="6" width="52" height="52" rx="14" fill="${accent}" opacity="0.08"/>
          <rect x="6" y="6" width="52" height="52" rx="14" fill="none" stroke="${accent}" stroke-width="1.5" opacity="0.25"/>
          <image href="${ZEPHYR_LOGO}" x="8" y="8" width="48" height="48"/>
        </svg>`,
    },
    futuristic: {
      svg: (accent) => `
        <svg viewBox="0 0 64 64" width="100%" height="100%">
          <rect x="4" y="4" width="56" height="56" rx="12" fill="none" stroke="${accent}" stroke-width="1.5" opacity="0.6"/>
          <rect x="8" y="8" width="48" height="48" rx="10" fill="${accent}" opacity="0.06"/>
          <circle cx="32" cy="6" r="2.5" fill="${accent}" opacity="0.8"/>
          <circle cx="32" cy="58" r="2" fill="${accent}" opacity="0.4"/>
          <circle cx="6" cy="32" r="2" fill="${accent}" opacity="0.4"/>
          <circle cx="58" cy="32" r="2" fill="${accent}" opacity="0.4"/>
          <image href="${ZEPHYR_LOGO}" x="10" y="10" width="44" height="44"/>
        </svg>`,
    },
  };

  // ─── Expression mutations ──────────────────────────────────
  const EXPRESSIONS = {
    neutral: { eyeRx: 3, eyeRy: 3.5, mouth: "M28,42 Q32,44 36,42" },
    happy: { eyeRx: 0, eyeRy: 0, mouth: "M26,42 Q32,48 38,42", eyeArc: true },
    surprised: { eyeRx: 4, eyeRy: 5, mouth: "M28,43 Q32,47 36,43" },
    thinking: { eyeRx: 3, eyeRy: 2.5, mouth: "M28,42 L36,42", dots: true },
    helping: { eyeRx: 3, eyeRy: 3.5, mouth: "M26,42 Q32,46 38,42" },
    speaking: { eyeRx: 3, eyeRy: 3.5, mouth: "M28,41 Q32,46 36,41" },
    wink: { eyeRx: 3, eyeRy: 3.5, mouth: "M26,42 Q32,47 38,42", winkLeft: true },
  };

  // ─── Theme definitions ─────────────────────────────────────
  const THEMES = {
    dark: {
      "--kw-bg": "#0f0f1a",
      "--kw-surface": "#1a1a2e",
      "--kw-text": "#e8e8f0",
      "--kw-muted": "#6b6b80",
      "--kw-border": "#2a2a40",
      "--kw-user-bubble": "var(--kw-accent, #ff6b35)",
      "--kw-user-text": "#ffffff",
    },
    light: {
      "--kw-bg": "#f5f5fa",
      "--kw-surface": "#ffffff",
      "--kw-text": "#1a1a2e",
      "--kw-muted": "#8888a0",
      "--kw-border": "#e0e0ee",
      "--kw-user-bubble": "var(--kw-accent, #e85d26)",
      "--kw-user-text": "#ffffff",
    },
  };

  // ─── CSS ───────────────────────────────────────────────────
  const CSS = `
    .kw-root {
      --kw-accent: #ff6b35;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      box-sizing: border-box;
    }
    .kw-root *, .kw-root *::before, .kw-root *::after {
      box-sizing: inherit;
    }

    /* Trigger button */
    .kw-trigger {
      position: fixed;
      width: 56px; height: 56px;
      border-radius: 50%;
      border: 2px solid var(--kw-accent);
      background: var(--kw-surface);
      cursor: pointer;
      z-index: var(--kw-z);
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
      transition: transform 0.25s ease, box-shadow 0.25s ease;
      padding: 6px;
      animation: kw-float 3s ease-in-out infinite;
    }
    .kw-trigger:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(0,0,0,0.35);
    }
    .kw-trigger.kw-sm { width: 44px; height: 44px; }
    .kw-trigger.kw-lg { width: 68px; height: 68px; }
    .kw-trigger.kw-open { animation: none; }

    /* Badge */
    .kw-badge {
      position: absolute; top: -4px; right: -4px;
      background: #ff4757; color: #fff; font-size: 10px; font-weight: 700;
      min-width: 18px; height: 18px; border-radius: 9px;
      display: flex; align-items: center; justify-content: center;
      padding: 0 4px;
    }
    .kw-badge:empty { display: none; }

    /* Panel */
    .kw-panel {
      position: fixed;
      width: 380px; max-width: calc(100vw - 24px);
      height: 520px; max-height: calc(100vh - 100px);
      border-radius: 16px;
      background: var(--kw-bg);
      border: 1px solid var(--kw-border);
      box-shadow: 0 12px 40px rgba(0,0,0,0.3);
      display: flex; flex-direction: column;
      overflow: hidden;
      z-index: var(--kw-z);
      opacity: 0; pointer-events: none;
      transform: translateY(12px) scale(0.95);
      transition: opacity 0.25s ease, transform 0.25s ease;
    }
    .kw-panel.kw-visible {
      opacity: 1; pointer-events: auto;
      transform: translateY(0) scale(1);
    }

    /* Header */
    .kw-header {
      display: flex; align-items: center; gap: 10px;
      padding: 12px 16px;
      background: var(--kw-surface);
      border-bottom: 1px solid var(--kw-border);
    }
    .kw-header-avatar { width: 36px; height: 36px; flex-shrink: 0; }
    .kw-header-info { flex: 1; min-width: 0; }
    .kw-header-title { font-weight: 600; color: var(--kw-accent); font-size: 15px; }
    .kw-header-sub { font-size: 11px; color: var(--kw-muted); }
    .kw-close {
      background: none; border: none; color: var(--kw-muted);
      font-size: 20px; cursor: pointer; padding: 4px 8px;
      border-radius: 6px; transition: background 0.2s;
    }
    .kw-close:hover { background: var(--kw-border); }

    /* Messages */
    .kw-messages {
      flex: 1; overflow-y: auto; padding: 12px;
      display: flex; flex-direction: column; gap: 8px;
    }
    .kw-msg {
      max-width: 82%; padding: 10px 14px;
      border-radius: 14px; font-size: 13px;
      animation: kw-slide-up 0.2s ease-out;
      word-wrap: break-word;
    }
    .kw-msg.kw-user {
      background: var(--kw-user-bubble); color: var(--kw-user-text);
      align-self: flex-end; border-bottom-right-radius: 4px;
    }
    .kw-msg.kw-bot {
      background: var(--kw-surface); color: var(--kw-text);
      border: 1px solid var(--kw-border);
      align-self: flex-start; border-bottom-left-radius: 4px;
    }
    .kw-msg.kw-system {
      align-self: center; font-size: 11px; color: var(--kw-muted);
      font-style: italic; max-width: 90%;
    }
    .kw-msg code {
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 12px; background: rgba(0,0,0,0.15);
      padding: 1px 4px; border-radius: 3px;
    }
    .kw-msg pre {
      background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px;
      overflow-x: auto; margin: 6px 0; font-size: 12px;
    }

    /* Typing indicator */
    .kw-typing {
      display: flex; align-items: center; gap: 4px; padding: 8px 14px;
      align-self: flex-start;
    }
    .kw-typing span {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--kw-accent); animation: kw-bounce 1.2s infinite;
    }
    .kw-typing span:nth-child(2) { animation-delay: 0.15s; }
    .kw-typing span:nth-child(3) { animation-delay: 0.3s; }

    /* Suggestions */
    .kw-suggestions {
      display: flex; flex-wrap: wrap; gap: 6px;
      padding: 6px 12px;
    }
    .kw-suggestion {
      font-size: 11px; padding: 5px 10px; border-radius: 12px;
      background: var(--kw-surface); border: 1px solid var(--kw-border);
      color: var(--kw-text); cursor: pointer; transition: all 0.15s;
    }
    .kw-suggestion:hover {
      border-color: var(--kw-accent); color: var(--kw-accent);
    }

    /* Input */
    .kw-input-wrap {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 12px; border-top: 1px solid var(--kw-border);
      background: var(--kw-surface);
    }
    .kw-input {
      flex: 1; border: 1px solid var(--kw-border); border-radius: 10px;
      padding: 8px 12px; font-size: 13px; resize: none; outline: none;
      background: var(--kw-bg); color: var(--kw-text);
      max-height: 80px; min-height: 36px; font-family: inherit;
      transition: border-color 0.2s;
    }
    .kw-input:focus { border-color: var(--kw-accent); }
    .kw-send {
      background: var(--kw-accent); color: #fff; border: none;
      width: 36px; height: 36px; border-radius: 50%;
      font-size: 16px; cursor: pointer; transition: opacity 0.2s;
      display: flex; align-items: center; justify-content: center;
    }
    .kw-send:disabled { opacity: 0.4; cursor: not-allowed; }

    /* Positions */
    .kw-pos-br .kw-trigger { bottom: 20px; right: 20px; }
    .kw-pos-br .kw-panel { bottom: 86px; right: 20px; }
    .kw-pos-bl .kw-trigger { bottom: 20px; left: 20px; }
    .kw-pos-bl .kw-panel { bottom: 86px; left: 20px; }
    .kw-pos-tr .kw-trigger { top: 20px; right: 20px; }
    .kw-pos-tr .kw-panel { top: 86px; right: 20px; }
    .kw-pos-tl .kw-trigger { top: 20px; left: 20px; }
    .kw-pos-tl .kw-panel { top: 86px; left: 20px; }

    /* Inline (no trigger) */
    .kw-inline .kw-trigger { display: none; }
    .kw-inline .kw-panel {
      position: relative; opacity: 1; pointer-events: auto;
      transform: none; width: 100%; height: 100%;
      max-width: none; max-height: none; border-radius: 12px;
    }

    /* Scrollbar */
    .kw-messages::-webkit-scrollbar { width: 4px; }
    .kw-messages::-webkit-scrollbar-thumb { background: var(--kw-border); border-radius: 2px; }

    /* Animations */
    @keyframes kw-float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }
    @keyframes kw-slide-up {
      from { transform: translateY(8px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    @keyframes kw-bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }

    /* Mobile */
    @media (max-width: 480px) {
      .kw-panel {
        width: calc(100vw - 16px);
        height: calc(100vh - 80px);
        bottom: 70px !important; right: 8px !important; left: 8px !important;
      }
    }
  `;

  // ─── Widget Class ──────────────────────────────────────────
  class Widget {
    constructor(options) {
      this.config = { ...DEFAULTS, ...options };
      this.ws = null;
      this.sessionId = null;
      this.messages = [];
      this.expression = "neutral";
      this.isOpen = this.config.open;
      this.isLoading = false;
      this.suggestions = [];
      this.el = null;
      this._mounted = false;
    }

    // ─── Public API ─────────────────────────────────────────

    mount(container) {
      if (this._mounted) return;
      this._mounted = true;

      const target = container
        ? (typeof container === "string" ? document.querySelector(container) : container)
        : document.body;

      // Inject CSS
      if (!document.getElementById("kw-styles")) {
        const style = document.createElement("style");
        style.id = "kw-styles";
        style.textContent = CSS + (this.config.customCSS || "");
        document.head.appendChild(style);
      }

      // Create root
      this.el = document.createElement("div");
      this.el.className = "kw-root " + this._posClass();
      this._applyTheme();
      this.el.style.setProperty("--kw-z", this.config.zIndex);
      this.el.style.setProperty("--kw-accent", this.config.accentColor);

      const isInline = this.config.containerSelector !== null;
      if (isInline) this.el.classList.add("kw-inline");

      this.el.innerHTML = this._renderHTML();
      target.appendChild(this.el);

      this._bindEvents();
      this._connectWS();

      if (this.config.onReady) this.config.onReady(this);
    }

    destroy() {
      if (this.ws) this.ws.close();
      if (this.el) this.el.remove();
      this._mounted = false;
    }

    open() { this._toggle(true); }
    close() { this._toggle(false); }
    toggle() { this._toggle(!this.isOpen); }

    send(text) {
      if (!text.trim()) return;
      this._addMessage("user", text);
      this._wsSend({ message: text, url: window.location.href });
    }

    setTheme(theme) {
      this.config.theme = theme;
      this._applyTheme();
    }

    setPersona(persona) {
      this.config.persona = persona;
      this._updateAvatar();
    }

    setAccentColor(color) {
      this.config.accentColor = color;
      this.el.style.setProperty("--kw-accent", color);
      this._updateAvatar();
    }

    on(event, handler) {
      this.config["on" + event.charAt(0).toUpperCase() + event.slice(1)] = handler;
    }

    // ─── Internal ───────────────────────────────────────────

    _posClass() {
      const map = {
        "bottom-right": "kw-pos-br",
        "bottom-left": "kw-pos-bl",
        "top-right": "kw-pos-tr",
        "top-left": "kw-pos-tl",
      };
      return map[this.config.position] || "kw-pos-br";
    }

    _applyTheme() {
      let theme = this.config.theme;
      if (theme === "auto") {
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      }
      const vars = THEMES[theme] || THEMES.dark;
      for (const [key, val] of Object.entries(vars)) {
        this.el.style.setProperty(key, val);
      }
    }

    _avatarSVG() {
      // Always use the actual logo image directly
      return `<img src="${ZEPHYR_LOGO}" style="width:100%;height:100%;object-fit:contain;border-radius:50%;" alt="Zephyr"/>`;
    }

    _renderHTML() {
      const sizeClass = "kw-" + (this.config.size || "md");
      const ph = this.config.placeholder ||
        (this.config.language === "fr" ? "Posez une question..." : "Ask a question...");

      return `
        <button class="kw-trigger ${sizeClass}" aria-label="Zephyr Assistant">
          <div class="kw-trigger-avatar">${this._avatarSVG()}</div>
          ${this.config.showBadge ? '<div class="kw-badge"></div>' : ""}
        </button>
        <div class="kw-panel ${this.isOpen ? "kw-visible" : ""}">
          <div class="kw-header">
            <div class="kw-header-avatar">${this._avatarSVG()}</div>
            <div class="kw-header-info">
              <div class="kw-header-title">Zephyr</div>
              <div class="kw-header-sub">Assistant Navigation</div>
            </div>
            <button class="kw-close" aria-label="Fermer">×</button>
          </div>
          <div class="kw-messages"></div>
          <div class="kw-suggestions"></div>
          <div class="kw-input-wrap">
            <textarea class="kw-input" rows="1" placeholder="${ph}"></textarea>
            <button class="kw-send" aria-label="Envoyer">➤</button>
          </div>
        </div>
      `;
    }

    _bindEvents() {
      const trigger = this.el.querySelector(".kw-trigger");
      const close = this.el.querySelector(".kw-close");
      const input = this.el.querySelector(".kw-input");
      const send = this.el.querySelector(".kw-send");

      trigger.addEventListener("click", () => this.toggle());
      close.addEventListener("click", () => this.close());

      send.addEventListener("click", () => {
        this.send(input.value);
        input.value = "";
        input.style.height = "auto";
      });

      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.send(input.value);
          input.value = "";
          input.style.height = "auto";
        }
      });

      // Auto-resize textarea
      input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 80) + "px";
      });
    }

    _toggle(open) {
      this.isOpen = open;
      const panel = this.el.querySelector(".kw-panel");
      const trigger = this.el.querySelector(".kw-trigger");
      panel.classList.toggle("kw-visible", open);
      trigger.classList.toggle("kw-open", open);
      if (this.config.onToggle) this.config.onToggle(open);

      if (open) {
        setTimeout(() => this.el.querySelector(".kw-input")?.focus(), 200);
      }
    }

    _addMessage(role, text, expr) {
      const cls = role === "user" ? "kw-user" : role === "system" ? "kw-system" : "kw-bot";
      const container = this.el.querySelector(".kw-messages");
      const msg = document.createElement("div");
      msg.className = `kw-msg ${cls}`;
      msg.innerHTML = this._renderMarkdown(text);
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;

      this.messages.push({ role, text, expression: expr || this.expression });
      if (this.config.onMessage) this.config.onMessage({ role, text, expression: expr });
    }

    _showTyping() {
      this.isLoading = true;
      const container = this.el.querySelector(".kw-messages");
      let typing = container.querySelector(".kw-typing");
      if (!typing) {
        typing = document.createElement("div");
        typing.className = "kw-typing";
        typing.innerHTML = "<span></span><span></span><span></span>";
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
      }
    }

    _hideTyping() {
      this.isLoading = false;
      const typing = this.el.querySelector(".kw-typing");
      if (typing) typing.remove();
    }

    _showSuggestions(items) {
      this.suggestions = items || [];
      const container = this.el.querySelector(".kw-suggestions");
      container.innerHTML = items
        .map((s) => `<button class="kw-suggestion">${this._esc(s)}</button>`)
        .join("");
      container.querySelectorAll(".kw-suggestion").forEach((btn) => {
        btn.addEventListener("click", () => {
          this.send(btn.textContent);
          container.innerHTML = "";
        });
      });
    }

    _updateAvatar() {
      const svg = this._avatarSVG();
      const triggerAv = this.el.querySelector(".kw-trigger-avatar");
      const headerAv = this.el.querySelector(".kw-header-avatar");
      if (triggerAv) triggerAv.innerHTML = svg;
      if (headerAv) headerAv.innerHTML = svg;
    }

    // ─── WebSocket ──────────────────────────────────────────

    _connectWS() {
      if (!this.config.server) {
        console.warn("[ZephyrWidget] No server URL configured.");
        return;
      }

      const base = this.config.server.replace(/\/$/, "");
      const protocol = base.startsWith("https") ? "wss:" : "ws:";
      const host = base.replace(/^https?:\/\//, "");
      const sid = this.sessionId || "";
      const url = `${protocol}//${host}/ws/chat?session_id=${sid}`;

      this.ws = new WebSocket(url);

      this.ws.onopen = () => {};

      this.ws.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch { return; }

        if (data.type === "welcome") {
          this.sessionId = data.session_id;
          this.expression = data.expression || "happy";
          const greeting = this.config.greeting || data.message;
          this._addMessage("bot", greeting, data.expression);
        } else if (data.type === "status") {
          this.expression = data.expression || "thinking";
          this._showTyping();
        } else if (data.type === "response") {
          this._hideTyping();
          this.expression = data.expression || "neutral";
          this._addMessage("bot", data.message, data.expression);
          if (data.suggestions?.length) this._showSuggestions(data.suggestions);
        } else if (data.type === "error") {
          this._hideTyping();
          this._addMessage("system", data.message, "surprised");
          if (this.config.onError) this.config.onError(data);
        }
      };

      this.ws.onclose = () => {
        setTimeout(() => this._connectWS(), 3000);
      };

      this.ws.onerror = () => {
        if (this.config.onError) this.config.onError({ message: "WebSocket error" });
      };
    }

    _wsSend(data) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      this._showTyping();
      this.ws.send(JSON.stringify(data));
    }

    // ─── Markdown (minimal) ─────────────────────────────────

    _renderMarkdown(text) {
      if (!text) return "";
      let html = this._esc(text);
      // Code blocks
      html = html.replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
      // Inline code
      html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
      // Bold
      html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      // Italic
      html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
      // Lists
      html = html.replace(/^[-•] (.+)$/gm, "<li>$1</li>");
      html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
      // Line breaks
      html = html.replace(/\n/g, "<br>");
      return html;
    }

    _esc(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }
  }

  // ─── Static API ────────────────────────────────────────────
  let instance = null;

  return {
    init(options) {
      instance = new Widget(options);
      instance.mount(options.containerSelector || null);
      return instance;
    },
    getInstance() {
      return instance;
    },
    Widget: Widget,
    PERSONAS: PERSONAS,
    THEMES: THEMES,
  };
});
