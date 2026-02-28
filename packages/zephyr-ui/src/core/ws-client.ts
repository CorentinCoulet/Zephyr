/**
 * 🔌 Zephyr WebSocket Client
 *
 * Handles connection to the Zephyr backend with auto-reconnect,
 * session management, and typed events.
 */

export interface ZephyrWSMessage {
  type: "welcome" | "status" | "response" | "error";
  session_id?: string;
  message?: string;
  expression?: string;
  suggestions?: string[];
  mode?: string;
  data?: Record<string, unknown>;
}

export interface ZephyrWSOptions {
  server: string;
  apiKey?: string;
  sessionId?: string;
  onMessage: (msg: ZephyrWSMessage) => void;
  onError?: (err: Event | Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

export class ZephyrWSClient {
  private ws: WebSocket | null = null;
  private options: Required<ZephyrWSOptions>;
  private sessionId: string = "";
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  constructor(options: ZephyrWSOptions) {
    this.options = {
      reconnectDelay: 3000,
      maxReconnectAttempts: 10,
      onError: () => {},
      onConnect: () => {},
      onDisconnect: () => {},
      apiKey: "",
      sessionId: "",
      ...options,
    };
    if (options.sessionId) this.sessionId = options.sessionId;
  }

  /** Connect to the WebSocket server */
  connect(): void {
    if (this.destroyed) return;
    if (!this.options.server) {
      console.warn("[Zephyr] No server URL configured.");
      return;
    }

    const base = this.options.server.replace(/\/$/, "");
    const protocol = base.startsWith("https") ? "wss:" : "ws:";
    const host = base.replace(/^https?:\/\//, "");
    const params = new URLSearchParams();
    if (this.sessionId) params.set("session_id", this.sessionId);
    if (this.options.apiKey) params.set("api_key", this.options.apiKey);

    const url = `${protocol}//${host}/ws/chat?${params.toString()}`;

    try {
      this.ws = new WebSocket(url);
    } catch (err) {
      this.options.onError(err as Error);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.options.onConnect();
    };

    this.ws.onmessage = (event) => {
      try {
        const data: ZephyrWSMessage = JSON.parse(event.data);
        if (data.session_id) this.sessionId = data.session_id;
        this.options.onMessage(data);
      } catch {
        // Ignore non-JSON messages
      }
    };

    this.ws.onclose = () => {
      this.options.onDisconnect();
      this.scheduleReconnect();
    };

    this.ws.onerror = (e) => {
      this.options.onError(e);
    };
  }

  /** Send a chat message */
  send(message: string, metadata?: Record<string, unknown>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.ws.send(
      JSON.stringify({
        message,
        session_id: this.sessionId,
        ...metadata,
      })
    );
  }

  /** Get current session ID */
  getSessionId(): string {
    return this.sessionId;
  }

  /** Check if connected */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /** Disconnect and cleanup */
  destroy(): void {
    this.destroyed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.close();
      this.ws = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.destroyed) return;
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(
      () => this.connect(),
      this.options.reconnectDelay
    );
  }
}
