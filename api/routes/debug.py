"""
Debug endpoints — Dev Agent interactions.
"""

from fastapi import APIRouter, Request

from api.models.requests import DebugRequest, DiffRequest, ChatRequest
from api.models.responses import DebugResponse, DiffResponse, AstrafoxResponse
from orchestrator.router import AgentTarget

router = APIRouter()


@router.post("/debug", response_model=DebugResponse)
async def debug_url(req: DebugRequest, request: Request):
    """Run Dev Agent debug analysis on a URL."""
    ctx_builder = request.app.state.context_builder
    session_mgr = request.app.state.session_manager
    dev_agent = request.app.state.dev_agent

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)
    session.mode = "dev"

    # Build context
    context = await ctx_builder.build_dev_context(
        url=req.url,
        viewport=req.viewport,
        session_id=session.session_id,
        include_perf=req.include_perf,
    )

    session.add_page(req.url)
    session.cache_analysis("last_debug", context)

    # Run Dev Agent
    query = req.query or f"Analyse de debug complète pour {req.url}"
    response = await dev_agent.chat(query, context, session.session_id)

    session.add_message("user", query)
    session.add_message("assistant", response.message)

    return DebugResponse(
        success=response.success,
        url=req.url,
        diagnosis=response.message,
        issues_count=response.data.get("issues_found", 0),
        data=response.data,
        expression=response.expression,
        suggestions=response.suggestions,
        session_id=session.session_id,
    )


@router.post("/diff", response_model=DiffResponse)
async def visual_diff(req: DiffRequest, request: Request):
    """Compare current page against a stored baseline."""
    browser = request.app.state.context_builder.browser
    session_mgr = request.app.state.session_manager

    from core.browser_engine import VIEWPORTS
    from core.visual_diff import VisualDiff

    session = session_mgr.get_or_create(req.session_id)

    vp = VIEWPORTS.get(req.viewport, VIEWPORTS["desktop"])
    page = await browser.navigate(req.url, viewport=vp)
    current_bytes = await browser.screenshot(page)
    await page.close()

    differ = VisualDiff()
    result = differ.compare_with_baseline(
        current_bytes, req.baseline_name, req.viewport
    )

    diff_path = ""
    if result.diff_image:
        diff_path = differ.save_diff_image(
            result,
            f"reports/diffs/{req.baseline_name}_{req.viewport}_diff.png"
        ) or ""

    return DiffResponse(
        success=True,
        match=result.match,
        mismatch_percentage=result.mismatch_percentage,
        diff_image_path=diff_path,
        session_id=session.session_id,
    )


@router.post("/chat/dev", response_model=AstrafoxResponse)
async def chat_dev(req: ChatRequest, request: Request):
    """Send a message to the Dev Agent."""
    dev_agent = request.app.state.dev_agent
    session_mgr = request.app.state.session_manager
    ctx_builder = request.app.state.context_builder

    session = session_mgr.get_or_create(req.session_id)
    session.mode = "dev"

    # Get context if URL provided
    context = {}
    if req.url:
        cached = session.get_cached("last_debug")
        if cached and cached.get("url") == req.url:
            context = cached
        else:
            context = await ctx_builder.build_dev_context(
                url=req.url, session_id=session.session_id
            )

    response = await dev_agent.chat(req.message, context, session.session_id)

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
