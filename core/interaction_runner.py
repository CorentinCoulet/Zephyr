"""
Interaction Runner — Simulates realistic user interactions.
Click, hover, scroll, drag & drop, form filling, navigation sequences, auth flows.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from playwright.async_api import Page

logger = logging.getLogger("zephyr.core.interaction")


@dataclass
class ClickOptions:
    button: str = "left"  # "left", "right", "middle"
    click_count: int = 1
    delay: int = 0  # ms between mousedown and mouseup
    force: bool = False
    timeout: int = 30_000


@dataclass
class NavigationStep:
    action: str  # "click", "fill", "select", "navigate", "wait"
    selector: str = ""
    value: str = ""
    url: str = ""
    wait_ms: int = 0
    description: str = ""


@dataclass
class InteractionResult:
    success: bool
    action: str
    selector: str = ""
    error: str = ""
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
    console_errors: list[str] = None

    def __post_init__(self):
        if self.console_errors is None:
            self.console_errors = []

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "action": self.action,
            "selector": self.selector,
            "error": self.error,
            "console_errors": self.console_errors,
        }


@dataclass
class AuthConfig:
    login_url: str
    username_selector: str = "#username"
    password_selector: str = "#password"
    submit_selector: str = '[type="submit"]'
    username: str = ""
    password: str = ""
    success_indicator: str = ""  # Selector that appears after successful login


class InteractionRunner:
    """Simulates realistic user interactions on a Playwright page."""

    def __init__(self):
        self._results: list[InteractionResult] = []

    async def click(
        self,
        page: Page,
        selector: str,
        options: Optional[ClickOptions] = None,
    ) -> InteractionResult:
        """Click on an element."""
        opts = options or ClickOptions()
        try:
            await page.click(
                selector,
                button=opts.button,
                click_count=opts.click_count,
                delay=opts.delay,
                force=opts.force,
                timeout=opts.timeout,
            )
            result = InteractionResult(success=True, action="click", selector=selector)
        except Exception as e:
            result = InteractionResult(
                success=False, action="click", selector=selector, error=str(e)
            )
        self._results.append(result)
        return result

    async def hover(self, page: Page, selector: str) -> InteractionResult:
        """Hover over an element."""
        try:
            await page.hover(selector, timeout=10_000)
            result = InteractionResult(success=True, action="hover", selector=selector)
        except Exception as e:
            result = InteractionResult(
                success=False, action="hover", selector=selector, error=str(e)
            )
        self._results.append(result)
        return result

    async def scroll(
        self, page: Page, direction: str = "down", amount: int = 500
    ) -> InteractionResult:
        """Scroll the page in a direction."""
        try:
            delta_y = amount if direction == "down" else -amount
            delta_x = amount if direction == "right" else (-amount if direction == "left" else 0)
            if direction in ("up", "down"):
                delta_x = 0
            await page.mouse.wheel(delta_x, delta_y)
            await asyncio.sleep(0.5)  # Wait for lazy loading
            result = InteractionResult(success=True, action="scroll", selector=direction)
        except Exception as e:
            result = InteractionResult(
                success=False, action="scroll", selector=direction, error=str(e)
            )
        self._results.append(result)
        return result

    async def drag_drop(
        self, page: Page, source: str, target: str
    ) -> InteractionResult:
        """Drag an element and drop it on another."""
        try:
            await page.drag_and_drop(source, target)
            result = InteractionResult(
                success=True, action="drag_drop", selector=f"{source} → {target}"
            )
        except Exception as e:
            result = InteractionResult(
                success=False,
                action="drag_drop",
                selector=f"{source} → {target}",
                error=str(e),
            )
        self._results.append(result)
        return result

    async def fill_form(
        self, page: Page, form_data: dict[str, str]
    ) -> InteractionResult:
        """Fill a form with the given field→value mapping."""
        errors = []
        for selector, value in form_data.items():
            try:
                await page.fill(selector, value, timeout=10_000)
            except Exception as e:
                errors.append(f"{selector}: {str(e)}")

        success = len(errors) == 0
        result = InteractionResult(
            success=success,
            action="fill_form",
            selector=str(list(form_data.keys())),
            error="; ".join(errors) if errors else "",
        )
        self._results.append(result)
        return result

    async def type_text(
        self, page: Page, selector: str, text: str, delay: int = 50
    ) -> InteractionResult:
        """Type text character by character (simulates real typing)."""
        try:
            await page.click(selector)
            await page.type(selector, text, delay=delay)
            result = InteractionResult(
                success=True, action="type_text", selector=selector
            )
        except Exception as e:
            result = InteractionResult(
                success=False, action="type_text", selector=selector, error=str(e)
            )
        self._results.append(result)
        return result

    async def select_option(
        self, page: Page, selector: str, value: str
    ) -> InteractionResult:
        """Select an option in a <select> element."""
        try:
            await page.select_option(selector, value)
            result = InteractionResult(
                success=True, action="select_option", selector=selector
            )
        except Exception as e:
            result = InteractionResult(
                success=False,
                action="select_option",
                selector=selector,
                error=str(e),
            )
        self._results.append(result)
        return result

    async def navigate_sequence(
        self, page: Page, steps: list[NavigationStep]
    ) -> list[InteractionResult]:
        """Execute a sequence of navigation steps."""
        logger.info("Running navigation sequence (%d steps)", len(steps))
        results = []
        for step in steps:
            if step.action == "click":
                result = await self.click(page, step.selector)
            elif step.action == "fill":
                result = await self.fill_form(page, {step.selector: step.value})
            elif step.action == "select":
                result = await self.select_option(page, step.selector, step.value)
            elif step.action == "navigate":
                try:
                    await page.goto(step.url, wait_until="networkidle")
                    result = InteractionResult(
                        success=True, action="navigate", selector=step.url
                    )
                except Exception as e:
                    result = InteractionResult(
                        success=False,
                        action="navigate",
                        selector=step.url,
                        error=str(e),
                    )
                self._results.append(result)
            elif step.action == "wait":
                await asyncio.sleep(step.wait_ms / 1000)
                result = InteractionResult(
                    success=True, action="wait", selector=f"{step.wait_ms}ms"
                )
                self._results.append(result)
            else:
                result = InteractionResult(
                    success=False,
                    action=step.action,
                    error=f"Unknown action: {step.action}",
                )
                self._results.append(result)

            results.append(result)
            if not result.success:
                break  # Stop on failure

        return results

    async def authenticate(
        self, page: Page, config: AuthConfig
    ) -> InteractionResult:
        """Perform a login flow."""
        logger.info("Authenticating at %s", config.login_url)
        try:
            await page.goto(config.login_url, wait_until="networkidle")
            await page.fill(config.username_selector, config.username)
            await page.fill(config.password_selector, config.password)
            await page.click(config.submit_selector)

            if config.success_indicator:
                await page.wait_for_selector(
                    config.success_indicator, timeout=10_000
                )

            result = InteractionResult(
                success=True, action="authenticate", selector=config.login_url
            )
        except Exception as e:
            result = InteractionResult(
                success=False,
                action="authenticate",
                selector=config.login_url,
                error=str(e),
            )
        self._results.append(result)
        return result

    async def wait_for(
        self, page: Page, selector: str, timeout: int = 10_000
    ) -> InteractionResult:
        """Wait for an element to appear."""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            result = InteractionResult(
                success=True, action="wait_for", selector=selector
            )
        except Exception as e:
            result = InteractionResult(
                success=False, action="wait_for", selector=selector, error=str(e)
            )
        self._results.append(result)
        return result

    def get_results(self) -> list[InteractionResult]:
        """Get all interaction results from this session."""
        return self._results.copy()

    def clear_results(self) -> None:
        """Clear the results buffer."""
        self._results.clear()
