# 🦊 @zephyr/ui

Embeddable AI assistant widget for any web project. Import `<Zephyr />` into React, Vue, or vanilla JS — configure everything via a single config file.

## Installation

```bash
npm install @zephyr/ui
```

## Quick Start

### React

```tsx
import { Zephyr } from '@zephyr/ui/react';

function App() {
  return (
    <div>
      <h1>Mon App</h1>
      <Zephyr
        server="http://localhost:8000"
        theme="dark"
        persona="friendly"
        logo="zephyr-default"
        accentColor="#ff6b35"
      />
    </div>
  );
}
```

### Vue 3

```vue
<script setup>
import { Zephyr } from '@zephyr/ui/vue';
</script>

<template>
  <div>
    <h1>Mon App</h1>
    <Zephyr
      server="http://localhost:8000"
      theme="dark"
      persona="friendly"
      logo="zephyr-default"
      accent-color="#ff6b35"
    />
  </div>
</template>
```

### Vanilla JS

```js
import { init } from '@zephyr/ui';

init({
  server: 'http://localhost:8000',
  theme: 'dark',
  persona: 'friendly',
  logo: 'zephyr-default',
  accentColor: '#ff6b35',
});
```

## Configuration File

Create a `zephyr.config.ts` in your project:

```ts
import { defineZephyrConfig } from '@zephyr/ui/config';

export default defineZephyrConfig({
  // Connection
  server: 'http://localhost:8000',
  apiKey: 'your-api-key',

  // Appearance
  logo: 'zephyr-default',    // Built-in or custom URL
  persona: 'friendly',         // Built-in or custom object
  theme: 'dark',               // 'dark' | 'light' | 'auto' | custom
  accentColor: '#ff6b35',

  // Animations
  openAnimation: 'slide-up',   // Panel open animation
  triggerAnimation: 'float',    // Trigger button animation

  // Panel
  panel: {
    position: 'bottom-right',
    size: 'md',
    borderRadius: 16,
    backdrop: false,
    draggable: false,
  },

  // Content
  language: 'fr',
  greeting: 'Bonjour ! Comment puis-je vous aider ? 🦊',
  placeholder: 'Posez une question...',
  features: ['chat', 'guide', 'search'],
});
```

Then use it:

```tsx
import config from './zephyr.config';
import { Zephyr } from '@zephyr/ui/react';

<Zephyr config={config} />
```

## Configuration Reference

### Logo

| Value | Description |
|---|---|
| `'zephyr-default'` | Official Zephyr fox logo |
| `'https://...'` | Custom image URL |
| `{ trigger: '...', header: '...' }` | Separate trigger & header images |

### Persona

| Value | Description |
|---|---|
| `'friendly'` | Warm, approachable (default) |
| `'professional'` | Clean, business-like |
| `'playful'` | Fun, animated |
| `'futuristic'` | Sci-fi, cyber |
| `{ name, avatar, avatarType }` | Custom persona (gif/svg/lottie/image) |

### Theme

| Value | Description |
|---|---|
| `'dark'` | Dark mode (default) |
| `'light'` | Light mode |
| `'auto'` | Follows system preference |
| `{ background, surface, text, ... }` | Full custom theme object |

### Open Animation

`slide-up` · `slide-down` · `slide-left` · `slide-right` · `fade` · `scale` · `bounce` · `none`

### Trigger Animation

`float` · `pulse` · `bounce` · `glow` · `none`

### Panel Position

`bottom-right` · `bottom-left` · `top-right` · `top-left`

### Panel Size

| Size | Width | Height |
|---|---|---|
| `sm` | 320px | 440px |
| `md` | 380px | 520px |
| `lg` | 440px | 600px |

## Runtime API

### React Hook

```tsx
import { useZephyr } from '@zephyr/ui/react';

function MyButton() {
  const { send, toggle, setTheme, setPersona, isOpen } = useZephyr();

  return (
    <button onClick={() => toggle()}>
      {isOpen() ? 'Close' : 'Open'} Zephyr
    </button>
  );
}
```

### Vanilla JS

```js
import { init, getInstance, destroy } from '@zephyr/ui';

const widget = init({ server: '...' });

widget.toggle();
widget.send('Hello!');
widget.setTheme('light');
widget.setAccentColor('#00bcd4');

// Later:
destroy();
```

## Backend Configuration

Create `zephyr.server.yaml` in your project to configure the LLM backend:

```yaml
# Which LLM subscription to use
provider: openai  # github-copilot | claude | openai | ollama

# Provider settings
openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4o

github-copilot:
  token: ${GITHUB_TOKEN}
  model: gpt-4o

claude:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-20250514

ollama:
  base_url: http://localhost:11434
  model: llama3
```

## Dev Mode (MCP)

For developers who want to debug UI with Copilot or Claude Code:

1. Configure `.vscode/mcp.json`:

```json
{
  "servers": {
    "zephyr": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "${workspaceFolder}/ui-intelligence"
    }
  }
}
```

2. Install the MCP server: `pip install mcp[cli]`

3. Reload VS Code and use MCP tools in Copilot Chat:
   - `capture_screenshot` — Visual page inspection
   - `extract_dom` — DOM structure analysis
   - `console_errors` — JavaScript error capture
   - `performance_audit` — Perf metrics
   - `accessibility_check` — A11y audit
   - `visual_diff` — Regression detection
   - `full_analysis` — Complete UI analysis

## Exports Map

| Import | Contents |
|---|---|
| `@zephyr/ui` | Everything: widget, types, config, themes |
| `@zephyr/ui/react` | `<Zephyr />`, `ZephyrProvider`, `useZephyr()` |
| `@zephyr/ui/vue` | `<Zephyr />` Vue component |
| `@zephyr/ui/config` | `defineZephyrConfig()`, types |
| `@zephyr/ui/themes` | Theme objects and helpers |

## License

MIT
