"""
Guide endpoints — User Agent interactions.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

from api.models.requests import GuideRequest, ChatRequest
from api.models.responses import GuideResponse, ZephyrResponse

router = APIRouter()


@router.post("/guide", response_model=GuideResponse)
async def guide_user(req: GuideRequest, request: Request):
    """Get step-by-step guidance from the User Agent."""
    ctx_builder = request.app.state.context_builder
    session_mgr = request.app.state.session_manager
    user_agent = request.app.state.user_agent

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)
    session.mode = "user"
    session.add_page(req.url)

    # Build user context
    context = await ctx_builder.build_user_context(
        url=req.url,
        session_id=session.session_id,
        pages_visited=session.pages_visited,
    )
    if session.user_preferences:
        context["user_preferences"] = session.user_preferences

    # Inject app context (from request or session)
    app_ctx = req.app_context or session.app_context
    if app_ctx:
        session.app_context = app_ctx
        context["app_context"] = app_ctx

    response = await user_agent.chat(req.query, context, session.session_id)

    session.add_message("user", req.query)
    session.add_message("assistant", response.message)

    return GuideResponse(
        success=response.success,
        guide=response.message,
        steps=response.data.get("guide_steps", []),
        expression=response.expression,
        suggestions=response.suggestions,
        session_id=session.session_id,
    )


@router.post("/guide/onboarding", response_model=GuideResponse)
async def onboarding(req: GuideRequest, request: Request):
    """Generate an onboarding tour for a new user."""
    ctx_builder = request.app.state.context_builder
    session_mgr = request.app.state.session_manager
    user_agent = request.app.state.user_agent

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)
    session.mode = "user"

    context = await ctx_builder.build_user_context(
        url=req.url, session_id=session.session_id
    )
    if session.user_preferences:
        context["user_preferences"] = session.user_preferences

    # Inject app context for richer onboarding
    app_ctx = req.app_context or session.app_context
    if app_ctx:
        session.app_context = app_ctx
        context["app_context"] = app_ctx

    # Try building a sitemap
    try:
        sitemap = await ctx_builder.build_sitemap(req.url, max_pages=15)
        context["sitemap"] = sitemap
    except Exception:
        pass

    response = await user_agent.generate_onboarding(context)

    return GuideResponse(
        success=response.success,
        guide=response.message,
        steps=response.data.get("guide_steps", []),
        expression="happy",
        suggestions=response.suggestions,
        session_id=session.session_id,
    )


@router.post("/guide/find", response_model=GuideResponse)
async def find_feature(req: GuideRequest, request: Request):
    """Find a specific feature in the app."""
    ctx_builder = request.app.state.context_builder
    session_mgr = request.app.state.session_manager
    user_agent = request.app.state.user_agent

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)

    context = await ctx_builder.build_user_context(
        url=req.url, session_id=session.session_id
    )

    response = await user_agent.find_feature(req.query, context)

    return GuideResponse(
        success=response.success,
        guide=response.message,
        steps=response.data.get("guide_steps", []),
        expression=response.expression,
        suggestions=response.suggestions,
        session_id=session.session_id,
    )


@router.post("/chat/user", response_model=ZephyrResponse)
async def chat_user(req: ChatRequest, request: Request):
    """Send a message to the User Agent."""
    user_agent = request.app.state.user_agent
    session_mgr = request.app.state.session_manager
    ctx_builder = request.app.state.context_builder

    session = session_mgr.get_or_create(req.session_id)
    session.mode = "user"

    context = {}
    if req.url:
        context = await ctx_builder.build_user_context(
            url=req.url,
            session_id=session.session_id,
            pages_visited=session.pages_visited,
        )

    # Inject app context (from request or session)
    app_ctx = getattr(req, 'app_context', None) or session.app_context
    if app_ctx:
        session.app_context = app_ctx
        context["app_context"] = app_ctx

    response = await user_agent.chat(req.message, context, session.session_id)

    session.add_message("user", req.message)
    session.add_message("assistant", response.message)

    return ZephyrResponse(
        success=response.success,
        message=response.message,
        data=response.data,
        expression=response.expression,
        suggestions=response.suggestions,
        session_id=session.session_id,
    )


# ── New endpoints ───────────────────────────────────────


class FrictionRequest(BaseModel):
    url: str = Field(..., description="Page URL to analyze for friction")
    session_id: Optional[str] = None


class TooltipRequest(BaseModel):
    url: str = Field(..., description="Page URL to generate tooltips for")
    max_tooltips: int = Field(10, description="Maximum number of tooltips")
    session_id: Optional[str] = None


class OnboardingStepRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    step_id: str = Field(..., description="Step identifier to mark complete")


@router.post("/guide/friction")
async def analyze_friction(req: FrictionRequest, request: Request):
    """Proactively detect UX friction points on a page."""
    ctx_builder = request.app.state.context_builder
    user_agent = request.app.state.user_agent
    session_mgr = request.app.state.session_manager

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)

    context = await ctx_builder.build_user_context(
        url=req.url, session_id=session.session_id
    )

    result = await user_agent.analyze_friction(context)
    return {
        "success": True,
        "url": req.url,
        "friction_points": result,
        "session_id": session.session_id,
    }


@router.post("/guide/tooltips")
async def page_tooltips(req: TooltipRequest, request: Request):
    """Generate contextual tooltips for all interactive elements on a page."""
    ctx_builder = request.app.state.context_builder
    user_agent = request.app.state.user_agent
    session_mgr = request.app.state.session_manager

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)

    context = await ctx_builder.build_user_context(
        url=req.url, session_id=session.session_id
    )

    tooltips = await user_agent.generate_page_tooltips(context, max_tooltips=req.max_tooltips)
    return {
        "success": True,
        "url": req.url,
        "tooltips": tooltips,
        "session_id": session.session_id,
    }


@router.post("/guide/onboarding/step")
async def mark_onboarding_step_endpoint(req: OnboardingStepRequest, request: Request):
    """Mark an onboarding step as completed."""
    user_agent = request.app.state.user_agent

    progress = user_agent.mark_onboarding_step(req.session_id, req.step_id)

    return {
        "success": True,
        "session_id": req.session_id,
        "step_id": req.step_id,
        "progress": progress,
    }


@router.get("/guide/onboarding/progress/{session_id}")
async def onboarding_progress(session_id: str, request: Request):
    """Get onboarding progress for a session."""
    user_agent = request.app.state.user_agent

    progress = user_agent.get_onboarding_progress(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "progress": progress,
    }


@router.delete("/guide/onboarding/progress/{session_id}")
async def reset_onboarding_endpoint(session_id: str, request: Request):
    """Reset onboarding progress for a session."""
    user_agent = request.app.state.user_agent

    user_agent.reset_onboarding(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "message": "Onboarding progress reset",
    }


@router.put("/guide/preferences")
async def update_user_preferences(request: Request):
    """Update user preferences for a session (language, verbosity, etc.)."""
    body = await request.json()
    session_id = body.get("session_id")
    preferences = body.get("preferences", {})

    if not session_id:
        return {"success": False, "error": "session_id required"}

    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    allowed = {
        "language", "verbosity", "expertise_level",
        "accessibility_mode", "notification_level",
    }
    filtered = {k: v for k, v in preferences.items() if k in allowed}
    session.user_preferences.update(filtered)

    return {
        "success": True,
        "session_id": session_id,
        "preferences": session.user_preferences,
    }


@router.put("/guide/app-context")
async def set_app_context(request: Request):
    """Set or update the application context for a session.

    The application context is provided by the developer who integrates Zephyr.
    It gives the chatbot pre-built knowledge about the app (features, FAQ,
    terminology, workflows) so it can answer user questions faster.
    """
    body = await request.json()
    session_id = body.get("session_id")
    app_context = body.get("app_context", {})

    if not session_id:
        return {"success": False, "error": "session_id required"}
    if not app_context:
        return {"success": False, "error": "app_context required"}

    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    session.app_context = app_context

    return {
        "success": True,
        "session_id": session_id,
        "message": "App context updated",
        "context_keys": list(app_context.keys()),
    }


@router.get("/guide/app-context/{session_id}")
async def get_app_context(session_id: str, request: Request):
    """Get the current application context for a session."""
    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    return {
        "success": True,
        "session_id": session_id,
        "app_context": session.app_context,
    }
