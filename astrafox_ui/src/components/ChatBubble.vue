<template>
  <div
    class="chat-bubble"
    :class="[role, { 'opacity-70': role === 'system' }]"
  >
    <!-- Avatar for assistant -->
    <div v-if="role === 'assistant'" class="flex items-start gap-2">
      <AstrafoxAvatar
        :expression="expression || 'neutral'"
        size="sm"
        class="flex-shrink-0 mt-0.5"
      />
      <div class="flex-1 min-w-0">
        <div class="markdown-content" v-html="rendered"></div>
        <span class="text-[10px] text-astrafox-muted mt-1 block">
          {{ formattedTime }}
        </span>
      </div>
    </div>

    <!-- User message -->
    <div v-else-if="role === 'user'">
      <div>{{ content }}</div>
      <span class="text-[10px] opacity-70 mt-1 block text-right">
        {{ formattedTime }}
      </span>
    </div>

    <!-- System message -->
    <div v-else class="text-center text-sm text-astrafox-muted italic">
      {{ content }}
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { marked } from "marked";
import AstrafoxAvatar from "./AstrafoxAvatar.vue";

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: "" },
  expression: { type: String, default: null },
  timestamp: { type: String, default: null },
});

const rendered = computed(() => {
  if (props.role !== "assistant") return props.content;
  try {
    return marked.parse(props.content || "", { breaks: true });
  } catch {
    return props.content;
  }
});

const formattedTime = computed(() => {
  if (!props.timestamp) return "";
  const d = new Date(props.timestamp);
  return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
});
</script>
