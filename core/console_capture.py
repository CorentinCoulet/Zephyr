"""
Console Capture — Intercepts and structures browser console output.
Captures errors, warnings, uncaught exceptions, and promise rejections.
"""

from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import Page, ConsoleMessage as PWConsoleMessage


@dataclass
class CapturedLog:
    """A single captured console log entry."""
    level: str  # "error", "warning", "info", "log", "debug"
    message: str
    source_url: str = ""
    line_number: int = 0
    column_number: int = 0
    stack_trace: str = ""
    timestamp: float = 0

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "message": self.message,
            "source_url": self.source_url,
            "line_number": self.line_number,
            "stack_trace": self.stack_trace,
        }


@dataclass
class CapturedError:
    """A captured JavaScript error or unhandled rejection."""
    type: str  # "error", "unhandledrejection"
    message: str
    stack: str = ""
    source_url: str = ""
    line_number: int = 0

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "message": self.message,
            "stack": self.stack,
            "source_url": self.source_url,
            "line_number": self.line_number,
        }


class ConsoleCapture:
    """Captures and categorizes browser console output and JS errors."""

    def __init__(self):
        self._logs: list[CapturedLog] = []
        self._errors: list[CapturedError] = []
        self._attached_pages: set[int] = set()

    def attach(self, page: Page) -> None:
        """Attach listeners to a Playwright page."""
        page_id = id(page)
        if page_id in self._attached_pages:
            return
        self._attached_pages.add(page_id)

        page.on("console", self._on_console)
        page.on("pageerror", self._on_page_error)

    def _on_console(self, msg: PWConsoleMessage) -> None:
        location = msg.location
        self._logs.append(
            CapturedLog(
                level=msg.type,
                message=msg.text,
                source_url=location.get("url", "") if location else "",
                line_number=location.get("lineNumber", 0) if location else 0,
                column_number=location.get("columnNumber", 0) if location else 0,
            )
        )

    def _on_page_error(self, error) -> None:
        self._errors.append(
            CapturedError(
                type="error",
                message=str(error),
                stack=error.stack if hasattr(error, "stack") else "",
            )
        )

    async def capture_unhandled_rejections(self, page: Page) -> None:
        """Inject a script to capture unhandled promise rejections."""
        await page.evaluate("""
            () => {
                window.__zephyr_rejections = [];
                window.addEventListener('unhandledrejection', (event) => {
                    window.__zephyr_rejections.push({
                        message: event.reason?.message || String(event.reason),
                        stack: event.reason?.stack || ''
                    });
                });
            }
        """)

    async def collect_rejections(self, page: Page) -> list[CapturedError]:
        """Collect any unhandled promise rejections captured so far."""
        rejections = await page.evaluate("""
            () => window.__zephyr_rejections || []
        """)
        errors = []
        for r in rejections:
            error = CapturedError(
                type="unhandledrejection",
                message=r.get("message", ""),
                stack=r.get("stack", ""),
            )
            self._errors.append(error)
            errors.append(error)
        return errors

    def get_logs(self, level: Optional[str] = None) -> list[CapturedLog]:
        """Get captured logs, optionally filtered by level."""
        if level:
            return [log for log in self._logs if log.level == level]
        return self._logs.copy()

    def get_errors(self) -> list[CapturedError]:
        """Get all captured JS errors and unhandled rejections."""
        return self._errors.copy()

    def get_warnings(self) -> list[CapturedLog]:
        """Get only warning-level logs."""
        return self.get_logs("warning")

    def get_error_logs(self) -> list[CapturedLog]:
        """Get only error-level console logs."""
        return self.get_logs("error")

    def get_summary(self) -> dict:
        """Get a summary of all captured console activity."""
        return {
            "total_logs": len(self._logs),
            "errors": len(self.get_error_logs()),
            "warnings": len(self.get_warnings()),
            "js_errors": len([e for e in self._errors if e.type == "error"]),
            "unhandled_rejections": len(
                [e for e in self._errors if e.type == "unhandledrejection"]
            ),
            "error_details": [e.to_dict() for e in self._errors],
            "warning_details": [w.to_dict() for w in self.get_warnings()],
        }

    def clear(self) -> None:
        """Clear all captured data."""
        self._logs.clear()
        self._errors.clear()
        self._attached_pages.clear()
