/**
 * 🦊 Zephyr Widget — Core engine
 *
 * Framework-agnostic widget that can be used standalone or wrapped
 * by React/Vue components. Handles DOM rendering, WebSocket, animations.
 */

import type { ZephyrConfig, ZephyrLogo, ZephyrPersona, ZephyrOpenAnimation, ZephyrTriggerAnimation } from "./config";
import { resolveConfig, ZEPHYR_DEFAULTS } from "./config";
import { resolveTheme, themeToCSSVars } from "./themes";
import { resolveLogo, type ResolvedLogo } from "./logos";
import { resolvePersona, type ResolvedPersona } from "./personas";
import {
  getOpenAnimationCSS,
  getOpenAnimationName,
  getCloseAnimationName,
  getTriggerAnimationCSS,
  getTriggerAnimationName,
} from "./animations";
import { injectStyles, updateExtraCSS } from "./styles";
import { ZephyrWSClient, type ZephyrWSMessage } from "./ws-client";

// ─── Types ───────────────────────────────────────────────────

export interface ZephyrMessage {
  role: "user" | "bot" | "system";
  text: string;
  expression?: string;
  timestamp: number;
}

export interface ZephyrWidgetEvents {
  onReady?: () => void;
  onMessage?: (msg: ZephyrMessage) => void;
  onError?: (err: { message: string }) => void;
  onToggle?: (open: boolean) => void;
}

// ─── Widget ──────────────────────────────────────────────────

export class ZephyrWidget {
  private config: ReturnType<typeof resolveConfig>;
  private events: ZephyrWidgetEvents;
  private el: HTMLElement | null = null;
  private wsClient: ZephyrWSClient | null = null;
  private isOpen = false;
  private messages: ZephyrMessage[] = [];
  private logo: ResolvedLogo;
  private persona: ResolvedPersona;
  private mounted = false;

  constructor(userConfig: ZephyrConfig, events: ZephyrWidgetEvents = {}) {
    this.config = resolveConfig(userConfig);
    this.events = events;
    this.logo = resolveLogo(this.config.logo, this.config.accentColor);
    this.persona = resolvePersona(this.config.persona, this.config.accentColor);
  }

  // ─── Lifecycle ────────────────────────────────────────────

  /** Mount the widget to the DOM */
  mount(container?: HTMLElement | string | null): void {
    if (this.mounted) return;

    // Inject CSS
    const animCSS = [
      getOpenAnimationCSS(this.config.openAnimation),
      getTriggerAnimationCSS(this.config.triggerAnimation),
    ].join("\n");
    injectStyles(this.config.customCSS, animCSS);

    // Create root element
    this.el = document.createElement("div");
    this.el.className = `zephyr-root ${this.positionClass()}`;
    this.el.setAttribute("data-zephyr", "");
    this.applyThemeVars();
    this.applyPanelVars();

    // Render HTML
    this.el.innerHTML = this.renderHTML();

    // Mount to target
    const target = typeof container === "string"
      ? document.querySelector(container)
      : container || document.body;
    target?.appendChild(this.el);

    // Bind events
    this.bindEvents();

    // Connect WebSocket
    this.connectWS();

    // Start open?
    if (this.config.startOpen) {
      requestAnimationFrame(() => this.open());
    }

    this.mounted = true;
    this.events.onReady?.();
  }

  /** Destroy the widget and clean up */
  destroy(): void {
    this.wsClient?.destroy();
    this.el?.remove();
    this.el = null;
    this.mounted = false;
  }

  // ─── Public API ───────────────────────────────────────────

  open(): void {
    this.setOpenState(true);
  }

  close(): void {
    this.setOpenState(false);
  }

  toggle(): void {
    this.setOpenState(!this.isOpen);
  }

  /** Send a message programmatically */
  send(text: string): void {
    if (!text.trim()) return;
    this.addMessage("user", text);
    this.wsClient?.send(text);
  }

  /** Change theme at runtime */
  setTheme(theme: ZephyrConfig["theme"]): void {
    this.config = { ...this.config, theme: theme || "dark" };
    this.applyThemeVars();
  }

  /** Change logo at runtime */
  setLogo(logo: ZephyrLogo): void {
    this.config = { ...this.config, logo };
    this.logo = resolveLogo(logo, this.config.accentColor);
    this.updateAvatars();
  }

  /** Change persona at runtime */
  setPersona(persona: ZephyrPersona): void {
    this.config = { ...this.config, persona };
    this.persona = resolvePersona(persona, this.config.accentColor);
    this.updateChatAvatar();
  }

  /** Change accent color at runtime */
  setAccentColor(color: string): void {
    this.config = { ...this.config, accentColor: color };
    this.logo = resolveLogo(this.config.logo, color);
    this.persona = resolvePersona(this.config.persona, color);
    this.el?.style.setProperty("--zephyr-accent", color);
    this.updateAvatars();
    this.updateChatAvatar();
  }

  /** Change open animation */
  setOpenAnimation(anim: ZephyrOpenAnimation): void {
    this.config = { ...this.config, openAnimation: anim };
    const css = getOpenAnimationCSS(anim);
    updateExtraCSS(css);
  }

  /** Change trigger animation */
  setTriggerAnimation(anim: ZephyrTriggerAnimation): void {
    this.config = { ...this.config, triggerAnimation: anim };
    const trigger = this.el?.querySelector(".zephyr-trigger") as HTMLElement;
    if (trigger) {
      const name = getTriggerAnimationName(anim);
      trigger.style.animation = name === "none" ? "none" : `${name} 3s ease-in-out infinite`;
    }
  }

  /** Get message history */
  getMessages(): ZephyrMessage[] {
    return [...this.messages];
  }

  /** Check if panel is open */
  getIsOpen(): boolean {
    return this.isOpen;
  }

  // ─── Private: Rendering ───────────────────────────────────

  private renderHTML(): string {
    const sizeClass = `zephyr-${this.config.panel.size || "md"}`;
    const triggerAnimName = getTriggerAnimationName(this.config.triggerAnimation);
    const triggerAnimCSS = triggerAnimName === "none"
      ? ""
      : `animation: ${triggerAnimName} 3s ease-in-out infinite;`;

    const ph = this.config.placeholder ||
      (this.config.language === "fr" ? "Posez une question..." : "Ask a question...");

    const triggerContent = `<img src="${this.escapeAttr(this.logo.trigger)}" alt="${this.escapeAttr(this.logo.alt)}" />`;
    const headerContent = `<img src="${this.escapeAttr(this.logo.header)}" alt="${this.escapeAttr(this.logo.alt)}" />`;

    const backdrop = this.config.panel.backdrop
      ? `<div class="zephyr-backdrop"></div>`
      : "";

    return `
      ${backdrop}
      <button class="zephyr-trigger ${sizeClass}" style="${triggerAnimCSS}" aria-label="Zephyr Assistant">
        <div class="zephyr-trigger-avatar">${triggerContent}</div>
        ${this.config.showBadge ? '<div class="zephyr-badge"></div>' : ""}
      </button>
      <div class="zephyr-panel">
        <div class="zephyr-header">
          <div class="zephyr-header-avatar">${headerContent}</div>
          <div class="zephyr-header-info">
            <div class="zephyr-header-title">Zephyr</div>
            <div class="zephyr-header-sub">${
              this.config.language === "fr" ? "Assistant Navigation" : "Navigation Assistant"
            }</div>
          </div>
          <button class="zephyr-close" aria-label="${this.config.language === "fr" ? "Fermer" : "Close"}">✕</button>
        </div>
        <div class="zephyr-messages"></div>
        <div class="zephyr-suggestions"></div>
        <div class="zephyr-input-wrap">
          <textarea class="zephyr-input" rows="1" placeholder="${this.escapeAttr(ph)}"></textarea>
          <button class="zephyr-send" aria-label="${this.config.language === "fr" ? "Envoyer" : "Send"}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    `;
  }

  private bindEvents(): void {
    if (!this.el) return;
    const trigger = this.el.querySelector(".zephyr-trigger")!;
    const close = this.el.querySelector(".zephyr-close")!;
    const input = this.el.querySelector(".zephyr-input") as HTMLTextAreaElement;
    const send = this.el.querySelector(".zephyr-send")!;
    const backdrop = this.el.querySelector(".zephyr-backdrop");

    trigger.addEventListener("click", () => this.toggle());
    close.addEventListener("click", () => this.close());
    backdrop?.addEventListener("click", () => this.close());

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

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 80) + "px";
    });
  }

  // ─── Private: State ───────────────────────────────────────

  private setOpenState(open: boolean): void {
    if (this.isOpen === open) return;
    this.isOpen = open;

    const panel = this.el?.querySelector(".zephyr-panel") as HTMLElement;
    const trigger = this.el?.querySelector(".zephyr-trigger") as HTMLElement;
    const backdrop = this.el?.querySelector(".zephyr-backdrop") as HTMLElement;

    if (!panel) return;

    if (open) {
      panel.classList.add("zephyr-visible");
      const animName = getOpenAnimationName(this.config.openAnimation);
      if (animName !== "none") {
        panel.style.animation = `${animName} 0.3s ease-out forwards`;
      }
      trigger?.classList.add("zephyr-open");
      backdrop?.classList.add("zephyr-visible");
      setTimeout(() => {
        (this.el?.querySelector(".zephyr-input") as HTMLTextAreaElement)?.focus();
      }, 200);
    } else {
      const animName = getCloseAnimationName(this.config.openAnimation);
      if (animName !== "none") {
        panel.style.animation = `${animName} 0.2s ease-in forwards`;
        panel.addEventListener("animationend", () => {
          panel.classList.remove("zephyr-visible");
          panel.style.animation = "";
        }, { once: true });
      } else {
        panel.classList.remove("zephyr-visible");
      }
      trigger?.classList.remove("zephyr-open");
      backdrop?.classList.remove("zephyr-visible");
    }

    this.events.onToggle?.(open);
  }

  // ─── Private: Messages ────────────────────────────────────

  private addMessage(role: ZephyrMessage["role"], text: string, expression?: string): void {
    const msg: ZephyrMessage = { role, text, expression, timestamp: Date.now() };
    this.messages.push(msg);

    const container = this.el?.querySelector(".zephyr-messages");
    if (!container) return;

    const div = document.createElement("div");
    div.className = `zephyr-msg zephyr-${role}`;
    div.innerHTML = this.renderMarkdown(text);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    this.events.onMessage?.(msg);
  }

  private showTyping(): void {
    const container = this.el?.querySelector(".zephyr-messages");
    if (!container || container.querySelector(".zephyr-typing")) return;
    const typing = document.createElement("div");
    typing.className = "zephyr-typing";
    typing.innerHTML = "<span></span><span></span><span></span>";
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
  }

  private hideTyping(): void {
    this.el?.querySelector(".zephyr-typing")?.remove();
  }

  private showSuggestions(items: string[]): void {
    const container = this.el?.querySelector(".zephyr-suggestions");
    if (!container) return;
    container.innerHTML = items
      .map((s) => `<button class="zephyr-suggestion">${this.escapeHTML(s)}</button>`)
      .join("");
    container.querySelectorAll(".zephyr-suggestion").forEach((btn) => {
      btn.addEventListener("click", () => {
        this.send(btn.textContent || "");
        container.innerHTML = "";
      });
    });
  }

  // ─── Private: Theme & Avatars ─────────────────────────────

  private applyThemeVars(): void {
    if (!this.el) return;
    const resolved = resolveTheme(this.config.theme);
    const vars = themeToCSSVars(resolved, this.config.accentColor);
    for (const [key, val] of Object.entries(vars)) {
      this.el.style.setProperty(key, val);
    }
  }

  private applyPanelVars(): void {
    if (!this.el) return;
    const p = this.config.panel;
    this.el.style.setProperty("--zephyr-panel-width", `${p.width}px`);
    this.el.style.setProperty("--zephyr-panel-height", `${p.height}px`);
    this.el.style.setProperty("--zephyr-panel-radius", `${p.borderRadius}px`);
    this.el.style.setProperty("z-index", String(p.zIndex));
  }

  private positionClass(): string {
    const map: Record<string, string> = {
      "bottom-right": "zephyr-pos-br",
      "bottom-left": "zephyr-pos-bl",
      "top-right": "zephyr-pos-tr",
      "top-left": "zephyr-pos-tl",
    };
    return map[this.config.panel.position] || "zephyr-pos-br";
  }

  private updateAvatars(): void {
    if (!this.el) return;
    const content = `<img src="${this.escapeAttr(this.logo.trigger)}" alt="${this.escapeAttr(this.logo.alt)}" />`;
    const headerContent = `<img src="${this.escapeAttr(this.logo.header)}" alt="${this.escapeAttr(this.logo.alt)}" />`;

    const triggerAv = this.el.querySelector(".zephyr-trigger-avatar");
    const headerAv = this.el.querySelector(".zephyr-header-avatar");
    if (triggerAv) triggerAv.innerHTML = content;
    if (headerAv) headerAv.innerHTML = headerContent;
  }

  private updateChatAvatar(): void {
    // Persona affects the header avatar in the chat
    const headerAv = this.el?.querySelector(".zephyr-header-avatar");
    if (!headerAv) return;
    if (this.persona.renderType === "svg-inline") {
      headerAv.innerHTML = this.persona.avatar;
    } else {
      headerAv.innerHTML = `<img src="${this.escapeAttr(this.persona.avatar)}" alt="${this.escapeAttr(this.persona.name)}" />`;
    }
  }

  // ─── Private: WebSocket ───────────────────────────────────

  private connectWS(): void {
    this.wsClient = new ZephyrWSClient({
      server: this.config.server,
      apiKey: this.config.apiKey,
      onMessage: (msg) => this.handleWSMessage(msg),
      onError: (err) => {
        this.events.onError?.({ message: err instanceof Error ? err.message : "WebSocket error" });
      },
    });
    this.wsClient.connect();
  }

  private handleWSMessage(msg: ZephyrWSMessage): void {
    switch (msg.type) {
      case "welcome":
        this.addMessage("bot", this.config.greeting || msg.message || "Bonjour !", msg.expression);
        break;
      case "status":
        this.showTyping();
        break;
      case "response":
        this.hideTyping();
        this.addMessage("bot", msg.message || "", msg.expression);
        if (msg.suggestions?.length) this.showSuggestions(msg.suggestions);
        break;
      case "error":
        this.hideTyping();
        this.addMessage("system", msg.message || "Erreur", "surprised");
        this.events.onError?.({ message: msg.message || "Error" });
        break;
    }
  }

  // ─── Private: Utilities ───────────────────────────────────

  private renderMarkdown(text: string): string {
    if (!text) return "";
    let html = this.escapeHTML(text);
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/^[-•] (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  private escapeHTML(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  private escapeAttr(text: string): string {
    return text.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
}
