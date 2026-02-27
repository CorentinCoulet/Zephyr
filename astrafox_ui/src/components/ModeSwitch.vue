<template>
  <div class="flex items-center gap-1 bg-astrafox-bg rounded-lg p-1 border border-astrafox-border">
    <button
      v-for="m in modes"
      :key="m.value"
      @click="chatStore.setMode(m.value)"
      class="px-3 py-1 text-xs rounded-md transition-all font-medium"
      :class="
        chatStore.mode === m.value
          ? 'bg-astrafox-primary text-white'
          : 'text-astrafox-muted hover:text-astrafox-text'
      "
    >
      {{ m.icon }} {{ m.label }}
    </button>
  </div>
</template>

<script setup>
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();

const modes = [
  { value: "auto", label: "Auto", icon: "🔀" },
  { value: "dev", label: "Dev", icon: "🔧" },
  { value: "user", label: "User", icon: "👤" },
];
</script>
