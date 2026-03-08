"""
Screenshot Manager — Manages screenshot capture, storage, and retrieval.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from playwright.async_api import Page

from config.settings import settings

logger = logging.getLogger("zephyr.core.screenshot")


# Characters allowed in session_id / label for path safety
_SAFE_PATH_RE = __import__("re").compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


def _sanitize_path_component(value: str, name: str = "value") -> str:
    """Validate that a path component is safe (no traversal, no special chars)."""
    if not _SAFE_PATH_RE.match(value):
        raise ValueError(
            f"Invalid {name}: must be 1-128 alphanumeric/dash/underscore/dot characters"
        )
    # Extra guard against traversal
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {name}: path traversal not allowed")
    return value


class ScreenshotManager:
    """Manages screenshots for analysis sessions."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.screenshots_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._captures: dict[str, str] = {}  # label → filepath

    async def capture(
        self,
        page: Page,
        label: str,
        full_page: bool = True,
        session_id: str = "default",
    ) -> str:
        """Capture a screenshot and store it with a label."""
        session_id = _sanitize_path_component(session_id, "session_id")
        label = _sanitize_path_component(label, "label")
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time() * 1000)
        filename = f"{label}_{timestamp}.png"
        filepath = session_dir / filename

        await page.screenshot(path=str(filepath), full_page=full_page)

        key = f"{session_id}/{label}"
        self._captures[key] = str(filepath)
        logger.info("Screenshot captured: %s", filepath)
        return str(filepath)

    async def capture_element(
        self,
        page: Page,
        selector: str,
        label: str,
        session_id: str = "default",
    ) -> Optional[str]:
        """Capture a screenshot of a specific element."""
        session_id = _sanitize_path_component(session_id, "session_id")
        label = _sanitize_path_component(label, "label")
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        element = await page.query_selector(selector)
        if not element:
            return None

        timestamp = int(time.time() * 1000)
        filename = f"{label}_{timestamp}.png"
        filepath = session_dir / filename

        await element.screenshot(path=str(filepath))

        key = f"{session_id}/{label}"
        self._captures[key] = str(filepath)
        return str(filepath)

    def get_capture(self, label: str, session_id: str = "default") -> Optional[str]:
        """Retrieve a previously captured screenshot path."""
        key = f"{session_id}/{label}"
        return self._captures.get(key)

    def get_all_captures(self, session_id: str = "default") -> dict[str, str]:
        """Get all captures for a session."""
        prefix = f"{session_id}/"
        return {
            k.removeprefix(prefix): v
            for k, v in self._captures.items()
            if k.startswith(prefix)
        }

    def list_sessions(self) -> list[str]:
        """List all session directories."""
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def cleanup_session(self, session_id: str) -> int:
        """Delete all screenshots for a session. Returns count deleted."""
        session_dir = self.base_dir / session_id
        if not session_dir.exists():
            return 0

        count = 0
        for f in session_dir.iterdir():
            f.unlink()
            count += 1
        session_dir.rmdir()

        # Clean from cache
        prefix = f"{session_id}/"
        to_remove = [k for k in self._captures if k.startswith(prefix)]
        for k in to_remove:
            del self._captures[k]

        return count

    def cleanup_old(self, max_age_seconds: int = 86_400) -> int:
        """Remove screenshots older than max_age_seconds."""
        now = time.time()
        count = 0

        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue
            for f in session_dir.iterdir():
                if (now - f.stat().st_mtime) > max_age_seconds:
                    f.unlink()
                    count += 1
            # Remove empty dirs
            if not any(session_dir.iterdir()):
                session_dir.rmdir()

        return count
