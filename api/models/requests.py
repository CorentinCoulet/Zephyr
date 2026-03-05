"""
Pydantic models for API requests.
"""

import ipaddress
import re
import socket

from pydantic import BaseModel, Field, field_validator
from typing import Optional


def _validate_url(url: str) -> str:
    """Validate that URL is a safe HTTP(S) URL (prevent SSRF)."""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("URL must start with http:// or https://")
    # Block dangerous schemes
    if re.match(r"^(file|ftp|data|javascript|vbscript|gopher):", url, re.IGNORECASE):
        raise ValueError("Invalid URL scheme")

    # Extract hostname and block internal/private IPs
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL must contain a hostname")

        # Allow configured target URL (dev server, Docker, etc.)
        from config.settings import settings
        _is_allowed_target = bool(
            settings.target_url and hostname in settings.target_url
        )

        # Block known dangerous internal hostnames (except allowed targets)
        _blocked_hosts = {"metadata.google.internal"}
        if hostname.lower() in _blocked_hosts and not _is_allowed_target:
            raise ValueError("Internal hostnames are not allowed")

        # Resolve hostname and check for private/reserved IPs
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for _, _, _, _, sockaddr in resolved:
                ip = ipaddress.ip_address(sockaddr[0])
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    if _is_allowed_target:
                        break  # Allow configured target
                    raise ValueError(
                        f"URL resolves to private/reserved IP ({ip}). "
                        "Internal network access is blocked."
                    )
        except socket.gaierror:
            pass  # DNS failure — let the browser handle it later

    except ValueError:
        raise
    except Exception:
        pass  # Parsing error — will fail later at navigation

    return url


class AnalyzeRequest(BaseModel):
    """Request to analyze a URL."""
    url: str = Field(..., description="Target URL to analyze", max_length=2048)
    viewport: Optional[str] = Field("desktop", description="Viewport name: mobile_s, mobile_m, tablet, desktop")
    include_perf: bool = Field(False, description="Include Lighthouse performance audit (slower)")
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class DebugRequest(BaseModel):
    """Request to debug a URL."""
    url: str = Field(..., description="Target URL to debug", max_length=2048)
    query: str = Field("", description="Optional debug question", max_length=2000)
    viewport: Optional[str] = Field("desktop", description="Viewport")
    include_perf: bool = Field(True, description="Include performance audit")
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class GuideRequest(BaseModel):
    """Request for user guidance."""
    url: str = Field(..., description="Current page URL", max_length=2048)
    query: str = Field(..., description="User's question or goal", max_length=2000)
    session_id: Optional[str] = Field(None, max_length=128)
    app_context: Optional[dict] = Field(None, description="Application context provided by integrator")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class ChatRequest(BaseModel):
    """Chat message from user."""
    message: str = Field(..., description="User message", max_length=4000)
    url: Optional[str] = Field(None, description="Current page URL", max_length=2048)
    mode: Optional[str] = Field(None, description="Force mode: dev or user")
    session_id: Optional[str] = Field(None, max_length=128)
    app_context: Optional[dict] = Field(None, description="Application context provided by integrator")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_url(v)
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str | None) -> str | None:
        if v is not None and v not in ("dev", "user"):
            raise ValueError("mode must be 'dev' or 'user'")
        return v


class ScreenshotRequest(BaseModel):
    """Request for screenshots."""
    url: str = Field(..., description="URL to screenshot", max_length=2048)
    viewports: list[str] = Field(
        default=["mobile_m", "tablet", "desktop"],
        description="List of viewport names"
    )
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class DiffRequest(BaseModel):
    """Visual diff request."""
    url: str = Field(..., description="URL to compare", max_length=2048)
    baseline_name: str = Field(..., description="Name of the baseline to compare against", max_length=200)
    viewport: str = Field("desktop", description="Viewport name")
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class SetBaselineRequest(BaseModel):
    """Store a new baseline."""
    url: str = Field(..., description="URL to capture as baseline", max_length=2048)
    name: str = Field(..., description="Name for this baseline", max_length=200)
    viewport: str = Field("desktop", description="Viewport name")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)
