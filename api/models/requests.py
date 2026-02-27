"""
Pydantic models for API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request to analyze a URL."""
    url: str = Field(..., description="Target URL to analyze")
    viewport: Optional[str] = Field("desktop", description="Viewport name: mobile_s, mobile_m, tablet, desktop")
    include_perf: bool = Field(False, description="Include Lighthouse performance audit (slower)")
    session_id: Optional[str] = None


class DebugRequest(BaseModel):
    """Request to debug a URL."""
    url: str = Field(..., description="Target URL to debug")
    query: str = Field("", description="Optional debug question")
    viewport: Optional[str] = Field("desktop", description="Viewport")
    include_perf: bool = Field(True, description="Include performance audit")
    session_id: Optional[str] = None


class GuideRequest(BaseModel):
    """Request for user guidance."""
    url: str = Field(..., description="Current page URL")
    query: str = Field(..., description="User's question or goal")
    session_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat message from user."""
    message: str = Field(..., description="User message")
    url: Optional[str] = Field(None, description="Current page URL")
    mode: Optional[str] = Field(None, description="Force mode: dev or user")
    session_id: Optional[str] = None


class ScreenshotRequest(BaseModel):
    """Request for screenshots."""
    url: str = Field(..., description="URL to screenshot")
    viewports: list[str] = Field(
        default=["mobile_m", "tablet", "desktop"],
        description="List of viewport names"
    )
    session_id: Optional[str] = None


class DiffRequest(BaseModel):
    """Visual diff request."""
    url: str = Field(..., description="URL to compare")
    baseline_name: str = Field(..., description="Name of the baseline to compare against")
    viewport: str = Field("desktop", description="Viewport name")
    session_id: Optional[str] = None


class SetBaselineRequest(BaseModel):
    """Store a new baseline."""
    url: str = Field(..., description="URL to capture as baseline")
    name: str = Field(..., description="Name for this baseline")
    viewport: str = Field("desktop", description="Viewport name")
