/**
 * 🦊 Zephyr — Vanilla JS API
 *
 * Usage:
 *   <script src="https://cdn.example.com/zephyr.umd.js"></script>
 *   <script>
 *     Zephyr.init({
 *       server: 'http://localhost:8000',
 *       persona: 'friendly',
 *       theme: 'dark',
 *     });
 *   </script>
 */

import type { ZephyrConfig } from "../core/config";
import { ZephyrWidget, type ZephyrWidgetEvents } from "../core/widget";

let instance: ZephyrWidget | null = null;

/**
 * Initialize the Zephyr widget (vanilla JS).
 * Call once. Returns the widget instance for imperative control.
 */
export function init(
  config: ZephyrConfig & ZephyrWidgetEvents
): ZephyrWidget {
  if (instance) {
    instance.destroy();
  }

  const { onReady, onMessage, onError, onToggle, ...widgetConfig } = config;

  instance = new ZephyrWidget(widgetConfig, {
    onReady,
    onMessage,
    onError,
    onToggle,
  });

  instance.mount(config.container || null);
  return instance;
}

/** Get the current widget instance */
export function getInstance(): ZephyrWidget | null {
  return instance;
}

/** Destroy the widget */
export function destroy(): void {
  instance?.destroy();
  instance = null;
}
