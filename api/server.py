"""
Zephyr Intelligence Platform — Main API Server.
FastAPI application with REST endpoints and WebSocket support.
"""

import logging
import uuid
from contextvars import ContextVar
from contextlib import asynccontextmanager
from pathlib import Path
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from config.logging_config import setup_logging
from config.providers import get_server_config, get_provider
from api.routes.analyze import router as analyze_router
from api.routes.debug import router as debug_router
from api.routes.guide import router as guide_router
from api.routes.reports import router as reports_router
from api.routes.widget import router as widget_router
from api.routes.ci import router as ci_router
from api.routes.compliance import router as compliance_router
from api.websocket.chat_ws import router as ws_router

from orchestrator.context_builder import ContextBuilder
from orchestrator.session_manager import SessionManager
from orchestrator.router import Router
from orchestrator.prompt_engine import PromptEngine
from agents.dev_agent import DevAgent
from agents.user_agent import UserAgent

logger = logging.getLogger("zephyr")

# --- Correlation ID context variable ---
# Accessible from any async code within a request via request_id_var.get()
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# --- Initialize structured logging ---
setup_logging(
    level="DEBUG" if settings.debug else "INFO",
    json_format=not settings.debug,
)


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

    # ── LLM Provider healthcheck ──
    server_config = get_server_config()
    provider_name = server_config.provider
    logger.info(f"LLM provider: {provider_name} (model: {server_config.model})")

    try:
        provider = get_provider()
        test_response = await provider.chat(
            [{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        if test_response:
            logger.info(f"LLM healthcheck OK — provider '{provider_name}' responded")
        else:
            logger.warning(f"LLM healthcheck WARNING — provider '{provider_name}' returned empty response")
    except Exception as e:
        logger.warning(
            f"LLM healthcheck FAILED — provider '{provider_name}' is not reachable: {e}. "
            f"Chat features will fail until the provider is available."
        )

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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# --- Global Exception Handler ---
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a clean error response."""
    req_id = request_id_var.get()
    logger.error(f"[{req_id}] Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "request_id": req_id,
        },
    )


from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean validation errors."""
    # Sanitize error dicts — pydantic v2 may include non-serializable ctx values
    clean_errors = []
    for err in exc.errors():
        clean = {
            "type": err.get("type", ""),
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "input": str(err.get("input", ""))[:200],
        }
        clean_errors.append(clean)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "detail": clean_errors,
        },
    )

# --- CORS ---
server_config = get_server_config()
_cors_origins = server_config.cors_origins if server_config.cors_origins != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],  # Disable credentials with wildcard
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
app.include_router(compliance_router, prefix="/api", tags=["Compliance"])
app.include_router(ws_router, tags=["WebSocket"])


# --- Security Headers Middleware ---
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'"
    )
    return response


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
        if not _rate_limit_store[client_ip]:
            del _rate_limit_store[client_ip]

    if client_ip not in _rate_limit_store:
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


# --- API Key Authentication Middleware ---
@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    """Optional API key authentication for all API endpoints."""
    import hmac
    expected_key = settings.widget_api_key
    if not expected_key:
        return await call_next(request)

    path = request.url.path
    # Skip auth for health, docs, static, and public endpoints
    skip_paths = ("/api/health", "/api/status", "/api/docs", "/api/redoc",
                   "/api/openapi.json", "/api/sdk")
    if not path.startswith("/api/") or any(path.startswith(p) for p in skip_paths):
        return await call_next(request)

    provided_key = (
        request.headers.get("x-api-key", "")
        or request.query_params.get("api_key", "")
    )
    if not provided_key or not hmac.compare_digest(
        provided_key.encode(), expected_key.encode()
    ):
        return Response(
            content='{"error": "Invalid or missing API key"}',
            status_code=401,
            media_type="application/json",
        )

    return await call_next(request)

# --- Correlation ID Middleware ---
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Assign a unique request ID for tracing and include it in logs/response."""
    # Accept client-provided ID or generate a new one
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    token = request_id_var.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_var.reset(token)

# --- Static files (Zephyr UI) ---
ui_dist = Path(__file__).parent.parent / "zephyr_ui" / "dist"
if ui_dist.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")


@app.get("/api/health")
async def health():
    """Health check endpoint with component status."""
    checks = {
        "api": "ok",
        "browser": "unknown",
        "llm_provider": "unknown",
    }

    # Check browser engine
    try:
        browser = app.state.context_builder.browser
        checks["browser"] = "ok" if browser else "not_initialized"
    except Exception:
        checks["browser"] = "error"

    # Check LLM provider availability
    try:
        server_cfg = get_server_config()
        checks["llm_provider"] = f"ok ({server_cfg.provider})"
    except Exception:
        checks["llm_provider"] = "error"

    overall = "ok" if all("ok" in str(v) for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "name": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
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
