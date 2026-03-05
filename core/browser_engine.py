"""
Browser Engine — Playwright-based headless browser management.
Handles browser lifecycle, page navigation, screenshot capture, and JS evaluation.
"""

import time
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
    Playwright,
    ConsoleMessage as PWConsoleMessage,
)

from config.settings import settings


class Viewport:
    def __init__(self, width: int, height: int, name: str = "custom"):
        self.width = width
        self.height = height
        self.name = name

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height}


# Pre-defined viewports
VIEWPORTS = {
    "mobile_s": Viewport(320, 568, "mobile_s"),
    "mobile_m": Viewport(375, 812, "mobile_m"),
    "tablet": Viewport(768, 1024, "tablet"),
    "desktop": Viewport(1440, 900, "desktop"),
    "4k": Viewport(2560, 1440, "4k"),
}


class ConsoleMessage:
    """Structured console message captured from the browser."""

    def __init__(self, type: str, text: str, url: str = "", line: int = 0):
        self.type = type
        self.text = text
        self.url = url
        self.line = line

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "url": self.url,
            "line": self.line,
        }


class NetworkError:
    """Captured network error (failed requests, CORS, timeouts)."""

    def __init__(
        self, url: str, status: int, method: str, error_text: str = "",
        response_headers: Optional[dict] = None,
    ):
        self.url = url
        self.status = status
        self.method = method
        self.error_text = error_text
        self.response_headers = response_headers or {}

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status,
            "method": self.method,
            "error_text": self.error_text,
            "response_headers": self.response_headers,
        }


class NetworkRequest:
    """Captured network request with full timing and size info."""

    def __init__(
        self,
        url: str,
        method: str,
        status: int = 0,
        resource_type: str = "",
        request_headers: Optional[dict] = None,
        response_headers: Optional[dict] = None,
        timing_ms: float = 0,
        size_bytes: int = 0,
        failed: bool = False,
        error_text: str = "",
    ):
        self.url = url
        self.method = method
        self.status = status
        self.resource_type = resource_type
        self.request_headers = request_headers or {}
        self.response_headers = response_headers or {}
        self.timing_ms = timing_ms
        self.size_bytes = size_bytes
        self.failed = failed
        self.error_text = error_text

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "resource_type": self.resource_type,
            "timing_ms": round(self.timing_ms, 1),
            "size_bytes": self.size_bytes,
            "failed": self.failed,
            "error_text": self.error_text,
        }


class BrowserEngine:
    """Manages the headless Chromium browser lifecycle via Playwright."""

    MAX_CONTEXTS = 10  # Maximum concurrent browser contexts

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: list[BrowserContext] = []
        self._console_messages: list[ConsoleMessage] = []
        self._network_errors: list[NetworkError] = []
        self._network_requests: list[NetworkRequest] = []
        self._request_start_times: dict[str, float] = {}

    async def launch(self) -> None:
        """Launch the browser instance."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

    async def new_context(
        self, viewport: Optional[Viewport] = None
    ) -> BrowserContext:
        """Create a new browser context with optional viewport."""
        if not self._browser:
            await self.launch()

        # Evict oldest contexts if at capacity
        while len(self._contexts) >= self.MAX_CONTEXTS:
            oldest = self._contexts.pop(0)
            try:
                await oldest.close()
            except Exception:
                pass

        vp = viewport.to_dict() if viewport else VIEWPORTS["desktop"].to_dict()
        context = await self._browser.new_context(
            viewport=vp,
            ignore_https_errors=True,
        )
        self._contexts.append(context)
        return context

    async def navigate(
        self,
        url: str,
        viewport: Optional[Viewport] = None,
        wait_until: str = "networkidle",
    ) -> Page:
        """Navigate to a URL and return the page object. Clears previous captures."""
        # Clear previous captures to isolate per-navigation
        self.clear_captures()

        context = await self.new_context(viewport)
        page = await context.new_page()

        # Attach console listener
        page.on("console", self._on_console_message)
        # Attach network listeners
        page.on("request", self._on_request_start)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

        await page.goto(
            url,
            wait_until=wait_until,
            timeout=settings.browser_timeout,
        )
        return page

    async def screenshot(
        self,
        page: Page,
        path: Optional[str] = None,
        full_page: bool = True,
    ) -> bytes:
        """Take a screenshot of the current page."""
        screenshot_bytes = await page.screenshot(full_page=full_page)

        if path:
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(screenshot_bytes)

        return screenshot_bytes

    async def screenshot_multi_viewport(
        self, url: str, output_dir: str
    ) -> dict[str, bytes]:
        """Capture screenshots at multiple predefined viewports."""
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, viewport in VIEWPORTS.items():
            page = await self.navigate(url, viewport=viewport)
            path = str(output_path / f"{name}.png")
            screenshot = await self.screenshot(page, path=path)
            results[name] = screenshot
            await page.close()

        return results

    def get_console_messages(
        self, type_filter: Optional[str] = None
    ) -> list[ConsoleMessage]:
        """Get captured console messages, optionally filtered by type."""
        if type_filter:
            return [m for m in self._console_messages if m.type == type_filter]
        return self._console_messages.copy()

    def get_network_errors(self) -> list[NetworkError]:
        """Get all captured network errors."""
        return self._network_errors.copy()

    def get_network_requests(self) -> list[NetworkRequest]:
        """Get all captured network requests (full waterfall)."""
        return self._network_requests.copy()

    def get_network_waterfall(self) -> dict:
        """Get a structured network waterfall summary."""
        requests = self._network_requests.copy()
        total_size = sum(r.size_bytes for r in requests)
        total_time = max((r.timing_ms for r in requests), default=0)
        by_type: dict[str, list] = {}
        slow_requests = []
        for r in requests:
            by_type.setdefault(r.resource_type or "other", []).append(r.to_dict())
            if r.timing_ms > 1000:
                slow_requests.append(r.to_dict())
        return {
            "total_requests": len(requests),
            "total_size_bytes": total_size,
            "total_time_ms": round(total_time, 1),
            "failed_count": sum(1 for r in requests if r.failed),
            "error_count": sum(1 for r in requests if r.status >= 400),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "slow_requests": slow_requests[:20],
            "requests": [r.to_dict() for r in requests[:100]],
        }

    def clear_captures(self) -> None:
        """Clear all captured console messages and network errors."""
        self._console_messages.clear()
        self._network_errors.clear()
        self._network_requests.clear()
        self._request_start_times.clear()

    async def evaluate_js(self, page: Page, script: str) -> Any:
        """Evaluate JavaScript on the page and return the result."""
        return await page.evaluate(script)

    async def close(self) -> None:
        """Close all contexts and the browser."""
        for context in self._contexts:
            await context.close()
        self._contexts.clear()

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # --- Private handlers ---

    def _on_console_message(self, msg: PWConsoleMessage) -> None:
        location = msg.location
        self._console_messages.append(
            ConsoleMessage(
                type=msg.type,
                text=msg.text,
                url=location.get("url", "") if location else "",
                line=location.get("lineNumber", 0) if location else 0,
            )
        )

    def _on_request_start(self, request) -> None:
        """Track request start time for waterfall."""
        self._request_start_times[request.url + request.method] = time.time()

    def _on_response(self, response) -> None:
        """Track completed responses including 4xx/5xx."""
        request = response.request
        key = request.url + request.method
        start = self._request_start_times.pop(key, None)
        timing_ms = (time.time() - start) * 1000 if start else 0

        headers = {}
        try:
            headers = dict(response.headers)
        except Exception:
            pass

        net_req = NetworkRequest(
            url=request.url,
            method=request.method,
            status=response.status,
            resource_type=request.resource_type,
            response_headers=headers,
            timing_ms=timing_ms,
            size_bytes=int(headers.get("content-length", 0)),
        )
        self._network_requests.append(net_req)

        # Also add to errors if 4xx/5xx
        if response.status >= 400:
            self._network_errors.append(
                NetworkError(
                    url=request.url,
                    status=response.status,
                    method=request.method,
                    error_text=f"HTTP {response.status}",
                    response_headers=headers,
                )
            )

    def _on_request_failed(self, request) -> None:
        key = request.url + request.method
        start = self._request_start_times.pop(key, None)
        timing_ms = (time.time() - start) * 1000 if start else 0

        self._network_errors.append(
            NetworkError(
                url=request.url,
                status=0,
                method=request.method,
                error_text=request.failure or "Request failed",
            )
        )
        self._network_requests.append(
            NetworkRequest(
                url=request.url,
                method=request.method,
                resource_type=request.resource_type,
                timing_ms=timing_ms,
                failed=True,
                error_text=request.failure or "Request failed",
            )
        )

    # --- Context manager ---

    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, *args):
        await self.close()
