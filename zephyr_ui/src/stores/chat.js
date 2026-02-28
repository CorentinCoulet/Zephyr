import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useChatStore = defineStore("chat", () => {
  // State
  const messages = ref([]);
  const isLoading = ref(false);
  const sessionId = ref(null);
  const currentUrl = ref("");
  const mode = ref("auto"); // "auto" | "dev" | "user"
  const expression = ref("neutral");
  const suggestions = ref([]);
  const ws = ref(null);
  const connected = ref(false);

  // Getters
  const messageCount = computed(() => messages.value.length);
  const lastMessage = computed(() => messages.value[messages.value.length - 1]);

  // Actions
  function connectWebSocket() {
    const sid = sessionId.value || "";
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/chat?session_id=${sid}`;

    ws.value = new WebSocket(url);

    ws.value.onopen = () => {
      connected.value = true;
    };

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "welcome") {
        sessionId.value = data.session_id;
        expression.value = data.expression || "happy";
        addMessage("assistant", data.message, data.expression);
      } else if (data.type === "status") {
        expression.value = data.expression || "thinking";
        isLoading.value = true;
      } else if (data.type === "response") {
        isLoading.value = false;
        expression.value = data.expression || "neutral";
        mode.value = data.mode || mode.value;
        suggestions.value = data.suggestions || [];
        addMessage("assistant", data.message, data.expression);
      } else if (data.type === "error") {
        isLoading.value = false;
        expression.value = "surprised";
        addMessage("system", data.message, "surprised");
      }
    };

    ws.value.onclose = () => {
      connected.value = false;
      // Auto-reconnect after 3s
      setTimeout(() => {
        if (!connected.value) connectWebSocket();
      }, 3000);
    };

    ws.value.onerror = () => {
      connected.value = false;
    };
  }

  function sendMessage(text) {
    if (!text.trim() || !ws.value || ws.value.readyState !== WebSocket.OPEN) return;

    addMessage("user", text);
    isLoading.value = true;

    ws.value.send(
      JSON.stringify({
        message: text,
        url: currentUrl.value,
        mode: mode.value === "auto" ? null : mode.value,
      })
    );
  }

  function addMessage(role, content, expr = null) {
    messages.value.push({
      id: Date.now() + Math.random(),
      role,
      content,
      expression: expr,
      timestamp: new Date().toISOString(),
    });
  }

  function setUrl(url) {
    currentUrl.value = url;
  }

  function setMode(m) {
    mode.value = m;
  }

  function clearChat() {
    messages.value = [];
    suggestions.value = [];
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
  }

  return {
    messages,
    isLoading,
    sessionId,
    currentUrl,
    mode,
    expression,
    suggestions,
    connected,
    messageCount,
    lastMessage,
    connectWebSocket,
    sendMessage,
    setUrl,
    setMode,
    clearChat,
    disconnect,
  };
});
