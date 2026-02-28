"""
🦊 Zephyr — LLM Provider System

Unified provider interface for multiple LLM backends.
Reads configuration from zephyr.server.yaml and environment variables.

Supported providers:
  - github-copilot  (GitHub Models API, OpenAI-compatible)
  - claude           (Anthropic Claude API)
  - openai           (OpenAI API)
  - ollama           (Local Ollama inference)
"""

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml


# ── Configuration loader ─────────────────────────────────────

def _resolve_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} with environment variable values."""
    if not isinstance(value, str):
        return value

    def replacer(match):
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(r"\$\{(\w+)\}", replacer, value)


def _resolve_config_values(obj: Any) -> Any:
    """Recursively resolve ${ENV_VAR} references in config values."""
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    elif isinstance(obj, dict):
        return {k: _resolve_config_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_config_values(item) for item in obj]
    return obj


@dataclass
class ServerConfig:
    """Parsed server configuration."""

    provider: str
    provider_config: dict
    server: dict
    target: dict
    dev: dict
    sessions: dict
    rate_limit: dict
    raw: dict  # Full YAML

    @property
    def model(self) -> str:
        return self.provider_config.get("model", "gpt-4o")

    @property
    def max_tokens(self) -> int:
        return self.provider_config.get("max_tokens", 4096)

    @property
    def temperature(self) -> float:
        return self.provider_config.get("temperature", 0.3)


def load_server_config(path: Optional[str] = None) -> ServerConfig:
    """
    Load zephyr.server.yaml configuration.

    Search order:
      1. Explicit path argument
      2. ZEPHYR_CONFIG env var
      3. ./zephyr.server.yaml (cwd)
      4. ../zephyr.server.yaml (parent)
    """
    search_paths = []

    if path:
        search_paths.append(Path(path))

    env_path = os.environ.get("ZEPHYR_CONFIG")
    if env_path:
        search_paths.append(Path(env_path))

    search_paths.extend([
        Path.cwd() / "zephyr.server.yaml",
        Path.cwd().parent / "zephyr.server.yaml",
        Path(__file__).parent.parent / "zephyr.server.yaml",
    ])

    config_path = None
    for p in search_paths:
        if p.exists():
            config_path = p
            break

    if config_path is None:
        # Fall back to defaults
        return _default_config()

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    raw = _resolve_config_values(raw)
    provider_name = raw.get("provider", "openai")
    provider_config = raw.get(provider_name, {})

    return ServerConfig(
        provider=provider_name,
        provider_config=provider_config,
        server=raw.get("server", {}),
        target=raw.get("target", {}),
        dev=raw.get("dev", {}),
        sessions=raw.get("sessions", {}),
        rate_limit=raw.get("rate_limit", {}),
        raw=raw,
    )


def _default_config() -> ServerConfig:
    """Default configuration when no YAML file found."""
    return ServerConfig(
        provider="openai",
        provider_config={
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.3,
        },
        server={"host": "0.0.0.0", "port": 8000, "debug": False},
        target={"url": "http://localhost:3000"},
        dev={"enabled": True},
        sessions={"timeout": 1800, "max_concurrent": 50},
        rate_limit={"max_requests_per_minute": 30},
        raw={},
    )


# ── Provider interface ───────────────────────────────────────

class LLMProviderBase(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: dict, http_client: Optional[httpx.AsyncClient] = None):
        self.config = config
        self._client = http_client or httpx.AsyncClient(timeout=config.get("timeout", 30))

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send chat messages and return the assistant's reply."""
        ...

    async def close(self):
        await self._client.aclose()


class GitHubCopilotProvider(LLMProviderBase):
    """
    GitHub Models API — OpenAI-compatible endpoint.
    Uses a GitHub Personal Access Token (PAT) for authentication.
    Works with GitHub Copilot subscriptions.
    """

    async def chat(self, messages, temperature=None, max_tokens=None) -> str:
        endpoint = self.config.get("endpoint", "https://models.inference.ai.azure.com")
        token = self.config.get("token", os.environ.get("GITHUB_TOKEN", ""))
        model = self.config.get("model", "gpt-4o")

        response = await self._client.post(
            f"{endpoint}/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature or self.config.get("temperature", 0.3),
                "max_tokens": max_tokens or self.config.get("max_tokens", 4096),
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class ClaudeProvider(LLMProviderBase):
    """Anthropic Claude API provider."""

    async def chat(self, messages, temperature=None, max_tokens=None) -> str:
        api_key = self.config.get("api_key", os.environ.get("ANTHROPIC_API_KEY", ""))
        model = self.config.get("model", "claude-sonnet-4-20250514")

        # Claude expects system message separated
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        response = await self._client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "system": system_msg,
                "messages": chat_messages,
                "temperature": temperature or self.config.get("temperature", 0.3),
                "max_tokens": max_tokens or self.config.get("max_tokens", 4096),
            },
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]


class OpenAIProvider(LLMProviderBase):
    """OpenAI API provider."""

    async def chat(self, messages, temperature=None, max_tokens=None) -> str:
        api_key = self.config.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        model = self.config.get("model", "gpt-4o")

        response = await self._client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature or self.config.get("temperature", 0.3),
                "max_tokens": max_tokens or self.config.get("max_tokens", 4096),
            },
        )
        response.raise_for_status()
        data = response.json()

        # Support fallback model on specific errors
        if "error" in data:
            fallback = self.config.get("fallback_model")
            if fallback:
                response = await self._client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": fallback,
                        "messages": messages,
                        "temperature": temperature or self.config.get("temperature", 0.3),
                        "max_tokens": max_tokens or self.config.get("max_tokens", 4096),
                    },
                )
                response.raise_for_status()
                data = response.json()

        return data["choices"][0]["message"]["content"]


class OllamaProvider(LLMProviderBase):
    """Ollama local inference provider."""

    async def chat(self, messages, temperature=None, max_tokens=None) -> str:
        base_url = self.config.get("base_url", "http://localhost:11434")
        model = self.config.get("model", "llama3")

        response = await self._client.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "options": {
                    "temperature": temperature or self.config.get("temperature", 0.3),
                    "num_predict": max_tokens or self.config.get("max_tokens", 4096),
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


# ── Provider registry ────────────────────────────────────────

PROVIDERS: dict[str, type[LLMProviderBase]] = {
    "github-copilot": GitHubCopilotProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def create_provider(config: ServerConfig) -> LLMProviderBase:
    """
    Create the appropriate LLM provider from server config.

    Usage:
        config = load_server_config()
        provider = create_provider(config)
        reply = await provider.chat([{"role": "user", "content": "Hello"}])
    """
    provider_cls = PROVIDERS.get(config.provider)
    if provider_cls is None:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider '{config.provider}'. "
            f"Available: {available}"
        )
    return provider_cls(config.provider_config)


# ── Singleton for app-wide use ───────────────────────────────

_server_config: Optional[ServerConfig] = None
_provider: Optional[LLMProviderBase] = None


def get_server_config() -> ServerConfig:
    """Get or load the singleton server config."""
    global _server_config
    if _server_config is None:
        _server_config = load_server_config()
    return _server_config


def get_provider() -> LLMProviderBase:
    """Get or create the singleton LLM provider."""
    global _provider
    if _provider is None:
        _provider = create_provider(get_server_config())
    return _provider


def reset_provider(config_path: Optional[str] = None) -> LLMProviderBase:
    """Reset and recreate provider (e.g. after config change)."""
    global _server_config, _provider
    _server_config = load_server_config(config_path)
    _provider = create_provider(_server_config)
    return _provider
