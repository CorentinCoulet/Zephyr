"""
🦊 Zephyr MCP Server — Model Context Protocol server for IDE integration.

Exposes UI analysis tools (screenshot, DOM, console, performance, accessibility,
visual diff) as MCP tools that can be called by GitHub Copilot / Claude
for intelligent frontend debugging with visual context.

Usage:
  python -m mcp_server.server

Configure in VS Code settings.json or .vscode/mcp.json:
  {
    "servers": {
      "zephyr": {
        "command": "python",
        "args": ["-m", "mcp_server.server"],
        "cwd": "/path/to/ui-intelligence"
      }
    }
  }
"""

import asyncio
import base64
import json
import sys
import os
from pathlib import Path

# Add project root to path so we can import core modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP

# Load server config for target URL and dev settings
from config.providers import get_server_config as _get_cfg

_cfg = _get_cfg()

# ─── Server instance ──────────────────────────────────────────
mcp = FastMCP(
    "Zephyr UI Intelligence",
    instructions=(
        "Analyse visuelle d'interfaces web : screenshots, extraction DOM, "
        "erreurs console, audit performance, accessibilité, régression visuelle. "
        "Donne à Copilot/Claude des yeux sur l'UI.\n"
        f"Provider configuré: {_cfg.provider} | "
        f"Target: {_cfg.target.get('url', 'http://localhost:3000')}"
    ),
)

# ─── Lazy-loaded core modules ────────────────────────────────
_browser = None
_dom = None
_console = None
_screenshot = None
_perf = None
_visual_diff = None


async def _get_browser():
    global _browser
    if _browser is None:
        from core.browser_engine import BrowserEngine
        _browser = BrowserEngine()
    return _browser


async def _get_dom():
    global _dom
    if _dom is None:
        from core.dom_extractor import DOMExtractor
        _dom = DOMExtractor()
    return _dom


async def _get_console():
    global _console
    if _console is None:
        from core.console_capture import ConsoleCapture
        _console = ConsoleCapture()
    return _console


async def _get_screenshot():
    global _screenshot
    if _screenshot is None:
        from core.screenshot_manager import ScreenshotManager
        _screenshot = ScreenshotManager()
    return _screenshot


async def _get_perf():
    global _perf
    if _perf is None:
        from core.perf_analyzer import PerfAnalyzer
        _perf = PerfAnalyzer()
    return _perf


# ═══════════════════════════════════════════════════════════════
# TOOL: capture_screenshot
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def capture_screenshot(
    url: str,
    viewport: str = "desktop",
    full_page: bool = True,
) -> str:
    """
    Capture a screenshot of a web page and return it as base64.

    Use this to visually inspect a page, check layout, see the current
    state of UI elements, or identify visual bugs.

    Args:
        url: Full URL to capture (e.g., "http://localhost:3000/dashboard")
        viewport: "mobile_s" (320px) | "mobile_m" (375px) | "tablet" (768px) | "desktop" (1440px) | "4k" (2560px)
        full_page: True for full page capture, False for viewport only
    """
    from core.browser_engine import VIEWPORTS

    browser = await _get_browser()
    vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])
    page = await browser.navigate(url, viewport=vp)

    screenshot_bytes = await browser.screenshot(page, full_page=full_page)
    await page.close()

    b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

    return json.dumps({
        "status": "ok",
        "url": url,
        "viewport": viewport,
        "resolution": f"{vp.width}x{vp.height}",
        "full_page": full_page,
        "image_base64": b64,
        "size_bytes": len(screenshot_bytes),
    })


# ═══════════════════════════════════════════════════════════════
# TOOL: capture_multi_viewport
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def capture_multi_viewport(
    url: str,
    viewports: str = "mobile_m,tablet,desktop",
) -> str:
    """
    Capture screenshots at multiple viewports to check responsive design.

    Returns base64 images for each viewport. Use this when you need to
    verify responsive behavior across breakpoints.

    Args:
        url: Full URL to capture
        viewports: Comma-separated viewport names (e.g., "mobile_m,tablet,desktop")
    """
    from core.browser_engine import VIEWPORTS

    browser = await _get_browser()
    results = {}

    for vp_name in viewports.split(","):
        vp_name = vp_name.strip()
        vp = VIEWPORTS.get(vp_name)
        if not vp:
            results[vp_name] = {"error": f"Unknown viewport '{vp_name}'"}
            continue

        page = await browser.navigate(url, viewport=vp)
        screenshot_bytes = await browser.screenshot(page, full_page=True)
        await page.close()

        results[vp_name] = {
            "resolution": f"{vp.width}x{vp.height}",
            "image_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
            "size_bytes": len(screenshot_bytes),
        }

    return json.dumps({"status": "ok", "url": url, "screenshots": results})


# ═══════════════════════════════════════════════════════════════
# TOOL: analyze_dom
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def analyze_dom(
    url: str,
    include_interactive: bool = True,
    include_forms: bool = True,
    include_navigation: bool = True,
    max_depth: int = 5,
) -> str:
    """
    Extract and analyze the DOM structure of a web page.

    Returns: simplified DOM tree, interactive elements (buttons, links, inputs),
    form structures, and navigation items. Use this to understand page structure
    without needing to see the actual code.

    Args:
        url: URL to analyze
        include_interactive: Include buttons, links, inputs list
        include_forms: Include form detection
        include_navigation: Include navigation elements
        max_depth: Max DOM tree depth (1-8)
    """
    browser = await _get_browser()
    dom = await _get_dom()

    page = await browser.navigate(url)
    result = {"url": url}

    # DOM tree
    tree = await dom.extract_full(page)
    result["dom_tree"] = tree

    # Interactive elements
    if include_interactive:
        elems = await dom.extract_interactive_elements(page)
        result["interactive_elements"] = [
            {"tag": e.tag, "text": e.text[:100], "selector": e.selector,
             "type": e.type, "href": e.href, "visible": e.is_visible,
             "enabled": e.is_enabled}
            for e in elems[:50]
        ]
        result["interactive_count"] = len(elems)

    # Forms
    if include_forms:
        forms = await dom.extract_forms(page)
        result["forms"] = [
            {"action": f.action, "method": f.method,
             "fields": [{"name": ff.name, "type": ff.type, "label": ff.label,
                          "required": ff.required, "placeholder": ff.placeholder}
                         for ff in f.fields]}
            for f in forms
        ]

    # Navigation
    if include_navigation:
        nav = await dom.extract_navigation(page)
        result["navigation"] = [
            {"text": n.text, "href": n.href, "active": n.is_active}
            for n in nav
        ]

    # Page info
    result["title"] = await page.title()
    result["page_url"] = page.url

    await page.close()
    return json.dumps(result, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: get_console_errors
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_console_errors(
    url: str,
    include_warnings: bool = True,
    wait_ms: int = 3000,
) -> str:
    """
    Navigate to a page and capture all JavaScript console errors and warnings.

    Returns console errors, warnings, and unhandled promise rejections.
    Essential for debugging runtime JS issues.

    Args:
        url: URL to monitor
        include_warnings: Also capture console.warn messages
        wait_ms: Time to wait for errors to appear (ms)
    """
    browser = await _get_browser()
    console_cap = await _get_console()

    page = await browser.navigate(url)
    console_cap.attach(page)
    await console_cap.capture_unhandled_rejections(page)

    # Wait for async errors
    await asyncio.sleep(wait_ms / 1000)
    await console_cap.collect_rejections(page)

    errors = [e.to_dict() for e in console_cap.get_errors()]
    warnings = [w.to_dict() for w in console_cap.get_warnings()] if include_warnings else []
    network_errors = [e.to_dict() for e in browser.get_network_errors()]

    console_cap.clear()
    browser.clear_captures()
    await page.close()

    result = {
        "url": url,
        "errors": errors,
        "error_count": len(errors),
        "warnings": warnings,
        "warning_count": len(warnings),
        "network_errors": network_errors,
        "network_error_count": len(network_errors),
    }

    if not errors and not network_errors:
        result["summary"] = "Aucune erreur détectée sur cette page."
    else:
        result["summary"] = (
            f"{len(errors)} erreur(s) console, "
            f"{len(network_errors)} erreur(s) réseau, "
            f"{len(warnings)} warning(s)."
        )

    return json.dumps(result, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: audit_performance
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def audit_performance(url: str) -> str:
    """
    Run a Lighthouse performance audit on a URL.

    Returns Core Web Vitals scores (Performance, Accessibility, Best Practices,
    SEO), key metrics (LCP, CLS, TTFB, FID), and optimization opportunities.
    Requires Lighthouse CLI installed.

    Args:
        url: URL to audit
    """
    perf = await _get_perf()

    try:
        report = await perf.run_audit(url)
    except Exception as e:
        return json.dumps({
            "url": url,
            "error": str(e),
            "hint": "Lighthouse CLI not found. Install with: npm install -g lighthouse"
        })

    if "error" in report:
        return json.dumps({"url": url, "error": report["error"]})

    scores = perf.extract_scores(report)
    metrics = perf.extract_metrics(report)
    opportunities = perf.extract_opportunities(report)

    return json.dumps({
        "url": url,
        "scores": scores.to_dict() if hasattr(scores, 'to_dict') else scores,
        "metrics": metrics,
        "opportunities": [
            o.to_dict() if hasattr(o, 'to_dict') else o
            for o in opportunities[:10]
        ],
    }, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: check_accessibility
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def check_accessibility(url: str) -> str:
    """
    Check a page for accessibility issues: WCAG contrast violations,
    overflow problems, missing alt text, form labels, etc.

    Returns a list of contrast issues (with selectors, actual vs required ratio)
    and overflow issues where content extends beyond its container.

    Args:
        url: URL to check
    """
    browser = await _get_browser()
    dom = await _get_dom()

    page = await browser.navigate(url)

    # Contrast
    contrast = await dom.check_contrast(page)
    contrast_issues = [
        {"selector": c.selector, "text": c.text[:80],
         "ratio": round(c.ratio, 2), "required": c.required_ratio,
         "level": c.level, "fg": c.foreground, "bg": c.background}
        for c in contrast
    ]

    # Overflow
    overflow = await dom.detect_overflow(page)
    overflow_issues = [
        {"selector": o.selector, "overflow_x": round(o.overflow_x, 1),
         "overflow_y": round(o.overflow_y, 1)}
        for o in overflow
    ]

    await page.close()

    total = len(contrast_issues) + len(overflow_issues)
    return json.dumps({
        "url": url,
        "total_issues": total,
        "contrast_issues": contrast_issues,
        "contrast_count": len(contrast_issues),
        "overflow_issues": overflow_issues,
        "overflow_count": len(overflow_issues),
        "summary": f"{len(contrast_issues)} problème(s) de contraste, "
                   f"{len(overflow_issues)} overflow(s)" if total > 0
                   else "Aucun problème d'accessibilité détecté.",
    }, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: full_page_analysis
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def full_page_analysis(
    url: str,
    viewport: str = "desktop",
    include_screenshot: bool = True,
    include_perf: bool = False,
) -> str:
    """
    Comprehensive analysis of a web page: screenshot + DOM + console errors +
    accessibility + network errors. This is the most complete analysis tool.

    Use this as the primary tool when investigating a frontend issue —
    it gives you visual context plus all the technical details in one call.

    Args:
        url: URL to analyze
        viewport: Viewport name
        include_screenshot: Include base64 screenshot
        include_perf: Include Lighthouse audit (slower)
    """
    from core.browser_engine import VIEWPORTS

    browser = await _get_browser()
    dom = await _get_dom()
    console_cap = await _get_console()

    vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])
    page = await browser.navigate(url, viewport=vp)
    console_cap.attach(page)
    await console_cap.capture_unhandled_rejections(page)

    result = {
        "url": url,
        "viewport": viewport,
        "resolution": f"{vp.width}x{vp.height}",
    }

    # Page info
    result["title"] = await page.title()

    # Screenshot
    if include_screenshot:
        screenshot_bytes = await browser.screenshot(page, full_page=True)
        result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode("utf-8")

    # DOM analysis
    interactive = await dom.extract_interactive_elements(page)
    result["interactive_elements"] = [
        {"tag": e.tag, "text": e.text[:80], "selector": e.selector,
         "visible": e.is_visible, "enabled": e.is_enabled}
        for e in interactive[:40]
    ]

    forms = await dom.extract_forms(page)
    result["forms"] = [
        {"action": f.action, "method": f.method,
         "fields": [{"name": ff.name, "type": ff.type, "label": ff.label}
                     for ff in f.fields]}
        for f in forms
    ]

    nav = await dom.extract_navigation(page)
    result["navigation"] = [
        {"text": n.text, "href": n.href, "active": n.is_active}
        for n in nav
    ]

    # Accessibility
    contrast = await dom.check_contrast(page)
    result["contrast_issues"] = [
        {"selector": c.selector, "text": c.text[:60], "ratio": round(c.ratio, 2)}
        for c in contrast[:10]
    ]

    overflow = await dom.detect_overflow(page)
    result["overflow_issues"] = [
        {"selector": o.selector, "overflow_x": round(o.overflow_x, 1),
         "overflow_y": round(o.overflow_y, 1)}
        for o in overflow[:10]
    ]

    # Console
    await asyncio.sleep(1)
    await console_cap.collect_rejections(page)
    result["console_errors"] = [e.to_dict() for e in console_cap.get_errors()]
    result["console_warnings"] = [w.to_dict() for w in console_cap.get_warnings()]
    result["network_errors"] = [e.to_dict() for e in browser.get_network_errors()]

    # Performance (optional)
    if include_perf:
        try:
            perf = await _get_perf()
            report = await perf.run_audit(url)
            if "error" not in report:
                scores = perf.extract_scores(report)
                result["performance"] = scores.to_dict() if hasattr(scores, 'to_dict') else scores
        except Exception:
            result["performance"] = {"error": "Lighthouse not available"}

    # Summary
    issues = (len(result.get("console_errors", [])) +
              len(result.get("network_errors", [])) +
              len(result.get("contrast_issues", [])) +
              len(result.get("overflow_issues", [])))
    result["issues_total"] = issues
    result["summary"] = (
        f"Page '{result['title']}' — {len(result['interactive_elements'])} éléments interactifs, "
        f"{len(result['forms'])} formulaire(s), {issues} problème(s) détecté(s)."
    )

    console_cap.clear()
    browser.clear_captures()
    await page.close()

    return json.dumps(result, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: visual_diff
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def compare_visual(
    url: str,
    baseline_name: str,
    viewport: str = "desktop",
    save_baseline: bool = False,
) -> str:
    """
    Compare a page's current appearance against a stored baseline screenshot.

    If save_baseline=True, captures the current page as the new baseline
    (use this first to set a reference). Then call again with save_baseline=False
    to detect visual changes.

    Returns: match status, mismatch percentage, diff image.

    Args:
        url: URL to compare
        baseline_name: Name identifier for this baseline (e.g., "homepage", "dashboard")
        viewport: Viewport name
        save_baseline: If True, save current state as baseline instead of comparing
    """
    from core.browser_engine import VIEWPORTS
    from core.visual_diff import VisualDiff

    browser = await _get_browser()
    vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])
    page = await browser.navigate(url, viewport=vp)
    screenshot_bytes = await browser.screenshot(page, full_page=True)
    await page.close()

    differ = VisualDiff()

    if save_baseline:
        path = differ.capture_baseline(screenshot_bytes, baseline_name, viewport)
        return json.dumps({
            "action": "baseline_saved",
            "name": baseline_name,
            "viewport": viewport,
            "path": str(path),
        })

    result = differ.compare_with_baseline(screenshot_bytes, baseline_name, viewport)

    response = {
        "url": url,
        "baseline": baseline_name,
        "viewport": viewport,
        "match": result.match,
        "mismatch_percentage": round(result.mismatch_percentage, 2),
        "total_pixels": result.total_pixels,
        "diff_pixels": result.diff_pixels,
    }

    if result.diff_image:
        response["diff_image_base64"] = base64.b64encode(
            result.diff_image
        ).decode("utf-8") if isinstance(result.diff_image, bytes) else ""

    return json.dumps(response, default=str)


# ═══════════════════════════════════════════════════════════════
# TOOL: interact_with_page
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def interact_with_page(
    url: str,
    action: str,
    selector: str,
    value: str = "",
    screenshot_after: bool = True,
) -> str:
    """
    Perform an interaction on a page element and optionally capture a screenshot
    of the result. Useful for testing click handlers, form fills, navigation.

    Args:
        url: URL to navigate to
        action: "click" | "type" | "hover" | "select" | "scroll"
        selector: CSS selector of the target element
        value: Text to type (for "type") or option value (for "select")
        screenshot_after: Capture screenshot after interaction
    """
    browser = await _get_browser()
    page = await browser.navigate(url)

    result = {"url": url, "action": action, "selector": selector}

    try:
        if action == "click":
            await page.click(selector, timeout=5000)
        elif action == "type":
            await page.fill(selector, value, timeout=5000)
        elif action == "hover":
            await page.hover(selector, timeout=5000)
        elif action == "select":
            await page.select_option(selector, value, timeout=5000)
        elif action == "scroll":
            await page.evaluate(f"document.querySelector('{selector}')?.scrollIntoView()")
        else:
            result["error"] = f"Unknown action '{action}'"
            return json.dumps(result)

        result["success"] = True

        # Wait for potential UI updates
        await asyncio.sleep(0.5)

        if screenshot_after:
            screenshot_bytes = await browser.screenshot(page, full_page=True)
            result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode("utf-8")

        result["current_url"] = page.url
        result["title"] = await page.title()

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    await page.close()
    return json.dumps(result, default=str)


# ═══════════════════════════════════════════════════════════════
# RESOURCE: project info
# ═══════════════════════════════════════════════════════════════

@mcp.resource("zephyr://info")
def get_info() -> str:
    """Returns information about the Zephyr MCP server and available tools."""
    return json.dumps({
        "name": "Zephyr UI Intelligence",
        "version": "0.1.0",
        "description": (
            "Serveur MCP donnant à Copilot/Claude un accès visuel aux interfaces web. "
            "Capture de screenshots, extraction DOM, erreurs console, audit perf, "
            "vérification accessibilité, et régression visuelle."
        ),
        "tools": [
            "capture_screenshot — Capture d'écran d'une page",
            "capture_multi_viewport — Screenshots multi-viewport (responsif)",
            "analyze_dom — Extraction structurée du DOM",
            "get_console_errors — Erreurs et warnings JavaScript",
            "audit_performance — Audit Lighthouse (Core Web Vitals)",
            "check_accessibility — Contraste WCAG + overflow",
            "full_page_analysis — Analyse complète (screenshot + DOM + erreurs + a11y)",
            "compare_visual — Régression visuelle (baseline/diff)",
            "interact_with_page — Interaction (click, type, hover) + screenshot",
        ],
        "usage_tips": [
            "Utilise full_page_analysis en premier pour avoir une vue complète",
            "Pour du debug spécifique, combine capture_screenshot + get_console_errors",
            "Pour le responsive, utilise capture_multi_viewport",
            "Pour tester un flux, enchaîne interact_with_page avec screenshot_after=True",
        ],
    }, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
