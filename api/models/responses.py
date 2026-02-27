"""
Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional


class AstrafoxResponse(BaseModel):
    """Standard response wrapper."""
    success: bool = True
    message: str = ""
    data: dict = Field(default_factory=dict)
    expression: str = "neutral"
    session_id: str = ""
    suggestions: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    """Response from URL analysis."""
    success: bool = True
    url: str = ""
    scores: dict = Field(default_factory=dict)
    issues: dict = Field(default_factory=dict)
    screenshot_path: str = ""
    session_id: str = ""


class DebugResponse(BaseModel):
    """Response from debug analysis."""
    success: bool = True
    url: str = ""
    diagnosis: str = ""
    issues_count: int = 0
    data: dict = Field(default_factory=dict)
    expression: str = "neutral"
    suggestions: list[str] = Field(default_factory=list)
    session_id: str = ""


class GuideResponse(BaseModel):
    """Response for user guidance."""
    success: bool = True
    guide: str = ""
    steps: list[str] = Field(default_factory=list)
    expression: str = "speaking"
    suggestions: list[str] = Field(default_factory=list)
    session_id: str = ""


class ScreenshotResponse(BaseModel):
    """Response with captured screenshots."""
    success: bool = True
    screenshots: dict[str, str] = Field(default_factory=dict)
    session_id: str = ""


class DiffResponse(BaseModel):
    """Visual diff response."""
    success: bool = True
    match: bool = True
    mismatch_percentage: float = 0.0
    diff_image_path: str = ""
    session_id: str = ""


class SessionResponse(BaseModel):
    """Session information."""
    session_id: str
    mode: str = "auto"
    target_url: str = ""
    message_count: int = 0
