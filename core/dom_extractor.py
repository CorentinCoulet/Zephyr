"""
DOM Extractor — Extracts structured, simplified representations of the DOM.
Provides element analysis, form detection, bounding boxes, contrast checks, etc.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from playwright.async_api import Page


@dataclass
class DOMNode:
    """Simplified representation of a DOM element."""
    tag: str
    id: str = ""
    classes: list[str] = field(default_factory=list)
    text: str = ""
    href: str = ""
    src: str = ""
    role: str = ""
    aria_label: str = ""
    bounding_box: Optional[dict] = None
    computed_styles: Optional[dict] = None
    children: list["DOMNode"] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "id": self.id,
            "classes": self.classes,
            "text": self.text[:200] if self.text else "",
            "href": self.href,
            "role": self.role,
            "aria_label": self.aria_label,
            "bounding_box": self.bounding_box,
            "children_count": len(self.children),
        }


@dataclass
class FormField:
    """Detected form field."""
    name: str
    type: str
    label: str = ""
    placeholder: str = ""
    required: bool = False
    value: str = ""
    selector: str = ""


@dataclass
class FormInfo:
    """Detected form and its fields."""
    action: str = ""
    method: str = "GET"
    fields: list[FormField] = field(default_factory=list)
    submit_selector: str = ""


@dataclass
class InteractiveElement:
    """An interactive DOM element (button, link, input, etc.)."""
    tag: str
    text: str
    selector: str
    type: str = ""
    href: str = ""
    role: str = ""
    bounding_box: Optional[dict] = None
    is_visible: bool = True
    is_enabled: bool = True


@dataclass
class ContrastIssue:
    """WCAG contrast violation."""
    selector: str
    text: str
    foreground: str
    background: str
    ratio: float
    required_ratio: float
    level: str  # "AA" or "AAA"


@dataclass
class OverflowIssue:
    """Element overflowing its container."""
    selector: str
    element_bounds: dict
    container_bounds: dict
    overflow_x: float
    overflow_y: float


@dataclass
class NavigationItem:
    """Navigation element detected in the page."""
    text: str
    href: str
    selector: str
    is_active: bool = False
    children: list["NavigationItem"] = field(default_factory=list)


@dataclass
class AccessibilityIssue:
    """General accessibility issue."""
    type: str  # "missing_alt", "missing_label", "invalid_aria", "missing_lang", "tabindex", "no_accessible_name"
    selector: str
    element_tag: str
    text: str = ""
    details: str = ""
    severity: str = "warning"  # "error" or "warning"


@dataclass
class StorageData:
    """Browser storage snapshot."""
    local_storage: dict = field(default_factory=dict)
    session_storage: dict = field(default_factory=dict)
    cookies: list[dict] = field(default_factory=list)
    indexed_db_names: list[str] = field(default_factory=list)


class DOMExtractor:
    """Extracts structured representations of the DOM from a Playwright page."""

    # --- JavaScript snippets injected into the page ---

    _JS_EXTRACT_DOM = """
    () => {
        function extractNode(el, depth = 0) {
            if (depth > 6 || !el || el.nodeType !== 1) return null;
            const tag = el.tagName.toLowerCase();
            if (['script', 'style', 'noscript', 'svg', 'path'].includes(tag)) return null;

            const rect = el.getBoundingClientRect();
            const styles = window.getComputedStyle(el);

            return {
                tag,
                id: el.id || '',
                classes: Array.from(el.classList),
                text: el.childNodes.length === 1 && el.childNodes[0].nodeType === 3
                    ? el.textContent.trim().substring(0, 200) : '',
                href: el.href || '',
                src: el.src || '',
                role: el.getAttribute('role') || '',
                aria_label: el.getAttribute('aria-label') || '',
                bounding_box: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                computed_styles: {
                    color: styles.color,
                    backgroundColor: styles.backgroundColor,
                    fontSize: styles.fontSize,
                    fontWeight: styles.fontWeight,
                    display: styles.display,
                    visibility: styles.visibility,
                    margin: styles.margin,
                    padding: styles.padding,
                    position: styles.position,
                    overflow: styles.overflow,
                    zIndex: styles.zIndex
                },
                children: Array.from(el.children)
                    .map(child => extractNode(child, depth + 1))
                    .filter(Boolean)
            };
        }
        return extractNode(document.body);
    }
    """

    _JS_EXTRACT_INTERACTIVE = """
    () => {
        const selectors = 'a, button, input, select, textarea, [role="button"], [onclick], [tabindex]';
        const elements = document.querySelectorAll(selectors);
        return Array.from(elements).map((el, i) => {
            const rect = el.getBoundingClientRect();
            const styles = window.getComputedStyle(el);
            const isVisible = rect.width > 0 && rect.height > 0
                && styles.visibility !== 'hidden'
                && styles.display !== 'none';
            return {
                tag: el.tagName.toLowerCase(),
                text: (el.textContent || el.value || el.placeholder || '').trim().substring(0, 100),
                type: el.type || '',
                href: el.href || '',
                role: el.getAttribute('role') || '',
                selector: el.id ? '#' + el.id
                    : el.className ? el.tagName.toLowerCase() + '.' + el.className.split(' ')[0]
                    : el.tagName.toLowerCase() + ':nth-of-type(' + (i + 1) + ')',
                bounding_box: {
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    width: Math.round(rect.width), height: Math.round(rect.height)
                },
                is_visible: isVisible,
                is_enabled: !el.disabled
            };
        });
    }
    """

    _JS_EXTRACT_FORMS = """
    () => {
        const forms = document.querySelectorAll('form');
        return Array.from(forms).map(form => {
            const fields = form.querySelectorAll('input, select, textarea');
            const submitBtn = form.querySelector('[type="submit"], button:not([type="button"])');
            return {
                action: form.action || '',
                method: (form.method || 'GET').toUpperCase(),
                submit_selector: submitBtn
                    ? (submitBtn.id ? '#' + submitBtn.id : 'button[type="submit"]')
                    : '',
                fields: Array.from(fields).map(f => {
                    const label = f.labels?.[0]?.textContent?.trim() || '';
                    return {
                        name: f.name || '',
                        type: f.type || f.tagName.toLowerCase(),
                        label,
                        placeholder: f.placeholder || '',
                        required: f.required || false,
                        value: f.value || '',
                        selector: f.id ? '#' + f.id : `[name="${f.name}"]`
                    };
                })
            };
        });
    }
    """

    _JS_EXTRACT_NAVIGATION = """
    () => {
        const navElements = document.querySelectorAll('nav, [role="navigation"], header');
        const results = [];
        navElements.forEach(nav => {
            const links = nav.querySelectorAll('a');
            links.forEach(a => {
                const isActive = a.classList.contains('active')
                    || a.getAttribute('aria-current') === 'page'
                    || window.location.pathname === new URL(a.href, window.location.origin).pathname;
                results.push({
                    text: a.textContent.trim().substring(0, 50),
                    href: a.href || '',
                    selector: a.id ? '#' + a.id : `a[href="${a.getAttribute('href')}"]`,
                    is_active: isActive
                });
            });
        });
        return results;
    }
    """

    _JS_DETECT_OVERFLOW = """
    () => {
        const issues = [];
        const all = document.querySelectorAll('*');
        all.forEach(el => {
            const parent = el.parentElement;
            if (!parent || el === document.body) return;
            const elRect = el.getBoundingClientRect();
            const parentRect = parent.getBoundingClientRect();
            const overflowX = elRect.right - parentRect.right;
            const overflowY = elRect.bottom - parentRect.bottom;
            if (overflowX > 5 || overflowY > 5) {
                const styles = window.getComputedStyle(parent);
                if (styles.overflow === 'visible') {
                    issues.push({
                        selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                        element_bounds: {x: elRect.x, y: elRect.y, width: elRect.width, height: elRect.height},
                        container_bounds: {x: parentRect.x, y: parentRect.y, width: parentRect.width, height: parentRect.height},
                        overflow_x: Math.round(overflowX),
                        overflow_y: Math.round(overflowY)
                    });
                }
            }
        });
        return issues.slice(0, 50);
    }
    """

    _JS_CHECK_CONTRAST = """
    () => {
        function getLuminance(r, g, b) {
            const [rs, gs, bs] = [r, g, b].map(c => {
                c = c / 255;
                return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
            });
            return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
        }
        function parseColor(color) {
            const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
            return match ? [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])] : null;
        }
        function isTransparent(color) {
            if (!color) return true;
            if (color === 'transparent' || color === 'rgba(0, 0, 0, 0)') return true;
            const m = color.match(/rgba\(\d+,\s*\d+,\s*\d+,\s*([\d.]+)\)/);
            return m && parseFloat(m[1]) < 0.1;
        }
        function getEffectiveBg(el) {
            let current = el;
            while (current && current !== document.documentElement) {
                const styles = window.getComputedStyle(current);
                const bg = styles.backgroundColor;
                if (!isTransparent(bg)) return parseColor(bg);
                current = current.parentElement;
            }
            return [255, 255, 255]; // default white
        }
        function contrastRatio(fg, bg) {
            const l1 = getLuminance(...fg);
            const l2 = getLuminance(...bg);
            const lighter = Math.max(l1, l2);
            const darker = Math.min(l1, l2);
            return (lighter + 0.05) / (darker + 0.05);
        }

        const textElements = document.querySelectorAll('p, span, a, h1, h2, h3, h4, h5, h6, li, td, th, label, button');
        const issues = [];

        textElements.forEach(el => {
            const styles = window.getComputedStyle(el);
            if (styles.display === 'none' || styles.visibility === 'hidden') return;
            const text = el.textContent.trim();
            if (!text) return;
            const fg = parseColor(styles.color);
            if (!fg) return;
            const bg = getEffectiveBg(el);
            if (!bg) return;

            const ratio = contrastRatio(fg, bg);
            const fontSize = parseFloat(styles.fontSize);
            const isBold = parseInt(styles.fontWeight) >= 700;
            const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && isBold);
            const requiredAA = isLargeText ? 3 : 4.5;

            if (ratio < requiredAA) {
                issues.push({
                    selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                    text: text.substring(0, 50),
                    foreground: styles.color,
                    background: `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})`,
                    ratio: Math.round(ratio * 100) / 100,
                    required_ratio: requiredAA,
                    level: 'AA'
                });
            }
        });
        return issues.slice(0, 50);
    }
    """

    _JS_CHECK_ACCESSIBILITY = """
    () => {
        const issues = [];
        // Images without alt
        document.querySelectorAll('img').forEach(img => {
            if (!img.hasAttribute('alt')) {
                issues.push({
                    type: 'missing_alt', selector: img.id ? '#' + img.id : 'img[src="' + (img.src || '').substring(0, 60) + '"]',
                    element_tag: 'img', text: img.src ? img.src.split('/').pop().substring(0, 40) : '',
                    details: 'Image has no alt attribute', severity: 'error'
                });
            }
        });
        // Inputs without labels
        document.querySelectorAll('input, select, textarea').forEach(inp => {
            if (inp.type === 'hidden' || inp.type === 'submit' || inp.type === 'button') return;
            const hasLabel = inp.labels && inp.labels.length > 0;
            const hasAria = inp.getAttribute('aria-label') || inp.getAttribute('aria-labelledby');
            const hasTitle = inp.title;
            const hasPlaceholder = inp.placeholder;
            if (!hasLabel && !hasAria && !hasTitle) {
                issues.push({
                    type: 'missing_label', selector: inp.id ? '#' + inp.id : `${inp.tagName.toLowerCase()}[name="${inp.name || ''}"]`,
                    element_tag: inp.tagName.toLowerCase(), text: inp.name || inp.placeholder || '',
                    details: hasPlaceholder ? 'Only has placeholder, no label' : 'No associated label, aria-label, or title',
                    severity: hasPlaceholder ? 'warning' : 'error'
                });
            }
        });
        // Interactive elements without accessible name
        document.querySelectorAll('button, a, [role="button"]').forEach(el => {
            const text = (el.textContent || '').trim();
            const ariaLabel = el.getAttribute('aria-label') || '';
            const title = el.title || '';
            if (!text && !ariaLabel && !title) {
                const icon = el.querySelector('svg, i, img');
                if (icon) {
                    issues.push({
                        type: 'no_accessible_name', selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                        element_tag: el.tagName.toLowerCase(), text: '',
                        details: 'Icon-only interactive element without accessible name', severity: 'error'
                    });
                }
            }
        });
        // Invalid tabindex
        document.querySelectorAll('[tabindex]').forEach(el => {
            const val = parseInt(el.getAttribute('tabindex'));
            if (val > 0) {
                issues.push({
                    type: 'tabindex', selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                    element_tag: el.tagName.toLowerCase(), text: el.textContent.trim().substring(0, 30),
                    details: `tabindex=${val} (positive tabindex disrupts natural focus order)`, severity: 'warning'
                });
            }
        });
        // Missing lang attribute
        if (!document.documentElement.lang) {
            issues.push({
                type: 'missing_lang', selector: 'html',
                element_tag: 'html', text: '', details: 'Missing lang attribute on <html>', severity: 'error'
            });
        }
        return issues.slice(0, 100);
    }
    """

    _JS_INSPECT_STORAGE = """
    () => {
        const ls = {};
        try { for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i); ls[k] = localStorage.getItem(k).substring(0, 200);
        }} catch(e) {}
        const ss = {};
        try { for (let i = 0; i < sessionStorage.length; i++) {
            const k = sessionStorage.key(i); ss[k] = sessionStorage.getItem(k).substring(0, 200);
        }} catch(e) {}
        let idb = [];
        try { if (window.indexedDB && window.indexedDB.databases) {
            // databases() is async but we do sync snapshot
        }} catch(e) {}
        return { local_storage: ls, session_storage: ss };
    }
    """

    _JS_SEARCH_TEXT = """
    (query) => {
        const results = [];
        const lowerQuery = query.toLowerCase();
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent.trim();
            if (!text || text.length < 2) continue;
            if (text.toLowerCase().includes(lowerQuery)) {
                const el = node.parentElement;
                if (!el) continue;
                const rect = el.getBoundingClientRect();
                results.push({
                    text: text.substring(0, 200),
                    selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                    tag: el.tagName.toLowerCase(),
                    visible: rect.width > 0 && rect.height > 0,
                    bounding_box: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
                });
            }
        }
        return results.slice(0, 50);
    }
    """

    _JS_DETECT_FRAMEWORK = """
    () => {
        const frameworks = [];
        // React
        if (document.querySelector('[data-reactroot]') || document.querySelector('[data-react-root]') || window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
            let version = '';
            try { version = window.__REACT_DEVTOOLS_GLOBAL_HOOK__?.renderers?.get(1)?.version || ''; } catch(e) {}
            frameworks.push({ name: 'React', version });
        }
        // Vue
        if (document.querySelector('[data-v-]') || document.querySelector('.__vue-root') || window.__VUE__) {
            let version = '';
            try { version = window.__VUE__?.version || ''; } catch(e) {}
            frameworks.push({ name: 'Vue', version });
        }
        // Angular
        if (document.querySelector('[ng-version]') || window.ng) {
            const ngEl = document.querySelector('[ng-version]');
            frameworks.push({ name: 'Angular', version: ngEl ? ngEl.getAttribute('ng-version') : '' });
        }
        // Svelte
        if (document.querySelector('[class*="svelte-"]')) {
            frameworks.push({ name: 'Svelte', version: '' });
        }
        // Next.js
        if (document.querySelector('#__next') || window.__NEXT_DATA__) {
            frameworks.push({ name: 'Next.js', version: '' });
        }
        // Nuxt
        if (document.querySelector('#__nuxt') || window.__NUXT__) {
            frameworks.push({ name: 'Nuxt', version: '' });
        }
        // jQuery
        if (window.jQuery) {
            frameworks.push({ name: 'jQuery', version: window.jQuery.fn?.jquery || '' });
        }
        // Bundles analysis
        const scripts = Array.from(document.querySelectorAll('script[src]'));
        const bundles = scripts.map(s => ({
            src: s.src,
            async: s.async,
            defer: s.defer,
            type: s.type || 'text/javascript'
        }));
        const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
        const cssFiles = styles.map(l => ({ href: l.href }));
        return { frameworks, js_bundles: bundles.slice(0, 30), css_files: cssFiles.slice(0, 20) };
    }
    """

    async def extract_full(self, page: Page) -> dict:
        """Extract full simplified DOM tree."""
        return await page.evaluate(self._JS_EXTRACT_DOM)

    async def extract_interactive_elements(
        self, page: Page
    ) -> list[InteractiveElement]:
        """Extract all interactive elements from the page."""
        raw = await page.evaluate(self._JS_EXTRACT_INTERACTIVE)
        return [InteractiveElement(**item) for item in raw]

    async def extract_forms(self, page: Page) -> list[FormInfo]:
        """Extract all forms and their fields."""
        raw = await page.evaluate(self._JS_EXTRACT_FORMS)
        results = []
        for form_data in raw:
            fields = [FormField(**f) for f in form_data.pop("fields", [])]
            results.append(FormInfo(**form_data, fields=fields))
        return results

    async def extract_navigation(self, page: Page) -> list[NavigationItem]:
        """Extract navigation elements and links."""
        raw = await page.evaluate(self._JS_EXTRACT_NAVIGATION)
        return [NavigationItem(**item) for item in raw]

    async def get_bounding_boxes(self, page: Page) -> list[dict]:
        """Get bounding boxes of all visible elements."""
        return await page.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                return Array.from(all)
                    .map(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return null;
                        return {
                            tag: el.tagName.toLowerCase(),
                            id: el.id || '',
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        };
                    })
                    .filter(Boolean);
            }
        """)

    async def detect_overflow(self, page: Page) -> list[OverflowIssue]:
        """Detect elements overflowing their containers."""
        raw = await page.evaluate(self._JS_DETECT_OVERFLOW)
        return [OverflowIssue(**item) for item in raw]

    async def check_contrast(self, page: Page) -> list[ContrastIssue]:
        """Check WCAG contrast ratios on text elements (walks up parent bg)."""
        raw = await page.evaluate(self._JS_CHECK_CONTRAST)
        return [ContrastIssue(**item) for item in raw]

    async def check_accessibility(self, page: Page) -> list[AccessibilityIssue]:
        """Run comprehensive accessibility audit (missing alt, labels, ARIA, tabindex, lang)."""
        raw = await page.evaluate(self._JS_CHECK_ACCESSIBILITY)
        return [AccessibilityIssue(**item) for item in raw]

    async def inspect_storage(self, page: Page) -> StorageData:
        """Extract localStorage, sessionStorage contents."""
        raw = await page.evaluate(self._JS_INSPECT_STORAGE)
        cookies = []
        try:
            context = page.context
            cookies = [c for c in await context.cookies()]
        except Exception:
            pass
        return StorageData(
            local_storage=raw.get("local_storage", {}),
            session_storage=raw.get("session_storage", {}),
            cookies=[{"name": c.get("name"), "domain": c.get("domain"),
                      "path": c.get("path"), "secure": c.get("secure"),
                      "httpOnly": c.get("httpOnly"),
                      "expires": c.get("expires", -1)}
                     for c in cookies],
        )

    async def search_text(self, page: Page, query: str) -> list[dict]:
        """Full-text search in page DOM content."""
        return await page.evaluate(self._JS_SEARCH_TEXT, query)

    async def detect_framework(self, page: Page) -> dict:
        """Detect frontend framework, libraries, and bundles."""
        return await page.evaluate(self._JS_DETECT_FRAMEWORK)
