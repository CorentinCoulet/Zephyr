"""
Dev Agent — AI-powered debug and technical audit assistant for developers.
Analyzes DOM, console logs, performance reports, UI consistency, and provides
actionable diagnostics with code fix suggestions.
"""

from pathlib import Path
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResponse


_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = _PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


SYSTEM_PROMPT = _load_prompt("dev_system")


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
            # Smart DOM summary instead of truncated JSON
            summary = self._summarize_dom(dom)
            context_parts.append(f"## DOM Summary\n{summary}")

        if "performance" in context:
            perf = context["performance"]
            # Extract key metrics instead of raw JSON
            if isinstance(perf, dict):
                scores_str = ""
                if "scores" in perf:
                    s = perf["scores"]
                    scores_str = f"Perf={s.get('performance', '?')} A11y={s.get('accessibility', '?')} BP={s.get('best_practices', '?')} SEO={s.get('seo', '?')}"
                metrics_str = ""
                if "metrics" in perf:
                    m = perf["metrics"]
                    metrics_str = ", ".join(f"{k}: {v.get('display', v.get('value', '?'))}" for k, v in m.items())
                opps = perf.get("opportunities", [])
                opps_str = ""
                if opps:
                    opps_str = "\n".join(f"- {o.get('title', '?')} (save {o.get('savings_ms', 0)}ms)" for o in opps[:5])
                context_parts.append(
                    f"## Rapport Performance\n{scores_str}\n{metrics_str}"
                    + (f"\n### Optimisations\n{opps_str}" if opps_str else "")
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

        if "accessibility_issues" in context:
            a11y = context["accessibility_issues"]
            if a11y:
                context_parts.append(
                    f"## Problèmes d'Accessibilité ({len(a11y)})\n"
                    + "\n".join(
                        f"- [{i.get('severity', 'warning')}] {i.get('type', '?')}: {i.get('details', '')} ({i.get('selector', '?')})"
                        for i in a11y[:15]
                    )
                )

        if "framework" in context:
            fw = context["framework"]
            if fw:
                frameworks = fw.get("frameworks", [])
                if frameworks:
                    context_parts.append(
                        f"## Framework détecté\n"
                        + ", ".join(f"{f.get('name')} {f.get('version', '')}".strip() for f in frameworks)
                    )

        if "storage" in context:
            storage = context["storage"]
            if storage:
                parts = []
                ls = storage.get("local_storage", {})
                ss = storage.get("session_storage", {})
                cookies = storage.get("cookies", [])
                if ls: parts.append(f"localStorage: {len(ls)} clés")
                if ss: parts.append(f"sessionStorage: {len(ss)} clés")
                if cookies: parts.append(f"cookies: {len(cookies)}")
                if parts:
                    context_parts.append(f"## Storage\n" + ", ".join(parts))

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
        """Detect which Zephyr expression to show based on results."""
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
        count += len(context.get("accessibility_issues", []))
        return count

    def _generate_suggestions(self, context: dict) -> list[str]:
        """Generate follow-up command suggestions based on context."""
        suggestions = []

        if context.get("console_errors"):
            suggestions.append("/debug — Analyser les erreurs en détail")
        if context.get("performance"):
            suggestions.append("/perf — Voir les recommandations performance")
        if context.get("contrast_issues") or context.get("overflow_issues") or context.get("accessibility_issues"):
            suggestions.append("/audit — Audit UI & accessibilité complet")
        if context.get("network_errors"):
            suggestions.append("/network — Analyser le waterfall réseau")
        if not suggestions:
            suggestions = [
                "/debug — Lancer un diagnostic",
                "/perf — Auditer la performance",
                "/screenshot — Capturer multi-viewport",
                "/storage — Inspecter le storage",
            ]

        return suggestions[:4]

    @staticmethod
    def _summarize_dom(dom: dict, depth: int = 0) -> str:
        """Generate an intelligent DOM summary instead of raw JSON."""
        if not dom or not isinstance(dom, dict):
            return "(DOM vide)"

        tag_counts: dict[str, int] = {}
        max_depth = 0
        total_nodes = 0
        text_nodes = 0
        interactive_tags = {"a", "button", "input", "select", "textarea", "form"}
        interactive_count = 0
        semantic_tags = {"header", "footer", "nav", "main", "section", "article", "aside"}
        semantic_used = set()

        def walk(node, d=0):
            nonlocal max_depth, total_nodes, text_nodes, interactive_count
            if not isinstance(node, dict):
                return
            total_nodes += 1
            tag = node.get("tag", "")
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                if tag in interactive_tags:
                    interactive_count += 1
                if tag in semantic_tags:
                    semantic_used.add(tag)
            if node.get("text"):
                text_nodes += 1
            max_depth = max(max_depth, d)
            for child in node.get("children", []):
                walk(child, d + 1)

        walk(dom)

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        lines = [
            f"Nœuds: {total_nodes} | Profondeur max: {max_depth} | Interactifs: {interactive_count} | Texte: {text_nodes}",
            f"Tags fréquents: {', '.join(f'{t}({c})' for t, c in top_tags)}",
        ]
        if semantic_used:
            lines.append(f"Tags sémantiques: {', '.join(sorted(semantic_used))}")
        missing_semantic = semantic_tags - semantic_used
        if missing_semantic:
            lines.append(f"Sémantique manquante: {', '.join(sorted(missing_semantic))}")
        return "\n".join(lines)
