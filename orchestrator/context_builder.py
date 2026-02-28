"""
Context Builder — Assembles the technical and navigational context
that agents need to make informed decisions.
"""

from typing import Any, Optional

from playwright.async_api import Page

from core.browser_engine import BrowserEngine, Viewport, VIEWPORTS
from core.dom_extractor import DOMExtractor
from core.console_capture import ConsoleCapture
from core.screenshot_manager import ScreenshotManager
from core.perf_analyzer import PerfAnalyzer
from core.interaction_runner import InteractionRunner


class ContextBuilder:
    """Builds rich contextual data from a target page for agent consumption."""

    def __init__(self):
        self.browser = BrowserEngine()
        self.dom_extractor = DOMExtractor()
        self.console_capture = ConsoleCapture()
        self.screenshot_mgr = ScreenshotManager()
        self.perf_analyzer = PerfAnalyzer()
        self.interaction_runner = InteractionRunner()
        # Smart context cache: invalidated by URL change not just time
        self._context_cache: dict[str, dict] = {}  # cache_key -> {url, data, timestamp}

    async def build_dev_context(
        self,
        url: str,
        page: Optional[Page] = None,
        viewport: Optional[str] = None,
        session_id: str = "default",
        include_perf: bool = False,
    ) -> dict:
        """Build context for the Dev Agent: errors, DOM, perf, UI issues."""
        import time

        # Smart cache: return cached data if same URL and < 2 min old
        cache_key = f"dev:{session_id}:{viewport or 'desktop'}"
        cached = self._context_cache.get(cache_key)
        if cached and cached["url"] == url and (time.time() - cached["timestamp"]) < 120:
            return cached["data"]

        context = {"url": url}
        own_page = page is None

        try:
            if own_page:
                vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])
                page = await self.browser.navigate(url, viewport=vp)
                context["viewport"] = vp.to_dict() if hasattr(vp, 'to_dict') else {"width": vp.width, "height": vp.height}

            # Attach console capture
            self.console_capture.attach(page)
            await self.console_capture.capture_unhandled_rejections(page)

            # Parallel-ish extraction (all use the same page)
            dom = await self.dom_extractor.extract_full(page)
            context["dom_snapshot"] = dom

            interactive = await self.dom_extractor.extract_interactive_elements(page)
            context["interactive_elements"] = [
                {"tag": e.tag, "text": e.text, "selector": e.selector,
                 "is_visible": e.is_visible, "is_enabled": e.is_enabled}
                for e in interactive
            ]

            forms = await self.dom_extractor.extract_forms(page)
            context["forms"] = [
                {"action": f.action, "method": f.method,
                 "fields": [{"name": ff.name, "type": ff.type, "label": ff.label,
                             "required": ff.required} for ff in f.fields]}
                for f in forms
            ]

            # UI Issues
            contrast = await self.dom_extractor.check_contrast(page)
            context["contrast_issues"] = [
                {"selector": c.selector, "text": c.text, "ratio": c.ratio,
                 "required_ratio": c.required_ratio, "level": c.level}
                for c in contrast
            ]

            overflow = await self.dom_extractor.detect_overflow(page)
            context["overflow_issues"] = [
                {"selector": o.selector, "overflow_x": o.overflow_x,
                 "overflow_y": o.overflow_y}
                for o in overflow
            ]

            # Console errors
            await self.console_capture.collect_rejections(page)
            context["console_errors"] = [
                e.to_dict() for e in self.console_capture.get_errors()
            ]
            context["console_warnings"] = [
                w.to_dict() for w in self.console_capture.get_warnings()
            ]

            # Network errors
            context["network_errors"] = [
                e.to_dict() for e in self.browser.get_network_errors()
            ]

            # Screenshot
            screenshot_path = await self.screenshot_mgr.capture(
                page, label="dev_analysis", session_id=session_id
            )
            context["screenshot_path"] = screenshot_path

            # Enhanced accessibility audit
            try:
                a11y = await self.dom_extractor.check_accessibility(page)
                context["accessibility_issues"] = [
                    {"type": a.type, "selector": a.selector, "tag": a.element_tag,
                     "text": a.text, "details": a.details, "severity": a.severity}
                    for a in a11y
                ]
            except Exception:
                pass

            # Framework detection
            try:
                context["framework"] = await self.dom_extractor.detect_framework(page)
            except Exception:
                pass

            # Performance (optional — expensive)
            if include_perf:
                try:
                    perf_report = await self.perf_analyzer.run_audit(url)
                    if "error" not in perf_report:
                        scores = self.perf_analyzer.extract_scores(perf_report)
                        metrics = self.perf_analyzer.extract_metrics(perf_report)
                        opportunities = self.perf_analyzer.extract_opportunities(perf_report)
                        context["performance"] = {
                            "scores": scores.to_dict(),
                            "metrics": metrics,
                            "opportunities": [o.to_dict() for o in opportunities[:10]],
                        }
                except Exception:
                    pass  # Lighthouse not available — skip

        finally:
            if own_page:
                self.console_capture.clear()
                self.browser.clear_captures()

        # Cache result
        import time
        self._context_cache[cache_key] = {"url": url, "data": context, "timestamp": time.time()}

        return context

    def invalidate_cache(self, session_id: str = None) -> None:
        """Invalidate context cache for a session or all."""
        if session_id:
            keys_to_remove = [k for k in self._context_cache if session_id in k]
            for k in keys_to_remove:
                del self._context_cache[k]
        else:
            self._context_cache.clear()

    async def build_user_context(
        self,
        url: str,
        page: Optional[Page] = None,
        session_id: str = "default",
        pages_visited: Optional[list[str]] = None,
    ) -> dict:
        """Build context for the User Agent: navigation, elements, structure."""
        context = {"current_page": url}
        own_page = page is None

        try:
            if own_page:
                page = await self.browser.navigate(url)

            # Page title
            title = await page.title()
            context["page_title"] = title

            # Navigation elements
            nav_items = await self.dom_extractor.extract_navigation(page)
            context["navigation"] = [
                {"text": n.text, "href": n.href, "is_active": n.is_active}
                for n in nav_items
            ]

            # Interactive elements (buttons, links)
            interactive = await self.dom_extractor.extract_interactive_elements(page)
            context["interactive_elements"] = [
                {"tag": e.tag, "text": e.text, "href": e.href,
                 "selector": e.selector, "is_visible": e.is_visible}
                for e in interactive if e.is_visible
            ]

            # Forms
            forms = await self.dom_extractor.extract_forms(page)
            context["forms"] = [
                {"action": f.action, "method": f.method,
                 "fields": [{"name": ff.name, "type": ff.type, "label": ff.label,
                             "placeholder": ff.placeholder, "required": ff.required}
                            for ff in f.fields]}
                for f in forms
            ]

            # Simplified DOM for understanding page structure
            dom = await self.dom_extractor.extract_full(page)
            context["dom_snapshot"] = dom

            # User journey
            if pages_visited:
                context["user_journey"] = pages_visited

        finally:
            if own_page:
                pass  # Page cleanup handled by browser engine

        return context

    async def build_sitemap(self, base_url: str, max_pages: int = 30) -> list[str]:
        """Crawl and build a simple sitemap of accessible pages."""
        visited = set()
        to_visit = [base_url]
        sitemap = []

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue

            visited.add(url)
            sitemap.append(url)

            try:
                page = await self.browser.navigate(url)
                nav_items = await self.dom_extractor.extract_navigation(page)

                for item in nav_items:
                    href = item.href
                    if (
                        href
                        and href.startswith(base_url)
                        and href not in visited
                        and "#" not in href
                    ):
                        to_visit.append(href)

                await page.close()
            except Exception:
                continue

        return sitemap

    async def close(self) -> None:
        """Clean up resources."""
        await self.browser.close()
