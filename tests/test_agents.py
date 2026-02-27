"""
Tests for agents.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestDevAgent:
    """Test Dev Agent logic."""

    def test_dev_agent_instantiates(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        assert agent.name == "DevAgent"
        assert agent.mode == "dev"

    def test_dev_agent_has_system_prompt(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        assert len(agent.system_prompt) > 100

    def test_expression_detection(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        # Critical context → surprised
        ctx = {"console_errors": [{"level": "error"}] * 5}
        expr = agent._detect_expression(ctx)
        assert expr == "surprised"

        # Clean context → happy
        ctx_clean = {"console_errors": [], "network_errors": [], "contrast_issues": []}
        expr_clean = agent._detect_expression(ctx_clean)
        assert expr_clean == "happy"


class TestUserAgent:
    """Test User Agent logic."""

    def test_user_agent_instantiates(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        assert agent.name == "UserAgent"
        assert agent.mode == "user"

    def test_user_agent_has_system_prompt(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        assert "navigation" in agent.system_prompt.lower() or "guide" in agent.system_prompt.lower()


class TestBaseAgent:
    """Test base agent."""

    def test_agent_message(self):
        from agents.base_agent import AgentMessage
        msg = AgentMessage(role="user", content="Help me debug")
        assert msg.role == "user"

    def test_agent_response(self):
        from agents.base_agent import AgentResponse
        resp = AgentResponse(
            success=True,
            message="All good",
            expression="happy",
            data={},
            suggestions=["Try this"],
        )
        assert resp.success
        assert resp.expression == "happy"
