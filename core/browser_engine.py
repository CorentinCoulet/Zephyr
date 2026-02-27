"""
Browser Engine — Playwright-based headless browser management.
Handles browser lifecycle, page navigation, screenshot capture, and JS evaluation.
"""

import asyncio
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
        self, url: str, status: int, method: str, error_text: str = ""
    ):
        self.url = url
        self.status = status
        self.method = method
        self.error_text = error_text

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status,
            "method": self.method,
            "error_text": self.error_text,
        }


class BrowserEngine:
    """Manages the headless Chromium browser lifecycle via Playwright."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: list[BrowserContext] = []
        self._console_messages: list[ConsoleMessage] = []
        self._network_errors: list[NetworkError] = []

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
        """Navigate to a URL and return the page object."""
        context = await self.new_context(viewport)
        page = await context.new_page()

        # Attach console listener
        page.on("console", self._on_console_message)
        # Attach request failure listener
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

    def clear_captures(self) -> None:
        """Clear all captured console messages and network errors."""
        self._console_messages.clear()
        self._network_errors.clear()

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

    def _on_request_failed(self, request) -> None:
        self._network_errors.append(
            NetworkError(
                url=request.url,
                status=0,
                method=request.method,
                error_text=request.failure or "Request failed",
            )
        )

    # --- Context manager ---

    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, *args):
        await self.close()
