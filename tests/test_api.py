"""
Tests for API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestHealthEndpoint:
    """Test basic API endpoints."""

    @pytest.mark.asyncio
    async def test_health(self):
        from fastapi.testclient import TestClient
        from api.server import app

        # Mock lifespan dependencies
        app.state.session_manager = MagicMock()
        app.state.session_manager.get_session_count.return_value = 0
        app.state.router = MagicMock()
        app.state.prompt_engine = MagicMock()
        app.state.context_builder = MagicMock()
        app.state.dev_agent = MagicMock()
        app.state.user_agent = MagicMock()

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_status(self):
        from fastapi.testclient import TestClient
        from api.server import app

        app.state.session_manager = MagicMock()
        app.state.session_manager.get_session_count.return_value = 3

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "running"
