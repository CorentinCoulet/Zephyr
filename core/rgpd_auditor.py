"""
RGPD Auditor — Automated GDPR/RGPD compliance checker for web pages.

Checks include:
  - Cookie analysis (before/after consent interaction)
  - Consent banner detection
  - Third-party tracker detection (analytics, advertising, social)
  - Privacy policy and legal notice presence
  - Form consent patterns
  - Data collection inventory

Uses Playwright to interact with the live page and inspect network activity,
cookies, localStorage, and DOM content.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from playwright.async_api import Page, BrowserContext


class RGPDSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class RGPDStatus(str, Enum):
    CONFORME = "conforme"
    NON_CONFORME = "non_conforme"
    WARNING = "warning"
    NON_APPLICABLE = "non_applicable"


# ─── Known third-party tracker patterns ───────────────────────

KNOWN_TRACKERS = {
    "google_analytics": {
        "label": "Google Analytics",
        "patterns": [
            "google-analytics.com", "analytics.google.com",
            "googletagmanager.com", "gtag/js", "gtag(", "ga.js", "analytics.js",
        ],
        "category": "analytics",
    },
    "google_ads": {
        "label": "Google Ads",
        "patterns": [
            "googleads.g.doubleclick.net", "googlesyndication.com",
            "googleadservices.com", "adservice.google.com",
        ],
        "category": "advertising",
    },
    "facebook_pixel": {
        "label": "Facebook Pixel",
        "patterns": [
            "connect.facebook.net", "facebook.com/tr",
            "fbevents.js", "fbq(", "pixel.facebook.com",
        ],
        "category": "advertising",
    },
    "hotjar": {
        "label": "Hotjar",
        "patterns": ["static.hotjar.com", "hotjar.com", "hj("],
        "category": "analytics",
    },
    "mixpanel": {
        "label": "Mixpanel",
        "patterns": ["cdn.mxpnl.com", "mixpanel.com", "api-js.mixpanel.com"],
        "category": "analytics",
    },
    "hubspot": {
        "label": "HubSpot",
        "patterns": ["js.hs-scripts.com", "js.hs-analytics.net", "hubspot.com"],
        "category": "marketing",
    },
    "linkedin_insight": {
        "label": "LinkedIn Insight Tag",
        "patterns": ["snap.licdn.com", "linkedin.com/px"],
        "category": "advertising",
    },
    "tiktok_pixel": {
        "label": "TikTok Pixel",
        "patterns": ["analytics.tiktok.com", "tiktok.com/i18n/pixel"],
        "category": "advertising",
    },
    "twitter_pixel": {
        "label": "Twitter/X Pixel",
        "patterns": ["static.ads-twitter.com", "t.co/i/adsct", "analytics.twitter.com"],
        "category": "advertising",
    },
    "matomo": {
        "label": "Matomo (Piwik)",
        "patterns": ["matomo.js", "piwik.js", "matomo.php", "piwik.php"],
        "category": "analytics",
    },
    "segment": {
        "label": "Segment",
        "patterns": ["cdn.segment.com", "api.segment.io"],
        "category": "analytics",
    },
    "amplitude": {
        "label": "Amplitude",
        "patterns": ["cdn.amplitude.com", "api.amplitude.com", "amplitude.js"],
        "category": "analytics",
    },
    "intercom": {
        "label": "Intercom",
        "patterns": ["widget.intercom.io", "js.intercomcdn.com", "intercom.io"],
        "category": "marketing",
    },
    "crisp": {
        "label": "Crisp Chat",
        "patterns": ["client.crisp.chat", "crisp.chat"],
        "category": "marketing",
    },
    "clarity": {
        "label": "Microsoft Clarity",
        "patterns": ["clarity.ms", "www.clarity.ms"],
        "category": "analytics",
    },
    "sentry": {
        "label": "Sentry",
        "patterns": ["browser.sentry-cdn.com", "sentry.io", "ingest.sentry.io"],
        "category": "monitoring",
    },
}


@dataclass
class CookieInfo:
    """Detailed cookie information."""
    name: str
    domain: str
    path: str = "/"
    value_preview: str = ""
    secure: bool = False
    http_only: bool = False
    same_site: str = ""
    expires: str = ""
    size: int = 0
    is_third_party: bool = False
    category: str = "unknown"  # functional, analytics, advertising, social, unknown

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "path": self.path,
            "secure": self.secure,
            "http_only": self.http_only,
            "same_site": self.same_site,
            "is_third_party": self.is_third_party,
            "category": self.category,
            "size": self.size,
        }


@dataclass
class TrackerInfo:
    """Detected third-party tracker."""
    name: str
    label: str
    category: str  # analytics, advertising, marketing, social, monitoring
    detected_via: str  # "script", "network", "cookie", "localstorage"
    urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "category": self.category,
            "detected_via": self.detected_via,
            "urls": self.urls[:5],
        }


@dataclass
class RGPDCheck:
    """Result for a single RGPD compliance check."""
    check_id: str
    category: str  # cookies, consent, trackers, privacy_policy, forms, data_retention
    title: str
    status: RGPDStatus = RGPDStatus.CONFORME
    severity: RGPDSeverity = RGPDSeverity.INFO
    details: str = ""
    elements: list[dict] = field(default_factory=list)
    recommendation: str = ""
    legal_reference: str = ""  # RGPD article reference

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "title": self.title,
            "status": self.status.value,
            "severity": self.severity.value,
            "details": self.details,
            "elements_count": len(self.elements),
            "elements": self.elements[:15],
            "recommendation": self.recommendation,
            "legal_reference": self.legal_reference,
        }


@dataclass
class RGPDReport:
    """Full RGPD compliance audit report."""
    url: str
    checks: list[RGPDCheck] = field(default_factory=list)
    cookies: list[CookieInfo] = field(default_factory=list)
    trackers: list[TrackerInfo] = field(default_factory=list)
    total_checks: int = 0
    conforme: int = 0
    non_conforme: int = 0
    warnings: int = 0

    def compute_stats(self):
        self.total_checks = len(self.checks)
        self.conforme = sum(1 for c in self.checks if c.status == RGPDStatus.CONFORME)
        self.non_conforme = sum(1 for c in self.checks if c.status == RGPDStatus.NON_CONFORME)
        self.warnings = sum(1 for c in self.checks if c.status == RGPDStatus.WARNING)

    def to_dict(self) -> dict:
        self.compute_stats()
        return {
            "url": self.url,
            "total_checks": self.total_checks,
            "conforme": self.conforme,
            "non_conforme": self.non_conforme,
            "warnings": self.warnings,
            "cookies_total": len(self.cookies),
            "cookies_third_party": sum(1 for c in self.cookies if c.is_third_party),
            "trackers_detected": len(self.trackers),
            "tracker_categories": list(set(t.category for t in self.trackers)),
            "checks": [c.to_dict() for c in self.checks],
            "cookies": [c.to_dict() for c in self.cookies],
            "trackers": [t.to_dict() for t in self.trackers],
        }


# ─── JavaScript snippets ─────────────────────────────────────

_JS_CONSENT_BANNER = """
() => {
    // Detect consent/cookie banners
    const keywords = [
        'cookie', 'consent', 'rgpd', 'gdpr', 'privacy', 'consentement',
        'accepter', 'accept', 'refuser', 'refuse', 'paramétrer', 'préférences',
        'données personnelles', 'personal data', 'vie privée'
    ];
    const bannerSelectors = [
        '[class*="cookie"]', '[class*="consent"]', '[class*="gdpr"]', '[class*="rgpd"]',
        '[class*="privacy"]', '[id*="cookie"]', '[id*="consent"]', '[id*="gdpr"]',
        '[id*="rgpd"]', '[id*="privacy"]', '#tarteaucitron', '.cc-window',
        '.cky-consent-container', '#onetrust-banner-sdk', '#didomi-host',
        '.osano-cm-dialog', '#CybotCookiebotDialog', '.otCenterRounded',
        '[data-nosnippet]'
    ];

    let banner = null;
    let method = '';

    // Method 1: CSS selectors
    for (const sel of bannerSelectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetHeight > 0) {
            banner = el;
            method = 'selector';
            break;
        }
    }

    // Method 2: keyword search in visible elements
    if (!banner) {
        const allElements = document.querySelectorAll('div, section, aside, dialog');
        for (const el of allElements) {
            if (el.offsetHeight === 0 || el.offsetWidth === 0) continue;
            const text = (el.textContent || '').toLowerCase();
            const matchCount = keywords.filter(k => text.includes(k)).length;
            if (matchCount >= 3 && text.length < 3000) {
                banner = el;
                method = 'keywords';
                break;
            }
        }
    }

    if (!banner) return {found: false};

    const text = banner.textContent.trim().substring(0, 500);
    const buttons = [...banner.querySelectorAll('button, a[role="button"], [class*="btn"], input[type="button"]')];
    const buttonTexts = buttons.map(b => ({
        text: b.textContent.trim().substring(0, 60),
        selector: b.id ? '#' + b.id : b.tagName.toLowerCase() + (b.className ? '.' + b.className.trim().split(/\\s+/).join('.') : ''),
    }));

    const hasAcceptAll = buttons.some(b => {
        const t = (b.textContent || '').toLowerCase();
        return t.includes('tout accepter') || t.includes('accept all') || t.includes('accepter');
    });
    const hasRejectAll = buttons.some(b => {
        const t = (b.textContent || '').toLowerCase();
        return t.includes('tout refuser') || t.includes('reject all') || t.includes('refuser');
    });
    const hasSettings = buttons.some(b => {
        const t = (b.textContent || '').toLowerCase();
        return t.includes('paramétrer') || t.includes('personnaliser') || t.includes('settings') ||
               t.includes('manage') || t.includes('préférences') || t.includes('customize');
    });

    return {
        found: true,
        method,
        text,
        buttons: buttonTexts,
        hasAcceptAll,
        hasRejectAll,
        hasSettings,
    };
}
"""

_JS_PRIVACY_LINKS = """
() => {
    const links = [...document.querySelectorAll('a[href]')];
    const results = {
        privacy_policy: null,
        legal_notice: null,
        terms: null,
        cookie_policy: null,
        data_protection_officer: null,
    };

    const patterns = {
        privacy_policy: ['politique de confidentialité', 'privacy policy', 'données personnelles',
                         'personal data', 'vie privée', 'privacy notice', 'politique de protection'],
        legal_notice: ['mentions légales', 'legal notice', 'legal information', 'mentions-legales',
                       'informations légales'],
        terms: ['conditions générales', 'terms of service', 'terms and conditions', 'cgu', 'cgv',
                'conditions d\\'utilisation', 'terms of use'],
        cookie_policy: ['politique de cookies', 'cookie policy', 'gestion des cookies',
                        'politique cookies', 'cookies policy'],
        data_protection_officer: ['dpo', 'délégué à la protection', 'data protection officer',
                                   'protection des données'],
    };

    for (const link of links) {
        const text = (link.textContent || '').toLowerCase().trim();
        const href = (link.getAttribute('href') || '').toLowerCase();

        for (const [key, kws] of Object.entries(patterns)) {
            if (!results[key]) {
                for (const kw of kws) {
                    if (text.includes(kw) || href.includes(kw.replace(/[\\s']/g, '-'))) {
                        results[key] = {
                            text: link.textContent.trim().substring(0, 100),
                            href: link.href || link.getAttribute('href') || '',
                        };
                        break;
                    }
                }
            }
        }
    }

    return results;
}
"""

_JS_FORM_CONSENT = """
() => {
    const results = [];

    document.querySelectorAll('form').forEach((form, idx) => {
        const fields = form.querySelectorAll('input, select, textarea');
        if (fields.length === 0) return;

        const info = {
            formIndex: idx,
            action: form.action || '',
            method: form.method || 'GET',
            fieldCount: fields.length,
            hasConsentCheckbox: false,
            hasPrivacyLink: false,
            collectsPersonalData: false,
            personalDataFields: [],
        };

        // Detect personal data fields
        const personalTypes = ['email', 'tel', 'password'];
        const personalNames = ['name', 'nom', 'prenom', 'firstname', 'lastname', 'email',
                                'phone', 'telephone', 'address', 'adresse', 'birth', 'naissance',
                                'ssn', 'iban', 'card', 'carte'];

        fields.forEach(f => {
            const type = (f.type || '').toLowerCase();
            const name = (f.name || '').toLowerCase();
            const id = (f.id || '').toLowerCase();
            const placeholder = (f.placeholder || '').toLowerCase();
            const autocomplete = (f.getAttribute('autocomplete') || '').toLowerCase();

            const isPersonal = personalTypes.includes(type) ||
                personalNames.some(p => name.includes(p) || id.includes(p) || placeholder.includes(p)) ||
                ['name', 'email', 'tel', 'address', 'bday', 'given-name', 'family-name'].some(a => autocomplete.includes(a));

            if (isPersonal) {
                info.collectsPersonalData = true;
                info.personalDataFields.push({
                    type: type || f.tagName.toLowerCase(),
                    name: f.name || '',
                    id: f.id || '',
                });
            }
        });

        // Detect consent checkbox
        form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            const label = cb.id ? document.querySelector('label[for="' + cb.id + '"]') : cb.closest('label');
            const labelText = label ? (label.textContent || '').toLowerCase() : '';
            if (labelText.includes('consentement') || labelText.includes('consent') ||
                labelText.includes('accepte') || labelText.includes('agree') ||
                labelText.includes('conditions') || labelText.includes('privacy') ||
                labelText.includes('données personnelles') || labelText.includes('rgpd')) {
                info.hasConsentCheckbox = true;
            }
        });

        // Detect privacy link in the form
        const formLinks = form.querySelectorAll('a[href]');
        formLinks.forEach(a => {
            const text = (a.textContent || '').toLowerCase();
            if (text.includes('confidentialité') || text.includes('privacy') ||
                text.includes('données') || text.includes('conditions')) {
                info.hasPrivacyLink = true;
            }
        });

        if (info.collectsPersonalData) {
            results.push(info);
        }
    });

    return results;
}
"""

_JS_LOCAL_STORAGE = """
() => {
    const items = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        items[key] = {
            size: (value || '').length,
            preview: (value || '').substring(0, 100),
        };
    }
    return items;
}
"""

_JS_THIRD_PARTY_SCRIPTS = """
() => {
    const pageOrigin = window.location.origin;
    const scripts = [...document.querySelectorAll('script[src]')];
    return scripts
        .map(s => s.src)
        .filter(src => {
            try {
                return new URL(src).origin !== pageOrigin;
            } catch { return false; }
        });
}
"""


class RGPDAuditor:
    """Automated RGPD (GDPR) compliance auditor using Playwright."""

    async def audit(self, page: Page, url: str = "", context: Optional[BrowserContext] = None) -> RGPDReport:
        """Run all RGPD compliance checks on the given page."""
        report = RGPDReport(url=url or page.url)

        # 1. Cookie analysis
        await self._check_cookies(page, context, report)

        # 2. Consent banner
        await self._check_consent_banner(page, report)

        # 3. Third-party trackers
        await self._check_trackers(page, report)

        # 4. Privacy policy and legal pages
        await self._check_privacy_links(page, report)

        # 5. Form consent patterns
        await self._check_form_consent(page, report)

        # 6. Local storage analysis
        await self._check_local_storage(page, report)

        report.compute_stats()
        return report

    # ─── Cookie analysis ──────────────────────────────────────

    async def _check_cookies(
        self, page: Page, context: Optional[BrowserContext], report: RGPDReport
    ) -> None:
        """Analyze cookies set by the page."""
        cookies = []
        if context:
            raw_cookies = await context.cookies()
        else:
            raw_cookies = await page.context.cookies()

        page_domain = _extract_domain(page.url)

        for c in raw_cookies:
            domain = c.get("domain", "")
            is_third_party = not domain.endswith(page_domain) and domain.lstrip(".") != page_domain

            cookie = CookieInfo(
                name=c.get("name", ""),
                domain=domain,
                path=c.get("path", "/"),
                value_preview=str(c.get("value", ""))[:30],
                secure=c.get("secure", False),
                http_only=c.get("httpOnly", False),
                same_site=c.get("sameSite", ""),
                size=len(str(c.get("value", ""))),
                is_third_party=is_third_party,
                category=_categorize_cookie(c.get("name", ""), domain),
            )
            cookies.append(cookie)

        report.cookies = cookies
        third_party = [c for c in cookies if c.is_third_party]
        non_functional = [c for c in cookies if c.category not in ("functional", "necessary")]

        # RGPD-1: Cookies before consent
        if non_functional:
            report.checks.append(RGPDCheck(
                check_id="RGPD-1",
                category="cookies",
                title="Cookies non essentiels avant consentement",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.CRITICAL,
                details=(
                    f"{len(non_functional)} cookie(s) potentiellement non essentiels "
                    f"détectés au chargement de la page (avant interaction avec la bannière de consentement)."
                ),
                elements=[c.to_dict() for c in non_functional],
                recommendation=(
                    "Aucun cookie non essentiel ne doit être déposé avant le consentement "
                    "explicite de l'utilisateur. Vérifier que ces cookies sont bien nécessaires "
                    "au fonctionnement du site."
                ),
                legal_reference="RGPD Art. 6, Directive ePrivacy Art. 5(3)",
            ))
        else:
            report.checks.append(RGPDCheck(
                check_id="RGPD-1",
                category="cookies",
                title="Cookies non essentiels avant consentement",
                status=RGPDStatus.CONFORME,
                details="Aucun cookie non essentiel détecté au chargement initial.",
                legal_reference="RGPD Art. 6, Directive ePrivacy Art. 5(3)",
            ))

        # RGPD-2: Cookie security
        insecure = [c for c in cookies if not c.secure and c.name]
        no_samesite = [c for c in cookies if not c.same_site and c.name]

        if insecure:
            report.checks.append(RGPDCheck(
                check_id="RGPD-2",
                category="cookies",
                title="Sécurité des cookies",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.MAJOR,
                details=f"{len(insecure)} cookie(s) sans attribut Secure.",
                elements=[c.to_dict() for c in insecure],
                recommendation="Configurer tous les cookies avec Secure, HttpOnly et SameSite.",
                legal_reference="RGPD Art. 32 (sécurité du traitement)",
            ))

        # Third-party cookies
        if third_party:
            report.checks.append(RGPDCheck(
                check_id="RGPD-3",
                category="cookies",
                title="Cookies tiers",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.MAJOR,
                details=f"{len(third_party)} cookie(s) tiers détecté(s).",
                elements=[c.to_dict() for c in third_party],
                recommendation=(
                    "Les cookies tiers nécessitent un consentement explicite. "
                    "Lister chaque cookie tiers dans la politique de cookies avec sa finalité."
                ),
                legal_reference="RGPD Art. 6, 7",
            ))

    # ─── Consent banner ───────────────────────────────────────

    async def _check_consent_banner(self, page: Page, report: RGPDReport) -> None:
        """Check for the presence and quality of a consent banner."""
        banner = await page.evaluate(_JS_CONSENT_BANNER)

        if not banner or not banner.get("found"):
            # Check if there are any cookies/trackers that would require one
            has_tracking = len(report.trackers) > 0 or any(
                c.category not in ("functional", "necessary") for c in report.cookies
            )
            if has_tracking:
                report.checks.append(RGPDCheck(
                    check_id="RGPD-4",
                    category="consent",
                    title="Bannière de consentement",
                    status=RGPDStatus.NON_CONFORME,
                    severity=RGPDSeverity.CRITICAL,
                    details=(
                        "Aucune bannière de consentement détectée alors que des cookies "
                        "non essentiels ou trackers sont présents."
                    ),
                    recommendation=(
                        "Implémenter une bannière de consentement conforme au RGPD "
                        "(ex: Tarteaucitron, Axeptio, OneTrust, Didomi)."
                    ),
                    legal_reference="RGPD Art. 7, Directive ePrivacy Art. 5(3)",
                ))
            else:
                report.checks.append(RGPDCheck(
                    check_id="RGPD-4",
                    category="consent",
                    title="Bannière de consentement",
                    status=RGPDStatus.CONFORME,
                    severity=RGPDSeverity.INFO,
                    details=(
                        "Pas de bannière de consentement, mais aucun cookie/tracker "
                        "non essentiel détecté."
                    ),
                ))
            return

        # Banner found — check quality
        checks = []

        if not banner.get("hasRejectAll"):
            checks.append(RGPDCheck(
                check_id="RGPD-5",
                category="consent",
                title="Option 'Tout refuser'",
                status=RGPDStatus.NON_CONFORME,
                severity=RGPDSeverity.CRITICAL,
                details="La bannière ne propose pas de bouton 'Tout refuser' facilement accessible.",
                recommendation=(
                    "Le refus doit être aussi simple que l'acceptation "
                    "(CNIL, lignes directrices cookies 2020)."
                ),
                legal_reference="RGPD Art. 7(3), CNIL Délibération 2020-091",
            ))
        else:
            checks.append(RGPDCheck(
                check_id="RGPD-5",
                category="consent",
                title="Option 'Tout refuser'",
                status=RGPDStatus.CONFORME,
            ))

        if not banner.get("hasSettings"):
            checks.append(RGPDCheck(
                check_id="RGPD-6",
                category="consent",
                title="Paramétrage granulaire des cookies",
                status=RGPDStatus.NON_CONFORME,
                severity=RGPDSeverity.MAJOR,
                details="La bannière ne propose pas d'option de personnalisation des choix.",
                recommendation=(
                    "Permettre à l'utilisateur de choisir finement les catégories "
                    "de cookies (analytiques, publicitaires, etc.)."
                ),
                legal_reference="RGPD Art. 7",
            ))
        else:
            checks.append(RGPDCheck(
                check_id="RGPD-6",
                category="consent",
                title="Paramétrage granulaire des cookies",
                status=RGPDStatus.CONFORME,
            ))

        # Check banner text length (should be informative)
        banner_text = banner.get("text", "")
        if len(banner_text) < 50:
            checks.append(RGPDCheck(
                check_id="RGPD-7",
                category="consent",
                title="Information dans la bannière",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.MINOR,
                details="La bannière contient peu de texte informatif.",
                recommendation=(
                    "La bannière doit informer clairement sur les finalités des cookies, "
                    "les tiers impliqués, et les droits de l'utilisateur."
                ),
                legal_reference="RGPD Art. 13",
            ))

        report.checks.extend(checks)

    # ─── Third-party trackers ─────────────────────────────────

    async def _check_trackers(self, page: Page, report: RGPDReport) -> None:
        """Detect third-party trackers via scripts, network patterns, and DOM."""
        detected: dict[str, TrackerInfo] = {}

        # Method 1: Third-party scripts in the DOM
        third_party_scripts = await page.evaluate(_JS_THIRD_PARTY_SCRIPTS)
        for script_url in third_party_scripts:
            for tracker_id, info in KNOWN_TRACKERS.items():
                if any(p in script_url.lower() for p in info["patterns"]):
                    if tracker_id not in detected:
                        detected[tracker_id] = TrackerInfo(
                            name=tracker_id,
                            label=info["label"],
                            category=info["category"],
                            detected_via="script",
                            urls=[script_url],
                        )
                    else:
                        detected[tracker_id].urls.append(script_url)

        # Method 2: Page source check for inline trackers
        page_source = await page.content()
        page_source_lower = page_source.lower()
        for tracker_id, info in KNOWN_TRACKERS.items():
            if tracker_id in detected:
                continue
            for pattern in info["patterns"]:
                if pattern.lower() in page_source_lower:
                    detected[tracker_id] = TrackerInfo(
                        name=tracker_id,
                        label=info["label"],
                        category=info["category"],
                        detected_via="inline_script",
                        urls=[],
                    )
                    break

        report.trackers = list(detected.values())

        # Assess compliance
        if detected:
            categories = set(t.category for t in detected.values())
            tracker_list = [
                {"name": t.label, "category": t.category}
                for t in detected.values()
            ]

            report.checks.append(RGPDCheck(
                check_id="RGPD-8",
                category="trackers",
                title="Trackers tiers détectés",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.CRITICAL if "advertising" in categories else RGPDSeverity.MAJOR,
                details=(
                    f"{len(detected)} tracker(s) tiers détecté(s) "
                    f"(catégories: {', '.join(sorted(categories))})."
                ),
                elements=tracker_list,
                recommendation=(
                    "Chaque tracker tiers doit être déclaré dans la politique de cookies, "
                    "soumis au consentement de l'utilisateur, et ne doit pas se charger "
                    "avant l'obtention du consentement."
                ),
                legal_reference="RGPD Art. 6, 7, 13, 14",
            ))
        else:
            report.checks.append(RGPDCheck(
                check_id="RGPD-8",
                category="trackers",
                title="Trackers tiers détectés",
                status=RGPDStatus.CONFORME,
                details="Aucun tracker tiers connu détecté.",
            ))

    # ─── Privacy policy and legal pages ───────────────────────

    async def _check_privacy_links(self, page: Page, report: RGPDReport) -> None:
        """Check for mandatory legal pages and links."""
        links = await page.evaluate(_JS_PRIVACY_LINKS)

        # Privacy policy
        if links.get("privacy_policy"):
            report.checks.append(RGPDCheck(
                check_id="RGPD-9",
                category="privacy_policy",
                title="Politique de confidentialité",
                status=RGPDStatus.CONFORME,
                details=f"Lien trouvé: \"{links['privacy_policy']['text']}\"",
                elements=[links["privacy_policy"]],
            ))
        else:
            report.checks.append(RGPDCheck(
                check_id="RGPD-9",
                category="privacy_policy",
                title="Politique de confidentialité",
                status=RGPDStatus.NON_CONFORME,
                severity=RGPDSeverity.CRITICAL,
                details="Aucun lien vers une politique de confidentialité détecté.",
                recommendation=(
                    "Ajouter un lien visible vers la politique de confidentialité, "
                    "détaillant les données collectées, les finalités, les destinataires, "
                    "la durée de conservation et les droits des personnes."
                ),
                legal_reference="RGPD Art. 13, 14",
            ))

        # Legal notices (mandatory in France)
        if links.get("legal_notice"):
            report.checks.append(RGPDCheck(
                check_id="RGPD-10",
                category="privacy_policy",
                title="Mentions légales",
                status=RGPDStatus.CONFORME,
                details=f"Lien trouvé: \"{links['legal_notice']['text']}\"",
                elements=[links["legal_notice"]],
            ))
        else:
            report.checks.append(RGPDCheck(
                check_id="RGPD-10",
                category="privacy_policy",
                title="Mentions légales",
                status=RGPDStatus.NON_CONFORME,
                severity=RGPDSeverity.MAJOR,
                details="Aucun lien vers les mentions légales détecté.",
                recommendation=(
                    "Les mentions légales sont obligatoires (Loi LCEN). "
                    "Elles doivent contenir l'identité de l'éditeur, "
                    "l'hébergeur, et le directeur de la publication."
                ),
                legal_reference="Loi n°2004-575 (LCEN) Art. 6 III",
            ))

        # Cookie policy
        if links.get("cookie_policy"):
            report.checks.append(RGPDCheck(
                check_id="RGPD-11",
                category="privacy_policy",
                title="Politique de cookies",
                status=RGPDStatus.CONFORME,
                details=f"Lien trouvé: \"{links['cookie_policy']['text']}\"",
                elements=[links["cookie_policy"]],
            ))
        elif report.cookies:
            report.checks.append(RGPDCheck(
                check_id="RGPD-11",
                category="privacy_policy",
                title="Politique de cookies",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.MINOR,
                details="Aucune page dédiée aux cookies détectée (peut être intégrée à la politique de confidentialité).",
                recommendation="Recommandé: page dédiée décrivant chaque cookie, sa finalité et sa durée.",
            ))

    # ─── Form consent ─────────────────────────────────────────

    async def _check_form_consent(self, page: Page, report: RGPDReport) -> None:
        """Check that forms collecting personal data have consent mechanisms."""
        forms = await page.evaluate(_JS_FORM_CONSENT)

        if not forms:
            report.checks.append(RGPDCheck(
                check_id="RGPD-12",
                category="forms",
                title="Consentement dans les formulaires",
                status=RGPDStatus.NON_APPLICABLE,
                details="Aucun formulaire collectant des données personnelles détecté.",
            ))
            return

        issues = []
        for form in forms:
            if not form.get("hasConsentCheckbox") and not form.get("hasPrivacyLink"):
                issues.append({
                    "formIndex": form.get("formIndex"),
                    "action": form.get("action", ""),
                    "personalDataFields": form.get("personalDataFields", []),
                    "fieldCount": form.get("fieldCount"),
                })

        if issues:
            report.checks.append(RGPDCheck(
                check_id="RGPD-12",
                category="forms",
                title="Consentement dans les formulaires",
                status=RGPDStatus.NON_CONFORME,
                severity=RGPDSeverity.MAJOR,
                details=(
                    f"{len(issues)} formulaire(s) collectant des données personnelles "
                    f"sans mécanisme de consentement explicite."
                ),
                elements=issues,
                recommendation=(
                    "Ajouter une case à cocher de consentement (non pré-cochée) "
                    "et un lien vers la politique de confidentialité à chaque formulaire "
                    "collectant des données personnelles."
                ),
                legal_reference="RGPD Art. 6(1)(a), 7",
            ))
        else:
            report.checks.append(RGPDCheck(
                check_id="RGPD-12",
                category="forms",
                title="Consentement dans les formulaires",
                status=RGPDStatus.CONFORME,
                details=f"{len(forms)} formulaire(s) avec mécanisme de consentement détecté.",
            ))

    # ─── Local storage analysis ───────────────────────────────

    async def _check_local_storage(self, page: Page, report: RGPDReport) -> None:
        """Analyze localStorage for potential tracking data."""
        storage = await page.evaluate(_JS_LOCAL_STORAGE)

        if not storage:
            return

        tracking_keys = []
        for key, info in storage.items():
            key_lower = key.lower()
            suspicious_patterns = [
                "_ga", "_gid", "fbp", "fbclid", "_hjid", "amplitude",
                "mixpanel", "segment", "intercom", "hubspot", "mp_",
                "ajs_", "_clck", "_clsk",
            ]
            if any(p in key_lower for p in suspicious_patterns):
                tracking_keys.append({
                    "key": key,
                    "size": info.get("size", 0),
                    "preview": info.get("preview", "")[:50],
                })

        if tracking_keys:
            report.checks.append(RGPDCheck(
                check_id="RGPD-13",
                category="cookies",
                title="Données de tracking dans localStorage",
                status=RGPDStatus.WARNING,
                severity=RGPDSeverity.MAJOR,
                details=(
                    f"{len(tracking_keys)} clé(s) de suivi détectée(s) dans localStorage."
                ),
                elements=tracking_keys,
                recommendation=(
                    "Le stockage local utilisé à des fins de tracking est soumis aux mêmes "
                    "règles que les cookies. Inclure dans la bannière de consentement."
                ),
                legal_reference="RGPD Art. 6, Directive ePrivacy Art. 5(3)",
            ))


# ─── Utility functions ────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extract base domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname or ""
    except Exception:
        return ""


def _categorize_cookie(name: str, domain: str) -> str:
    """Heuristic categorization of a cookie."""
    name_lower = name.lower()

    # Known functional cookies
    functional_patterns = [
        "session", "csrf", "xsrf", "token", "auth", "lang", "locale",
        "currency", "cart", "basket", "consent", "cookieconsent",
        "tarteaucitron", "axeptio", "didomi", "onetrust",
        "cc_cookie", "CookieConsent",
    ]
    if any(p in name_lower for p in functional_patterns):
        return "functional"

    # Analytics
    analytics_patterns = [
        "_ga", "_gid", "_gat", "__utm", "_hjid", "_hjsession",
        "mp_", "ajs_", "_clck", "_clsk", "amplitude",
    ]
    if any(p in name_lower for p in analytics_patterns):
        return "analytics"

    # Advertising
    ad_patterns = [
        "_fbp", "_fbc", "_gcl", "IDE", "test_cookie", "fr",
        "__adroll", "_uetsid", "li_", "_pin_", "tiktok",
    ]
    if any(p in name_lower for p in ad_patterns):
        return "advertising"

    return "unknown"
