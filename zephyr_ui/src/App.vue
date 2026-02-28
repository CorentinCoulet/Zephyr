<template>
  <div class="min-h-screen bg-zephyr-bg text-zephyr-text flex flex-col">
    <!-- Header -->
    <header
      class="flex items-center justify-between px-4 py-3 bg-zephyr-surface border-b border-zephyr-border"
    >
      <div class="flex items-center gap-3">
        <ZephyrAvatar :expression="chatStore.expression" size="sm" />
        <div>
          <h1 class="text-lg font-semibold text-zephyr-primary">Zephyr</h1>
          <p class="text-xs text-zephyr-muted">UI Intelligence Platform</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <ModeSwitch />
        <button
          @click="themeStore.toggle(); themeStore.save()"
          class="p-2 rounded-lg hover:bg-zephyr-border transition-colors"
          :title="themeStore.isDark ? 'Mode clair' : 'Mode sombre'"
        >
          {{ themeStore.isDark ? "☀️" : "🌙" }}
        </button>
        <router-link
          to="/dashboard"
          class="text-sm text-zephyr-muted hover:text-zephyr-primary transition-colors"
        >
          Dashboard
        </router-link>
      </div>
    </header>

    <!-- Main content -->
    <router-view class="flex-1" />

    <!-- Status bar -->
    <footer
      class="flex items-center justify-between px-4 py-1.5 bg-zephyr-surface border-t border-zephyr-border text-xs text-zephyr-muted"
    >
      <span>
        <span
          :class="chatStore.connected ? 'text-green-400' : 'text-red-400'"
          class="inline-block w-2 h-2 rounded-full mr-1"
          :style="{
            backgroundColor: chatStore.connected ? 'var(--zephyr-success)' : 'var(--zephyr-error)',
          }"
        ></span>
        {{ chatStore.connected ? "Connecté" : "Déconnecté" }}
      </span>
      <span v-if="chatStore.currentUrl" class="truncate max-w-xs">
        {{ chatStore.currentUrl }}
      </span>
      <span>Mode: {{ chatStore.mode }}</span>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import { useChatStore } from "./stores/chat";
import { useThemeStore } from "./stores/theme";
import ZephyrAvatar from "./components/ZephyrAvatar.vue";
import ModeSwitch from "./components/ModeSwitch.vue";

const chatStore = useChatStore();
const themeStore = useThemeStore();

onMounted(() => {
  themeStore.init();
  chatStore.connectWebSocket();
});

onUnmounted(() => {
  chatStore.disconnect();
});
</script>
