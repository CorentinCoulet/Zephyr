"""
Analyze endpoints — URL analysis, screenshots, and audits.
"""

from fastapi import APIRouter, Request

from api.models.requests import AnalyzeRequest, ScreenshotRequest, SetBaselineRequest
from api.models.responses import AnalyzeResponse, ScreenshotResponse, AstrafoxResponse
from core.browser_engine import VIEWPORTS

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(req: AnalyzeRequest, request: Request):
    """Analyze a URL: extract DOM, capture errors, UI issues, optional perf."""
    ctx_builder = request.app.state.context_builder
    session_mgr = request.app.state.session_manager

    session = session_mgr.get_or_create(req.session_id, target_url=req.url)

    context = await ctx_builder.build_dev_context(
        url=req.url,
        viewport=req.viewport,
        session_id=session.session_id,
        include_perf=req.include_perf,
    )

    session.add_page(req.url)
    session.cache_analysis("last_analysis", context)

    # Build scores summary
    scores = {}
    if "performance" in context:
        scores = context["performance"].get("scores", {})

    issues = {
        "console_errors": len(context.get("console_errors", [])),
        "network_errors": len(context.get("network_errors", [])),
        "contrast_issues": len(context.get("contrast_issues", [])),
        "overflow_issues": len(context.get("overflow_issues", [])),
    }

    return AnalyzeResponse(
        success=True,
        url=req.url,
        scores=scores,
        issues=issues,
        screenshot_path=context.get("screenshot_path", ""),
        session_id=session.session_id,
    )


@router.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshots(req: ScreenshotRequest, request: Request):
    """Capture screenshots at multiple viewports."""
    browser = request.app.state.context_builder.browser
    session_mgr = request.app.state.session_manager
    screenshot_mgr = request.app.state.context_builder.screenshot_mgr

    session = session_mgr.get_or_create(req.session_id)
    screenshots = {}

    for vp_name in req.viewports:
        vp = VIEWPORTS.get(vp_name)
        if not vp:
            continue

        page = await browser.navigate(req.url, viewport=vp)
        path = await screenshot_mgr.capture(
            page, label=vp_name, session_id=session.session_id
        )
        screenshots[vp_name] = path
        await page.close()

    return ScreenshotResponse(
        success=True,
        screenshots=screenshots,
        session_id=session.session_id,
    )


@router.post("/baseline", response_model=AstrafoxResponse)
async def set_baseline(req: SetBaselineRequest, request: Request):
    """Capture and store a visual baseline for regression testing."""
    browser = request.app.state.context_builder.browser
    visual_diff = request.app.state.context_builder

    vp = VIEWPORTS.get(req.viewport, VIEWPORTS["desktop"])
    page = await browser.navigate(req.url, viewport=vp)
    screenshot_bytes = await browser.screenshot(page)
    await page.close()

    from core.visual_diff import VisualDiff
    differ = VisualDiff()
    path = differ.capture_baseline(screenshot_bytes, req.name, req.viewport)

    return AstrafoxResponse(
        success=True,
        message=f"Baseline '{req.name}' saved at {path}",
        data={"path": path, "name": req.name, "viewport": req.viewport},
        expression="happy",
    )
