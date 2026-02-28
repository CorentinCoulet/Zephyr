"""
Tests for orchestrator modules.
"""

import pytest


class TestRouter:
    """Test request routing."""

    def test_router_instantiates(self):
        from orchestrator.router import Router
        router = Router()
        assert router is not None

    def test_route_dev_keywords(self):
        from orchestrator.router import Router, AgentTarget
        router = Router()
        target = router.route("J'ai une erreur console javascript")
        assert target == AgentTarget.DEV

    def test_route_user_keywords(self):
        from orchestrator.router import Router, AgentTarget
        router = Router()
        target = router.route("Comment trouver la page paramètres ?")
        assert target == AgentTarget.USER

    def test_slash_commands(self):
        from orchestrator.router import Router, AgentTarget
        router = Router()
        assert router.route("/debug crash page") == AgentTarget.DEV
        assert router.route("/guide comment créer") == AgentTarget.USER

    def test_mode_override(self):
        from orchestrator.router import Router, AgentTarget
        router = Router()
        router.set_mode_override("s1", AgentTarget.DEV)
        target = router.route("Comment naviguer ?", session_id="s1")
        assert target == AgentTarget.DEV


class TestSessionManager:
    def test_create_session(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("test-123")
        assert session.session_id == "test-123"

    def test_session_conversation(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("conv-1")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Bonjour !")
        assert len(session.conversation_history) == 2

    def test_session_destroy(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        mgr.get_or_create("to-delete")
        mgr.destroy_session("to-delete")
        assert mgr.get_session("to-delete") is None

    def test_session_user_preferences(self):
        from orchestrator.session_manager import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("prefs-1")
        session.user_preferences["language"] = "en"
        session.user_preferences["verbosity"] = "detailed"
        assert session.user_preferences["language"] == "en"
        assert session.user_preferences["verbosity"] == "detailed"


class TestContextBuilder:
    def test_context_builder_has_cache(self):
        from orchestrator.context_builder import ContextBuilder
        # invalidate_cache is an instance method
        assert hasattr(ContextBuilder, "invalidate_cache")

    def test_invalidate_cache(self):
        from orchestrator.context_builder import ContextBuilder
        from unittest.mock import MagicMock
        builder = ContextBuilder.__new__(ContextBuilder)
        builder._context_cache = {"session1_url": {"url": "http://test", "data": {}, "timestamp": 0}}
        builder.invalidate_cache("session1")
        assert len(builder._context_cache) == 0


class TestPromptEngine:
    def test_prompt_engine_instantiates(self):
        from orchestrator.prompt_engine import PromptEngine
        engine = PromptEngine()
        assert engine is not None
