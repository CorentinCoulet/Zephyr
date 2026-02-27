/**
 * 🦊 @kitsune/widget/react — React component wrapper
 *
 * Usage:
 *   import { KitsuneChat } from '@kitsune/widget/react';
 *
 *   function App() {
 *     return (
 *       <KitsuneChat
 *         server="https://your-kitsune-server"
 *         persona="minimal"
 *         theme="dark"
 *         position="bottom-right"
 *         accentColor="#ff6b35"
 *         onMessage={(msg) => console.log(msg)}
 *       />
 *     );
 *   }
 */

import React, { useEffect, useRef, useCallback } from "react";

// Widget is loaded as an IIFE — import the core
let WidgetModule = null;
try {
  WidgetModule = require("../kitsune-widget.js");
} catch {
  // Dynamic import fallback handled in useEffect
}

/**
 * Configuration props — matches KitsuneWidgetOptions
 */
const defaultProps = {
  server: "",
  persona: "minimal",
  theme: "dark",
  position: "bottom-right",
  size: "md",
  language: "fr",
  accentColor: "#ff6b35",
  zIndex: 99999,
  open: false,
};

export function KitsuneChat(props) {
  const containerRef = useRef(null);
  const instanceRef = useRef(null);

  const {
    server,
    apiKey,
    persona,
    theme,
    position,
    size,
    language,
    greeting,
    placeholder,
    accentColor,
    zIndex,
    draggable,
    open,
    showBadge,
    features,
    customCSS,
    inline,
    onReady,
    onMessage,
    onError,
    onToggle,
    className,
    style,
    ...rest
  } = { ...defaultProps, ...props };

  useEffect(() => {
    let widget = null;

    const init = async () => {
      let Mod = WidgetModule;
      if (!Mod) {
        // Fallback: load from CDN or relative path
        try {
          Mod = await import("../kitsune-widget.js");
        } catch {
          console.error("[KitsuneChat] Could not load kitsune-widget.js");
          return;
        }
      }

      const Cls = Mod.Widget || Mod.default?.Widget;
      if (!Cls) return;

      widget = new Cls({
        server,
        apiKey,
        persona,
        theme,
        position,
        size,
        language,
        greeting,
        placeholder,
        accentColor,
        zIndex,
        draggable,
        open,
        showBadge,
        features,
        customCSS,
        containerSelector: inline ? null : null,
        onReady,
        onMessage,
        onError,
        onToggle,
      });

      if (inline && containerRef.current) {
        widget.mount(containerRef.current);
      } else {
        widget.mount();
      }

      instanceRef.current = widget;
    };

    init();

    return () => {
      if (widget) widget.destroy();
    };
  }, [server]); // Re-init only on server change

  // React to prop changes
  useEffect(() => {
    if (!instanceRef.current) return;
    instanceRef.current.setTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (!instanceRef.current) return;
    instanceRef.current.setPersona(persona);
  }, [persona]);

  useEffect(() => {
    if (!instanceRef.current) return;
    instanceRef.current.setAccentColor(accentColor);
  }, [accentColor]);

  // Inline renders a container div; floating renders nothing
  if (inline) {
    return React.createElement("div", {
      ref: containerRef,
      className: `kitsune-react-container ${className || ""}`,
      style: { width: "100%", height: "100%", ...style },
      ...rest,
    });
  }

  return null;
}

/**
 * Hook for imperative widget control
 */
export function useKitsune() {
  const send = useCallback((text) => {
    const w = typeof KitsuneWidget !== "undefined" ? KitsuneWidget.getInstance() : null;
    if (w) w.send(text);
  }, []);

  const open = useCallback(() => {
    const w = typeof KitsuneWidget !== "undefined" ? KitsuneWidget.getInstance() : null;
    if (w) w.open();
  }, []);

  const close = useCallback(() => {
    const w = typeof KitsuneWidget !== "undefined" ? KitsuneWidget.getInstance() : null;
    if (w) w.close();
  }, []);

  return { send, open, close };
}

export default KitsuneChat;
