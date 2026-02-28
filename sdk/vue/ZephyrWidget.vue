<!--
  🦊 @zephyr/widget/vue — Vue 3 component wrapper

  Usage:
    <script setup>
    import ZephyrWidget from '@zephyr/widget/vue';
    </script>

    <template>
      <ZephyrWidget
        server="https://your-zephyr-server"
        persona="minimal"
        theme="dark"
        position="bottom-right"
        accent-color="#ff6b35"
        @message="onMessage"
      />
    </template>

    Or inline:
    <ZephyrWidget server="..." :inline="true" style="height: 500px" />
-->

<template>
  <div v-if="inline" ref="containerEl" class="zephyr-vue-container" :style="containerStyle">
    <!-- Widget mounts here in inline mode -->
  </div>
  <!-- In floating mode, widget is appended to body — no template needed -->
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from "vue";

const props = defineProps({
  /** Zephyr backend server URL (required) */
  server: { type: String, required: true },
  /** API key */
  apiKey: { type: String, default: "" },
  /** Persona: "mascot" | "spirit" | "minimal" | "futuristic" | custom URL */
  persona: { type: String, default: "minimal" },
  /** Theme */
  theme: { type: String, default: "dark" },
  /** Position */
  position: { type: String, default: "bottom-right" },
  /** Size */
  size: { type: String, default: "md" },
  /** Language */
  language: { type: String, default: "fr" },
  /** Custom greeting */
  greeting: { type: String, default: null },
  /** Placeholder */
  placeholder: { type: String, default: null },
  /** Accent color */
  accentColor: { type: String, default: "#ff6b35" },
  /** z-index */
  zIndex: { type: Number, default: 99999 },
  /** Start open */
  open: { type: Boolean, default: false },
  /** Show badge */
  showBadge: { type: Boolean, default: true },
  /** Features */
  features: { type: Array, default: () => ["chat", "guide", "search"] },
  /** Inline mode — renders inside container instead of floating */
  inline: { type: Boolean, default: false },
  /** Custom CSS */
  customCSS: { type: String, default: "" },
});

const emit = defineEmits(["ready", "message", "error", "toggle"]);

const containerEl = ref(null);
let widget = null;
let WidgetClass = null;

const containerStyle = computed(() =>
  props.inline ? { width: "100%", height: "100%" } : {}
);

async function loadWidget() {
  if (WidgetClass) return;
  try {
    const mod = await import("../zephyr-widget.js");
    WidgetClass = mod.Widget || mod.default?.Widget;
  } catch (e) {
    console.error("[ZephyrWidget] Could not load zephyr-widget.js", e);
  }
}

onMounted(async () => {
  await loadWidget();
  if (!WidgetClass) return;

  widget = new WidgetClass({
    server: props.server,
    apiKey: props.apiKey,
    persona: props.persona,
    theme: props.theme,
    position: props.position,
    size: props.size,
    language: props.language,
    greeting: props.greeting,
    placeholder: props.placeholder,
    accentColor: props.accentColor,
    zIndex: props.zIndex,
    open: props.open,
    showBadge: props.showBadge,
    features: props.features,
    customCSS: props.customCSS,
    containerSelector: props.inline ? null : null,
    onReady: (w) => emit("ready", w),
    onMessage: (msg) => emit("message", msg),
    onError: (err) => emit("error", err),
    onToggle: (isOpen) => emit("toggle", isOpen),
  });

  if (props.inline && containerEl.value) {
    widget.mount(containerEl.value);
  } else {
    widget.mount();
  }
});

onUnmounted(() => {
  if (widget) widget.destroy();
});

// Reactivity
watch(() => props.theme, (val) => widget?.setTheme(val));
watch(() => props.persona, (val) => widget?.setPersona(val));
watch(() => props.accentColor, (val) => widget?.setAccentColor(val));

// Expose methods
defineExpose({
  send: (text) => widget?.send(text),
  open: () => widget?.open(),
  close: () => widget?.close(),
  toggle: () => widget?.toggle(),
  getInstance: () => widget,
});
</script>
