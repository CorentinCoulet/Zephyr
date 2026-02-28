/**
 * @zephyr/widget — TypeScript type definitions
 */

export interface ZephyrWidgetOptions {
  /** URL of the Zephyr backend server */
  server: string;
  /** API key for authentication (optional) */
  apiKey?: string;
  /** Persona style: "mascot" | "spirit" | "minimal" | "futuristic" | custom image URL */
  persona?: "mascot" | "spirit" | "minimal" | "futuristic" | string;
  /** Color theme */
  theme?: "dark" | "light" | "auto";
  /** Widget position on screen */
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  /** Avatar size */
  size?: "sm" | "md" | "lg";
  /** Language */
  language?: "fr" | "en";
  /** Custom greeting message */
  greeting?: string | null;
  /** Input placeholder */
  placeholder?: string | null;
  /** Primary accent color (CSS) */
  accentColor?: string;
  /** CSS z-index */
  zIndex?: number;
  /** Allow dragging the trigger button */
  draggable?: boolean;
  /** Start with panel open */
  open?: boolean;
  /** Show notification badge */
  showBadge?: boolean;
  /** Badge count */
  badgeCount?: number;
  /** Enabled features */
  features?: Array<"chat" | "guide" | "search">;
  /** Mount inside a specific selector (inline mode — no floating trigger) */
  containerSelector?: string | null;
  /** Additional CSS to inject */
  customCSS?: string;

  // Callbacks
  onReady?: (widget: ZephyrWidgetInstance) => void;
  onMessage?: (msg: { role: string; text: string; expression: string }) => void;
  onError?: (err: { message: string }) => void;
  onToggle?: (isOpen: boolean) => void;
}

export interface ZephyrWidgetInstance {
  mount(container?: string | HTMLElement | null): void;
  destroy(): void;
  open(): void;
  close(): void;
  toggle(): void;
  send(text: string): void;
  setTheme(theme: "dark" | "light" | "auto"): void;
  setPersona(persona: string): void;
  setAccentColor(color: string): void;
  on(event: "ready" | "message" | "error" | "toggle", handler: Function): void;
  readonly messages: Array<{ role: string; text: string; expression: string }>;
  readonly isOpen: boolean;
  readonly sessionId: string | null;
  readonly expression: string;
}

export interface ZephyrWidgetStatic {
  init(options: ZephyrWidgetOptions): ZephyrWidgetInstance;
  getInstance(): ZephyrWidgetInstance | null;
  Widget: new (options: ZephyrWidgetOptions) => ZephyrWidgetInstance;
  PERSONAS: Record<string, { svg: (accent: string) => string }>;
  THEMES: Record<string, Record<string, string>>;
}

declare const ZephyrWidget: ZephyrWidgetStatic;
export default ZephyrWidget;
