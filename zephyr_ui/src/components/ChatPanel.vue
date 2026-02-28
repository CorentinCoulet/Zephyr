<template>
  <div class="flex flex-col h-full">
    <!-- Messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
      <ChatBubble
        v-for="msg in chatStore.messages"
        :key="msg.id"
        :role="msg.role"
        :content="msg.content"
        :expression="msg.expression"
        :timestamp="msg.timestamp"
      />

      <!-- Typing indicator -->
      <div v-if="chatStore.isLoading" class="flex items-center gap-2 animate-fade-in">
        <ZephyrAvatar expression="thinking" size="sm" />
        <div class="flex gap-1.5">
          <span class="w-2 h-2 bg-zephyr-accent rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-2 h-2 bg-zephyr-accent rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-2 h-2 bg-zephyr-accent rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
      </div>
    </div>

    <!-- Suggestions -->
    <div v-if="chatStore.suggestions.length" class="px-4 pb-2 flex flex-wrap gap-2">
      <button
        v-for="(suggestion, i) in chatStore.suggestions"
        :key="i"
        @click="sendSuggestion(suggestion)"
        class="text-xs px-3 py-1.5 rounded-full bg-zephyr-surface border border-zephyr-border
               hover:border-zephyr-accent hover:text-zephyr-accent transition-colors"
      >
        {{ suggestion }}
      </button>
    </div>

    <!-- URL Input -->
    <div class="px-4 pb-2">
      <div class="flex gap-2 items-center">
        <span class="text-xs text-zephyr-muted">URL:</span>
        <input
          v-model="urlInput"
          @keyup.enter="chatStore.setUrl(urlInput)"
          type="url"
          placeholder="https://example.com"
          class="flex-1 text-xs bg-zephyr-bg border border-zephyr-border rounded-lg px-3 py-1.5
                 focus:outline-none focus:border-zephyr-accent transition-colors"
        />
        <button
          @click="chatStore.setUrl(urlInput)"
          class="text-xs px-3 py-1.5 bg-zephyr-border rounded-lg hover:bg-zephyr-accent
                 hover:text-white transition-colors"
        >
          Analyser
        </button>
      </div>
    </div>

    <!-- Input area -->
    <div class="p-4 border-t border-zephyr-border bg-zephyr-surface">
      <div class="flex gap-2">
        <textarea
          ref="inputEl"
          v-model="inputText"
          @keydown="handleKeydown"
          rows="1"
          placeholder="Posez une question à Zephyr..."
          class="flex-1 bg-zephyr-bg border border-zephyr-border rounded-xl px-4 py-2.5
                 resize-none focus:outline-none focus:border-zephyr-accent transition-colors
                 max-h-32"
        ></textarea>
        <button
          @click="send"
          :disabled="!inputText.trim() || chatStore.isLoading"
          class="px-4 py-2 bg-zephyr-primary text-white rounded-xl font-medium
                 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed
                 transition-all"
        >
          ➤
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import { useChatStore } from "../stores/chat";
import ChatBubble from "./ChatBubble.vue";
import ZephyrAvatar from "./ZephyrAvatar.vue";

const chatStore = useChatStore();

const inputText = ref("");
const urlInput = ref("");
const inputEl = ref(null);
const messagesContainer = ref(null);

function send() {
  if (!inputText.value.trim()) return;
  chatStore.sendMessage(inputText.value);
  inputText.value = "";
  nextTick(() => inputEl.value?.focus());
}

function sendSuggestion(text) {
  chatStore.sendMessage(text);
}

function handleKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

// Auto-scroll on new messages
watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      const el = messagesContainer.value;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
);
</script>
