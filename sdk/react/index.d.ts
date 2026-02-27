import React from "react";

export interface AstrafoxChatProps {
  /** Astrafox backend server URL */
  server: string;
  /** API key */
  apiKey?: string;
  /** Persona: "mascot" | "spirit" | "minimal" | "futuristic" | custom URL */
  persona?: "mascot" | "spirit" | "minimal" | "futuristic" | string;
  /** Theme */
  theme?: "dark" | "light" | "auto";
  /** Position */
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  /** Size */
  size?: "sm" | "md" | "lg";
  /** Language */
  language?: "fr" | "en";
  /** Custom greeting */
  greeting?: string;
  /** Input placeholder */
  placeholder?: string;
  /** Accent color */
  accentColor?: string;
  /** z-index */
  zIndex?: number;
  /** Start open */
  open?: boolean;
  /** Show badge */
  showBadge?: boolean;
  /** Features */
  features?: Array<"chat" | "guide" | "search">;
  /** Inline mode (render inside container) */
  inline?: boolean;
  /** Custom CSS */
  customCSS?: string;
  /** CSS class */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;

  // Callbacks
  onReady?: (widget: any) => void;
  onMessage?: (msg: { role: string; text: string; expression: string }) => void;
  onError?: (err: { message: string }) => void;
  onToggle?: (isOpen: boolean) => void;
}

export declare function AstrafoxChat(props: AstrafoxChatProps): React.ReactElement | null;
export declare function useAstrafox(): {
  send: (text: string) => void;
  open: () => void;
  close: () => void;
};

export default AstrafoxChat;
