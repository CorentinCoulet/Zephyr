"""
Base Agent — Abstract base class for all Astrafox AI agents.
Provides common LLM interaction, context management, and reporting.

Uses the provider system from config/providers.py which reads
astrafox.server.yaml for LLM configuration.
"""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

# New provider system (reads astrafox.server.yaml)
from config.providers import get_provider, get_server_config, LLMProviderBase

# Backward compat: still importable but no longer used internally
try:
    from config.llm_config import llm_config, LLMProvider
except ImportError:
    llm_config = None
    LLMProvider = None


@dataclass
class AgentMessage:
    """A message in the agent conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class AgentResponse:
    """Structured response from an agent."""
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    expression: str = "neutral"  # Astrafox expression to display
    session_id: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "suggestions": self.suggestions,
            "expression": self.expression,
            "session_id": self.session_id,
        }


class BaseAgent(ABC):
    """Abstract base class for Astrafox AI agents."""

    agent_name: str = "base"
    agent_mode: str = "generic"  # "dev" or "user"

    def __init__(self):
        self._conversations: dict[str, list[AgentMessage]] = {}
        self._provider: LLMProviderBase = get_provider()
        self._server_config = get_server_config()
        self._http_client = httpx.AsyncClient(
            timeout=self._server_config.provider_config.get("timeout", 30)
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    @abstractmethod
    async def process(
        self, query: str, context: dict, session_id: str
    ) -> AgentResponse:
        """Process a user query with the given context."""
        ...

    async def chat(
        self,
        query: str,
        context: dict,
        session_id: Optional[str] = None,
    ) -> AgentResponse:
        """High-level chat entry point."""
        sid = session_id or str(uuid.uuid4())

        # Initialize conversation if new
        if sid not in self._conversations:
            self._conversations[sid] = [
                AgentMessage(role="system", content=self.get_system_prompt())
            ]

        # Add user message
        self._conversations[sid].append(
            AgentMessage(role="user", content=query, metadata={"context_keys": list(context.keys())})
        )

        # Process via concrete agent
        response = await self.process(query, context, sid)
        response.session_id = sid

        # Store assistant reply
        self._conversations[sid].append(
            AgentMessage(role="assistant", content=response.message)
        )

        return response

    async def call_llm(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call the configured LLM provider.

        Uses the provider system from config/providers.py which reads
        astrafox.server.yaml. Supports: github-copilot, claude, openai, ollama.
        """
        return await self._provider.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ── Legacy provider methods (kept for backward compat) ──────

    async def _call_openai(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        """Call OpenAI-compatible API. (Legacy — use call_llm instead)"""
        response = await self._http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {llm_config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": llm_config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _call_anthropic(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        """Call Anthropic Claude API. (Legacy — use call_llm instead)"""
        # Extract system message
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        response = await self._http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": llm_config.anthropic_api_key or llm_config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": llm_config.anthropic_model,
                "system": system_msg,
                "messages": chat_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    async def _call_ollama(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        """Call Ollama local API. (Legacy — use call_llm instead)"""
        response = await self._http_client.post(
            f"{llm_config.ollama_base_url}/api/chat",
            json={
                "model": llm_config.ollama_model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def get_conversation(self, session_id: str) -> list[AgentMessage]:
        """Get the conversation history for a session."""
        return self._conversations.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Clear a conversation session."""
        self._conversations.pop(session_id, None)

    async def close(self) -> None:
        """Clean up resources."""
        await self._http_client.aclose()
        await self._provider.close()
