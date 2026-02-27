<!--
  🦊 Astrafox — Vue 3 Component

  Usage:
    import { Astrafox } from '@astrafox/ui/vue';
    import config from './astrafox.config';

    // Then in template:
    //   Astrafox server="http://localhost:8000" persona="friendly" theme="dark"
    //   Astrafox :config="config"
-->

<template>
  <!-- Widget renders itself to the DOM — this is just a lifecycle wrapper -->
  <slot />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, type PropType } from "vue";
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

const props = defineProps({
  /** Full config object (from defineAstrafoxConfig) */
  config: { type: Object as PropType<AstrafoxConfig>, default: null },

  /** Astrafox server URL */
  server: { type: String, default: "" },
  /** API key */
  apiKey: { type: String, default: "" },
  /** Logo preset or custom URL */
  logo: { type: [String, Object] as PropType<AstrafoxLogo>, default: undefined },
  /** Persona preset or custom */
  persona: { type: [String, Object] as PropType<AstrafoxPersona>, default: undefined },
  /** Theme (dark/light/auto or custom object) */
  theme: { type: [String, Object] as PropType<AstrafoxTheme>, default: undefined },
  /** Accent color */
  accentColor: { type: String, default: undefined },
  /** Panel open animation */
  openAnimation: { type: String as PropType<AstrafoxOpenAnimation>, default: undefined },
  /** Trigger button animation */
  triggerAnimation: { type: String as PropType<AstrafoxTriggerAnimation>, default: undefined },
  /** Position */
  position: { type: String as PropType<AstrafoxPosition>, default: undefined },
  /** Size */
  size: { type: String as PropType<AstrafoxSize>, default: undefined },
  /** Language */
  language: { type: String, default: undefined },
  /** Greeting */
  greeting: { type: String, default: undefined },
  /** Input placeholder */
  placeholder: { type: String, default: undefined },
  /** Enabled features */
  features: { type: Array as PropType<AstrafoxFeature[]>, default: undefined },
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
  message: [msg: AstrafoxMessage];
  error: [err: { message: string }];
  toggle: [open: boolean];
}>();

// ─── Widget instance ─────────────────────────────────────────

let widget: AstrafoxWidget | null = null;

function buildConfig(): AstrafoxConfig {
  const base: AstrafoxConfig = {
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
    console.warn("[Astrafox] No server URL. Provide server prop or config.");
    return;
  }

  widget = new AstrafoxWidget(config, {
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
  setTheme: (t: AstrafoxTheme) => widget?.setTheme(t),
  setLogo: (l: AstrafoxLogo) => widget?.setLogo(l),
  setPersona: (p: AstrafoxPersona) => widget?.setPersona(p),
  setAccentColor: (c: string) => widget?.setAccentColor(c),
  getMessages: () => widget?.getMessages() || [],
  isOpen: () => widget?.getIsOpen() || false,
});
</script>
