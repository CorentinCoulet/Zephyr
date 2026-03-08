"""
Shared test fixtures for Zephyr Intelligence Platform.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_session():
    """Return a mock session object matching SessionManager.get_or_create()."""
    return MagicMock(
        session_id="test-session",
        mode="auto",
        target_url="",
        pages_visited=[],
        conversation_history=[],
        analysis_cache={},
        user_preferences={},
        events=[],
        add_page=MagicMock(),
        add_message=MagicMock(),
        add_event=MagicMock(),
        get_events=MagicMock(return_value=[]),
        app_context=None,
    )


@pytest.fixture
def mock_session_manager(mock_session):
    """Return a mock SessionManager with common defaults."""
    mgr = MagicMock()
    mgr.get_session_count.return_value = 0
    mgr.list_sessions.return_value = []
    mgr.get_session.return_value = None
    mgr.get_or_create.return_value = mock_session
    return mgr


@pytest.fixture
def mock_browser():
    """Return a mock BrowserEngine."""
    browser = MagicMock()
    browser.navigate = AsyncMock(return_value=MagicMock())
    browser.screenshot = AsyncMock(return_value=b"\x89PNG")
    browser.close = AsyncMock()
    browser.launch = AsyncMock()
    browser.get_console_messages.return_value = []
    browser.get_network_errors.return_value = []
    browser.get_network_requests.return_value = []
    browser.get_network_waterfall.return_value = {"requests": []}
    browser.clear_captures = MagicMock()
    return browser


@pytest.fixture
def mock_context_builder(mock_browser):
    """Return a mock ContextBuilder."""
    ctx = MagicMock()
    ctx.browser = mock_browser
    return ctx


@pytest.fixture
def app_client(mock_session_manager, mock_context_builder):
    """
    Create a FastAPI TestClient with fully mocked app state.

    Usage:
        def test_something(self, app_client):
            with app_client as client:
                resp = client.get("/api/health")
    """
    from api.server import app

    app.state.session_manager = mock_session_manager
    app.state.router = MagicMock()
    app.state.prompt_engine = MagicMock()
    app.state.context_builder = mock_context_builder
    app.state.dev_agent = MagicMock()
    app.state.user_agent = MagicMock()
    return TestClient(app, raise_server_exceptions=False)
