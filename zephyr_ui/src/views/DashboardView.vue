<template>
  <div class="p-6 space-y-6 overflow-y-auto">
    <h2 class="text-2xl font-bold text-zephyr-primary">Dashboard</h2>

    <!-- Status cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-zephyr-surface border border-zephyr-border rounded-2xl p-5">
        <p class="text-sm text-zephyr-muted mb-1">Sessions actives</p>
        <p class="text-3xl font-bold">{{ stats.sessions }}</p>
      </div>
      <div class="bg-zephyr-surface border border-zephyr-border rounded-2xl p-5">
        <p class="text-sm text-zephyr-muted mb-1">Messages échangés</p>
        <p class="text-3xl font-bold">{{ stats.messages }}</p>
      </div>
      <div class="bg-zephyr-surface border border-zephyr-border rounded-2xl p-5">
        <p class="text-sm text-zephyr-muted mb-1">Statut</p>
        <p class="text-3xl font-bold" :class="stats.online ? 'text-green-400' : 'text-red-400'">
          {{ stats.online ? "En ligne" : "Hors ligne" }}
        </p>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="bg-zephyr-surface border border-zephyr-border rounded-2xl p-5">
      <h3 class="text-lg font-semibold mb-4">Actions rapides</h3>
      <div class="flex flex-wrap gap-3">
        <button
          @click="quickAnalyze"
          class="px-4 py-2 bg-zephyr-primary text-white rounded-xl hover:opacity-90 transition-opacity"
        >
          🔍 Analyse rapide
        </button>
        <button
          @click="quickDebug"
          class="px-4 py-2 bg-zephyr-secondary text-white rounded-xl hover:opacity-90 transition-opacity"
        >
          🐛 Debug
        </button>
        <button
          @click="quickScreenshot"
          class="px-4 py-2 bg-zephyr-accent text-white rounded-xl hover:opacity-90 transition-opacity"
        >
          📸 Captures
        </button>
      </div>
    </div>

    <!-- Recent sessions -->
    <div class="bg-zephyr-surface border border-zephyr-border rounded-2xl p-5">
      <h3 class="text-lg font-semibold mb-4">Sessions récentes</h3>
      <div v-if="sessions.length === 0" class="text-zephyr-muted text-sm">
        Aucune session active.
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          class="flex items-center justify-between p-3 rounded-xl bg-zephyr-bg border border-zephyr-border"
        >
          <div>
            <span class="text-sm font-medium">{{ s.session_id.slice(0, 8) }}...</span>
            <span class="text-xs text-zephyr-muted ml-2">{{ s.mode }}</span>
          </div>
          <span class="text-xs text-zephyr-muted">{{ s.message_count }} msg</span>
        </div>
      </div>
    </div>

    <router-link to="/" class="inline-block text-zephyr-primary hover:underline text-sm">
      ← Retour au chat
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();

const stats = ref({ sessions: 0, messages: 0, online: false });
const sessions = ref([]);

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    stats.value.online = data.status === "running";
    stats.value.sessions = data.active_sessions || 0;
    stats.value.messages = chatStore.messageCount;
  } catch {
    stats.value.online = false;
  }
}

async function fetchSessions() {
  try {
    const res = await fetch("/api/sessions");
    const data = await res.json();
    sessions.value = data.sessions || [];
  } catch {
    sessions.value = [];
  }
}

function quickAnalyze() {
  const url = prompt("URL à analyser:");
  if (url) {
    chatStore.setUrl(url);
    chatStore.sendMessage(`/analyze ${url}`);
  }
}

function quickDebug() {
  const url = prompt("URL à debugger:");
  if (url) {
    chatStore.setUrl(url);
    chatStore.sendMessage(`/debug ${url}`);
  }
}

function quickScreenshot() {
  const url = prompt("URL à capturer:");
  if (url) {
    chatStore.setUrl(url);
    chatStore.sendMessage(`/screenshot ${url}`);
  }
}

onMounted(() => {
  fetchStatus();
  fetchSessions();
});
</script>
