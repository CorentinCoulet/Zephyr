<template>
  <div class="zephyr-avatar" :class="`size-${size}`">
    <!-- Glow effect -->
    <div v-if="glow" class="zephyr-glow"></div>

    <!-- Main avatar circle -->
    <div
      class="relative rounded-full flex items-center justify-center overflow-hidden border-2 transition-all duration-300"
      :class="[
        sizeClasses,
        borderColor,
      ]"
      :style="{ backgroundColor: 'var(--zephyr-surface)' }"
    >
      <!-- Fox face SVG -->
      <svg
        :width="svgSize"
        :height="svgSize"
        viewBox="0 0 64 64"
        class="transition-transform duration-300"
        :class="{ 'animate-float': floating }"
      >
        <!-- Ears -->
        <polygon
          points="12,8 22,24 4,24"
          :fill="earColor"
          class="transition-all duration-500"
        />
        <polygon
          points="52,8 42,24 60,24"
          :fill="earColor"
          class="transition-all duration-500"
        />
        <!-- Inner ears -->
        <polygon points="14,14 20,24 8,24" fill="#ffb088" />
        <polygon points="50,14 44,24 56,24" fill="#ffb088" />

        <!-- Face -->
        <ellipse cx="32" cy="36" rx="20" ry="18" :fill="faceColor" />

        <!-- Eyes -->
        <g :class="expressionClass">
          <!-- Left eye -->
          <ellipse
            v-if="expression !== 'wink'"
            cx="24"
            cy="32"
            :rx="eyeRx"
            :ry="eyeRy"
            fill="#1a1a2e"
            class="transition-all duration-300"
          />
          <!-- Right eye -->
          <ellipse
            cx="40"
            cy="32"
            :rx="eyeRx"
            :ry="eyeRy"
            fill="#1a1a2e"
            class="transition-all duration-300"
          />
          <!-- Wink left eye -->
          <line
            v-if="expression === 'wink'"
            x1="20" y1="32" x2="28" y2="32"
            stroke="#1a1a2e"
            stroke-width="2"
            stroke-linecap="round"
          />
          <!-- Happy eyes (curved lines) -->
          <template v-if="expression === 'happy'">
            <path d="M20,32 Q24,28 28,32" fill="none" stroke="#1a1a2e" stroke-width="2" />
            <path d="M36,32 Q40,28 44,32" fill="none" stroke="#1a1a2e" stroke-width="2" />
          </template>
        </g>

        <!-- Sparkle (surprised) -->
        <template v-if="expression === 'surprised'">
          <circle cx="24" cy="30" r="0.8" fill="white" />
          <circle cx="40" cy="30" r="0.8" fill="white" />
        </template>

        <!-- Nose -->
        <ellipse cx="32" cy="38" rx="2.5" ry="1.8" fill="#1a1a2e" />

        <!-- Mouth -->
        <path :d="mouthPath" fill="none" stroke="#1a1a2e" stroke-width="1.5" stroke-linecap="round" />

        <!-- Whiskers -->
        <g opacity="0.4" stroke="#1a1a2e" stroke-width="0.8">
          <line x1="6" y1="34" x2="18" y2="36" />
          <line x1="6" y1="38" x2="18" y2="38" />
          <line x1="46" y1="36" x2="58" y2="34" />
          <line x1="46" y1="38" x2="58" y2="38" />
        </g>

        <!-- Thinking dots -->
        <g v-if="expression === 'thinking'" class="animate-pulse">
          <circle cx="24" cy="46" r="1.5" fill="var(--zephyr-accent)" />
          <circle cx="32" cy="46" r="1.5" fill="var(--zephyr-accent)" />
          <circle cx="40" cy="46" r="1.5" fill="var(--zephyr-accent)" />
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  expression: { type: String, default: "neutral" },
  size: { type: String, default: "md" },   // sm, md, lg
  glow: { type: Boolean, default: false },
  floating: { type: Boolean, default: false },
});

const sizeClasses = computed(() => ({
  sm: "w-10 h-10",
  md: "w-16 h-16",
  lg: "w-24 h-24",
}[props.size] || "w-16 h-16"));

const svgSize = computed(() => ({
  sm: 32,
  md: 48,
  lg: 64,
}[props.size] || 48));

const earColor = computed(() => "var(--zephyr-primary)");
const faceColor = computed(() => "#ffe0cc");

const borderColor = computed(() => {
  const map = {
    happy: "border-green-400",
    surprised: "border-red-400",
    thinking: "border-yellow-400",
    helping: "border-blue-400",
    wink: "border-purple-400",
    neutral: "border-zephyr-accent",
    speaking: "border-zephyr-primary",
  };
  return map[props.expression] || "border-zephyr-accent";
});

const expressionClass = computed(() => `expr-${props.expression}`);

const eyeRx = computed(() => {
  if (props.expression === "surprised") return 4;
  if (props.expression === "happy") return 0; // hidden, replaced by arcs
  return 3;
});

const eyeRy = computed(() => {
  if (props.expression === "surprised") return 5;
  if (props.expression === "happy") return 0;
  if (props.expression === "thinking") return 2.5;
  return 3.5;
});

const mouthPath = computed(() => {
  const map = {
    happy: "M26,42 Q32,48 38,42",
    surprised: "M28,43 Q32,47 36,43",
    thinking: "M28,42 L36,42",
    helping: "M26,42 Q32,46 38,42",
    speaking: "M28,41 Q32,46 36,41",
    wink: "M26,42 Q32,47 38,42",
    neutral: "M28,42 Q32,44 36,42",
  };
  return map[props.expression] || map.neutral;
});
</script>
