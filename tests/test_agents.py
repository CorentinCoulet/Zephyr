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
        assert agent.agent_name == "dev_agent"
        assert agent.agent_mode == "dev"

    def test_dev_agent_has_system_prompt(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        assert len(agent.get_system_prompt()) > 100

    def test_expression_detection(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        # Critical context → surprised
        ctx = {"console_errors": [{"level": "error"}] * 5}
        expr = agent._detect_expression("🔴 Erreur critique détectée", ctx)
        assert expr == "surprised"

        # Clean context with positive words → happy
        ctx_clean = {"console_errors": [], "network_errors": [], "contrast_issues": []}
        expr_clean = agent._detect_expression("Aucun problème détecté, tout est bon", ctx_clean)
        assert expr_clean == "happy"

    def test_summarize_dom(self):
        from agents.dev_agent import DevAgent
        dom = {
            "tag": "html",
            "children": [
                {"tag": "body", "children": [
                    {"tag": "header", "children": []},
                    {"tag": "main", "children": [
                        {"tag": "div", "children": [
                            {"tag": "p", "children": []},
                            {"tag": "a", "children": [], "attributes": {"href": "/test"}},
                        ]},
                    ]},
                    {"tag": "footer", "children": []},
                ]}
            ]
        }
        summary = DevAgent._summarize_dom(dom)
        assert isinstance(summary, str)
        assert len(summary) > 10
        # Should contain node count and tag info
        assert "html" in summary.lower() or "Nœuds" in summary or "noeud" in summary.lower()

    def test_count_issues_with_accessibility(self):
        from agents.dev_agent import DevAgent
        agent = DevAgent()
        ctx = {
            "console_errors": [{"level": "error"}, {"level": "error"}],
            "network_errors": [{"url": "http://x"}],
            "contrast_issues": [],
            "accessibility_issues": [
                {"issue_type": "missing_alt", "severity": "error"},
                {"issue_type": "missing_label", "severity": "warning"},
            ],
        }
        count = agent._count_issues(ctx)
        assert count >= 5  # 2 console + 1 network + 2 a11y


class TestUserAgent:
    """Test User Agent logic."""

    def test_user_agent_instantiates(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        assert agent.agent_name == "user_agent"
        assert agent.agent_mode == "user"

    def test_user_agent_has_system_prompt(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        prompt = agent.get_system_prompt()
        assert "navigation" in prompt.lower() or "guide" in prompt.lower()

    def test_user_agent_preferences_prompt(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        prefs = {"language": "en", "verbosity": "detailed", "expertise_level": "advanced"}
        prompt = agent.get_system_prompt(preferences=prefs)
        assert "en" in prompt.lower() or "english" in prompt.lower() or "language" in prompt.lower()

    def test_onboarding_progress_tracking(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        sid = "test-onboard-123"
        agent.reset_onboarding(sid)

        agent.mark_onboarding_step(sid, 1)
        agent.mark_onboarding_step(sid, 2)
        progress = agent.get_onboarding_progress(sid)
        assert 1 in progress.get("completed", [])
        assert 2 in progress.get("completed", [])

        agent.reset_onboarding(sid)
        progress = agent.get_onboarding_progress(sid)
        assert len(progress.get("completed", [])) == 0

    def test_user_agent_has_new_methods(self):
        from agents.user_agent import UserAgent
        agent = UserAgent()
        assert hasattr(agent, "generate_page_tooltips")
        assert hasattr(agent, "analyze_friction")


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
