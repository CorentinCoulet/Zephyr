"""
Tests for input validation, security, and error handling.
"""

import pytest
from pydantic import ValidationError


class TestURLValidation:
    """Test URL validation prevents SSRF attacks."""

    def test_valid_http_url(self):
        from unittest.mock import patch
        from api.models.requests import AnalyzeRequest
        with patch("config.settings.settings") as mock_settings:
            mock_settings.target_url = "http://localhost:3000"
            req = AnalyzeRequest(url="http://localhost:3000")
            assert req.url == "http://localhost:3000"

    def test_valid_https_url(self):
        from api.models.requests import AnalyzeRequest
        req = AnalyzeRequest(url="https://example.com/path?q=1")
        assert req.url.startswith("https://")

    def test_reject_file_protocol(self):
        from api.models.requests import AnalyzeRequest
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(url="file:///etc/passwd")
        assert "URL must start with http" in str(exc_info.value)

    def test_reject_ftp_protocol(self):
        from api.models.requests import AnalyzeRequest
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="ftp://malicious.com/exploit")

    def test_reject_javascript_protocol(self):
        from api.models.requests import AnalyzeRequest
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="javascript:alert(1)")

    def test_reject_data_protocol(self):
        from api.models.requests import DebugRequest
        with pytest.raises(ValidationError):
            DebugRequest(url="data:text/html,<h1>test</h1>", query="test")

    def test_reject_empty_url(self):
        from api.models.requests import AnalyzeRequest
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="")


class TestFieldLengthLimits:
    """Test field length constraints."""

    def test_url_max_length(self):
        from api.models.requests import AnalyzeRequest
        long_url = "http://example.com/" + "a" * 3000
        with pytest.raises(ValidationError):
            AnalyzeRequest(url=long_url)

    def test_message_max_length(self):
        from api.models.requests import ChatRequest
        long_msg = "x" * 5000
        with pytest.raises(ValidationError):
            ChatRequest(message=long_msg)

    def test_session_id_max_length(self):
        from api.models.requests import AnalyzeRequest
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="http://test.com", session_id="x" * 200)


class TestModeValidation:
    """Test mode field validation on ChatRequest."""

    def test_valid_modes(self):
        from api.models.requests import ChatRequest
        for mode in ("dev", "user", None):
            req = ChatRequest(message="hello", mode=mode)
            assert req.mode == mode

    def test_invalid_mode(self):
        from api.models.requests import ChatRequest
        with pytest.raises(ValidationError):
            ChatRequest(message="hello", mode="admin")


class TestErrorResponseModel:
    """Test the unified error response model."""

    def test_error_response(self):
        from api.models.responses import ErrorResponse
        err = ErrorResponse(error="Not found", detail="Session does not exist", status_code=404)
        assert err.success is False
        assert err.status_code == 404

    def test_error_response_defaults(self):
        from api.models.responses import ErrorResponse
        err = ErrorResponse()
        assert err.success is False
        assert err.status_code == 500


class TestConversationTrimming:
    """Test that agent conversations don't grow unbounded."""

    def test_max_conversation_length(self):
        from agents.base_agent import BaseAgent, AgentMessage
        assert BaseAgent.MAX_CONVERSATION_LENGTH == 50

    def test_conversation_structure(self):
        from agents.base_agent import AgentMessage
        msg = AgentMessage(role="user", content="test")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "test"


class TestSecurityHeaders:
    """Test that security headers middleware is present."""

    def test_security_headers_on_response(self):
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient
        from api.server import app

        app.state.session_manager = MagicMock()
        app.state.session_manager.get_session_count.return_value = 0
        app.state.router = MagicMock()
        app.state.prompt_engine = MagicMock()
        app.state.context_builder = MagicMock()
        app.state.dev_agent = MagicMock()
        app.state.user_agent = MagicMock()

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/health")
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"
            assert resp.headers.get("X-Frame-Options") == "DENY"
            assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
