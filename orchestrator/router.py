"""
Router — Routes incoming requests to the appropriate agent (Dev or User).
Implements automatic mode detection based on query analysis and signals.
"""

import re
from enum import Enum
from typing import Optional


class AgentTarget(str, Enum):
    DEV = "dev"
    USER = "user"


# --- Signal keywords ---

DEV_KEYWORDS = [
    "error", "erreur", "bug", "crash", "exception", "debug",
    "performance", "perf", "lighthouse", "audit", "console",
    "dom", "css", "html", "javascript", "js", "api", "endpoint",
    "responsive", "overflow", "contraste", "contrast", "diff",
    "regression", "screenshot", "viewport", "network", "cors",
    "timeout", "stack", "trace", "log", "warn", "lint",
    "build", "deploy", "webpack", "bundle", "render",
    "component", "composant", "hook", "state", "props",
    "null", "undefined", "typeerror", "referenceerror",
]

USER_KEYWORDS = [
    "comment", "où", "ou", "aide", "help", "guide",
    "trouver", "cherche", "find", "montrer", "show",
    "expliquer", "explain", "comprendre", "understand",
    "étape", "step", "tutoriel", "tutorial", "tour",
    "naviguer", "navigate", "aller", "go", "page",
    "bouton", "button", "formulaire", "form", "menu",
    "connexion", "login", "inscription", "register",
    "exporter", "export", "importer", "import",
    "modifier", "edit", "supprimer", "delete",
    "créer", "create", "nouveau", "new",
    "quoi", "what", "pourquoi", "why",
    "c'est quoi", "ça fait quoi", "à quoi sert",
]

DEV_URL_PATTERNS = [
    r"localhost",
    r"127\.0\.0\.1",
    r":3000",
    r":5000",
    r":8080",
    r"/admin",
    r"/debug",
    r"/api/",
    r"/swagger",
    r"/graphql",
]


class Router:
    """Routes requests to the appropriate agent based on intent analysis."""

    def __init__(self):
        self._overrides: dict[str, AgentTarget] = {}  # session_id → forced mode

    def set_mode_override(self, session_id: str, mode: AgentTarget) -> None:
        """Force a specific mode for a session (user manually chose)."""
        self._overrides[session_id] = mode

    def clear_override(self, session_id: str) -> None:
        """Clear the forced mode for a session."""
        self._overrides.pop(session_id, None)

    def route(
        self,
        query: str,
        session_id: Optional[str] = None,
        url: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> AgentTarget:
        """Determine which agent should handle this request."""

        # Check for manual override first
        if session_id and session_id in self._overrides:
            return self._overrides[session_id]

        # Check for explicit commands
        explicit = self._check_explicit_command(query)
        if explicit:
            return explicit

        # Score-based detection
        dev_score = self._compute_dev_score(query, url, headers)
        user_score = self._compute_user_score(query)

        if dev_score > user_score:
            return AgentTarget.DEV
        elif user_score > dev_score:
            return AgentTarget.USER
        else:
            # Default: if URL looks like dev environment, use dev; else user
            if url and self._is_dev_url(url):
                return AgentTarget.DEV
            return AgentTarget.USER

    def _check_explicit_command(self, query: str) -> Optional[AgentTarget]:
        """Check if the query contains an explicit slash command."""
        query_stripped = query.strip().lower()

        dev_commands = ["/debug", "/perf", "/screenshot", "/diff", "/console", "/audit", "/test", "/report"]
        user_commands = ["/guide", "/help", "/find", "/explain", "/steps"]

        for cmd in dev_commands:
            if query_stripped.startswith(cmd):
                return AgentTarget.DEV

        for cmd in user_commands:
            if query_stripped.startswith(cmd):
                return AgentTarget.USER

        return None

    def _compute_dev_score(
        self, query: str, url: Optional[str], headers: Optional[dict]
    ) -> float:
        """Compute the likelihood this is a dev query."""
        score = 0.0
        query_lower = query.lower()

        # Keyword matching
        for keyword in DEV_KEYWORDS:
            if keyword in query_lower:
                score += 1.0

        # URL signals
        if url:
            for pattern in DEV_URL_PATTERNS:
                if re.search(pattern, url):
                    score += 0.5

        # Header signals
        if headers:
            if headers.get("X-Debug"):
                score += 2.0
            if "developer" in headers.get("X-Astrafox-Mode", "").lower():
                score += 5.0

        # Code-like content in query
        if re.search(r'[{}\[\];=<>()]', query):
            score += 0.5
        if re.search(r'\.(js|ts|py|css|html|vue|jsx|tsx)', query):
            score += 1.0

        return score

    def _compute_user_score(self, query: str) -> float:
        """Compute the likelihood this is a user query."""
        score = 0.0
        query_lower = query.lower()

        for keyword in USER_KEYWORDS:
            if keyword in query_lower:
                score += 1.0

        # Question patterns (more likely user)
        if query_lower.startswith(("comment", "où", "est-ce", "c'est quoi", "pourquoi")):
            score += 1.5

        if "?" in query:
            score += 0.3

        # Absence of technical terms
        has_technical = any(kw in query_lower for kw in ["error", "bug", "console", "dom", "api"])
        if not has_technical:
            score += 0.5

        return score

    def _is_dev_url(self, url: str) -> bool:
        """Check if the URL looks like a development environment."""
        return any(re.search(p, url) for p in DEV_URL_PATTERNS)
