"""
Tests for API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def _make_test_client():
    """Create a TestClient with mocked app state."""
    from fastapi.testclient import TestClient
    from api.server import app

    app.state.session_manager = MagicMock()
    app.state.session_manager.get_session_count.return_value = 0
    app.state.session_manager.list_sessions.return_value = []
    app.state.session_manager.get_session.return_value = None
    app.state.session_manager.get_or_create.return_value = MagicMock(
        session_id="test-session",
        mode="auto",
        target_url="",
        pages_visited=[],
        conversation_history=[],
        analysis_cache={},
        user_preferences={},
        add_page=MagicMock(),
        add_message=MagicMock(),
    )
    app.state.router = MagicMock()
    app.state.prompt_engine = MagicMock()
    app.state.context_builder = MagicMock()
    app.state.dev_agent = MagicMock()
    app.state.user_agent = MagicMock()
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    """Test basic API endpoints."""

    @pytest.mark.asyncio
    async def test_health(self):
        with _make_test_client() as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_status(self):
        from api.server import app
        app.state.session_manager = MagicMock()
        app.state.session_manager.get_session_count.return_value = 3

        with _make_test_client() as client:
            resp = client.get("/api/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "running"


class TestWidgetEndpoints:
    """Test widget SDK endpoints."""

    def test_widget_config_returns_full_schema(self):
        with _make_test_client() as client:
            resp = client.get("/api/sdk/config")
            assert resp.status_code == 200
            data = resp.json()
            assert "personas" in data
            assert "themes" in data
            assert "features" in data
            assert "modes" in data
            assert "positions" in data
            assert "sizes" in data
            assert "verbosity_levels" in data
            assert "expertise_levels" in data
            assert "keyboard_shortcuts" in data
            assert "accessibility" in data
            assert "onboarding" in data["features"] or "tooltips" in data["features"]


class TestReportEndpoints:
    """Test report endpoints."""

    def test_list_sessions(self):
        with _make_test_client() as client:
            resp = client.get("/api/sessions")
            assert resp.status_code == 200
            data = resp.json()
            assert "sessions" in data

    def test_report_404(self):
        with _make_test_client() as client:
            resp = client.get("/api/report/nonexistent")
            assert resp.status_code == 404

    def test_export_404(self):
        with _make_test_client() as client:
            resp = client.get("/api/report/nonexistent/export?format=md")
            assert resp.status_code == 404


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_allows_normal_traffic(self):
        with _make_test_client() as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200


class TestGuideEndpoints:
    """Test new guide endpoints exist."""

    def test_onboarding_progress_endpoint(self):
        with _make_test_client() as client:
            resp = client.get("/api/guide/onboarding/progress/test-session")
            assert resp.status_code == 200
            data = resp.json()
            assert "progress" in data

    def test_reset_onboarding_endpoint(self):
        with _make_test_client() as client:
            resp = client.delete("/api/guide/onboarding/progress/test-session")
            assert resp.status_code == 200
