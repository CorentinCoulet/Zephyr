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
- Tu adaptes ton niveau de détail au profil de l'utilisateur

## Niveau de verbosité
- minimal : réponses courtes, étapes essentielles uniquement
- normal : explication claire avec contexte
- detailed : très détaillé, chaque étape expliquée en profondeur

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
Si des préférences utilisateur sont fournies, adapte ton style en conséquence.

## Contexte applicatif (fourni par le développeur)
Si un contexte applicatif est fourni, utilise-le EN PRIORITÉ pour répondre aux questions.
Ce contexte décrit l'application, ses fonctionnalités, son vocabulaire métier et ses workflows.
Il est plus fiable que l'analyse du DOM pour les questions métier.
Si la réponse est dans le contexte applicatif, réponds directement sans hésiter.
Si la FAQ contient une réponse exacte, utilise-la telle quelle.
"""

# Onboarding step tracking per session
_onboarding_progress: dict[str, dict] = {}  # session_id -> {"completed_steps": set, "total_steps": int}


class UserAgent(BaseAgent):
    """User-focused navigation guide and assistant."""

    agent_name = "user_agent"
    agent_mode = "user"

    def get_system_prompt(self, preferences: Optional[dict] = None) -> str:
        prompt = SYSTEM_PROMPT
        if preferences:
            lang = preferences.get("language", "fr")
            verbosity = preferences.get("verbosity", "normal")
            expertise = preferences.get("expertise_level", "beginner")
            a11y_mode = preferences.get("accessibility_mode", False)
            prompt += f"\n## Préférences utilisateur\n"
            prompt += f"- Langue: {lang}\n"
            prompt += f"- Verbosité: {verbosity}\n"
            prompt += f"- Niveau: {expertise}\n"
            if lang == "en":
                prompt += "- Réponds en anglais\n"
            if a11y_mode:
                prompt += "- Mode accessibilité: descriptions compatibles lecteur d'écran\n"
        return prompt

    async def process(
        self, query: str, context: dict, session_id: str
    ) -> AgentResponse:
        """Process a user navigation/help query."""

        # Apply user preferences if available
        preferences = context.get("user_preferences", {})

        # Build contextual information for the LLM
        context_parts = []

        # ── App context (highest priority — pre-provided by developer) ──
        if "app_context" in context:
            app_ctx = context["app_context"]
            app_parts = []
            if app_ctx.get("name") or app_ctx.get("description"):
                app_parts.append(
                    f"**{app_ctx.get('name', 'Application')}** — {app_ctx.get('description', '')}"
                )
            if app_ctx.get("features"):
                features_desc = "\n".join(
                    f"- **{f.get('name', '?')}** ({f.get('path', '')}) : {f.get('description', '')}"
                    for f in app_ctx["features"]
                )
                app_parts.append(f"### Fonctionnalités\n{features_desc}")
            if app_ctx.get("faq"):
                faq_desc = "\n".join(
                    f"- **Q:** {f.get('question', f.get('q', '?'))}\n  **R:** {f.get('answer', f.get('a', '?'))}"
                    for f in app_ctx["faq"]
                )
                app_parts.append(f"### FAQ\n{faq_desc}")
            if app_ctx.get("terminology"):
                terms = "\n".join(
                    f"- **{term}** : {definition}"
                    for term, definition in app_ctx["terminology"].items()
                )
                app_parts.append(f"### Vocabulaire métier\n{terms}")
            if app_ctx.get("workflows"):
                wf = "\n".join(f"- {w}" for w in app_ctx["workflows"])
                app_parts.append(f"### Parcours types\n{wf}")
            if app_ctx.get("custom"):
                app_parts.append(f"### Informations complémentaires\n{app_ctx['custom']}")
            if app_parts:
                context_parts.append("## 📋 Contexte applicatif (fourni par le développeur)\n" + "\n\n".join(app_parts))

        # Add friction alerts if detected
        if "friction_alerts" in context:
            alerts = context["friction_alerts"]
            if alerts:
                context_parts.append(
                    f"## ⚠️ Signaux de friction détectés ({len(alerts)})\n"
                    + "\n".join(f"- {a.get('type', '?')}: {a.get('suggestion', '')}" for a in alerts)
                )

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

        # Build messages — use preferences-aware system prompt
        conversation = self.get_conversation(session_id)
        messages = []
        for msg in conversation[:-1]:
            d = msg.to_dict()
            if d["role"] == "system":
                d["content"] = self.get_system_prompt(preferences)
            messages.append(d)
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": self.get_system_prompt(preferences)})
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

    async def generate_onboarding(self, context: dict, session_id: str = "default") -> AgentResponse:
        """Generate an onboarding tour for a new user. Tracks progress."""
        # Check if already started
        progress = _onboarding_progress.get(session_id)
        if progress and progress.get("completed_steps"):
            completed = progress["completed_steps"]
            total = progress["total_steps"]
            query = (
                f"Continue le tour guidé. L'utilisateur a déjà vu les étapes {sorted(completed)} sur {total}. "
                f"Reprends à partir de l'étape suivante."
            )
        else:
            query = (
                "Génère un tour guidé de bienvenue pour un nouvel utilisateur. "
                "Présente les sections principales de l'application et ce qu'on peut y faire. "
                "Numérote chaque étape clairement."
            )
        response = await self.chat(query, context, session_id)
        # Track total steps
        steps = self._extract_steps(response.message)
        if session_id not in _onboarding_progress:
            _onboarding_progress[session_id] = {"completed_steps": set(), "total_steps": len(steps)}
        return response

    def mark_onboarding_step(self, session_id: str, step: int) -> dict:
        """Mark an onboarding step as completed."""
        if session_id not in _onboarding_progress:
            _onboarding_progress[session_id] = {"completed_steps": set(), "total_steps": 0}
        _onboarding_progress[session_id]["completed_steps"].add(step)
        return {
            "completed": sorted(_onboarding_progress[session_id]["completed_steps"]),
            "total": _onboarding_progress[session_id]["total_steps"],
            "done": len(_onboarding_progress[session_id]["completed_steps"]) >= _onboarding_progress[session_id]["total_steps"] > 0,
        }

    def get_onboarding_progress(self, session_id: str) -> dict:
        """Get current onboarding progress."""
        progress = _onboarding_progress.get(session_id, {"completed_steps": set(), "total_steps": 0})
        return {
            "completed": sorted(progress["completed_steps"]),
            "total": progress["total_steps"],
            "done": len(progress["completed_steps"]) >= progress["total_steps"] > 0,
        }

    def reset_onboarding(self, session_id: str) -> None:
        """Reset onboarding progress for a session."""
        _onboarding_progress.pop(session_id, None)

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

    async def generate_page_tooltips(self, context: dict) -> AgentResponse:
        """Generate tooltips/descriptions for all visible interactive elements."""
        elements = context.get("interactive_elements", [])
        visible = [e for e in elements if e.get("is_visible", True)]
        if not visible:
            return AgentResponse(
                success=True,
                message="Aucun élément interactif visible sur cette page.",
                expression="neutral",
            )
        elements_desc = "\n".join(
            f"- [{e.get('tag')}] \"{e.get('text', '?')}\" selector={e.get('selector', '?')}"
            for e in visible[:40]
        )
        return await self.chat(
            f"Génère une courte description/tooltip (1 phrase max) pour chacun de ces éléments interactifs. "
            f"Retourne le résultat sous forme de liste avec le selector et la description.\n\n{elements_desc}",
            context,
        )

    async def analyze_friction(self, session_events: list[dict], context: dict) -> AgentResponse:
        """Analyze friction points and generate proactive help."""
        friction_points = self.detect_friction(session_events)
        if not friction_points:
            return AgentResponse(
                success=True,
                message="Aucun signe de difficulté détecté. L'utilisateur semble à l'aise.",
                expression="happy",
            )
        context["friction_alerts"] = friction_points
        friction_desc = "\n".join(f"- {f['type']}: {f.get('suggestion', '')}" for f in friction_points)
        return await self.chat(
            f"Des signaux de difficulté ont été détectés chez l'utilisateur :\n{friction_desc}\n\n"
            f"Propose une aide proactive et bienveillante, sans être intrusif.",
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
