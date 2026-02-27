"""
Prompt Engine — Assembles and optimizes prompts for LLM calls.
Handles template selection, context injection, token optimization.
"""

from pathlib import Path
from typing import Optional


PROMPTS_DIR = Path(__file__).parent.parent / "agents" / "prompts"


class PromptEngine:
    """Assembles optimized prompts for the agents."""

    def __init__(self):
        self._templates: dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all prompt templates from disk."""
        if PROMPTS_DIR.exists():
            for path in PROMPTS_DIR.glob("*.md"):
                key = path.stem  # e.g. "dev_system", "user_guide"
                self._templates[key] = path.read_text(encoding="utf-8")

    def get_template(self, name: str) -> str:
        """Get a prompt template by name."""
        return self._templates.get(name, "")

    def build_system_prompt(self, mode: str, task: str = "system") -> str:
        """Build a full system prompt for an agent."""
        key = f"{mode}_{task}"
        template = self.get_template(key)

        if not template:
            # Fallback to system prompt
            template = self.get_template(f"{mode}_system")

        return template

    def build_context_prompt(self, context: dict, max_chars: int = 6000) -> str:
        """Build a context section from available data, respecting token budget."""
        parts = []
        budget = max_chars

        # Priority order for context inclusion
        priority_keys = [
            ("url", "## URL analysée\n{value}"),
            ("current_page", "## Page actuelle\n{value}"),
            ("page_title", "## Titre: {value}"),
            ("console_errors", "## Erreurs Console\n{value}"),
            ("network_errors", "## Erreurs Réseau\n{value}"),
            ("performance", "## Performance\n{value}"),
            ("contrast_issues", "## Problèmes Contraste\n{value}"),
            ("overflow_issues", "## Problèmes Overflow\n{value}"),
            ("navigation", "## Navigation\n{value}"),
            ("interactive_elements", "## Éléments interactifs\n{value}"),
            ("forms", "## Formulaires\n{value}"),
            ("dom_snapshot", "## DOM (simplifié)\n{value}"),
            ("user_journey", "## Parcours: {value}"),
        ]

        for key, template in priority_keys:
            if key not in context:
                continue

            value = context[key]
            if isinstance(value, list):
                if not value:
                    continue
                value_str = self._format_list(value)
            elif isinstance(value, dict):
                value_str = self._format_dict(value)
            else:
                value_str = str(value)

            formatted = template.format(value=value_str)

            if len(formatted) > budget:
                # Truncate to fit budget
                formatted = formatted[:budget - 20] + "\n...(tronqué)"
                parts.append(formatted)
                break
            else:
                parts.append(formatted)
                budget -= len(formatted)

            if budget <= 100:
                break

        return "\n\n".join(parts)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (~4 chars per token for French/English)."""
        return len(text) // 4

    # --- Private ---

    @staticmethod
    def _format_list(items: list, max_items: int = 15) -> str:
        """Format a list of items for prompt inclusion."""
        lines = []
        for item in items[:max_items]:
            if isinstance(item, dict):
                summary = ", ".join(f"{k}={v}" for k, v in item.items() if v)
                lines.append(f"- {summary[:150]}")
            else:
                lines.append(f"- {str(item)[:150]}")
        if len(items) > max_items:
            lines.append(f"... et {len(items) - max_items} de plus")
        return "\n".join(lines)

    @staticmethod
    def _format_dict(data: dict, max_depth: int = 2) -> str:
        """Format a dict for prompt inclusion."""
        lines = []
        for k, v in data.items():
            if isinstance(v, dict) and max_depth > 0:
                lines.append(f"**{k}**:")
                for k2, v2 in v.items():
                    lines.append(f"  - {k2}: {str(v2)[:100]}")
            elif isinstance(v, list):
                lines.append(f"**{k}**: [{len(v)} éléments]")
            else:
                lines.append(f"**{k}**: {str(v)[:100]}")
        return "\n".join(lines)
