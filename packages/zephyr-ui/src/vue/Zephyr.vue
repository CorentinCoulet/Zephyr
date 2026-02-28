<!--
  🦊 Zephyr — Vue 3 Component

  Usage:
    import { Zephyr } from '@zephyr/ui/vue';
    import config from './zephyr.config';

    // Then in template:
    //   Zephyr server="http://localhost:8000" persona="friendly" theme="dark"
    //   Zephyr :config="config"
-->

<template>
  <!-- Widget renders itself to the DOM — this is just a lifecycle wrapper -->
  <slot />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, type PropType } from "vue";
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

const props = defineProps({
  /** Full config object (from defineZephyrConfig) */
  config: { type: Object as PropType<ZephyrConfig>, default: null },

  /** Zephyr server URL */
  server: { type: String, default: "" },
  /** API key */
  apiKey: { type: String, default: "" },
  /** Logo preset or custom URL */
  logo: { type: [String, Object] as PropType<ZephyrLogo>, default: undefined },
  /** Persona preset or custom */
  persona: { type: [String, Object] as PropType<ZephyrPersona>, default: undefined },
  /** Theme (dark/light/auto or custom object) */
  theme: { type: [String, Object] as PropType<ZephyrTheme>, default: undefined },
  /** Accent color */
  accentColor: { type: String, default: undefined },
  /** Panel open animation */
  openAnimation: { type: String as PropType<ZephyrOpenAnimation>, default: undefined },
  /** Trigger button animation */
  triggerAnimation: { type: String as PropType<ZephyrTriggerAnimation>, default: undefined },
  /** Position */
  position: { type: String as PropType<ZephyrPosition>, default: undefined },
  /** Size */
  size: { type: String as PropType<ZephyrSize>, default: undefined },
  /** Language */
  language: { type: String, default: undefined },
  /** Greeting */
  greeting: { type: String, default: undefined },
  /** Input placeholder */
  placeholder: { type: String, default: undefined },
  /** Enabled features */
  features: { type: Array as PropType<ZephyrFeature[]>, default: undefined },
  /** Start open */
  startOpen: { type: Boolean, default: undefined },
  /** Show badge */
  showBadge: { type: Boolean, default: undefined },
  /** Custom CSS */
  customCSS: { type: String, default: undefined },
  /** Container selector */
  container: { type: String as PropType<string | null>, default: undefined },
  /** Panel width */
  panelWidth: { type: Number, default: undefined },
  /** Panel height */
  panelHeight: { type: Number, default: undefined },
  /** Border radius */
  panelBorderRadius: { type: Number, default: undefined },
  /** Backdrop */
  backdrop: { type: Boolean, default: undefined },
  /** z-index */
  zIndex: { type: Number, default: undefined },
});

// ─── Emits ───────────────────────────────────────────────────

const emit = defineEmits<{
  ready: [];
  message: [msg: ZephyrMessage];
  error: [err: { message: string }];
  toggle: [open: boolean];
}>();

// ─── Widget instance ─────────────────────────────────────────

let widget: ZephyrWidget | null = null;

function buildConfig(): ZephyrConfig {
  const base: ZephyrConfig = {
    ...(props.config || {}),
    server: props.server || props.config?.server || "",
  };

  if (props.apiKey) base.apiKey = props.apiKey;
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

  if (props.position || props.size || props.panelWidth || props.panelHeight ||
      props.panelBorderRadius != null || props.backdrop !== undefined || props.zIndex) {
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

onMounted(() => {
  const config = buildConfig();
  if (!config.server) {
    console.warn("[Zephyr] No server URL. Provide server prop or config.");
    return;
  }

  widget = new ZephyrWidget(config, {
    onReady: () => emit("ready"),
    onMessage: (msg) => emit("message", msg),
    onError: (err) => emit("error", err),
    onToggle: (open) => emit("toggle", open),
  });
  widget.mount(props.container || null);
});

onUnmounted(() => {
  widget?.destroy();
  widget = null;
});

// ─── Watchers for reactive prop changes ──────────────────────

watch(() => props.theme, (val) => { if (val !== undefined) widget?.setTheme(val); });
watch(() => props.accentColor, (val) => { if (val) widget?.setAccentColor(val); });
watch(() => props.persona, (val) => { if (val !== undefined) widget?.setPersona(val); });
watch(() => props.logo, (val) => { if (val !== undefined) widget?.setLogo(val); });
watch(() => props.openAnimation, (val) => { if (val) widget?.setOpenAnimation(val); });
watch(() => props.triggerAnimation, (val) => { if (val) widget?.setTriggerAnimation(val); });

// ─── Expose imperative API ───────────────────────────────────

defineExpose({
  send: (text: string) => widget?.send(text),
  open: () => widget?.open(),
  close: () => widget?.close(),
  toggle: () => widget?.toggle(),
  setTheme: (t: ZephyrTheme) => widget?.setTheme(t),
  setLogo: (l: ZephyrLogo) => widget?.setLogo(l),
  setPersona: (p: ZephyrPersona) => widget?.setPersona(p),
  setAccentColor: (c: string) => widget?.setAccentColor(c),
  getMessages: () => widget?.getMessages() || [],
  isOpen: () => widget?.getIsOpen() || false,
});
</script>
