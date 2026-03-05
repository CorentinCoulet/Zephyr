"""
CI endpoints — Automated quality checks for CI/CD pipelines.
Returns structured pass/fail results for accessibility, performance, and errors.
"""

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from api.models.requests import _validate_url

logger = logging.getLogger("zephyr.ci")
router = APIRouter()


class CICheckRequest(BaseModel):
    """Request for CI quality check."""
    url: str = Field(..., description="URL to check", max_length=2048)
    thresholds: dict = Field(
        default_factory=lambda: {
            "max_errors": 0,
            "max_warnings": 5,
            "min_perf_score": 60,
            "max_a11y_issues": 0,
        },
        description="Pass/fail thresholds",
    )
    viewport: str = Field("desktop", description="Viewport to test")
    include_perf: bool = Field(False, description="Include perf audit (slower)")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_url(v)


class CICheckResult(BaseModel):
    """Result of a CI quality check."""
    passed: bool = True
    url: str = ""
    summary: str = ""
    checks: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


@router.post("/ci/check", response_model=CICheckResult)
async def ci_check(req: CICheckRequest, request: Request):
    """
    Run automated quality checks suitable for CI pipelines.
    Returns structured pass/fail with details on each check category.
    """
    ctx_builder = request.app.state.context_builder
    browser = ctx_builder.browser

    errors: list[str] = []
    warnings: list[str] = []
    checks: dict = {}
    all_passed = True
    page = None

    try:
        # Navigate
        page = await browser.navigate(req.url)
        if not page:
            return CICheckResult(
                passed=False,
                url=req.url,
                summary="Failed to navigate to URL",
                errors=["Navigation failed"],
            )

        # 1. Console errors
        console_messages = browser.get_console_messages()
        js_errors = [e for e in console_messages if e.type == "error"]
        js_warnings = [e for e in console_messages if e.type == "warning"]

        max_errors = req.thresholds.get("max_errors", 0)
        error_pass = len(js_errors) <= max_errors
        checks["console_errors"] = {
            "passed": error_pass,
            "count": len(js_errors),
            "threshold": max_errors,
            "details": [e.text for e in js_errors[:10]],
        }
        if not error_pass:
            all_passed = False
            errors.append(f"Console errors: {len(js_errors)} (max: {max_errors})")

        max_warnings = req.thresholds.get("max_warnings", 5)
        warning_pass = len(js_warnings) <= max_warnings
        checks["console_warnings"] = {
            "passed": warning_pass,
            "count": len(js_warnings),
            "threshold": max_warnings,
        }
        if not warning_pass:
            warnings.append(f"Console warnings: {len(js_warnings)} (max: {max_warnings})")

        # 2. Network errors (4xx/5xx)
        network_errors = browser.get_network_errors()
        net_pass = len(network_errors) <= max_errors
        checks["network_errors"] = {
            "passed": net_pass,
            "count": len(network_errors),
            "threshold": max_errors,
            "details": [
                {"url": r.url, "status": r.status}
                for r in network_errors[:10]
            ],
        }
        if not net_pass:
            all_passed = False
            errors.append(f"Network errors: {len(network_errors)}")

        # 3. Accessibility
        from core.dom_extractor import DOMExtractor
        extractor = DOMExtractor()
        a11y_issues = await extractor.check_accessibility(page)
        max_a11y = req.thresholds.get("max_a11y_issues", 0)
        a11y_pass = len(a11y_issues) <= max_a11y
        checks["accessibility"] = {
            "passed": a11y_pass,
            "count": len(a11y_issues),
            "threshold": max_a11y,
            "details": [
                {"type": i.type, "severity": i.severity, "selector": i.selector}
                for i in a11y_issues[:10]
            ],
        }
        if not a11y_pass:
            all_passed = False
            errors.append(f"Accessibility issues: {len(a11y_issues)} (max: {max_a11y})")

        # 4. Performance (optional)
        if req.include_perf:
            from core.perf_analyzer import PerfAnalyzer
            analyzer = PerfAnalyzer()
            perf_data = await analyzer.run_audit(req.url)
            perf_score = perf_data.get("score", 0) if perf_data else 0
            min_score = req.thresholds.get("min_perf_score", 60)
            perf_pass = perf_score >= min_score
            checks["performance"] = {
                "passed": perf_pass,
                "score": perf_score,
                "threshold": min_score,
            }
            if not perf_pass:
                all_passed = False
                errors.append(f"Performance score: {perf_score} (min: {min_score})")
        else:
            checks["performance"] = {"passed": True, "skipped": True}

        # 5. Contrast check
        contrast_issues = await extractor.check_contrast(page)
        contrast_fails = [c for c in contrast_issues if c.ratio < 4.5]
        checks["contrast"] = {
            "passed": len(contrast_fails) == 0,
            "count": len(contrast_fails),
            "details": contrast_fails[:5],
        }
        if contrast_fails:
            all_passed = False
            errors.append(f"Contrast failures: {len(contrast_fails)}")

        summary_parts = []
        for name, check in checks.items():
            status = "PASS" if check.get("passed") else "FAIL"
            if check.get("skipped"):
                status = "SKIP"
            summary_parts.append(f"{name}: {status}")

        return CICheckResult(
            passed=all_passed,
            url=req.url,
            summary=" | ".join(summary_parts),
            checks=checks,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        return CICheckResult(
            passed=False,
            url=req.url,
            summary=f"Check failed: {str(e)}",
            errors=[str(e)],
        )
    finally:
        try:
            if page:
                await page.close()
        except Exception:
            pass
