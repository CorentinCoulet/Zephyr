"""
Zephyr Intelligence Platform — Main API Server.
FastAPI application with REST endpoints and WebSocket support.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from config.providers import get_server_config
from api.routes.analyze import router as analyze_router
from api.routes.debug import router as debug_router
from api.routes.guide import router as guide_router
from api.routes.reports import router as reports_router
from api.routes.widget import router as widget_router
from api.routes.ci import router as ci_router
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
    description="🦊 Zephyr — Universal UI Intelligence Platform",
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
app.include_router(ci_router, prefix="/api", tags=["CI"])
app.include_router(ws_router, tags=["WebSocket"])


# --- Rate Limiting Middleware ---
_rate_limit_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter."""
    server_config = get_server_config()
    max_rpm = server_config.rate_limit.get("max_requests_per_minute", 30)

    # Skip rate limiting for health/status/static
    path = request.url.path
    if path.startswith("/api/health") or path.startswith("/api/status") or not path.startswith("/api/"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Clean old entries
    if client_ip in _rate_limit_store:
        _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < 60]
    else:
        _rate_limit_store[client_ip] = []

    if len(_rate_limit_store[client_ip]) >= max_rpm:
        return Response(
            content='{"error": "Rate limit exceeded", "retry_after": 60}',
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": "60"},
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)

# --- Static files (Zephyr UI) ---
ui_dist = Path(__file__).parent.parent / "zephyr_ui" / "dist"
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
        "theme": settings.zephyr_theme.value,
        "zephyr_version": settings.zephyr_version.value,
        "llm_provider": server_config.provider,
        "llm_model": server_config.model,
    }
