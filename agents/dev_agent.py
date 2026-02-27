"""
Dev Agent — AI-powered debug and technical audit assistant for developers.
Analyzes DOM, console logs, performance reports, UI consistency, and provides
actionable diagnostics with code fix suggestions.
"""

import json
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResponse


SYSTEM_PROMPT = """Tu es Astrafox 🦊 en mode Développeur — un assistant IA expert en debug et audit technique pour projets web.

## Ton rôle
- Analyser les erreurs JavaScript, logs console, et erreurs réseau
- Auditer les performances (Core Web Vitals, Lighthouse)
- Détecter les incohérences UI (contraste, overflow, spacing, responsive)
- Diagnostiquer les bugs avec précision (fichier, ligne, cause probable)
- Proposer des corrections de code actionnables
- Évaluer l'accessibilité (WCAG AA/AAA)

## Ton style
- Technique mais accessible. Tu expliques clairement.
- Tu structures tes réponses : diagnostic → cause → solution → code
- Tu fournis toujours un score de confiance pour tes diagnostics
- Tu utilises des émojis pertinents (🔴 critique, 🟡 warning, 🟢 ok, 💡 suggestion)
- Tu réponds en français sauf si le contexte est explicitement en anglais.

## Format de réponse
Pour chaque problème trouvé :
1. **Sévérité** : 🔴 Critique / 🟡 Warning / 🔵 Info
2. **Description** : Explication claire du problème
3. **Cause probable** : Analyse technique de la source
4. **Fichier/Ligne** : Localisation si identifiable
5. **Fix suggéré** : Code correctif concret
6. **Impact** : Ce que ça affecte (UX, perf, SEO, accessibilité)

## Contexte
Tu reçois en contexte : DOM snapshot, console logs, erreurs réseau, rapport Lighthouse, screenshots, et la question du développeur.
Analyse tous les éléments fournis pour donner le diagnostic le plus complet possible.
"""


class DevAgent(BaseAgent):
    """Developer-focused debug and audit agent."""

    agent_name = "dev_agent"
    agent_mode = "dev"

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(
        self, query: str, context: dict, session_id: str
    ) -> AgentResponse:
        """Process a developer query with technical context."""

        # Build contextual prompt with available data
        context_parts = []

        if "console_errors" in context:
            errors = context["console_errors"]
            if errors:
                context_parts.append(
                    f"## Erreurs Console ({len(errors)} trouvées)\n"
                    + "\n".join(
                        f"- [{e.get('level', 'error')}] {e.get('message', '')}"
                        f" (source: {e.get('source_url', 'unknown')}:{e.get('line_number', '?')})"
                        for e in errors[:20]
                    )
                )

        if "network_errors" in context:
            net_errors = context["network_errors"]
            if net_errors:
                context_parts.append(
                    f"## Erreurs Réseau ({len(net_errors)} trouvées)\n"
                    + "\n".join(
                        f"- {e.get('method', 'GET')} {e.get('url', '')} → {e.get('status', 0)} {e.get('error_text', '')}"
                        for e in net_errors[:20]
                    )
                )

        if "dom_snapshot" in context:
            dom = context["dom_snapshot"]
            context_parts.append(
                f"## DOM Snapshot (simplifié)\n```json\n{json.dumps(dom, indent=2, default=str)[:3000]}\n```"
            )

        if "performance" in context:
            perf = context["performance"]
            context_parts.append(
                f"## Rapport Performance\n```json\n{json.dumps(perf, indent=2, default=str)[:2000]}\n```"
            )

        if "contrast_issues" in context:
            issues = context["contrast_issues"]
            if issues:
                context_parts.append(
                    f"## Problèmes de Contraste ({len(issues)})\n"
                    + "\n".join(
                        f"- {i.get('selector', '?')}: ratio {i.get('ratio', 0)} (requis: {i.get('required_ratio', 4.5)})"
                        for i in issues[:10]
                    )
                )

        if "overflow_issues" in context:
            issues = context["overflow_issues"]
            if issues:
                context_parts.append(
                    f"## Problèmes d'Overflow ({len(issues)})\n"
                    + "\n".join(
                        f"- {i.get('selector', '?')}: overflow_x={i.get('overflow_x', 0)}px, overflow_y={i.get('overflow_y', 0)}px"
                        for i in issues[:10]
                    )
                )

        if "forms" in context:
            forms = context["forms"]
            if forms:
                context_parts.append(
                    f"## Formulaires détectés ({len(forms)})\n"
                    + "\n".join(
                        f"- Form action={f.get('action', '?')} method={f.get('method', '?')} "
                        f"fields={len(f.get('fields', []))}"
                        for f in forms
                    )
                )

        if "interactive_elements" in context:
            elements = context["interactive_elements"]
            context_parts.append(
                f"## Éléments interactifs ({len(elements)} trouvés)"
            )

        if "visual_diff" in context:
            diff = context["visual_diff"]
            context_parts.append(
                f"## Diff Visuel\n"
                f"- Match: {diff.get('match', '?')}\n"
                f"- Mismatch: {diff.get('mismatch_percentage', 0)}%\n"
                f"- Pixels différents: {diff.get('diff_pixel_count', 0)}"
            )

        if "url" in context:
            context_parts.append(f"## URL analysée\n{context['url']}")

        if "viewport" in context:
            vp = context["viewport"]
            context_parts.append(f"## Viewport\n{vp.get('width', '?')}×{vp.get('height', '?')}")

        # Assemble the full user message
        context_text = "\n\n".join(context_parts) if context_parts else "(Aucun contexte technique fourni)"

        user_message = f"""Question du développeur : {query}

--- CONTEXTE TECHNIQUE ---

{context_text}

--- FIN CONTEXTE ---

Analyse ces informations et fournis un diagnostic complet."""

        # Build messages for LLM
        conversation = self.get_conversation(session_id)
        messages = [msg.to_dict() for msg in conversation[:-1]]  # Exclude last user msg
        messages.append({"role": "user", "content": user_message})

        try:
            llm_response = await self.call_llm(messages)
            expression = self._detect_expression(llm_response, context)

            return AgentResponse(
                success=True,
                message=llm_response,
                data={
                    "mode": "dev",
                    "context_keys": list(context.keys()),
                    "issues_found": self._count_issues(context),
                },
                suggestions=self._generate_suggestions(context),
                expression=expression,
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Erreur lors de l'analyse : {str(e)}",
                expression="surprised",
            )

    async def quick_debug(self, url: str, context: dict) -> AgentResponse:
        """Perform a quick debug analysis on a URL."""
        return await self.chat(
            f"Analyse rapide de debug pour {url}. Résume les problèmes trouvés par priorité.",
            context,
        )

    async def audit_performance(self, url: str, context: dict) -> AgentResponse:
        """Focused performance audit."""
        return await self.chat(
            f"Audit performance complet pour {url}. Focus sur Core Web Vitals et optimisations.",
            context,
        )

    async def audit_ui(self, url: str, context: dict) -> AgentResponse:
        """Focused UI consistency audit."""
        return await self.chat(
            f"Audit UI/UX complet pour {url}. Vérifie contraste, overflow, spacing, responsive, accessibilité.",
            context,
        )

    async def analyze_visual_diff(self, context: dict) -> AgentResponse:
        """Analyze visual regression results."""
        return await self.chat(
            "Analyse la régression visuelle détectée. Est-ce un changement intentionnel ou un bug ?",
            context,
        )

    # --- Private helpers ---

    def _detect_expression(self, response: str, context: dict) -> str:
        """Detect which Astrafox expression to show based on results."""
        issues = self._count_issues(context)
        lower_response = response.lower()

        if "🔴" in response or "critique" in lower_response:
            return "surprised"
        elif issues == 0 and ("aucun" in lower_response or "tout est" in lower_response):
            return "happy"
        elif "🟡" in response or "warning" in lower_response:
            return "helping"
        else:
            return "speaking"

    def _count_issues(self, context: dict) -> int:
        """Count total issues found in context."""
        count = 0
        count += len(context.get("console_errors", []))
        count += len(context.get("network_errors", []))
        count += len(context.get("contrast_issues", []))
        count += len(context.get("overflow_issues", []))
        return count

    def _generate_suggestions(self, context: dict) -> list[str]:
        """Generate follow-up command suggestions based on context."""
        suggestions = []

        if context.get("console_errors"):
            suggestions.append("/debug — Analyser les erreurs en détail")
        if context.get("performance"):
            suggestions.append("/perf — Voir les recommandations performance")
        if context.get("contrast_issues") or context.get("overflow_issues"):
            suggestions.append("/audit — Audit UI complet")
        if not suggestions:
            suggestions = [
                "/debug — Lancer un diagnostic",
                "/perf — Auditer la performance",
                "/screenshot — Capturer multi-viewport",
            ]

        return suggestions[:4]
