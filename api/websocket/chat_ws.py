"""
WebSocket endpoint for real-time chat with Zephyr.
Supports both Dev and User agent modes with automatic routing.
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from orchestrator.router import Router, AgentTarget

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str) -> None:
        self.active_connections.pop(session_id, None)

    async def send_json(self, session_id: str, data: dict) -> None:
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with Zephyr."""

    session_id = websocket.query_params.get("session_id", str(uuid.uuid4()))
    await manager.connect(websocket, session_id)

    # Get app state
    app = websocket.app
    session_mgr = app.state.session_manager
    agent_router = app.state.router
    dev_agent = app.state.dev_agent
    user_agent = app.state.user_agent
    ctx_builder = app.state.context_builder

    session = session_mgr.get_or_create(session_id)

    # Send welcome message
    await manager.send_json(session_id, {
        "type": "welcome",
        "session_id": session_id,
        "message": "Bonjour ! Je suis Zephyr 🦊 — Comment puis-je vous aider ?",
        "expression": "happy",
        "mode": session.mode,
    })

    try:
        while True:
            # Receive message
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"message": raw}

            message = data.get("message", "")
            url = data.get("url", session.target_url)
            forced_mode = data.get("mode")
            incoming_app_context = data.get("app_context")

            # Handle app_context messages (sent on connect or via setAppContext)
            if data.get("type") == "app_context" and incoming_app_context:
                session.app_context = incoming_app_context
                await manager.send_json(session_id, {
                    "type": "status",
                    "message": "Contexte applicatif reçu.",
                    "expression": "happy",
                })
                continue

            # Store app_context from regular messages (fallback)
            if incoming_app_context and not session.app_context:
                session.app_context = incoming_app_context

            if not message:
                continue

            # Send "thinking" state
            await manager.send_json(session_id, {
                "type": "status",
                "expression": "thinking",
                "message": "Analyse en cours...",
            })

            # Route to appropriate agent
            if forced_mode:
                target = AgentTarget(forced_mode)
                agent_router.set_mode_override(session_id, target)
            else:
                target = agent_router.route(
                    query=message,
                    session_id=session_id,
                    url=url,
                )

            session.mode = target.value

            # Build context
            try:
                if target == AgentTarget.DEV:
                    context = await ctx_builder.build_dev_context(
                        url=url, session_id=session_id
                    )
                    agent = dev_agent
                else:
                    context = await ctx_builder.build_user_context(
                        url=url,
                        session_id=session_id,
                        pages_visited=session.pages_visited,
                    )
                    agent = user_agent

                # Inject app context and user preferences into context
                if session.app_context:
                    context["app_context"] = session.app_context
                if session.user_preferences:
                    context["user_preferences"] = session.user_preferences

                # Get agent response
                response = await agent.chat(message, context, session_id)

                session.add_message("user", message)
                session.add_message("assistant", response.message)
                session.add_page(url)

                # Send response
                await manager.send_json(session_id, {
                    "type": "response",
                    "message": response.message,
                    "expression": response.expression,
                    "mode": target.value,
                    "data": response.data,
                    "suggestions": response.suggestions,
                    "session_id": session_id,
                })

            except Exception as e:
                await manager.send_json(session_id, {
                    "type": "error",
                    "message": f"Une erreur est survenue : {str(e)}",
                    "expression": "surprised",
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
