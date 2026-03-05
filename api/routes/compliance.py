"""
Compliance endpoints — RGAA and RGPD auditing.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from api.models.requests import _validate_url
from api.models.responses import ZephyrResponse

router = APIRouter()


class ComplianceRequest(BaseModel):
    """Request for RGAA/RGPD compliance audit."""
    url: str = Field(..., description="Target URL to audit", max_length=2048)
    viewport: Optional[str] = Field("desktop", description="Viewport name")
    audit_type: str = Field(
        "full",
        description="Audit type: 'rgaa', 'rgpd', or 'full' (both)",
        pattern="^(rgaa|rgpd|full)$",
    )
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


@router.post("/audit/compliance", response_model=ZephyrResponse)
async def audit_compliance(req: ComplianceRequest, request: Request):
    """
    Run an RGAA 4.1 and/or RGPD compliance audit on a URL.

    Returns structured criteria results with conformity rates.
    """
    from core.browser_engine import BrowserEngine, VIEWPORTS
    from core.rgaa_auditor import RGAAAuditor
    from core.rgpd_auditor import RGPDAuditor

    session_mgr = request.app.state.session_manager
    session = session_mgr.get_or_create(req.session_id, target_url=req.url)

    browser = request.app.state.context_builder.browser
    vp = VIEWPORTS.get(req.viewport or "desktop", VIEWPORTS["desktop"])
    page = await browser.navigate(req.url, viewport=vp)

    data = {}
    summary_parts = []

    try:
        # RGAA Audit
        if req.audit_type in ("rgaa", "full"):
            rgaa = RGAAAuditor()
            rgaa_report = await rgaa.audit(page, url=req.url)
            data["rgaa"] = rgaa_report.to_dict()
            summary_parts.append(
                f"RGAA: {rgaa_report.conformity_rate}% conforme "
                f"({rgaa_report.conforme}/{rgaa_report.total_tested - rgaa_report.non_applicable} critères)"
            )

        # RGPD Audit
        if req.audit_type in ("rgpd", "full"):
            rgpd = RGPDAuditor()
            rgpd_report = await rgpd.audit(page, url=req.url)
            data["rgpd"] = rgpd_report.to_dict()
            summary_parts.append(
                f"RGPD: {rgpd_report.conforme}/{rgpd_report.total_checks} vérification(s) conformes, "
                f"{rgpd_report.non_conforme} non conforme(s)"
            )
    finally:
        await page.close()

    session.cache_analysis("last_compliance_audit", data)
    session.add_event({"type": "compliance_audit", "url": req.url, "audit_type": req.audit_type})

    # Build suggestions
    suggestions = []
    if "rgaa" in data:
        rgaa_data = data["rgaa"]
        if rgaa_data.get("non_conforme", 0) > 0:
            suggestions.append("Corriger les critères RGAA non conformes (voir détails)")
        if rgaa_data.get("conformity_rate", 0) < 75:
            suggestions.append("Taux de conformité RGAA insuffisant — prioriser les critères critiques")
    if "rgpd" in data:
        rgpd_data = data["rgpd"]
        if rgpd_data.get("non_conforme", 0) > 0:
            suggestions.append("Résoudre les points RGPD non conformes (priorité haute)")
        if rgpd_data.get("trackers_detected", 0) > 0:
            suggestions.append("Déclarer les trackers tiers dans la politique de cookies")

    return ZephyrResponse(
        success=True,
        message=" | ".join(summary_parts),
        data=data,
        expression="thinking" if any(s for s in summary_parts if "non conforme" in s.lower()) else "happy",
        session_id=session.session_id,
        suggestions=suggestions,
    )


@router.post("/audit/rgaa", response_model=ZephyrResponse)
async def audit_rgaa(req: ComplianceRequest, request: Request):
    """Shortcut for RGAA-only audit."""
    req.audit_type = "rgaa"
    return await audit_compliance(req, request)


@router.post("/audit/rgpd", response_model=ZephyrResponse)
async def audit_rgpd(req: ComplianceRequest, request: Request):
    """Shortcut for RGPD-only audit."""
    req.audit_type = "rgpd"
    return await audit_compliance(req, request)
