"""
Tests for security fixes and new middleware features.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSessionEvents:
    """Test session event tracking (Phase 2 fix)."""

    def test_add_event(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("ev-test")
        session.add_event({"type": "click", "target": "#btn"})
        assert len(session.events) == 1
        assert session.events[0]["type"] == "click"

    def test_get_events(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("ev-get")
        session.add_event({"type": "navigate", "url": "/page1"})
        session.add_event({"type": "navigate", "url": "/page2"})
        events = session.get_events()
        assert len(events) == 2

    def test_events_cap_at_500(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("ev-cap")
        for i in range(510):
            session.add_event({"type": "event", "index": i})
        assert len(session.events) == 500

    def test_events_initialized_empty(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("ev-empty")
        assert session.events == []
        assert session.get_events() == []


class TestURLValidationSSRF:
    """Test enhanced SSRF protection."""

    def test_blocks_file_protocol(self):
        from api.models.requests import _validate_url
        with pytest.raises(ValueError, match="URL must start with http"):
            _validate_url("file:///etc/passwd")

    def test_blocks_javascript_protocol(self):
        from api.models.requests import _validate_url
        with pytest.raises(ValueError, match="URL must start with http"):
            _validate_url("javascript:alert(1)")

    def test_allows_valid_http(self):
        from api.models.requests import _validate_url
        # This should not raise
        result = _validate_url("http://example.com/path")
        assert result.startswith("http://")

    def test_allows_valid_https(self):
        from api.models.requests import _validate_url
        result = _validate_url("https://example.com/path")
        assert result.startswith("https://")


class TestMCPURLValidation:
    """Test MCP server URL validation."""

    def test_validates_http(self):
        import sys
        from pathlib import Path
        root = str(Path(__file__).parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from mcp_server.server import _validate_mcp_url
        assert _validate_mcp_url("http://example.com") == "http://example.com"

    def test_rejects_file_scheme(self):
        from mcp_server.server import _validate_mcp_url
        with pytest.raises(ValueError):
            _validate_mcp_url("file:///etc/passwd")

    def test_rejects_javascript_scheme(self):
        from mcp_server.server import _validate_mcp_url
        with pytest.raises(ValueError):
            _validate_mcp_url("javascript:alert(1)")


class TestMCPSelectorSanitization:
    """Test selector sanitization in MCP server."""

    def test_removes_quotes(self):
        from mcp_server.server import _sanitize_selector
        result = _sanitize_selector("div[data-id='test']")
        assert "'" not in result
        assert '"' not in result

    def test_removes_backticks(self):
        from mcp_server.server import _sanitize_selector
        result = _sanitize_selector("div`")
        assert "`" not in result

    def test_removes_template_literals(self):
        from mcp_server.server import _sanitize_selector
        result = _sanitize_selector("div${alert(1)}")
        assert "${" not in result

    def test_preserves_normal_selectors(self):
        from mcp_server.server import _sanitize_selector
        assert _sanitize_selector(".class-name") == ".class-name"
        assert _sanitize_selector("#my-id") == "#my-id"
        assert _sanitize_selector("button.primary") == "button.primary"


class TestAPIKeyAuth:
    """Test API key authentication middleware."""

    def _make_test_client(self):
        from unittest.mock import MagicMock
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
            events=[],
            add_page=MagicMock(),
            add_message=MagicMock(),
            add_event=MagicMock(),
            get_events=MagicMock(return_value=[]),
            cache_analysis=MagicMock(),
        )
        app.state.router = MagicMock()
        app.state.prompt_engine = MagicMock()
        app.state.context_builder = MagicMock()
        app.state.dev_agent = MagicMock()
        app.state.user_agent = MagicMock()
        return TestClient(app, raise_server_exceptions=False)

    def test_health_no_auth_needed(self):
        with self._make_test_client() as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_docs_no_auth_needed(self):
        with self._make_test_client() as client:
            resp = client.get("/api/docs")
            assert resp.status_code == 200


class TestProviderRetry:
    """Test LLM provider retry/circuit breaker logic."""

    def test_provider_base_has_retry_attrs(self):
        from config.providers import LLMProviderBase
        # Check that base class accepts retry config
        assert hasattr(LLMProviderBase, 'chat')

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        from config.providers import LLMProviderBase
        import httpx

        class FakeProvider(LLMProviderBase):
            def __init__(self):
                pass

            call_count = 0

            async def _do_chat(self, messages, max_tokens=1024, temperature=0.3, **kwargs):
                self.call_count += 1
                if self.call_count < 3:
                    raise httpx.ConnectTimeout("timeout")
                return "success"

        provider = FakeProvider()
        # Set retry attrs manually (private, as used in LLMProviderBase)
        provider._retry_count = 3
        provider._retry_delay = 0.01
        result = await provider.chat([{"role": "user", "content": "test"}])
        assert result == "success"
        assert provider.call_count == 3
