"""
LLM provider configuration for Astrafox Intelligence Platform.
Supports OpenAI, Anthropic, Ollama, and local models.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


class LLMConfig(BaseSettings):
    """LLM provider settings."""

    provider: LLMProvider = LLMProvider.OPENAI
    api_key: Optional[str] = None
    model: str = "gpt-4o"
    fallback_model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout: int = 30
    retry_count: int = 3

    # --- Anthropic specific ---
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # --- Ollama specific ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # --- Local model ---
    local_enabled: bool = False
    local_model_path: str = "./models/mistral-7b-instruct.gguf"
    local_context_length: int = 8192

    # --- Rate limiting ---
    max_requests_per_minute: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds

    model_config = {"env_prefix": "LLM_", "env_file": ".env"}


llm_config = LLMConfig()
