"""
Widget endpoints — Serves the embeddable SDK and handles widget-specific auth.
"""

from pathlib import Path

from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from config.settings import settings

router = APIRouter()

SDK_DIR = Path(__file__).parent.parent.parent / "sdk"


@router.get("/sdk/astrafox-widget.js")
async def serve_widget_js():
    """Serve the embeddable widget JavaScript file."""
    path = SDK_DIR / "astrafox-widget.js"
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

    html = f"""<!-- 🦊 Astrafox Widget -->
<script src="{base}/api/sdk/astrafox-widget.js"></script>
<script>
  AstrafoxWidget.init({{
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
    """Returns widget configuration (validates API key if set)."""
    expected = settings.widget_api_key
    if expected and x_api_key != expected:
        raise HTTPException(403, "Invalid API key")

    return {
        "personas": ["mascot", "spirit", "minimal", "futuristic"],
        "themes": ["dark", "light", "auto"],
        "features": ["chat", "guide", "search"],
        "default_language": "fr",
        "version": settings.app_version,
    }
