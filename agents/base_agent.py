"""
Base Agent — Abstract base class for all Zephyr AI agents.
Provides common LLM interaction, context management, and reporting.

Uses the provider system from config/providers.py which reads
zephyr.server.yaml for LLM configuration.
"""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

# Provider system (reads zephyr.server.yaml)
from config.providers import get_provider, get_server_config, LLMProviderBase


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
    expression: str = "neutral"  # Zephyr expression to display
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
    """Abstract base class for Zephyr AI agents."""

    agent_name: str = "base"
    agent_mode: str = "generic"  # "dev" or "user"
    MAX_CONVERSATION_LENGTH = 50  # Max messages per session before trimming

    def __init__(self):
        self._conversations: dict[str, list[AgentMessage]] = {}
        self._provider: LLMProviderBase = get_provider()
        self._server_config = get_server_config()

    def clear_session(self, session_id: str) -> None:
        """Remove conversation history for a session."""
        self._conversations.pop(session_id, None)

    @abstractmethod
    def get_system_prompt(self, preferences: Optional[dict] = None) -> str:
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

        # Trim conversation if too long (keep system prompt + last N messages)
        if len(self._conversations[sid]) > self.MAX_CONVERSATION_LENGTH:
            system_msg = self._conversations[sid][0]
            self._conversations[sid] = [system_msg] + self._conversations[sid][-self.MAX_CONVERSATION_LENGTH + 1:]

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
        zephyr.server.yaml. Supports: github-copilot, claude, openai, ollama.
        """
        return await self._provider.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def close(self) -> None:
        """Cleanup resources."""
        self._conversations.clear()
        await self._provider.close()

    def get_conversation(self, session_id: str) -> list[AgentMessage]:
        """Get the conversation history for a session."""
        return self._conversations.get(session_id, [])
