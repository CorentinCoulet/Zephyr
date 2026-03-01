# 🦊 @zephyr/widget — Embeddable AI Navigation Assistant

Composant réutilisable d'assistant IA pour guider les utilisateurs dans n'importe quelle application web.

## Installation

### Option 1 : Script tag (le plus simple)

```html
<script src="https://your-zephyr-server/api/sdk/zephyr-widget.js"></script>
<script>
  ZephyrWidget.init({
    server: 'https://your-zephyr-server',
    persona: 'minimal',
    theme: 'dark',
    position: 'bottom-right',
    accentColor: '#ff6b35',
    language: 'fr',
  });
</script>
```

### Option 2 : npm

```bash
npm install @zephyr/widget
```

## Utilisation React

```jsx
import { ZephyrChat } from '@zephyr/widget/react';

function App() {
  return (
    <ZephyrChat
      server="https://your-zephyr-server"
      persona="spirit"
      theme="auto"
      position="bottom-right"
      accentColor="#6c63ff"
      language="fr"
      onMessage={(msg) => console.log(msg)}
    />
  );
}
```

### Inline (dans un conteneur)

```jsx
<ZephyrChat
  server="https://your-zephyr-server"
  inline
  style={{ height: '500px', width: '100%' }}
/>
```

### Hook impératif

```jsx
import { useZephyr } from '@zephyr/widget/react';

function HelpButton() {
  const { open, send } = useZephyr();
  return <button onClick={() => { open(); send("Comment faire X ?"); }}>Aide</button>;
}
```

## Utilisation Vue 3

```vue
<script setup>
import ZephyrWidget from '@zephyr/widget/vue';
</script>

<template>
  <ZephyrWidget
    server="https://your-zephyr-server"
    persona="futuristic"
    theme="dark"
    position="bottom-left"
    accent-color="#ff9f43"
    @message="onMessage"
    @toggle="onToggle"
  />
</template>
```

### Inline + ref

```vue
<template>
  <ZephyrWidget
    ref="zephyr"
    server="..."
    :inline="true"
    style="height: 500px"
  />
  <button @click="$refs.zephyr.send('Bonjour')">Envoyer</button>
</template>
```

## Utilisation Vanilla JS (Web Component / n'importe quel framework)

```js
import { ZephyrWidget } from '@zephyr/widget';

const widget = ZephyrWidget.init({
  server: 'https://your-zephyr-server',
  persona: 'mascot',
  theme: 'light',
  position: 'bottom-right',
});

// API impérative
widget.open();
widget.send("Où trouver les paramètres ?");
widget.setTheme('dark');
widget.setPersona('spirit');
widget.close();
widget.destroy();
```

## Props / Options

| Prop | Type | Default | Description |
|---|---|---|---|
| `server` | string | **required** | URL du serveur Zephyr |
| `apiKey` | string | `""` | Clé API pour l'authentification |
| `persona` | string | `"minimal"` | `"mascot"` \| `"spirit"` \| `"minimal"` \| `"futuristic"` \| URL image custom |
| `theme` | string | `"dark"` | `"dark"` \| `"light"` \| `"auto"` |
| `position` | string | `"bottom-right"` | `"bottom-right"` \| `"bottom-left"` \| `"top-right"` \| `"top-left"` |
| `size` | string | `"md"` | `"sm"` \| `"md"` \| `"lg"` |
| `language` | string | `"fr"` | `"fr"` \| `"en"` |
| `greeting` | string | `null` | Message d'accueil custom |
| `placeholder` | string | `null` | Placeholder du champ de saisie |
| `accentColor` | string | `"#ff6b35"` | Couleur d'accent (CSS) |
| `zIndex` | number | `99999` | Z-index CSS |
| `open` | boolean | `false` | Ouvrir au chargement |
| `showBadge` | boolean | `true` | Afficher le badge de notification |
| `features` | array | `["chat","guide","search"]` | Fonctionnalités activées |
| `appContext` | object | `null` | Contexte applicatif métier (voir ci-dessous) |
| `inline` | boolean | `false` | Mode inline (dans un conteneur) |
| `customCSS` | string | `""` | CSS additionnel |

## Personas

| ID | Style | Description |
|---|---|---|
| `mascot` | Mascotte complète | Renard Zephyr avec moustaches, détails complets |
| `spirit` | Esprit flottant | Version éthérée avec glow radial |
| `minimal` | Ultra minimal SaaS | Fond arrondi, traits simples |
| `futuristic` | Futuriste | Dégradé, yeux rectangulaires, point lumineux |

Vous pouvez aussi passer une **URL d'image** pour un persona custom :
```js
ZephyrWidget.init({
  server: '...',
  persona: 'https://example.com/my-custom-avatar.svg',
});
```

## Events / Callbacks

| Event | Payload | Description |
|---|---|---|
| `onReady` / `@ready` | `widget` | Widget initialisé |
| `onMessage` / `@message` | `{ role, text, expression }` | Nouveau message |
| `onError` / `@error` | `{ message }` | Erreur WebSocket/serveur |
| `onToggle` / `@toggle` | `boolean` | Panel ouvert/fermé |

## API Impérative

| Méthode | Description |
|---|---|
| `widget.open()` | Ouvre le panel |
| `widget.close()` | Ferme le panel |
| `widget.toggle()` | Bascule |
| `widget.send(text)` | Envoie un message |
| `widget.setTheme(theme)` | Change le thème |
| `widget.setPersona(persona)` | Change le persona |
| `widget.setAccentColor(color)` | Change la couleur d'accent |
| `widget.setAppContext(ctx)` | Met à jour le contexte applicatif (utile pour les SPAs) |
| `widget.destroy()` | Détruit le widget |

## Application Context (`appContext`)

Le contexte applicatif permet au chatbot de répondre **instantanément** aux questions métier sans analyser le DOM à chaque fois.

Le développeur qui intègre Zephyr décrit son application : ses features, sa FAQ, sa terminologie et ses workflows.

### Structure

```js
ZephyrWidget.init({
  server: 'https://...',
  appContext: {
    // Nom et description de l'application
    name: 'MonApp',
    description: 'Plateforme de gestion de projets collaboratifs',

    // Fonctionnalités principales (utilisé pour guider la navigation)
    features: [
      { name: 'Dashboard', path: '/dashboard', description: 'Vue d\'ensemble des projets actifs' },
      { name: 'Kanban', path: '/board', description: 'Tableau de suivi des tâches drag & drop' },
      { name: 'Paramètres', path: '/settings', description: 'Configuration du compte et des projets' },
    ],

    // FAQ — réponses pré-écrites (le chatbot les renvoie directement)
    faq: [
      { question: 'Comment créer un projet ?', answer: 'Menu + > Nouveau projet > Remplir le formulaire' },
      { question: 'Comment inviter un membre ?', answer: 'Paramètres du projet > Membres > Inviter' },
    ],

    // Terminologie métier (le chatbot utilisera ces définitions)
    terminology: {
      sprint: 'période de travail de 2 semaines',
      story: 'tâche utilisateur à compléter',
      backlog: 'liste des tâches à planifier',
    },

    // Workflows typiques (parcours utilisateur)
    workflows: [
      'Créer un projet → Ajouter des membres → Créer des tâches → Suivre l\'avancement',
      'Se connecter → Dashboard → Sélectionner un projet → Vue Kanban',
    ],

    // Texte libre complémentaire
    custom: 'L\'app supporte 3 rôles : Admin, Manager et Contributeur.',
  },
});
```

### Mise à jour dynamique (SPA)

Pour les Single Page Applications, mettez à jour le contexte lors des changements de route :

```js
const widget = ZephyrWidget.init({ server: '...', appContext: globalContext });

// Quand l'utilisateur change de page
router.afterEach((to) => {
  widget.setAppContext({
    ...globalContext,
    custom: `L'utilisateur est sur la page ${to.name}.`,
  });
});
```

### API REST

Le contexte applicatif peut aussi être défini via l'API REST :

```bash
# Définir le contexte
curl -X PUT https://your-server/api/guide/app-context \
  -H 'Content-Type: application/json' \
  -d '{ "session_id": "...", "app_context": { "name": "MonApp", ... } }'

# Récupérer le contexte
curl https://your-server/api/guide/app-context/{session_id}
```

### Comment ça marche

1. Le widget envoie le `appContext` au serveur via WebSocket à la connexion
2. Le serveur le stocke dans la session utilisateur
3. À chaque question, le contexte applicatif est injecté **en priorité** dans le prompt LLM
4. Si la FAQ contient la réponse, le chatbot la renvoie directement
5. Sinon, il combine le contexte applicatif + l'analyse DOM pour une réponse complète

**Avantages :**
- ⚡ Réponses instantanées aux questions métier (pas d'analyse DOM nécessaire)
- 🎯 Réponses plus précises (le dev connaît mieux son app que le DOM)
- 💰 Moins de tokens LLM consommés
- 🗣️ Le chatbot parle le "langage" de l'app
