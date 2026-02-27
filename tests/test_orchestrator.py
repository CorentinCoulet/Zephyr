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


class TestPromptEngine:
    def test_prompt_engine_instantiates(self):
        from orchestrator.prompt_engine import PromptEngine
        engine = PromptEngine()
        assert engine is not None
