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
        assert engine._browser is None
        assert engine._playwright is None

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

    def test_network_request_dataclass(self):
        from core.browser_engine import NetworkRequest
        req = NetworkRequest(
            url="http://example.com/api",
            method="GET",
            status=200,
            resource_type="fetch",
            timing_ms=150.5,
            size_bytes=1024,
            response_headers={"Content-Type": "application/json"},
        )
        assert req.status == 200
        assert req.timing_ms == 150.5
        assert req.size_bytes == 1024

    def test_engine_has_network_methods(self):
        from core.browser_engine import BrowserEngine
        engine = BrowserEngine()
        assert hasattr(engine, "get_network_waterfall")
        assert hasattr(engine, "get_network_requests")
        waterfall = engine.get_network_waterfall()
        assert isinstance(waterfall, dict)
        assert waterfall["requests"] == []

    def test_engine_clear_captures(self):
        from core.browser_engine import BrowserEngine, NetworkRequest
        engine = BrowserEngine()
        engine._network_requests.append(
            NetworkRequest(url="test", method="GET", status=200, resource_type="fetch")
        )
        engine.clear_captures()
        assert len(engine._network_requests) == 0


# ───── DOMExtractor ─────

class TestDOMExtractor:
    """Test DOM extraction scripts."""

    def test_extractor_has_methods(self):
        from core.dom_extractor import DOMExtractor
        extractor = DOMExtractor()
        assert hasattr(extractor, "extract_full")
        assert hasattr(extractor, "extract_interactive_elements")
        assert hasattr(extractor, "extract_forms")

    def test_extractor_has_new_methods(self):
        from core.dom_extractor import DOMExtractor
        extractor = DOMExtractor()
        assert hasattr(extractor, "check_accessibility")
        assert hasattr(extractor, "inspect_storage")
        assert hasattr(extractor, "search_text")
        assert hasattr(extractor, "detect_framework")

    def test_dataclasses(self):
        from core.dom_extractor import DOMNode, FormField, ContrastIssue
        node = DOMNode(tag="div", text="Hello", children=[])
        assert node.tag == "div"

        field = FormField(name="email", type="email", label="Email")
        assert field.type == "email"

        issue = ContrastIssue(
            selector="p.low", text="Low", ratio=2.5,
            foreground="#fff", background="#eee",
            required_ratio=4.5, level="AA"
        )
        assert issue.ratio == 2.5

    def test_accessibility_issue_dataclass(self):
        from core.dom_extractor import AccessibilityIssue
        issue = AccessibilityIssue(
            type="missing_alt",
            severity="error",
            selector="img.hero",
            element_tag="img",
            text="",
            details="Image missing alt text",
        )
        assert issue.severity == "error"
        assert issue.type == "missing_alt"

    def test_storage_data_dataclass(self):
        from core.dom_extractor import StorageData
        data = StorageData(
            local_storage={"theme": "dark"},
            session_storage={"token": "abc"},
            cookies=[{"name": "session", "value": "xyz"}],
        )
        assert data.local_storage["theme"] == "dark"
        assert len(data.cookies) == 1


# ───── InteractionRunner ─────

class TestInteractionRunner:
    def test_click_options(self):
        from core.interaction_runner import ClickOptions
        opts = ClickOptions(click_count=2)
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
            best_practices=80, seo=75
        )
        assert card.performance == 90

    def test_audit_config(self):
        from core.perf_analyzer import AuditConfig
        config = AuditConfig()
        assert isinstance(config.categories, list)
        assert "performance" in config.categories


# ───── ConsoleCapture ─────

class TestConsoleCapture:
    def test_captured_log(self):
        from core.console_capture import CapturedLog
        log = CapturedLog(level="error", message="Something failed", source_url="http://test.com")
        assert log.level == "error"


# ───── VisualDiff ─────

class TestVisualDiff:
    def test_diff_result(self):
        from core.visual_diff import DiffResult
        result = DiffResult(
            match=False,
            mismatch_percentage=5.2,
            total_pixels=1000,
            diff_pixel_count=52,
        )
        assert not result.match
        assert result.mismatch_percentage == 5.2


# ───── ScreenshotManager ─────

class TestScreenshotManager:
    def test_manager_creates(self):
        from core.screenshot_manager import ScreenshotManager
        mgr = ScreenshotManager()
        assert mgr is not None
