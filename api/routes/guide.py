"""
Guide endpoints — User Agent interactions.
"""

from fastapi import APIRouter, Request

from api.models.requests import GuideRequest, ChatRequest
from api.models.responses import GuideResponse, AstrafoxResponse

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


@router.post("/chat/user", response_model=AstrafoxResponse)
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

    response = await user_agent.chat(req.message, context, session.session_id)

    session.add_message("user", req.message)
    session.add_message("assistant", response.message)

    return AstrafoxResponse(
        success=response.success,
        message=response.message,
        data=response.data,
        expression=response.expression,
        suggestions=response.suggestions,
        session_id=session.session_id,
    )
