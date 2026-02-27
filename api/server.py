"""
Astrafox Intelligence Platform — Main API Server.
FastAPI application with REST endpoints and WebSocket support.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from config.providers import get_server_config
from api.routes.analyze import router as analyze_router
from api.routes.debug import router as debug_router
from api.routes.guide import router as guide_router
from api.routes.reports import router as reports_router
from api.routes.widget import router as widget_router
from api.websocket.chat_ws import router as ws_router

from orchestrator.context_builder import ContextBuilder
from orchestrator.session_manager import SessionManager
from orchestrator.router import Router
from orchestrator.prompt_engine import PromptEngine
from agents.dev_agent import DevAgent
from agents.user_agent import UserAgent


# --- Shared state (available via app.state) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    app.state.session_manager = SessionManager()
    app.state.router = Router()
    app.state.prompt_engine = PromptEngine()
    app.state.context_builder = ContextBuilder()
    app.state.dev_agent = DevAgent()
    app.state.user_agent = UserAgent()

    yield

    # Shutdown
    await app.state.context_builder.close()
    await app.state.dev_agent.close()
    await app.state.user_agent.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="🦊 Astrafox — Universal UI Intelligence Platform",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(analyze_router, prefix="/api", tags=["Analyze"])
app.include_router(debug_router, prefix="/api", tags=["Debug"])
app.include_router(guide_router, prefix="/api", tags=["Guide"])
app.include_router(reports_router, prefix="/api", tags=["Reports"])
app.include_router(widget_router, prefix="/api", tags=["Widget SDK"])
app.include_router(ws_router, tags=["WebSocket"])

# --- Static files (Astrafox UI) ---
ui_dist = Path(__file__).parent.parent / "astrafox_ui" / "dist"
if ui_dist.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "name": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/status")
async def status():
    """Platform status with session count and provider info."""
    server_config = get_server_config()
    return {
        "status": "running",
        "active_sessions": app.state.session_manager.get_session_count(),
        "target_url": settings.target_url,
        "theme": settings.astrafox_theme.value,
        "astrafox_version": settings.astrafox_version.value,
        "llm_provider": server_config.provider,
        "llm_model": server_config.model,
    }
