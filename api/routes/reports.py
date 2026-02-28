"""
Reports endpoints — Session history, report export (JSON / Markdown / HTML).
"""

import time

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

from api.models.responses import ZephyrResponse

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

    return ZephyrResponse(
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


@router.get("/report/{session_id}/export")
async def export_report(
    session_id: str,
    request: Request,
    format: str = Query("md", description="Export format: json, md, html"),
):
    """Export a session report in JSON, Markdown, or HTML format."""
    session_mgr = request.app.state.session_manager
    session = session_mgr.get_session(session_id)

    if not session:
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"},
        )

    # Build report data
    report_data = {
        "session_id": session_id,
        "mode": session.mode,
        "target_url": session.target_url,
        "pages_visited": session.pages_visited,
        "conversation_count": len(session.conversation_history),
        "created_at": session.created_at,
        "analyses": {},
    }

    for key, cached in session.analysis_cache.items():
        report_data["analyses"][key] = cached.get("data", {})

    if format == "json":
        return report_data

    elif format == "md":
        md = _render_markdown(report_data, session)
        return PlainTextResponse(content=md, media_type="text/markdown")

    elif format == "html":
        html = _render_html(report_data, session)
        return HTMLResponse(content=html)

    return JSONResponse(
        status_code=400,
        content={"error": f"Unknown format: {format}. Use json, md, or html."},
    )


def _render_markdown(data: dict, session) -> str:
    """Render a session report as Markdown."""
    lines = [
        f"# 🦊 Zephyr Report — {data['session_id'][:8]}",
        "",
        f"**Mode:** {data['mode']}  ",
        f"**URL:** {data['target_url']}  ",
        f"**Pages visited:** {len(data['pages_visited'])}  ",
        f"**Messages:** {data['conversation_count']}  ",
        "",
        "---",
        "",
    ]

    # Pages
    if data["pages_visited"]:
        lines.append("## Pages Visited")
        for p in data["pages_visited"]:
            lines.append(f"- {p}")
        lines.append("")

    # Conversation
    if session.conversation_history:
        lines.append("## Conversation")
        lines.append("")
        for msg in session.conversation_history:
            role = msg["role"].capitalize()
            content = msg["content"][:500]
            lines.append(f"**{role}:**  ")
            lines.append(f"{content}")
            lines.append("")

    # Analyses
    if data["analyses"]:
        lines.append("## Analyses")
        lines.append("")
        for key, analysis in data["analyses"].items():
            lines.append(f"### {key}")
            if isinstance(analysis, dict):
                for k, v in analysis.items():
                    lines.append(f"- **{k}:** {v}")
            else:
                lines.append(f"{analysis}")
            lines.append("")

    return "\n".join(lines)


def _render_html(data: dict, session) -> str:
    """Render a session report as HTML."""
    md = _render_markdown(data, session)
    # Simple markdown-to-html conversion
    html_body = md
    html_body = html_body.replace("# 🦊", "<h1>🦊")
    html_body = html_body.replace("\n## ", "\n<h2>")
    html_body = html_body.replace("\n### ", "\n<h3>")

    # Wrap in proper HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Zephyr Report — {data['session_id'][:8]}</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
        h1 {{ color: #ff6b35; border-bottom: 2px solid #ff6b35; padding-bottom: 0.5rem; }}
        h2 {{ color: #444; margin-top: 2rem; }}
        h3 {{ color: #666; }}
        pre {{ background: #f5f5f5; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
        .meta {{ background: #fff8f0; padding: 1rem; border-left: 3px solid #ff6b35; margin: 1rem 0; }}
    </style>
</head>
<body>
    <div class="meta">
        <strong>Mode:</strong> {data['mode']} |
        <strong>URL:</strong> {data['target_url']} |
        <strong>Messages:</strong> {data['conversation_count']}
    </div>
    <pre>{md}</pre>
</body>
</html>"""
