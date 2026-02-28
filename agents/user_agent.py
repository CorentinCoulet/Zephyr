"""
User Agent — AI-powered navigation guide and assistant for end-users.
Provides guided navigation, onboarding, contextual help, and UX friction detection.
"""

import json
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResponse


SYSTEM_PROMPT = """Tu es Zephyr 🦊 en mode Guide Utilisateur — un assistant IA bienveillant qui aide les utilisateurs à naviguer dans une application web.

## Ton rôle
- Guider l'utilisateur pas-à-pas pour accomplir ses tâches
- Expliquer l'interface en langage simple et accessible
- Proposer un onboarding interactif pour les nouveaux utilisateurs
- Détecter quand l'utilisateur est perdu et proposer de l'aide
- Expliquer ce que font les boutons et éléments de la page

## Ton style
- Chaleureux, patient et encourageant
- Tu utilises un langage simple, sans jargon technique
- Tu structures tes guides en étapes numérotées claires
- Tu utilises des émojis pour rendre le guide agréable (📍 étape, ✅ fait, 👆 action, 💡 astuce)
- Tu réponds en français sauf si le contexte est explicitement en anglais

## Format de guide pas-à-pas
📍 **Étape X/N** : Description de l'action
👆 Ce que l'utilisateur doit faire
💡 Astuce ou information complémentaire

## Quand l'utilisateur demande de l'aide
1. Identifie sa page actuelle et son objectif
2. Trouve le chemin le plus court pour atteindre son but
3. Génère un guide étape par étape avec des éléments visuels précis
4. Propose des alternatives si le chemin principal n'est pas clair

## Contexte
Tu reçois en contexte : la structure de navigation du site, les éléments interactifs de la page, les formulaires, et la position actuelle de l'utilisateur.
"""


class UserAgent(BaseAgent):
    """User-focused navigation guide and assistant."""

    agent_name = "user_agent"
    agent_mode = "user"

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(
        self, query: str, context: dict, session_id: str
    ) -> AgentResponse:
        """Process a user navigation/help query."""

        # Build contextual information for the LLM
        context_parts = []

        if "navigation" in context:
            nav_items = context["navigation"]
            if nav_items:
                context_parts.append(
                    "## Menu de navigation\n"
                    + "\n".join(
                        f"- {'[ACTIF] ' if n.get('is_active') else ''}"
                        f"{n.get('text', '?')} → {n.get('href', '?')}"
                        for n in nav_items
                    )
                )

        if "current_page" in context:
            context_parts.append(f"## Page actuelle\n{context['current_page']}")

        if "page_title" in context:
            context_parts.append(f"## Titre de la page\n{context['page_title']}")

        if "interactive_elements" in context:
            elements = context["interactive_elements"]
            if elements:
                buttons = [e for e in elements if e.get("tag") in ("button", "a") and e.get("is_visible")]
                if buttons:
                    context_parts.append(
                        f"## Boutons et liens visibles ({len(buttons)})\n"
                        + "\n".join(
                            f"- [{e.get('tag')}] \"{e.get('text', '?')}\" → {e.get('href', '-')}"
                            for e in buttons[:30]
                        )
                    )

        if "forms" in context:
            forms = context["forms"]
            if forms:
                for i, form in enumerate(forms):
                    fields_desc = ", ".join(
                        f"{f.get('label') or f.get('name', '?')} ({f.get('type', '?')})"
                        for f in form.get("fields", [])
                    )
                    context_parts.append(
                        f"## Formulaire {i + 1}\n"
                        f"- Action: {form.get('action', '?')}\n"
                        f"- Champs: {fields_desc}"
                    )

        if "sitemap" in context:
            sitemap = context["sitemap"]
            context_parts.append(
                "## Pages disponibles\n"
                + "\n".join(f"- {page}" for page in sitemap[:30])
            )

        if "user_journey" in context:
            journey = context["user_journey"]
            context_parts.append(
                "## Parcours utilisateur (pages visitées)\n"
                + " → ".join(journey[-10:])  # Last 10 pages
            )

        if "dom_snapshot" in context:
            dom = context["dom_snapshot"]
            # Simplified version for user context
            context_parts.append(
                f"## Structure de la page (simplifié)\n```json\n"
                f"{json.dumps(dom, indent=2, default=str)[:2000]}\n```"
            )

        # Assemble context
        context_text = "\n\n".join(context_parts) if context_parts else "(Page en cours d'analyse)"

        user_message = f"""Question de l'utilisateur : {query}

--- CONTEXTE PAGE ---

{context_text}

--- FIN CONTEXTE ---

Aide l'utilisateur de manière simple et guidée."""

        # Build messages
        conversation = self.get_conversation(session_id)
        messages = [msg.to_dict() for msg in conversation[:-1]]
        messages.append({"role": "user", "content": user_message})

        try:
            llm_response = await self.call_llm(messages, temperature=0.5)
            expression = self._detect_expression(query, llm_response)

            return AgentResponse(
                success=True,
                message=llm_response,
                data={
                    "mode": "user",
                    "current_page": context.get("current_page", ""),
                    "guide_steps": self._extract_steps(llm_response),
                },
                suggestions=self._generate_suggestions(query, context),
                expression=expression,
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Désolé, je n'ai pas pu traiter votre demande : {str(e)}",
                expression="surprised",
            )

    async def generate_onboarding(self, context: dict) -> AgentResponse:
        """Generate an onboarding tour for a new user."""
        return await self.chat(
            "Génère un tour guidé de bienvenue pour un nouvel utilisateur. "
            "Présente les sections principales de l'application et ce qu'on peut y faire.",
            context,
        )

    async def explain_element(
        self, selector: str, element_info: dict, context: dict
    ) -> AgentResponse:
        """Explain what a specific element does."""
        context["target_element"] = element_info
        return await self.chat(
            f"Explique-moi à quoi sert cet élément : {element_info.get('text', selector)}",
            context,
        )

    async def find_feature(self, feature: str, context: dict) -> AgentResponse:
        """Help user find a specific feature in the app."""
        return await self.chat(
            f"Où se trouve la fonctionnalité : {feature} ?",
            context,
        )

    async def generate_steps(self, goal: str, context: dict) -> AgentResponse:
        """Generate step-by-step instructions to achieve a goal."""
        return await self.chat(
            f"Guide-moi étape par étape pour : {goal}",
            context,
        )

    # --- Friction detection ---

    def detect_friction(self, session_events: list[dict]) -> list[dict]:
        """Analyze session events to detect UX friction points."""
        friction_points = []

        # Detect dead clicks
        dead_clicks = self._detect_dead_clicks(session_events)
        friction_points.extend(dead_clicks)

        # Detect rage clicks
        rage_clicks = self._detect_rage_clicks(session_events)
        friction_points.extend(rage_clicks)

        # Detect circular navigation
        circular = self._detect_circular_navigation(session_events)
        friction_points.extend(circular)

        # Detect form abandonment
        abandoned = self._detect_form_abandonment(session_events)
        friction_points.extend(abandoned)

        return friction_points

    # --- Private helpers ---

    def _detect_expression(self, query: str, response: str) -> str:
        """Detect which expression Zephyr should show."""
        query_lower = query.lower()

        if any(w in query_lower for w in ["bonjour", "salut", "hello", "bienvenue"]):
            return "happy"
        elif any(w in query_lower for w in ["perdu", "comprends pas", "bloqué", "aide"]):
            return "helping"
        elif "étape" in response.lower() or "📍" in response:
            return "helping"
        else:
            return "speaking"

    def _extract_steps(self, response: str) -> list[str]:
        """Extract numbered steps from the LLM response."""
        steps = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("📍") or line.startswith("**Étape"):
                steps.append(line)
            elif len(line) > 3 and line[0].isdigit() and (line[1] == "." or line[1] == ")"):
                steps.append(line)
        return steps

    def _generate_suggestions(self, query: str, context: dict) -> list[str]:
        """Generate follow-up suggestions."""
        suggestions = [
            "/guide — Tour guidé de la page",
            "/help — Poser une autre question",
        ]

        if context.get("forms"):
            suggestions.append("/explain — Comprendre un formulaire")
        if context.get("sitemap"):
            suggestions.append("/find — Chercher une fonctionnalité")

        return suggestions[:4]

    def _detect_dead_clicks(self, events: list[dict]) -> list[dict]:
        """Detect clicks on non-interactive elements."""
        dead = []
        for event in events:
            if event.get("type") == "click" and not event.get("interactive", True):
                dead.append({
                    "type": "dead_click",
                    "element": event.get("selector", "unknown"),
                    "page": event.get("page", ""),
                    "suggestion": "Cet élément ressemble à un bouton mais n'est pas cliquable.",
                })
        return dead

    def _detect_rage_clicks(self, events: list[dict]) -> list[dict]:
        """Detect rapid repeated clicks (frustration signal)."""
        rage = []
        click_events = [e for e in events if e.get("type") == "click"]

        for i in range(len(click_events) - 2):
            a, b, c = click_events[i], click_events[i + 1], click_events[i + 2]
            if (
                a.get("selector") == b.get("selector") == c.get("selector")
                and (c.get("timestamp", 0) - a.get("timestamp", 0)) < 2.0
            ):
                rage.append({
                    "type": "rage_click",
                    "element": a.get("selector", ""),
                    "page": a.get("page", ""),
                    "occurrences": 3,
                    "suggestion": "L'utilisateur clique frénétiquement. L'élément ne répond peut-être pas assez vite.",
                })
        return rage

    def _detect_circular_navigation(self, events: list[dict]) -> list[dict]:
        """Detect when user visits the same pages in a loop."""
        nav_events = [e.get("page", "") for e in events if e.get("type") == "navigate"]
        if len(nav_events) < 4:
            return []

        # Check for A→B→A→B pattern
        for i in range(len(nav_events) - 3):
            if (
                nav_events[i] == nav_events[i + 2]
                and nav_events[i + 1] == nav_events[i + 3]
                and nav_events[i] != nav_events[i + 1]
            ):
                return [{
                    "type": "circular_navigation",
                    "pages": [nav_events[i], nav_events[i + 1]],
                    "suggestion": "L'utilisateur tourne en rond entre ces pages. Il est probablement perdu.",
                }]
        return []

    def _detect_form_abandonment(self, events: list[dict]) -> list[dict]:
        """Detect forms that were started but not submitted."""
        abandoned = []
        forms_started = {}

        for event in events:
            if event.get("type") == "form_input":
                form_id = event.get("form_id", "unknown")
                forms_started[form_id] = event.get("page", "")
            elif event.get("type") == "form_submit":
                form_id = event.get("form_id", "unknown")
                forms_started.pop(form_id, None)

        for form_id, page in forms_started.items():
            abandoned.append({
                "type": "form_abandonment",
                "form_id": form_id,
                "page": page,
                "suggestion": "Le formulaire a été commencé mais jamais soumis.",
            })
        return abandoned
