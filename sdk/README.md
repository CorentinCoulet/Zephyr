# 🦊 @astrafox/widget — Embeddable AI Navigation Assistant

Composant réutilisable d'assistant IA pour guider les utilisateurs dans n'importe quelle application web.

## Installation

### Option 1 : Script tag (le plus simple)

```html
<script src="https://your-astrafox-server/api/sdk/astrafox-widget.js"></script>
<script>
  AstrafoxWidget.init({
    server: 'https://your-astrafox-server',
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
npm install @astrafox/widget
```

## Utilisation React

```jsx
import { AstrafoxChat } from '@astrafox/widget/react';

function App() {
  return (
    <AstrafoxChat
      server="https://your-astrafox-server"
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
<AstrafoxChat
  server="https://your-astrafox-server"
  inline
  style={{ height: '500px', width: '100%' }}
/>
```

### Hook impératif

```jsx
import { useAstrafox } from '@astrafox/widget/react';

function HelpButton() {
  const { open, send } = useAstrafox();
  return <button onClick={() => { open(); send("Comment faire X ?"); }}>Aide</button>;
}
```

## Utilisation Vue 3

```vue
<script setup>
import AstrafoxWidget from '@astrafox/widget/vue';
</script>

<template>
  <AstrafoxWidget
    server="https://your-astrafox-server"
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
  <AstrafoxWidget
    ref="astrafox"
    server="..."
    :inline="true"
    style="height: 500px"
  />
  <button @click="$refs.astrafox.send('Bonjour')">Envoyer</button>
</template>
```

## Utilisation Vanilla JS (Web Component / n'importe quel framework)

```js
import { AstrafoxWidget } from '@astrafox/widget';

const widget = AstrafoxWidget.init({
  server: 'https://your-astrafox-server',
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
| `server` | string | **required** | URL du serveur Astrafox |
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
| `inline` | boolean | `false` | Mode inline (dans un conteneur) |
| `customCSS` | string | `""` | CSS additionnel |

## Personas

| ID | Style | Description |
|---|---|---|
| `mascot` | Mascotte complète | Renard Astrafox avec moustaches, détails complets |
| `spirit` | Esprit flottant | Version éthérée avec glow radial |
| `minimal` | Ultra minimal SaaS | Fond arrondi, traits simples |
| `futuristic` | Futuriste | Dégradé, yeux rectangulaires, point lumineux |

Vous pouvez aussi passer une **URL d'image** pour un persona custom :
```js
AstrafoxWidget.init({
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
| `widget.destroy()` | Détruit le widget |
