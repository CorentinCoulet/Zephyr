"""
Reports endpoints — Session history, report export.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.models.responses import AstrafoxResponse

router = APIRouter()


@router.get("/sessions")
async def list_sessions(request: Request):
    """List all active sessions."""
    session_mgr = request.app.state.session_manager
    return {"sessions": session_mgr.list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, request: Request):
    """Get details of a specific session."""
    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)

    if not session:
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found or expired"},
        )

    return {
        "session": session.to_dict(),
        "conversation": session.conversation_history,
        "pages_visited": session.pages_visited,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    """Delete a session and its data."""
    session_mgr = request.app.state.session_manager
    dev_agent = request.app.state.dev_agent
    user_agent = request.app.state.user_agent

    session_mgr.destroy_session(session_id)
    dev_agent.clear_session(session_id)
    user_agent.clear_session(session_id)

    return AstrafoxResponse(
        success=True,
        message=f"Session {session_id} deleted",
        expression="neutral",
    )


@router.get("/report/{session_id}")
async def get_report(session_id: str, request: Request):
    """Get a full report for a session (all analyses combined)."""
    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)

    if not session:
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"},
        )

    report = {
        "session_id": session_id,
        "mode": session.mode,
        "target_url": session.target_url,
        "pages_visited": session.pages_visited,
        "conversation_count": len(session.conversation_history),
        "analyses": {},
    }

    # Include cached analyses
    for key, cached in session.analysis_cache.items():
        report["analyses"][key] = {
            "timestamp": cached.get("timestamp"),
            "data_keys": list(cached.get("data", {}).keys())
            if isinstance(cached.get("data"), dict)
            else "cached",
        }

    return report
