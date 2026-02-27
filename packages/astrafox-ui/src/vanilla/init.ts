/**
 * 🦊 Astrafox — Vanilla JS API
 *
 * Usage:
 *   <script src="https://cdn.example.com/astrafox.umd.js"></script>
 *   <script>
 *     Astrafox.init({
 *       server: 'http://localhost:8000',
 *       persona: 'friendly',
 *       theme: 'dark',
 *     });
 *   </script>
 */

import type { AstrafoxConfig } from "../core/config";
import { AstrafoxWidget, type AstrafoxWidgetEvents } from "../core/widget";

let instance: AstrafoxWidget | null = null;

/**
 * Initialize the Astrafox widget (vanilla JS).
 * Call once. Returns the widget instance for imperative control.
 */
export function init(
  config: AstrafoxConfig & AstrafoxWidgetEvents
): AstrafoxWidget {
  if (instance) {
    instance.destroy();
  }

  const { onReady, onMessage, onError, onToggle, ...widgetConfig } = config;

  instance = new AstrafoxWidget(widgetConfig, {
    onReady,
    onMessage,
    onError,
    onToggle,
  });

  instance.mount(config.container || null);
  return instance;
}

/** Get the current widget instance */
export function getInstance(): AstrafoxWidget | null {
  return instance;
}

/** Destroy the widget */
export function destroy(): void {
  instance?.destroy();
  instance = null;
}
