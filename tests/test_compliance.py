"""
Tests for RGAA and RGPD compliance auditing modules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── RGAA Auditor ──────────────────────────────────────────

class TestRGAADataclasses:
    """Test RGAA data models."""

    def test_criterion_defaults(self):
        from core.rgaa_auditor import RGAACriterion, RGAAConformance, RGAASeverity
        c = RGAACriterion(
            criterion_id="1.1",
            theme="Images",
            title="Alt text",
        )
        assert c.status == RGAAConformance.CONFORME
        assert c.severity == RGAASeverity.INFO
        assert c.elements == []
        assert c.recommendation == ""

    def test_criterion_to_dict(self):
        from core.rgaa_auditor import RGAACriterion, RGAAConformance, RGAASeverity
        c = RGAACriterion(
            criterion_id="6.1",
            theme="Liens",
            title="Nom accessible des liens",
            status=RGAAConformance.NON_CONFORME,
            severity=RGAASeverity.CRITICAL,
            details="3 liens sans nom accessible",
            elements=[{"type": "link_no_name"}, {"type": "link_no_name"}, {"type": "link_no_name"}],
            recommendation="Ajouter un texte visible",
        )
        d = c.to_dict()
        assert d["criterion_id"] == "6.1"
        assert d["status"] == "non_conforme"
        assert d["severity"] == "critical"
        assert d["elements_count"] == 3
        assert len(d["elements"]) == 3

    def test_criterion_caps_elements_at_20(self):
        from core.rgaa_auditor import RGAACriterion
        c = RGAACriterion(
            criterion_id="3.2",
            theme="Couleurs",
            title="Contraste",
            elements=[{"i": i} for i in range(50)],
        )
        d = c.to_dict()
        assert d["elements_count"] == 50
        assert len(d["elements"]) == 20

    def test_report_stats(self):
        from core.rgaa_auditor import RGAAReport, RGAACriterion, RGAAConformance
        report = RGAAReport(url="http://example.com")
        report.criteria = [
            RGAACriterion(criterion_id="1.1", theme="Images", title="Alt", status=RGAAConformance.CONFORME),
            RGAACriterion(criterion_id="3.2", theme="Couleurs", title="Contraste", status=RGAAConformance.NON_CONFORME),
            RGAACriterion(criterion_id="2.1", theme="Cadres", title="Titre", status=RGAAConformance.NON_APPLICABLE),
            RGAACriterion(criterion_id="8.3", theme="Obligatoires", title="Lang", status=RGAAConformance.CONFORME),
        ]
        report.compute_stats()
        assert report.total_tested == 4
        assert report.conforme == 2
        assert report.non_conforme == 1
        assert report.non_applicable == 1
        # Rate = 2/(4-1) = 66.7%
        assert report.conformity_rate == 66.7

    def test_report_to_dict(self):
        from core.rgaa_auditor import RGAAReport, RGAACriterion, RGAAConformance
        report = RGAAReport(url="http://test.com")
        report.criteria = [
            RGAACriterion(criterion_id="1.1", theme="Images", title="Alt", status=RGAAConformance.CONFORME),
        ]
        d = report.to_dict()
        assert d["url"] == "http://test.com"
        assert d["conformity_rate"] == 100.0
        assert len(d["criteria"]) == 1

    def test_report_all_non_applicable(self):
        from core.rgaa_auditor import RGAAReport, RGAACriterion, RGAAConformance
        report = RGAAReport(url="http://empty.com")
        report.criteria = [
            RGAACriterion(criterion_id="2.1", theme="Cadres", title="Titre", status=RGAAConformance.NON_APPLICABLE),
        ]
        report.compute_stats()
        assert report.conformity_rate == 0  # No applicable criteria


class TestRGAAAuditor:
    """Test RGAA auditor with mocked Playwright page."""

    def _mock_page(self, evaluate_results=None):
        page = AsyncMock()
        page.url = "http://test.local"
        if evaluate_results:
            page.evaluate = AsyncMock(side_effect=evaluate_results)
        else:
            page.evaluate = AsyncMock(return_value=[])
        return page

    @pytest.mark.asyncio
    async def test_audit_all_pass(self):
        from core.rgaa_auditor import RGAAAuditor, RGAAConformance
        page = self._mock_page()
        # All evaluations return empty lists → conformant
        page.evaluate = AsyncMock(return_value=[])
        auditor = RGAAAuditor()
        report = await auditor.audit(page, url="http://test.local")
        assert report.url == "http://test.local"
        assert report.total_tested > 0
        assert report.non_conforme == 0

    @pytest.mark.asyncio
    async def test_audit_image_issues(self):
        from core.rgaa_auditor import RGAAAuditor, RGAAConformance
        page = AsyncMock()
        page.url = "http://test.local"

        call_count = 0
        async def side_effect(script, *args):
            nonlocal call_count
            call_count += 1
            # First call is _JS_IMAGES
            if call_count == 1:
                return [{"type": "missing_alt", "selector": "img.hero", "src": "/hero.jpg", "tag": "img", "text": "Image sans alt"}]
            return []

        page.evaluate = side_effect
        auditor = RGAAAuditor()
        report = await auditor.audit(page)
        image_criteria = [c for c in report.criteria if c.theme == "Images"]
        assert len(image_criteria) >= 1
        assert any(c.status == RGAAConformance.NON_CONFORME for c in image_criteria)

    @pytest.mark.asyncio
    async def test_audit_frames_not_applicable(self):
        from core.rgaa_auditor import RGAAAuditor, RGAAConformance
        page = AsyncMock()
        page.url = "http://test.local"

        # _check_frames calls page.evaluate twice:
        # 1. _JS_FRAMES → no issues
        # 2. count of iframes → 0
        page.evaluate = AsyncMock(side_effect=[[], 0])
        auditor = RGAAAuditor()
        results = await auditor._check_frames(page)
        # When no frames found, should be non_applicable
        assert any(c.status == RGAAConformance.NON_APPLICABLE for c in results)


# ─── RGPD Auditor ──────────────────────────────────────────

class TestRGPDDataclasses:
    """Test RGPD data models."""

    def test_cookie_info(self):
        from core.rgpd_auditor import CookieInfo
        c = CookieInfo(
            name="_ga",
            domain=".example.com",
            secure=True,
            http_only=False,
            same_site="Lax",
            is_third_party=False,
            category="analytics",
        )
        d = c.to_dict()
        assert d["name"] == "_ga"
        assert d["category"] == "analytics"
        assert d["secure"] is True

    def test_tracker_info(self):
        from core.rgpd_auditor import TrackerInfo
        t = TrackerInfo(
            name="google_analytics",
            label="Google Analytics",
            category="analytics",
            detected_via="script",
            urls=["https://www.google-analytics.com/analytics.js"],
        )
        d = t.to_dict()
        assert d["label"] == "Google Analytics"
        assert len(d["urls"]) == 1

    def test_rgpd_check(self):
        from core.rgpd_auditor import RGPDCheck, RGPDStatus, RGPDSeverity
        check = RGPDCheck(
            check_id="RGPD-1",
            category="cookies",
            title="Cookies avant consentement",
            status=RGPDStatus.NON_CONFORME,
            severity=RGPDSeverity.CRITICAL,
            legal_reference="RGPD Art. 6",
        )
        d = check.to_dict()
        assert d["check_id"] == "RGPD-1"
        assert d["status"] == "non_conforme"
        assert d["legal_reference"] == "RGPD Art. 6"

    def test_report_stats(self):
        from core.rgpd_auditor import RGPDReport, RGPDCheck, RGPDStatus
        report = RGPDReport(url="http://test.com")
        report.checks = [
            RGPDCheck(check_id="1", category="cookies", title="T1", status=RGPDStatus.CONFORME),
            RGPDCheck(check_id="2", category="consent", title="T2", status=RGPDStatus.NON_CONFORME),
            RGPDCheck(check_id="3", category="trackers", title="T3", status=RGPDStatus.WARNING),
        ]
        report.compute_stats()
        assert report.total_checks == 3
        assert report.conforme == 1
        assert report.non_conforme == 1
        assert report.warnings == 1

    def test_report_to_dict(self):
        from core.rgpd_auditor import RGPDReport, CookieInfo, TrackerInfo
        report = RGPDReport(url="http://test.com")
        report.cookies = [
            CookieInfo(name="_ga", domain=".test.com", is_third_party=False, category="analytics"),
            CookieInfo(name="_fbp", domain=".facebook.com", is_third_party=True, category="advertising"),
        ]
        report.trackers = [
            TrackerInfo(name="ga", label="Google Analytics", category="analytics", detected_via="script"),
        ]
        d = report.to_dict()
        assert d["cookies_total"] == 2
        assert d["cookies_third_party"] == 1
        assert d["trackers_detected"] == 1
        assert "analytics" in d["tracker_categories"]


class TestRGPDCookieCategorization:
    """Test cookie categorization heuristic."""

    def test_functional_cookies(self):
        from core.rgpd_auditor import _categorize_cookie
        assert _categorize_cookie("session_id", ".example.com") == "functional"
        assert _categorize_cookie("csrf_token", ".example.com") == "functional"
        assert _categorize_cookie("tarteaucitron", ".example.com") == "functional"

    def test_analytics_cookies(self):
        from core.rgpd_auditor import _categorize_cookie
        assert _categorize_cookie("_ga", ".google.com") == "analytics"
        assert _categorize_cookie("_gid", ".google.com") == "analytics"
        assert _categorize_cookie("_hjid", ".hotjar.com") == "analytics"

    def test_advertising_cookies(self):
        from core.rgpd_auditor import _categorize_cookie
        assert _categorize_cookie("_fbp", ".facebook.com") == "advertising"
        assert _categorize_cookie("_gcl_au", ".google.com") == "advertising"

    def test_unknown_cookies(self):
        from core.rgpd_auditor import _categorize_cookie
        assert _categorize_cookie("my_custom_cookie", ".example.com") == "unknown"


class TestRGPDDomainExtraction:
    """Test domain extraction utility."""

    def test_extract_domain(self):
        from core.rgpd_auditor import _extract_domain
        assert _extract_domain("https://www.example.com/page") == "www.example.com"
        assert _extract_domain("http://localhost:3000") == "localhost"
        assert _extract_domain("invalid") == ""


class TestRGPDAuditor:
    """Test RGPD auditor with mocked page."""

    def _mock_page(self):
        page = AsyncMock()
        page.url = "http://test.local"
        page.context = AsyncMock()
        page.context.cookies = AsyncMock(return_value=[])
        page.evaluate = AsyncMock(return_value=[])
        page.content = AsyncMock(return_value="<html><body>Hello</body></html>")
        return page

    @pytest.mark.asyncio
    async def test_audit_clean_site(self):
        from core.rgpd_auditor import RGPDAuditor, RGPDStatus
        page = self._mock_page()
        # No cookies, no trackers, privacy link found
        page.evaluate = AsyncMock(side_effect=[
            # _JS_CONSENT_BANNER
            {"found": False},
            # _JS_THIRD_PARTY_SCRIPTS
            [],
            # page.content() is separate
            # _JS_PRIVACY_LINKS
            {
                "privacy_policy": {"text": "Politique de confidentialité", "href": "/privacy"},
                "legal_notice": {"text": "Mentions légales", "href": "/mentions"},
                "terms": None,
                "cookie_policy": None,
                "data_protection_officer": None,
            },
            # _JS_FORM_CONSENT
            [],
            # _JS_LOCAL_STORAGE
            {},
        ])
        page.content = AsyncMock(return_value="<html><body>Clean</body></html>")

        auditor = RGPDAuditor()
        report = await auditor.audit(page)
        assert report.total_checks > 0
        # Should have some conformant checks
        assert report.conforme > 0

    @pytest.mark.asyncio
    async def test_audit_detects_trackers_in_source(self):
        from core.rgpd_auditor import RGPDAuditor
        page = self._mock_page()
        page.content = AsyncMock(return_value='<html><body><script>gtag("js")</script></body></html>')
        page.evaluate = AsyncMock(side_effect=[
            {"found": False},  # consent banner
            [],  # third party scripts
            # _JS_PRIVACY_LINKS
            {"privacy_policy": None, "legal_notice": None, "terms": None, "cookie_policy": None, "data_protection_officer": None},
            [],  # form consent
            {},  # local storage
        ])

        auditor = RGPDAuditor()
        report = await auditor.audit(page)
        # Should detect google analytics via inline script
        ga_trackers = [t for t in report.trackers if "google" in t.name.lower()]
        assert len(ga_trackers) > 0


class TestKnownTrackers:
    """Test tracker pattern definitions."""

    def test_tracker_patterns_are_defined(self):
        from core.rgpd_auditor import KNOWN_TRACKERS
        assert "google_analytics" in KNOWN_TRACKERS
        assert "facebook_pixel" in KNOWN_TRACKERS
        assert "hotjar" in KNOWN_TRACKERS
        assert len(KNOWN_TRACKERS) >= 10

    def test_all_trackers_have_required_fields(self):
        from core.rgpd_auditor import KNOWN_TRACKERS
        for name, info in KNOWN_TRACKERS.items():
            assert "label" in info, f"{name} missing label"
            assert "patterns" in info, f"{name} missing patterns"
            assert "category" in info, f"{name} missing category"
            assert len(info["patterns"]) > 0, f"{name} has no patterns"


# ─── Compliance API Route ──────────────────────────────────

class TestComplianceModels:
    """Test compliance request model validation."""

    def test_valid_request(self):
        from api.routes.compliance import ComplianceRequest
        req = ComplianceRequest(url="http://localhost:3000", audit_type="full")
        assert req.audit_type == "full"

    def test_rgaa_only(self):
        from api.routes.compliance import ComplianceRequest
        req = ComplianceRequest(url="http://example.com", audit_type="rgaa")
        assert req.audit_type == "rgaa"

    def test_rgpd_only(self):
        from api.routes.compliance import ComplianceRequest
        req = ComplianceRequest(url="http://example.com", audit_type="rgpd")
        assert req.audit_type == "rgpd"

    def test_invalid_audit_type(self):
        from pydantic import ValidationError
        from api.routes.compliance import ComplianceRequest
        with pytest.raises(ValidationError):
            ComplianceRequest(url="http://example.com", audit_type="invalid")

    def test_url_validation(self):
        from pydantic import ValidationError
        from api.routes.compliance import ComplianceRequest
        with pytest.raises(ValidationError):
            ComplianceRequest(url="file:///etc/passwd", audit_type="full")
