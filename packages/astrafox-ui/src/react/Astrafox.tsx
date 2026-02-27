/**
 * 🦊 <Astrafox /> — React Component
 *
 * Usage:
 *   import { Astrafox } from '@astrafox/ui/react';
 *   // or: import { Astrafox } from '@astrafox/ui';
 *
 *   // Option A: Props-based (all config via props)
 *   <Astrafox server="http://localhost:8000" persona="friendly" theme="dark" />
 *
 *   // Option B: Config-file based (uses astrafox.config.ts)
 *   import config from './astrafox.config';
 *   <Astrafox config={config} />
 *
 *   // Option C: Provider pattern (config shared across app)
 *   import { AstrafoxProvider } from '@astrafox/ui/react';
 *   <AstrafoxProvider config={config}><App /></AstrafoxProvider>
 *   // Then anywhere: <Astrafox />
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
  AstrafoxConfig,
  AstrafoxTheme,
  AstrafoxLogo,
  AstrafoxPersona,
  AstrafoxOpenAnimation,
  AstrafoxTriggerAnimation,
  AstrafoxPosition,
  AstrafoxSize,
  AstrafoxFeature,
} from "../core/config";
import { AstrafoxWidget, type AstrafoxMessage } from "../core/widget";

// ─── Props ───────────────────────────────────────────────────

export interface AstrafoxProps {
  // ── Config object (takes precedence over individual props) ──
  /** Full config object (from defineAstrafoxConfig) */
  config?: AstrafoxConfig;

  // ── Individual props (override config) ─────────────────────
  /** Astrafox server URL */
  server?: string;
  /** API key */
  apiKey?: string;
  /** Logo preset or custom */
  logo?: AstrafoxLogo;
  /** Persona preset or custom */
  persona?: AstrafoxPersona;
  /** Theme */
  theme?: AstrafoxTheme;
  /** Accent color */
  accentColor?: string;
  /** Opening animation */
  openAnimation?: AstrafoxOpenAnimation;
  /** Trigger button animation */
  triggerAnimation?: AstrafoxTriggerAnimation;
  /** Position */
  position?: AstrafoxPosition;
  /** Size */
  size?: AstrafoxSize;
  /** Language */
  language?: string;
  /** Greeting message */
  greeting?: string;
  /** Input placeholder */
  placeholder?: string;
  /** Enabled features */
  features?: AstrafoxFeature[];
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
  onMessage?: (msg: AstrafoxMessage) => void;
  onError?: (err: { message: string }) => void;
  onToggle?: (open: boolean) => void;
}

// ─── Context ─────────────────────────────────────────────────

interface AstrafoxContextValue {
  config: AstrafoxConfig | null;
  widget: AstrafoxWidget | null;
}

const AstrafoxContext = createContext<AstrafoxContextValue>({
  config: null,
  widget: null,
});

// ─── Provider ────────────────────────────────────────────────

export interface AstrafoxProviderProps {
  config: AstrafoxConfig;
  children: ReactNode;
}

export function AstrafoxProvider({ config, children }: AstrafoxProviderProps) {
  const widgetRef = useRef<AstrafoxWidget | null>(null);

  return (
    <AstrafoxContext.Provider value={{ config, widget: widgetRef.current }}>
      {children}
    </AstrafoxContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────

export interface UseAstrafoxReturn {
  /** Send a message */
  send: (text: string) => void;
  /** Open the panel */
  open: () => void;
  /** Close the panel */
  close: () => void;
  /** Toggle the panel */
  toggle: () => void;
  /** Change theme */
  setTheme: (theme: AstrafoxTheme) => void;
  /** Change logo */
  setLogo: (logo: AstrafoxLogo) => void;
  /** Change persona */
  setPersona: (persona: AstrafoxPersona) => void;
  /** Change accent color */
  setAccentColor: (color: string) => void;
  /** Get all messages */
  getMessages: () => AstrafoxMessage[];
  /** Is the panel open? */
  isOpen: () => boolean;
}

/**
 * Imperative access to the Astrafox widget instance.
 * Must be used in a component that renders <Astrafox />.
 */
export function useAstrafox(): UseAstrafoxReturn {
  const widgetRef = useRef<AstrafoxWidget | null>(null);

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
 * <Astrafox /> — Renders the Astrafox chat widget.
 *
 * @example
 * ```tsx
 * import { Astrafox } from '@astrafox/ui/react';
 *
 * function App() {
 *   return (
 *     <div>
 *       <h1>My App</h1>
 *       <Astrafox
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
export function Astrafox(props: AstrafoxProps) {
  const context = useContext(AstrafoxContext);
  const widgetRef = useRef<AstrafoxWidget | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Merge: context config < config prop < individual props
  const resolvedConfig = buildConfig(context.config, props);

  // Mount effect
  useEffect(() => {
    if (!resolvedConfig.server) {
      console.warn("[Astrafox] No server URL. Provide server prop or config.");
      return;
    }

    const widget = new AstrafoxWidget(resolvedConfig, {
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
  contextConfig: AstrafoxConfig | null,
  props: AstrafoxProps
): AstrafoxConfig {
  const base: AstrafoxConfig = {
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
