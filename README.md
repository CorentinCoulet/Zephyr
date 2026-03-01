# 🦊 Zephyr — Universal UI Intelligence Platform

Plateforme d'intelligence artificielle pour l'analyse, le debug et la navigation assistée d'interfaces web.

**Deux modes d'utilisation :**
- **Mode User** → Package `@zephyr/ui` — composant `<Zephyr />` intégrable dans React, Vue ou vanilla JS
- **Mode Dev** → Serveur MCP pour GitHub Copilot / Claude — donne des "yeux" sur l'UI directement dans l'IDE

## Installation

```bash
# Frontend — Plugin widget
npm install @zephyr/ui

# Backend — Serveur Python
pip install -r requirements.txt
```

## Quick Start

### 1. Configurer le frontend (`zephyr.config.ts`)

```ts
import { defineZephyrConfig } from '@zephyr/ui/config';

export default defineZephyrConfig({
  server: 'http://localhost:8000',
  theme: 'dark',
  persona: 'friendly',
  logo: 'zephyr-default',
  accentColor: '#ff6b35',
  openAnimation: 'slide-up',
});
```

### 2. Intégrer le composant

**React :**
```tsx
import { Zephyr } from '@zephyr/ui/react';
import config from './zephyr.config';

function App() {
  return <Zephyr config={config} />;
}
```

**Vue 3 :**
```vue
<script setup>
import { Zephyr } from '@zephyr/ui/vue';
import config from './zephyr.config';
</script>
<template>
  <Zephyr :config="config" />
</template>
```

### 3. Configurer le backend (`zephyr.server.yaml`)

```yaml
provider: openai          # github-copilot | claude | openai | ollama

openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4o
```

### 4. Lancer le serveur

```bash
uvicorn api.server:app --reload --port 8000
```

## Architecture

```
┌─── Projet cible (React, Vue, Angular…) ───┐
│  import { Zephyr } from '@zephyr/ui'     │  ← @zephyr/ui package
│  <Zephyr config={...} />                  │
└──────────────────┬─────────────────────────┘
                   │ WebSocket
┌──────────────────┴─────────────────────────┐
│           FastAPI (api/server.py)           │
│  zephyr.server.yaml → Provider config     │
│  /ws/chat      /api/status                 │
└──────┬──────────────────────────┬──────────┘
       │                          │
┌──────┴───────┐          ┌───────┴──────┐
│  User Agent  │          │  Dev Agent   │
│  (guide/nav) │          │  (debug)     │
└──────┬───────┘          └───────┬──────┘
       │                          │
┌──────┴──────────────────────────┴──────┐
│           Core Analysis Engine          │
│  Browser │ DOM │ Console │ Perf │ Diff  │
└──────────────────┬─────────────────────┘
                   │
           ┌───────┴───────┐
           │  MCP Server   │  ← GitHub Copilot / Claude (Dev Mode)
           │  (stdio)      │
           └───────────────┘
```

## Fonctionnalités

### 🔧 Mode Dev (Debug) — via MCP Server + Copilot
- **Intégration directe avec GitHub Copilot (Claude Opus 4.6)** via MCP
- 9 outils MCP : screenshot, multi-viewport, DOM, console, perf, a11y, full analysis, visual diff, interaction
- Capture automatique des erreurs console et réseau
- Extraction DOM structurée (formulaires, éléments interactifs)
- Audit de performance via Lighthouse (Core Web Vitals)
- Détection des problèmes de contraste WCAG
- Détection des overflow CSS
- Régression visuelle (baseline + diff pixel)
- Copilot peut "voir" l'UI et faire des suggestions contextuelles

### 👤 Mode User (Navigation) — Widget SDK embedable
- **Composant réutilisable** : React, Vue 3, ou vanilla JS `<script>`
- 4 personas : Mascot, Spirit, Minimal, Futuristic (+ URL custom)
- Thème dark/light/auto, couleur d'accent configurable
- Position configurable (4 coins), taille (sm/md/lg)
- **Application Context** — le développeur fournit un contexte métier (features, FAQ, terminologie, workflows) pour des réponses instantanées
- Onboarding interactif guidé par IA
- Recherche de fonctionnalités en langage naturel
- Guide étape par étape
- Détection de friction (dead clicks, rage clicks)
- Mode inline ou floating

### 🦊 Zephyr (Persona)
- Avatar SVG animé avec 7 expressions (neutral, happy, surprised, thinking, helping, speaking, wink)
- Thème dark/light avec variables CSS
- Réponses en Markdown avec coloration syntaxique
- Suggestions contextuelles
- Bulle de chat ergonomique

## Stack technique

| Composant     | Technologie                        |
|---------------|------------------------------------|
| Backend       | Python 3.11, FastAPI, uvicorn      |
| Browser       | Playwright + Chromium headless     |
| LLM           | OpenAI / Anthropic / Ollama        |
| Performance   | Lighthouse CLI                     |
| Visual diff   | Pillow + pixelmatch                |
| Frontend      | Vue 3, Vite, Tailwind CSS, Pinia   |
| Widget SDK    | Vanilla JS + React + Vue wrappers  |
| MCP Server    | mcp[cli] (Model Context Protocol)  |
| Container     | Docker + docker-compose            |

## Installation

### Prérequis
- Python 3.11+
- Node.js 20+
- Docker (optionnel)

### Setup local

```bash
# Backend
cd ui-intelligence
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd zephyr_ui
npm install
npm run build
cd ..

# Configuration
cp .env.example .env
# Editer .env avec votre clé API LLM

# Lancer
uvicorn api.server:app --reload --port 8000
```

### Docker

```bash
cp .env.example .env
# Editer .env
docker-compose up --build
```

## API Endpoints

| Méthode | Endpoint              | Description                          |
|---------|-----------------------|--------------------------------------|
| GET     | `/api/health`         | Health check                         |
| GET     | `/api/status`         | Statut de la plateforme              |
| POST    | `/api/analyze`        | Analyse complète d'une URL           |
| POST    | `/api/debug`          | Debug avec Dev Agent                 |
| POST    | `/api/guide`          | Guidance utilisateur                 |
| POST    | `/api/guide/onboarding` | Génération tour d'onboarding       |
| POST    | `/api/guide/find`     | Trouver une fonctionnalité           |
| PUT     | `/api/guide/app-context` | Définir/mettre à jour le contexte applicatif |
| GET     | `/api/guide/app-context/:id` | Récupérer le contexte applicatif d'une session |
| POST    | `/api/chat/dev`       | Chat Dev Agent                       |
| POST    | `/api/chat/user`      | Chat User Agent                      |
| POST    | `/api/screenshot`     | Captures multi-viewport              |
| POST    | `/api/baseline`       | Sauvegarder baseline visuel          |
| POST    | `/api/diff`           | Comparaison visuelle                 |
| GET     | `/api/sessions`       | Lister les sessions                  |
| WS      | `/ws/chat`            | WebSocket chat temps réel            |

## Tests

```bash
pytest -v
```

## Mode Dev — MCP Server pour Copilot/Claude

Le serveur MCP donne à GitHub Copilot (Claude Opus 4.6) un accès direct aux outils d'analyse visuelle de l'UI.

### Setup

1. Installer les dépendances :
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Configurer VS Code — créer `.vscode/mcp.json` :
```json
{
  "servers": {
    "zephyr": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/chemin/vers/ui-intelligence"
    }
  }
}
```

3. Relancer VS Code — Zephyr apparaît dans les outils MCP disponibles.

### Outils MCP disponibles

| Outil | Description |
|---|---|
| `capture_screenshot` | Capture d'écran d'une page (base64) |
| `capture_multi_viewport` | Screenshots responsive (mobile, tablet, desktop) |
| `analyze_dom` | Extraction structurée du DOM, éléments interactifs, formulaires |
| `get_console_errors` | Erreurs console JS, warnings, erreurs réseau |
| `audit_performance` | Audit Lighthouse (Core Web Vitals) |
| `check_accessibility` | Contraste WCAG + overflow detection |
| `full_page_analysis` | Analyse complète (screenshot + DOM + erreurs + a11y) |
| `compare_visual` | Régression visuelle (baseline/diff) |
| `interact_with_page` | Click, type, hover sur un élément + screenshot résultat |

### Exemples d'utilisation avec Copilot

```
Toi : "Peux-tu regarder ma page http://localhost:3000/dashboard et me dire
       s'il y a des problèmes ?"

Copilot appelle : full_page_analysis(url="http://localhost:3000/dashboard")
→ Reçoit screenshot + DOM + erreurs + accessibilité
→ Te donne un diagnostic contextualisé avec les vrais problèmes visuels
```

```
Toi : "Le bouton submit ne marche pas sur mobile"

Copilot appelle : capture_screenshot(url="...", viewport="mobile_m")
                + get_console_errors(url="...")
→ Voit le layout mobile + les erreurs JS associées
→ Identifie le problème précis
```

## Mode User — Widget SDK embedable

Widget AI insérable en une ligne dans n'importe quel projet web.

### Intégration rapide (script tag)

```html
<script src="https://your-zephyr-server/api/sdk/zephyr-widget.js"></script>
<script>
  ZephyrWidget.init({
    server: 'https://your-zephyr-server',
    persona: 'minimal',      // mascot | spirit | minimal | futuristic
    theme: 'auto',
    position: 'bottom-right',
    accentColor: '#ff6b35',
    // Contexte applicatif — permet des réponses instantanées
    appContext: {
      name: 'MonApp',
      description: 'Plateforme de gestion de projets collaboratifs',
      features: [
        { name: 'Dashboard', path: '/dashboard', description: 'Vue d\'ensemble des projets' },
        { name: 'Kanban', path: '/board', description: 'Tableau de tâches drag & drop' },
      ],
      faq: [
        { question: 'Comment créer un projet ?', answer: 'Menu + > Nouveau projet > Remplir le formulaire' },
      ],
      terminology: { sprint: 'période de 2 semaines', story: 'tâche utilisateur' },
      workflows: ['Créer projet → Ajouter membres → Créer tâches → Suivre'],
    },
  });
</script>
```

### React
```jsx
import { ZephyrChat } from '@zephyr/widget/react';
<ZephyrChat server="https://..." persona="spirit" theme="dark" />
```

### Vue 3
```vue
<script setup>
import ZephyrWidget from '@zephyr/widget/vue';
</script>
<template>
  <ZephyrWidget server="https://..." persona="futuristic" theme="dark" />
</template>
```

Voir [sdk/README.md](sdk/README.md) pour la documentation complète des props, events, et API.

## Tests

```bash
pytest -v
```

## Structure du projet

```
ui-intelligence/
├── api/
│   ├── server.py              # FastAPI main
│   ├── routes/
│   │   ├── analyze.py         # Analyse & screenshots
│   │   ├── debug.py           # Debug & diff
│   │   ├── guide.py           # Navigation guide
│   │   ├── reports.py         # Sessions & rapports
│   │   └── widget.py          # Widget SDK serving
│   ├── websocket/
│   │   └── chat_ws.py         # WebSocket chat
│   └── models/
│       ├── requests.py        # Schémas requêtes
│       └── responses.py       # Schémas réponses
├── agents/
│   ├── base_agent.py          # Agent abstrait + LLM
│   ├── dev_agent.py           # Agent développeur
│   ├── user_agent.py          # Agent utilisateur
│   └── prompts/               # Templates Markdown
├── core/
│   ├── browser_engine.py      # Playwright browser
│   ├── dom_extractor.py       # Extraction DOM (JS)
│   ├── interaction_runner.py  # Simulation interactions
│   ├── perf_analyzer.py       # Lighthouse wrapper
│   ├── console_capture.py     # Capture console/erreurs
│   ├── visual_diff.py         # Régression visuelle
│   └── screenshot_manager.py  # Gestion screenshots
├── orchestrator/
│   ├── router.py              # Routage Dev/User
│   ├── session_manager.py     # Sessions
│   ├── context_builder.py     # Assemblage contexte
│   └── prompt_engine.py       # Templates prompts
├── config/
│   ├── settings.py            # Configuration globale
│   └── llm_config.py          # Config LLM
├── mcp_server/                # 🔧 MCP Server pour Copilot
│   ├── server.py              # 9 outils MCP (screenshot, DOM, perf…)
│   ├── __main__.py            # python -m mcp_server
│   └── requirements.txt
├── sdk/                       # 👤 Widget SDK embedable
│   ├── zephyr-widget.js      # Core widget (vanilla JS, ~500 lignes)
│   ├── react/index.jsx        # React wrapper <ZephyrChat />
│   ├── vue/ZephyrWidget.vue  # Vue 3 wrapper
│   ├── index.d.ts             # TypeScript types
│   └── README.md              # Documentation SDK
├── zephyr_ui/                # Frontend admin Vue 3
│   ├── src/
│   │   ├── components/        # ZephyrAvatar, Chat, etc.
│   │   ├── stores/            # Pinia stores
│   │   ├── views/             # ChatView, Dashboard
│   │   └── styles/            # Tailwind + thèmes
│   ├── package.json
│   └── vite.config.js
├── tests/                     # Pytest
├── .vscode/mcp.json           # Config MCP pour VS Code
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Licence

MIT
