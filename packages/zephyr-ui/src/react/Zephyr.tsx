/**
 * 🦊 <Zephyr /> — React Component
 *
 * Usage:
 *   import { Zephyr } from '@zephyr/ui/react';
 *   // or: import { Zephyr } from '@zephyr/ui';
 *
 *   // Option A: Props-based (all config via props)
 *   <Zephyr server="http://localhost:8000" persona="friendly" theme="dark" />
 *
 *   // Option B: Config-file based (uses zephyr.config.ts)
 *   import config from './zephyr.config';
 *   <Zephyr config={config} />
 *
 *   // Option C: Provider pattern (config shared across app)
 *   import { ZephyrProvider } from '@zephyr/ui/react';
 *   <ZephyrProvider config={config}><App /></ZephyrProvider>
 *   // Then anywhere: <Zephyr />
 */

import React, {
  useEffect,
  useRef,
  useCallback,
  createContext,
  useContext,
  type ReactNode,
} from "react";

import type {
  ZephyrConfig,
  ZephyrTheme,
  ZephyrLogo,
  ZephyrPersona,
  ZephyrOpenAnimation,
  ZephyrTriggerAnimation,
  ZephyrPosition,
  ZephyrSize,
  ZephyrFeature,
} from "../core/config";
import { ZephyrWidget, type ZephyrMessage } from "../core/widget";

// ─── Props ───────────────────────────────────────────────────

export interface ZephyrProps {
  // ── Config object (takes precedence over individual props) ──
  /** Full config object (from defineZephyrConfig) */
  config?: ZephyrConfig;

  // ── Individual props (override config) ─────────────────────
  /** Zephyr server URL */
  server?: string;
  /** API key */
  apiKey?: string;
  /** Logo preset or custom */
  logo?: ZephyrLogo;
  /** Persona preset or custom */
  persona?: ZephyrPersona;
  /** Theme */
  theme?: ZephyrTheme;
  /** Accent color */
  accentColor?: string;
  /** Opening animation */
  openAnimation?: ZephyrOpenAnimation;
  /** Trigger button animation */
  triggerAnimation?: ZephyrTriggerAnimation;
  /** Position */
  position?: ZephyrPosition;
  /** Size */
  size?: ZephyrSize;
  /** Language */
  language?: string;
  /** Greeting message */
  greeting?: string;
  /** Input placeholder */
  placeholder?: string;
  /** Enabled features */
  features?: ZephyrFeature[];
  /** Start open */
  startOpen?: boolean;
  /** Show badge */
  showBadge?: boolean;
  /** Custom CSS */
  customCSS?: string;
  /** Mount container selector */
  container?: string | null;
  /** Panel width */
  panelWidth?: number;
  /** Panel height */
  panelHeight?: number;
  /** Panel border radius */
  panelBorderRadius?: number;
  /** Show backdrop */
  backdrop?: boolean;
  /** z-index */
  zIndex?: number;

  // ── Events ─────────────────────────────────────────────────
  onReady?: () => void;
  onMessage?: (msg: ZephyrMessage) => void;
  onError?: (err: { message: string }) => void;
  onToggle?: (open: boolean) => void;
}

// ─── Context ─────────────────────────────────────────────────

interface ZephyrContextValue {
  config: ZephyrConfig | null;
  widget: ZephyrWidget | null;
}

const ZephyrContext = createContext<ZephyrContextValue>({
  config: null,
  widget: null,
});

// ─── Provider ────────────────────────────────────────────────

export interface ZephyrProviderProps {
  config: ZephyrConfig;
  children: ReactNode;
}

export function ZephyrProvider({ config, children }: ZephyrProviderProps) {
  const widgetRef = useRef<ZephyrWidget | null>(null);

  return (
    <ZephyrContext.Provider value={{ config, widget: widgetRef.current }}>
      {children}
    </ZephyrContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────

export interface UseZephyrReturn {
  /** Send a message */
  send: (text: string) => void;
  /** Open the panel */
  open: () => void;
  /** Close the panel */
  close: () => void;
  /** Toggle the panel */
  toggle: () => void;
  /** Change theme */
  setTheme: (theme: ZephyrTheme) => void;
  /** Change logo */
  setLogo: (logo: ZephyrLogo) => void;
  /** Change persona */
  setPersona: (persona: ZephyrPersona) => void;
  /** Change accent color */
  setAccentColor: (color: string) => void;
  /** Get all messages */
  getMessages: () => ZephyrMessage[];
  /** Is the panel open? */
  isOpen: () => boolean;
}

/**
 * Imperative access to the Zephyr widget instance.
 * Must be used in a component that renders <Zephyr />.
 */
export function useZephyr(): UseZephyrReturn {
  const widgetRef = useRef<ZephyrWidget | null>(null);

  return {
    send: (text) => widgetRef.current?.send(text),
    open: () => widgetRef.current?.open(),
    close: () => widgetRef.current?.close(),
    toggle: () => widgetRef.current?.toggle(),
    setTheme: (t) => widgetRef.current?.setTheme(t),
    setLogo: (l) => widgetRef.current?.setLogo(l),
    setPersona: (p) => widgetRef.current?.setPersona(p),
    setAccentColor: (c) => widgetRef.current?.setAccentColor(c),
    getMessages: () => widgetRef.current?.getMessages() || [],
    isOpen: () => widgetRef.current?.getIsOpen() || false,
  };
}

// ─── Component ───────────────────────────────────────────────

/**
 * <Zephyr /> — Renders the Zephyr chat widget.
 *
 * @example
 * ```tsx
 * import { Zephyr } from '@zephyr/ui/react';
 *
 * function App() {
 *   return (
 *     <div>
 *       <h1>My App</h1>
 *       <Zephyr
 *         server="http://localhost:8000"
 *         persona="friendly"
 *         theme="dark"
 *         accentColor="#ff6b35"
 *         openAnimation="bounce"
 *       />
 *     </div>
 *   );
 * }
 * ```
 */
export function Zephyr(props: ZephyrProps) {
  const context = useContext(ZephyrContext);
  const widgetRef = useRef<ZephyrWidget | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Merge: context config < config prop < individual props
  const resolvedConfig = buildConfig(context.config, props);

  // Mount effect
  useEffect(() => {
    if (!resolvedConfig.server) {
      console.warn("[Zephyr] No server URL. Provide server prop or config.");
      return;
    }

    const widget = new ZephyrWidget(resolvedConfig, {
      onReady: props.onReady,
      onMessage: props.onMessage,
      onError: props.onError,
      onToggle: props.onToggle,
    });

    widget.mount(props.container || null);
    widgetRef.current = widget;

    return () => {
      widget.destroy();
      widgetRef.current = null;
    };
    // Intentionally only depend on server — other changes are handled by watchers below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedConfig.server]);

  // Watch runtime changes
  useEffect(() => {
    widgetRef.current?.setTheme(resolvedConfig.theme);
  }, [resolvedConfig.theme]);

  useEffect(() => {
    widgetRef.current?.setAccentColor(resolvedConfig.accentColor || "#ff6b35");
  }, [resolvedConfig.accentColor]);

  useEffect(() => {
    if (resolvedConfig.persona) {
      widgetRef.current?.setPersona(resolvedConfig.persona);
    }
  }, [resolvedConfig.persona]);

  useEffect(() => {
    if (resolvedConfig.logo) {
      widgetRef.current?.setLogo(resolvedConfig.logo);
    }
  }, [resolvedConfig.logo]);

  useEffect(() => {
    if (resolvedConfig.openAnimation) {
      widgetRef.current?.setOpenAnimation(resolvedConfig.openAnimation);
    }
  }, [resolvedConfig.openAnimation]);

  useEffect(() => {
    if (resolvedConfig.triggerAnimation) {
      widgetRef.current?.setTriggerAnimation(resolvedConfig.triggerAnimation);
    }
  }, [resolvedConfig.triggerAnimation]);

  // The widget renders itself to the DOM — this component is just a lifecycle manager
  return null;
}

// ─── Utility ─────────────────────────────────────────────────

function buildConfig(
  contextConfig: ZephyrConfig | null,
  props: ZephyrProps
): ZephyrConfig {
  const base: ZephyrConfig = {
    ...(contextConfig || {}),
    ...(props.config || {}),
    server: props.server || props.config?.server || contextConfig?.server || "",
  };

  // Override with individual props
  if (props.apiKey !== undefined) base.apiKey = props.apiKey;
  if (props.logo !== undefined) base.logo = props.logo;
  if (props.persona !== undefined) base.persona = props.persona;
  if (props.theme !== undefined) base.theme = props.theme;
  if (props.accentColor !== undefined) base.accentColor = props.accentColor;
  if (props.openAnimation !== undefined) base.openAnimation = props.openAnimation;
  if (props.triggerAnimation !== undefined) base.triggerAnimation = props.triggerAnimation;
  if (props.language !== undefined) base.language = props.language;
  if (props.greeting !== undefined) base.greeting = props.greeting;
  if (props.placeholder !== undefined) base.placeholder = props.placeholder;
  if (props.features !== undefined) base.features = props.features;
  if (props.startOpen !== undefined) base.startOpen = props.startOpen;
  if (props.showBadge !== undefined) base.showBadge = props.showBadge;
  if (props.customCSS !== undefined) base.customCSS = props.customCSS;
  if (props.container !== undefined) base.container = props.container;

  // Panel overrides
  if (props.position || props.size || props.panelWidth || props.panelHeight ||
      props.panelBorderRadius || props.backdrop !== undefined || props.zIndex) {
    base.panel = {
      ...base.panel,
      ...(props.position && { position: props.position }),
      ...(props.size && { size: props.size }),
      ...(props.panelWidth && { width: props.panelWidth }),
      ...(props.panelHeight && { height: props.panelHeight }),
      ...(props.panelBorderRadius != null && { borderRadius: props.panelBorderRadius }),
      ...(props.backdrop !== undefined && { backdrop: props.backdrop }),
      ...(props.zIndex && { zIndex: props.zIndex }),
    };
  }

  return base;
}
