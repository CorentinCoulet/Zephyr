"""
Widget endpoints — Serves the embeddable SDK and handles widget-specific auth.
"""

import hmac
from pathlib import Path

from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional

from config.settings import settings

router = APIRouter()

SDK_DIR = Path(__file__).parent.parent.parent / "sdk"


def _validate_api_key(provided: Optional[str]) -> None:
    """Validate API key using timing-safe comparison."""
    expected = settings.widget_api_key
    if not expected:
        return  # No key configured = no auth
    if not provided or not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(403, "Invalid API key")


@router.get("/sdk/zephyr-widget.js")
async def serve_widget_js():
    """Serve the embeddable widget JavaScript file."""
    path = SDK_DIR / "zephyr-widget.js"
    if not path.exists():
        raise HTTPException(404, "Widget SDK not found")
    return FileResponse(
        path, media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/sdk/snippet")
async def widget_snippet():
    """Returns a ready-to-paste HTML snippet for embedding the widget."""
    base = settings.widget_base_url or f"http://{settings.host}:{settings.port}"
    api_key = settings.widget_api_key or ""

    html = f"""<!-- 🦊 Zephyr Widget -->
<script src="{base}/api/sdk/zephyr-widget.js"></script>
<script>
  ZephyrWidget.init({{
    server: '{base}',
    apiKey: '{api_key}',
    persona: 'minimal',     // "mascot" | "spirit" | "minimal" | "futuristic"
    theme: 'auto',           // "dark" | "light" | "auto"
    position: 'bottom-right',// "bottom-right" | "bottom-left" | "top-right" | "top-left"
    size: 'md',              // "sm" | "md" | "lg"
    language: 'fr',          // "fr" | "en"
    accentColor: '#ff6b35',
  }});
</script>"""

    return HTMLResponse(
        content=f"<pre>{html}</pre>",
        headers={"Access-Control-Allow-Origin": "*"},
    )


@router.get("/sdk/config")
async def widget_config(request: Request, x_api_key: str = Header(None)):
    """Returns full widget configuration (validates API key if set)."""
    _validate_api_key(x_api_key)

    return {
        "personas": ["mascot", "spirit", "minimal", "futuristic"],
        "themes": ["dark", "light", "auto"],
        "features": ["chat", "guide", "search", "onboarding", "tooltips"],
        "default_language": "fr",
        "version": settings.app_version,
        "modes": ["dev", "user", "auto"],
        "positions": ["bottom-right", "bottom-left", "top-right", "top-left"],
        "sizes": ["sm", "md", "lg"],
        "verbosity_levels": ["minimal", "normal", "detailed"],
        "expertise_levels": ["beginner", "intermediate", "advanced"],
        "keyboard_shortcuts": {
            "toggle": "Ctrl+Shift+Z",
            "search": "Ctrl+K",
            "close": "Escape",
        },
        "accessibility": {
            "high_contrast": False,
            "reduced_motion": False,
            "screen_reader_mode": False,
        },
    }


class WidgetPreferencesRequest(BaseModel):
    session_id: Optional[str] = None
    preferences: dict = Field(default_factory=dict)


@router.put("/sdk/config/preferences")
async def update_preferences(
    req: WidgetPreferencesRequest, request: Request, x_api_key: str = Header(None)
):
    """Update per-session widget preferences (language, verbosity, etc.)."""
    _validate_api_key(x_api_key)

    allowed_keys = {
        "language", "verbosity", "expertise_level", "theme",
        "persona", "position", "size", "accessibility_mode",
        "keyboard_shortcuts",
    }
    filtered = {k: v for k, v in req.preferences.items() if k in allowed_keys}

    if req.session_id:
        session_mgr = request.app.state.session_manager
        session = session_mgr.get_session(req.session_id)
        if session:
            session.user_preferences.update(filtered)

    return {"success": True, "preferences": filtered}
