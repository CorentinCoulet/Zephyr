"""
Tests for CI endpoints (api/routes/ci.py).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _make_test_client():
    """Create a TestClient with mocked app state."""
    from api.server import app

    mock_browser = MagicMock()
    mock_browser.navigate = AsyncMock(return_value=MagicMock())
    mock_browser.get_console_messages.return_value = []
    mock_browser.get_network_errors.return_value = []

    mock_ctx = MagicMock()
    mock_ctx.browser = mock_browser

    app.state.session_manager = MagicMock()
    app.state.session_manager.get_session_count.return_value = 0
    app.state.session_manager.list_sessions.return_value = []
    app.state.session_manager.get_or_create.return_value = MagicMock(
        session_id="test", mode="auto", target_url="",
        pages_visited=[], conversation_history=[], analysis_cache={},
        user_preferences={}, add_page=MagicMock(), add_message=MagicMock(),
        app_context=None,
    )
    app.state.router = MagicMock()
    app.state.prompt_engine = MagicMock()
    app.state.context_builder = mock_ctx
    app.state.dev_agent = MagicMock()
    app.state.user_agent = MagicMock()
    return TestClient(app, raise_server_exceptions=False)


class TestCIEndpoint:
    """Test CI quality check endpoint."""

    def test_ci_check_returns_result_structure(self):
        """Test that CI check returns proper result structure."""
        with _make_test_client() as client:
            with patch("core.dom_extractor.DOMExtractor") as mock_dom_cls, \
                 patch("config.settings.settings") as mock_settings:
                mock_settings.target_url = "http://localhost:3000"
                mock_settings.debug = False
                mock_settings.widget_api_key = ""
                mock_dom = MagicMock()
                mock_dom.check_accessibility = AsyncMock(return_value=[])
                mock_dom.check_contrast = AsyncMock(return_value=[])
                mock_dom_cls.return_value = mock_dom

                resp = client.post("/api/ci/check", json={
                    "url": "http://localhost:3000",
                    "viewport": "desktop",
                })
                # May fail due to mocking complexity, but should return 200
                assert resp.status_code == 200
                data = resp.json()
                assert "passed" in data
                assert "errors" in data

    def test_ci_check_invalid_url(self):
        """Test CI check with invalid URL returns validation error."""
        with _make_test_client() as client:
            resp = client.post("/api/ci/check", json={
                "url": "file:///etc/passwd",
            })
            # Should fail URL validation and return 422
            assert resp.status_code == 422


class TestCICheckModel:
    """Test CI check request/response models."""

    def test_ci_check_request_defaults(self):
        from api.routes.ci import CICheckRequest
        req = CICheckRequest(url="http://example.com")
        assert req.thresholds["max_errors"] == 0
        assert req.thresholds["max_warnings"] == 5
        assert req.viewport == "desktop"
        assert req.include_perf is False

    def test_ci_check_result_defaults(self):
        from api.routes.ci import CICheckResult
        result = CICheckResult()
        assert result.passed is True
        assert result.errors == []
        assert result.warnings == []
