"""
Tests for core modules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


# ───── BrowserEngine ─────

class TestBrowserEngine:
    """Test browser engine lifecycle."""

    @pytest.mark.asyncio
    async def test_engine_initializes(self):
        from core.browser_engine import BrowserEngine
        engine = BrowserEngine()
        assert engine.browser is None
        assert engine.playwright is None

    def test_viewports_defined(self):
        from core.browser_engine import VIEWPORTS
        assert "desktop" in VIEWPORTS
        assert "mobile_m" in VIEWPORTS
        assert VIEWPORTS["desktop"].width >= 1280

    def test_viewport_dataclass(self):
        from core.browser_engine import Viewport
        vp = Viewport(name="test", width=800, height=600)
        assert vp.name == "test"
        assert vp.width == 800


# ───── DOMExtractor ─────

class TestDOMExtractor:
    """Test DOM extraction scripts."""

    def test_extractor_has_js_scripts(self):
        from core.dom_extractor import DOMExtractor
        extractor = DOMExtractor()
        # Should have extraction methods
        assert hasattr(extractor, "extract_dom_tree")
        assert hasattr(extractor, "extract_interactive_elements")
        assert hasattr(extractor, "extract_forms")

    def test_dataclasses(self):
        from core.dom_extractor import DOMNode, FormField, ContrastIssue
        node = DOMNode(tag="div", text="Hello", children=[])
        assert node.tag == "div"

        field = FormField(name="email", type="email", label="Email")
        assert field.type == "email"

        issue = ContrastIssue(
            element="p", text="Low", ratio=2.5,
            foreground="#fff", background="#eee"
        )
        assert issue.ratio == 2.5


# ───── InteractionRunner ─────

class TestInteractionRunner:
    def test_click_options(self):
        from core.interaction_runner import ClickOptions
        opts = ClickOptions(selector="#btn", click_count=2)
        assert opts.click_count == 2

    def test_nav_step(self):
        from core.interaction_runner import NavigationStep
        step = NavigationStep(action="click", selector="#next")
        assert step.action == "click"


# ───── PerfAnalyzer ─────

class TestPerfAnalyzer:
    def test_scorecard(self):
        from core.perf_analyzer import ScoreCard
        card = ScoreCard(
            performance=90, accessibility=85,
            best_practices=80, seo=75, pwa=0
        )
        assert card.performance == 90

    def test_audit_config(self):
        from core.perf_analyzer import AuditConfig
        config = AuditConfig(url="http://test.com")
        assert "http" in config.url


# ───── ConsoleCapture ─────

class TestConsoleCapture:
    def test_captured_log(self):
        from core.console_capture import CapturedLog
        log = CapturedLog(level="error", text="Something failed", url="http://test.com")
        assert log.level == "error"


# ───── VisualDiff ─────

class TestVisualDiff:
    def test_diff_result(self):
        from core.visual_diff import DiffResult
        result = DiffResult(
            match=False,
            mismatch_percentage=5.2,
            total_pixels=1000,
            diff_pixels=52,
        )
        assert not result.match
        assert result.mismatch_percentage == 5.2


# ───── ScreenshotManager ─────

class TestScreenshotManager:
    def test_manager_creates(self):
        from core.screenshot_manager import ScreenshotManager
        mgr = ScreenshotManager()
        assert mgr is not None
