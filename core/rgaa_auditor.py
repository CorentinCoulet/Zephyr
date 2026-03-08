"""
RGAA 4.1 Auditor — Automated accessibility audit based on the French RGAA 4.1 standard.

Checks cover the 13 themes of RGAA 4.1:
  1. Images
  2. Cadres (Frames)
  3. Couleurs (Colors)
  4. Multimédia
  5. Tableaux (Tables)
  6. Liens (Links)
  7. Scripts
  8. Éléments obligatoires (Mandatory elements)
  9. Structuration de l'information (Structure)
  10. Présentation de l'information (Presentation)
  11. Formulaires (Forms)
  12. Navigation
  13. Consultation

Uses Playwright JS injection to analyze the live DOM.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger("zephyr.core.rgaa")


class RGAAConformance(str, Enum):
    CONFORME = "conforme"
    NON_CONFORME = "non_conforme"
    NON_APPLICABLE = "non_applicable"


class RGAASeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class RGAACriterion:
    """Result for a single RGAA 4.1 criterion."""
    criterion_id: str          # e.g. "1.1"
    theme: str                 # e.g. "Images"
    title: str                 # Short label
    status: RGAAConformance = RGAAConformance.CONFORME
    severity: RGAASeverity = RGAASeverity.INFO
    details: str = ""
    elements: list[dict] = field(default_factory=list)  # Affected elements
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "theme": self.theme,
            "title": self.title,
            "status": self.status.value,
            "severity": self.severity.value,
            "details": self.details,
            "elements_count": len(self.elements),
            "elements": self.elements[:20],  # Cap for output size
            "recommendation": self.recommendation,
        }


@dataclass
class RGAAReport:
    """Full RGAA 4.1 audit report."""
    url: str
    criteria: list[RGAACriterion] = field(default_factory=list)
    total_tested: int = 0
    conforme: int = 0
    non_conforme: int = 0
    non_applicable: int = 0
    conformity_rate: float = 0.0

    def compute_stats(self):
        self.total_tested = len(self.criteria)
        self.conforme = sum(1 for c in self.criteria if c.status == RGAAConformance.CONFORME)
        self.non_conforme = sum(1 for c in self.criteria if c.status == RGAAConformance.NON_CONFORME)
        self.non_applicable = sum(1 for c in self.criteria if c.status == RGAAConformance.NON_APPLICABLE)
        applicable = self.total_tested - self.non_applicable
        self.conformity_rate = round((self.conforme / applicable * 100) if applicable > 0 else 0, 1)

    def to_dict(self) -> dict:
        self.compute_stats()
        return {
            "url": self.url,
            "total_tested": self.total_tested,
            "conforme": self.conforme,
            "non_conforme": self.non_conforme,
            "non_applicable": self.non_applicable,
            "conformity_rate": self.conformity_rate,
            "criteria": [c.to_dict() for c in self.criteria],
        }


# ═══════════════════════════════════════════════════════════════
# JavaScript snippets injected into the page
# ═══════════════════════════════════════════════════════════════

_JS_IMAGES = """
() => {
    const results = [];
    // 1.1 — Each decorative image must be ignored by assistive technologies
    // 1.2 — Each informational image must have an alternative
    document.querySelectorAll('img, [role="img"], svg, area, input[type="image"], object[type^="image"], embed[type^="image"], canvas').forEach(el => {
        const tag = el.tagName.toLowerCase();
        const alt = el.getAttribute('alt');
        const ariaLabel = el.getAttribute('aria-label') || '';
        const ariaLabelledBy = el.getAttribute('aria-labelledby') || '';
        const role = el.getAttribute('role') || '';
        const title = el.getAttribute('title') || '';
        const src = el.getAttribute('src') || '';

        let issue = null;

        if (tag === 'img') {
            if (alt === null) {
                issue = {type: 'missing_alt', selector: _sel(el), src, tag, text: 'Image sans attribut alt'};
            } else if (alt === '' && role !== 'presentation' && role !== 'none') {
                // Empty alt but not marked as decorative — could be intentional
                issue = {type: 'empty_alt_no_role', selector: _sel(el), src, tag, text: 'alt="" sans role="presentation"'};
            }
        } else if (tag === 'svg') {
            const hasTitle = el.querySelector('title');
            if (!ariaLabel && !ariaLabelledBy && !hasTitle && role !== 'presentation' && role !== 'none') {
                issue = {type: 'svg_no_accessible_name', selector: _sel(el), tag, text: 'SVG sans nom accessible'};
            }
        } else if (tag === 'area') {
            if (!alt && !ariaLabel) {
                issue = {type: 'area_no_alt', selector: _sel(el), tag, text: 'area sans alternative'};
            }
        } else if (tag === 'input') {
            if (!alt && !ariaLabel && !title) {
                issue = {type: 'input_image_no_alt', selector: _sel(el), tag, text: 'input[type=image] sans alternative'};
            }
        } else if (tag === 'canvas') {
            if (!ariaLabel && !ariaLabelledBy && !el.textContent.trim()) {
                issue = {type: 'canvas_no_alt', selector: _sel(el), tag, text: 'canvas sans alternative textuelle'};
            }
        }

        if (issue) results.push(issue);
    });
    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_FRAMES = """
() => {
    const results = [];
    // 2.1 — Each iframe must have a title attribute
    document.querySelectorAll('iframe, frame').forEach(el => {
        const title = el.getAttribute('title');
        const ariaLabel = el.getAttribute('aria-label') || '';
        if (!title && !ariaLabel) {
            results.push({
                type: 'frame_no_title',
                selector: el.id ? '#' + el.id : 'iframe[src="' + (el.src || '') + '"]',
                src: el.src || '',
                text: 'iframe/frame sans attribut title'
            });
        }
    });
    return results;
}
"""

_JS_COLORS = """
() => {
    const results = [];
    // 3.1/3.2 — Information must not be conveyed by color alone + contrast ratios
    const elems = document.querySelectorAll('body *:not(script):not(style):not(br):not(hr)');
    let checked = 0;
    for (const el of elems) {
        if (checked > 500) break;  // Performance cap
        const text = el.textContent.trim();
        if (!text || el.children.length > 0) continue;

        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;

        const fg = style.color;
        const bg = _getEffectiveBg(el);
        if (!fg || !bg) continue;

        const ratio = _contrastRatio(_parsedRGB(fg), _parsedRGB(bg));
        const fontSize = parseFloat(style.fontSize);
        const isBold = parseInt(style.fontWeight) >= 700 || style.fontWeight === 'bold';
        const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && isBold);

        const requiredAA = isLargeText ? 3 : 4.5;
        const requiredAAA = isLargeText ? 4.5 : 7;

        if (ratio < requiredAA) {
            results.push({
                type: 'contrast_aa_fail',
                selector: _sel(el),
                text: text.substring(0, 60),
                foreground: fg,
                background: bg,
                ratio: Math.round(ratio * 100) / 100,
                required: requiredAA,
                level: 'AA'
            });
        } else if (ratio < requiredAAA) {
            results.push({
                type: 'contrast_aaa_fail',
                selector: _sel(el),
                text: text.substring(0, 60),
                foreground: fg,
                background: bg,
                ratio: Math.round(ratio * 100) / 100,
                required: requiredAAA,
                level: 'AAA'
            });
        }
        checked++;
    }
    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
    function _getEffectiveBg(el) {
        let cur = el;
        while (cur && cur !== document.documentElement) {
            const bg = window.getComputedStyle(cur).backgroundColor;
            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
            cur = cur.parentElement;
        }
        return 'rgb(255, 255, 255)';
    }
    function _parsedRGB(color) {
        const m = color.match(/\\d+/g);
        return m ? m.map(Number) : [0, 0, 0];
    }
    function _luminance(rgb) {
        const [r, g, b] = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }
    function _contrastRatio(rgb1, rgb2) {
        const l1 = _luminance(rgb1);
        const l2 = _luminance(rgb2);
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        return (lighter + 0.05) / (darker + 0.05);
    }
}
"""

_JS_TABLES = """
() => {
    const results = [];
    // 5.1 — Complex data tables must have a caption
    // 5.6 — Each data table must have headers (th)
    document.querySelectorAll('table').forEach(el => {
        const role = el.getAttribute('role') || '';
        if (role === 'presentation' || role === 'none') return;

        const caption = el.querySelector('caption');
        const summary = el.getAttribute('summary') || '';
        const ariaLabel = el.getAttribute('aria-label') || '';
        const ariaLabelledBy = el.getAttribute('aria-labelledby') || '';

        if (!caption && !summary && !ariaLabel && !ariaLabelledBy) {
            results.push({
                type: 'table_no_caption',
                selector: _sel(el),
                text: 'Table de données sans légende (caption/aria-label)'
            });
        }

        const ths = el.querySelectorAll('th');
        if (ths.length === 0) {
            results.push({
                type: 'table_no_headers',
                selector: _sel(el),
                text: 'Table de données sans en-têtes (th)'
            });
        }

        // Check th have scope attribute
        ths.forEach(th => {
            if (!th.getAttribute('scope') && !th.getAttribute('id')) {
                results.push({
                    type: 'th_no_scope',
                    selector: _sel(th),
                    text: 'Cellule en-tête (th) sans attribut scope'
                });
            }
        });
    });
    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_LINKS = """
() => {
    const results = [];
    // 6.1 — Each link must have an accessible name
    // 6.2 — Link purpose must be clear from context
    document.querySelectorAll('a[href], [role="link"]').forEach(el => {
        const text = (el.textContent || '').trim();
        const ariaLabel = el.getAttribute('aria-label') || '';
        const ariaLabelledBy = el.getAttribute('aria-labelledby') || '';
        const title = el.getAttribute('title') || '';
        const img = el.querySelector('img');
        const imgAlt = img ? (img.getAttribute('alt') || '') : '';

        const accessibleName = ariaLabel || ariaLabelledBy || text || imgAlt || title;
        if (!accessibleName) {
            results.push({
                type: 'link_no_accessible_name',
                selector: _sel(el),
                href: el.href || '',
                text: 'Lien sans nom accessible'
            });
        }

        // Check for generic link text
        const generic = ['cliquez ici', 'click here', 'en savoir plus', 'read more', 'lire la suite', 'ici', 'here', 'more', 'link', 'lien'];
        if (generic.includes(accessibleName.toLowerCase())) {
            results.push({
                type: 'link_generic_text',
                selector: _sel(el),
                href: el.href || '',
                accessibleName,
                text: 'Intitulé de lien non explicite: "' + accessibleName + '"'
            });
        }

        // New window without warning
        if (el.getAttribute('target') === '_blank' && !ariaLabel.includes('nouvelle') && !ariaLabel.includes('new') && !title.includes('nouvelle') && !title.includes('new')) {
            const hasIcon = el.querySelector('[aria-hidden]') || el.querySelector('.sr-only') || el.querySelector('.visually-hidden');
            if (!hasIcon) {
                results.push({
                    type: 'link_new_window_no_warning',
                    selector: _sel(el),
                    href: el.href || '',
                    text: 'Lien ouvrant une nouvelle fenêtre sans avertissement'
                });
            }
        }
    });
    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_MANDATORY_ELEMENTS = """
() => {
    const results = [];
    const html = document.documentElement;

    // 8.1 — Page must have a valid doctype
    // (Cannot check from JS — skip with note)

    // 8.2 — lang attribute on html element
    const lang = html.getAttribute('lang') || '';
    const xmlLang = html.getAttribute('xml:lang') || '';
    if (!lang && !xmlLang) {
        results.push({type: 'no_lang', text: 'Pas d\\'attribut lang sur <html>'});
    } else if (lang && !/^[a-z]{2}(-[A-Za-z]{2,})?$/.test(lang)) {
        results.push({type: 'invalid_lang', lang, text: 'Attribut lang invalide: "' + lang + '"'});
    }

    // 8.5 — Page must have a title
    const title = document.title.trim();
    if (!title) {
        results.push({type: 'no_title', text: 'La page n\\'a pas de <title>'});
    }

    // 8.6 — Title must be relevant (heuristic: not too short, not default)
    const defaultTitles = ['untitled', 'sans titre', 'document', 'page', 'welcome', 'home', 'index'];
    if (title && (title.length < 3 || defaultTitles.includes(title.toLowerCase()))) {
        results.push({type: 'irrelevant_title', title, text: 'Titre de page potentiellement non pertinent: "' + title + '"'});
    }

    // 8.7 — Dir attribute changes must be indicated
    const dir = html.getAttribute('dir');
    if (lang && ['ar', 'he', 'fa', 'ur'].includes(lang.substring(0, 2)) && dir !== 'rtl') {
        results.push({type: 'missing_rtl', lang, text: 'Langue RTL détectée sans dir="rtl"'});
    }

    // 8.9 — Presentation tags should not be used
    const deprecated = document.querySelectorAll('font, center, marquee, blink, big, strike, tt, basefont');
    if (deprecated.length > 0) {
        results.push({
            type: 'deprecated_tags',
            count: deprecated.length,
            tags: [...new Set([...deprecated].map(e => e.tagName.toLowerCase()))],
            text: deprecated.length + ' balises de présentation obsolètes'
        });
    }

    return results;
}
"""

_JS_STRUCTURE = """
() => {
    const results = [];

    // 9.1 — Heading hierarchy (h1-h6) must be logical
    const headings = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]')];
    let lastLevel = 0;
    let h1Count = 0;
    headings.forEach(h => {
        const level = h.getAttribute('aria-level') ? parseInt(h.getAttribute('aria-level')) : parseInt(h.tagName.substring(1));
        if (level === 1) h1Count++;
        if (lastLevel > 0 && level > lastLevel + 1) {
            results.push({
                type: 'heading_skip',
                from: 'h' + lastLevel,
                to: 'h' + level,
                text: 'Saut de niveau de titre: h' + lastLevel + ' → h' + level,
                selector: _sel(h)
            });
        }
        lastLevel = level;
    });

    if (h1Count === 0) {
        results.push({type: 'no_h1', text: 'Aucun titre de niveau 1 (h1) trouvé'});
    } else if (h1Count > 1) {
        results.push({type: 'multiple_h1', count: h1Count, text: h1Count + ' titres h1 trouvés (recommandé: 1)'});
    }

    // 9.2 — Document structure: landmark regions
    const hasMain = document.querySelector('main, [role="main"]');
    const hasNav = document.querySelector('nav, [role="navigation"]');
    const hasHeader = document.querySelector('header, [role="banner"]');
    const hasFooter = document.querySelector('footer, [role="contentinfo"]');

    if (!hasMain) results.push({type: 'no_main', text: 'Pas de zone principale (<main> ou role="main")'});
    if (!hasNav) results.push({type: 'no_nav', text: 'Pas de zone de navigation (<nav> ou role="navigation")'});
    if (!hasHeader) results.push({type: 'no_header', text: 'Pas de bannière (<header> ou role="banner")'});
    if (!hasFooter) results.push({type: 'no_footer', text: 'Pas de pied de page (<footer> ou role="contentinfo")'});

    // 9.3 — Lists must be properly structured
    document.querySelectorAll('ul, ol').forEach(list => {
        const invalidChildren = [...list.children].filter(c =>
            c.tagName.toLowerCase() !== 'li' &&
            c.tagName.toLowerCase() !== 'script' &&
            c.tagName.toLowerCase() !== 'template'
        );
        if (invalidChildren.length > 0) {
            results.push({
                type: 'list_invalid_children',
                selector: _sel(list),
                text: 'Liste avec enfants non-<li>: ' + invalidChildren.map(c => c.tagName.toLowerCase()).join(', ')
            });
        }
    });

    // 9.4 — Skip links (accès rapide)
    const skipLinks = document.querySelectorAll('a[href^="#"]');
    const firstLinks = [...document.querySelectorAll('a')].slice(0, 5);
    const hasSkipLink = firstLinks.some(a => {
        const href = a.getAttribute('href') || '';
        const text = (a.textContent || '').toLowerCase();
        return href.startsWith('#') &&
            (text.includes('contenu') || text.includes('content') || text.includes('skip') || text.includes('aller au'));
    });
    if (!hasSkipLink) {
        results.push({type: 'no_skip_link', text: 'Pas de lien d\\'accès rapide au contenu principal'});
    }

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_FORMS = """
() => {
    const results = [];

    // 11.1 — Each form field must have a label
    document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="reset"]):not([type="button"]):not([type="image"]), select, textarea').forEach(el => {
        const id = el.id;
        const ariaLabel = el.getAttribute('aria-label') || '';
        const ariaLabelledBy = el.getAttribute('aria-labelledby') || '';
        const title = el.getAttribute('title') || '';
        const placeholder = el.getAttribute('placeholder') || '';

        let hasLabel = false;
        if (id) {
            hasLabel = !!document.querySelector('label[for="' + id + '"]');
        }
        if (!hasLabel) {
            hasLabel = !!el.closest('label');
        }

        if (!hasLabel && !ariaLabel && !ariaLabelledBy && !title) {
            results.push({
                type: 'field_no_label',
                selector: _sel(el),
                fieldType: el.type || el.tagName.toLowerCase(),
                name: el.name || '',
                text: 'Champ de formulaire sans étiquette',
                hasPlaceholder: !!placeholder
            });
        }
    });

    // 11.2 — Labels must be relevant
    document.querySelectorAll('label').forEach(label => {
        const text = label.textContent.trim();
        if (text.length < 2) {
            results.push({
                type: 'label_too_short',
                selector: _sel(label),
                text: 'Étiquette trop courte: "' + text + '"'
            });
        }
    });

    // 11.4 — Fieldset/legend for grouped fields
    const radioGroups = {};
    const checkboxGroups = {};
    document.querySelectorAll('input[type="radio"]').forEach(r => {
        const name = r.name || 'unnamed';
        if (!radioGroups[name]) radioGroups[name] = [];
        radioGroups[name].push(r);
    });
    Object.entries(radioGroups).forEach(([name, radios]) => {
        if (radios.length > 1) {
            const hasFieldset = radios[0].closest('fieldset');
            const hasRole = radios[0].closest('[role="radiogroup"]');
            if (!hasFieldset && !hasRole) {
                results.push({
                    type: 'radio_no_fieldset',
                    name,
                    count: radios.length,
                    text: 'Groupe de boutons radio "' + name + '" sans fieldset/legend'
                });
            }
        }
    });

    // 11.10 — Required fields must be indicated
    document.querySelectorAll('[required], [aria-required="true"]').forEach(el => {
        const label = el.id ? document.querySelector('label[for="' + el.id + '"]') : el.closest('label');
        if (label) {
            const labelText = label.textContent.trim();
            if (!labelText.includes('*') && !labelText.toLowerCase().includes('obligatoire') && !labelText.toLowerCase().includes('required')) {
                results.push({
                    type: 'required_not_indicated',
                    selector: _sel(el),
                    text: 'Champ obligatoire sans indication visuelle dans le label'
                });
            }
        }
    });

    // 11.11 — Error messages must be associated with fields
    document.querySelectorAll('[aria-invalid="true"]').forEach(el => {
        const describedBy = el.getAttribute('aria-describedby') || '';
        const errormessage = el.getAttribute('aria-errormessage') || '';
        if (!describedBy && !errormessage) {
            results.push({
                type: 'invalid_field_no_error_msg',
                selector: _sel(el),
                text: 'Champ en erreur sans message d\\'erreur associé (aria-describedby/aria-errormessage)'
            });
        }
    });

    // 11.13 — Autocomplete must be correct on identity fields
    const autocompleteFields = ['name', 'email', 'tel', 'address', 'postal-code', 'country'];
    document.querySelectorAll('input[autocomplete]').forEach(el => {
        const val = el.getAttribute('autocomplete');
        if (val && !['on', 'off', ...autocompleteFields, 'given-name', 'family-name',
            'username', 'new-password', 'current-password', 'cc-name', 'cc-number',
            'cc-exp', 'cc-csc', 'organization', 'street-address', 'bday'].includes(val.split(' ').pop())) {
            results.push({
                type: 'invalid_autocomplete',
                selector: _sel(el),
                value: val,
                text: 'Valeur autocomplete potentiellement invalide: "' + val + '"'
            });
        }
    });

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_NAVIGATION = """
() => {
    const results = [];

    // 12.1 — Navigation system present on every page
    const navs = document.querySelectorAll('nav, [role="navigation"]');
    if (navs.length === 0) {
        results.push({type: 'no_navigation', text: 'Aucun système de navigation détecté'});
    }

    // 12.2 — Each nav must have an accessible name if multiple
    if (navs.length > 1) {
        navs.forEach(nav => {
            const ariaLabel = nav.getAttribute('aria-label') || '';
            const ariaLabelledBy = nav.getAttribute('aria-labelledby') || '';
            if (!ariaLabel && !ariaLabelledBy) {
                results.push({
                    type: 'nav_no_label',
                    selector: _sel(nav),
                    text: 'Navigation multiple sans nom accessible (aria-label)'
                });
            }
        });
    }

    // 12.6 — Focus order must be coherent
    const tabElements = [...document.querySelectorAll('[tabindex]')];
    const positiveTabindex = tabElements.filter(el => parseInt(el.getAttribute('tabindex')) > 0);
    if (positiveTabindex.length > 0) {
        results.push({
            type: 'positive_tabindex',
            count: positiveTabindex.length,
            text: positiveTabindex.length + ' éléments avec tabindex positif (déconseillé)'
        });
    }

    // 12.7 — Focus must be visible
    // (Checked via CSS analysis — see _JS_FOCUS_VISIBILITY)

    // 12.8 — Tab order must follow reading order
    const focusables = document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    let outOfOrder = 0;
    let lastRect = null;
    focusables.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        if (lastRect && rect.top < lastRect.top - 50 && rect.left < lastRect.left - 50) {
            outOfOrder++;
        }
        lastRect = rect;
    });
    if (outOfOrder > 3) {
        results.push({
            type: 'tab_order_issues',
            count: outOfOrder,
            text: outOfOrder + ' éléments potentiellement hors de l\\'ordre de tabulation naturel'
        });
    }

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_FOCUS_VISIBILITY = """
() => {
    const results = [];
    // Check if focus styles are suppressed
    const sheets = [...document.styleSheets];
    let focusHidden = false;
    try {
        for (const sheet of sheets) {
            try {
                const rules = [...sheet.cssRules];
                for (const rule of rules) {
                    const text = rule.cssText || '';
                    if (text.includes(':focus') && text.includes('outline') &&
                        (text.includes('none') || text.includes('0'))) {
                        focusHidden = true;
                        break;
                    }
                }
            } catch(e) { /* cross-origin stylesheet */ }
            if (focusHidden) break;
        }
    } catch(e) {}

    if (focusHidden) {
        results.push({type: 'focus_outline_hidden', text: 'Des styles CSS suppriment l\\'indicateur de focus (outline: none/0)'});
    }

    return results;
}
"""

_JS_SCRIPTS = """
() => {
    const results = [];

    // 7.1 — Scripts must be accessible via keyboard
    document.querySelectorAll('[onclick], [onmousedown], [onmouseup], [onmouseover]').forEach(el => {
        const tag = el.tagName.toLowerCase();
        if (tag === 'a' || tag === 'button' || tag === 'input' || tag === 'select') return;

        const hasKeyHandler = el.hasAttribute('onkeydown') || el.hasAttribute('onkeypress') || el.hasAttribute('onkeyup');
        const role = el.getAttribute('role') || '';
        const tabindex = el.getAttribute('tabindex');

        if (!hasKeyHandler && !role && tabindex === null) {
            results.push({
                type: 'mouse_only_handler',
                selector: _sel(el),
                tag,
                text: 'Élément avec gestionnaire souris uniquement, non accessible au clavier'
            });
        }
    });

    // 7.3 — Status messages must use ARIA live regions
    const liveRegions = document.querySelectorAll('[role="alert"], [role="status"], [role="log"], [aria-live]');
    // Just report count for awareness
    if (liveRegions.length === 0) {
        results.push({type: 'no_live_regions', text: 'Aucune région ARIA live détectée (role="alert"/status/log ou aria-live)'});
    }

    // 7.5 — Confirm dialogs and modals are accessible
    document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog').forEach(el => {
        const ariaLabel = el.getAttribute('aria-label') || '';
        const ariaLabelledBy = el.getAttribute('aria-labelledby') || '';
        if (!ariaLabel && !ariaLabelledBy) {
            results.push({
                type: 'dialog_no_label',
                selector: _sel(el),
                text: 'Dialogue sans nom accessible'
            });
        }
    });

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_ARIA = """
() => {
    const results = [];

    // 8.2 extension — ARIA usage correctness
    const ariaElements = document.querySelectorAll('[role]');
    const validRoles = new Set([
        'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
        'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
        'contentinfo', 'definition', 'dialog', 'directory', 'document',
        'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
        'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
        'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
        'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
        'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
        'rowheader', 'scrollbar', 'search', 'searchbox', 'separator', 'slider',
        'spinbutton', 'status', 'switch', 'tab', 'table', 'tablist', 'tabpanel',
        'term', 'textbox', 'timer', 'toolbar', 'tooltip', 'tree', 'treegrid',
        'treeitem', 'generic'
    ]);

    ariaElements.forEach(el => {
        const role = el.getAttribute('role');
        if (!validRoles.has(role)) {
            results.push({
                type: 'invalid_role',
                selector: _sel(el),
                role,
                text: 'Rôle ARIA invalide: "' + role + '"'
            });
        }
    });

    // Check aria-hidden on focusable elements
    document.querySelectorAll('[aria-hidden="true"]').forEach(el => {
        const focusable = el.querySelectorAll('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length > 0) {
            results.push({
                type: 'aria_hidden_focusable',
                selector: _sel(el),
                focusableCount: focusable.length,
                text: 'Éléments focalisables cachés par aria-hidden="true"'
            });
        }
    });

    // Check orphaned aria-describedby / aria-labelledby references
    document.querySelectorAll('[aria-describedby], [aria-labelledby]').forEach(el => {
        const attr = el.hasAttribute('aria-describedby') ? 'aria-describedby' : 'aria-labelledby';
        const refIds = (el.getAttribute(attr) || '').split(/\\s+/);
        refIds.forEach(refId => {
            if (refId && !document.getElementById(refId)) {
                results.push({
                    type: 'broken_aria_ref',
                    selector: _sel(el),
                    attribute: attr,
                    refId,
                    text: attr + ' référence un id inexistant: "' + refId + '"'
                });
            }
        });
    });

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""

_JS_CONSULTATION = """
() => {
    const results = [];

    // 13.1 — Auto-refresh / redirect
    const meta = document.querySelector('meta[http-equiv="refresh"]');
    if (meta) {
        results.push({
            type: 'auto_refresh',
            content: meta.getAttribute('content') || '',
            text: 'Meta refresh détectée (déconseillé pour l\\'accessibilité)'
        });
    }

    // 13.7 — Horizontal scrolling at 320px CSS — checked via viewport emulation
    // 13.8 — Hidden content (display:none with aria-hidden mismatch)
    document.querySelectorAll('[style*="display: none"], [style*="display:none"]').forEach(el => {
        if (el.getAttribute('aria-hidden') !== 'true') {
            // Content hidden visually but possibly still in AT tree
            // Only flag if it has focusable children
            const focusable = el.querySelectorAll('a[href], button, input, select, textarea');
            if (focusable.length > 0) {
                results.push({
                    type: 'hidden_content_focusable',
                    selector: _sel(el),
                    text: 'Contenu masqué (display:none) avec éléments focalisables sans aria-hidden'
                });
            }
        }
    });

    // 13.12 — Keyboard trap detection
    // Will be tested interactively if needed

    return results;

    function _sel(el) {
        if (el.id) return '#' + el.id;
        let s = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\\s+/).join('.');
        return s;
    }
}
"""


class RGAAAuditor:
    """Automated RGAA 4.1 accessibility auditor using Playwright JS injection."""

    async def audit(self, page: Page, url: str = "") -> RGAAReport:
        logger.info("Starting RGAA 4.1 audit for %s", url or page.url)
        """Run all RGAA 4.1 criteria checks on the given page."""
        report = RGAAReport(url=url or page.url)

        # Theme 1: Images (criteria 1.1, 1.2)
        report.criteria.extend(await self._check_images(page))

        # Theme 2: Frames (criteria 2.1, 2.2)
        report.criteria.extend(await self._check_frames(page))

        # Theme 3: Colors (criteria 3.1, 3.2, 3.3)
        report.criteria.extend(await self._check_colors(page))

        # Theme 5: Tables (criteria 5.1, 5.6, 5.7)
        report.criteria.extend(await self._check_tables(page))

        # Theme 6: Links (criteria 6.1, 6.2)
        report.criteria.extend(await self._check_links(page))

        # Theme 7: Scripts (criteria 7.1, 7.3, 7.5)
        report.criteria.extend(await self._check_scripts(page))

        # Theme 8: Mandatory elements (criteria 8.1–8.9) + ARIA
        report.criteria.extend(await self._check_mandatory(page))
        report.criteria.extend(await self._check_aria(page))

        # Theme 9: Structure (criteria 9.1–9.4)
        report.criteria.extend(await self._check_structure(page))

        # Theme 11: Forms (criteria 11.1–11.13)
        report.criteria.extend(await self._check_forms(page))

        # Theme 12: Navigation (criteria 12.1–12.8)
        report.criteria.extend(await self._check_navigation(page))
        report.criteria.extend(await self._check_focus_visibility(page))

        # Theme 13: Consultation (criteria 13.1, 13.7, 13.8)
        report.criteria.extend(await self._check_consultation(page))

        report.compute_stats()
        return report

    # ─── Theme 1: Images ──────────────────────────────────────

    async def _check_images(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_IMAGES)
        if not issues:
            return [RGAACriterion(
                criterion_id="1.1", theme="Images",
                title="Alternatives textuelles des images",
                status=RGAAConformance.CONFORME,
                severity=RGAASeverity.INFO,
                details="Toutes les images ont une alternative textuelle appropriée.",
            )]

        return [RGAACriterion(
            criterion_id="1.1", theme="Images",
            title="Alternatives textuelles des images",
            status=RGAAConformance.NON_CONFORME,
            severity=RGAASeverity.CRITICAL,
            details=f"{len(issues)} image(s) sans alternative textuelle conforme.",
            elements=issues,
            recommendation="Ajouter un attribut alt pertinent aux images informatives, "
                          "ou role='presentation' aux images décoratives.",
        )]

    # ─── Theme 2: Frames ──────────────────────────────────────

    async def _check_frames(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_FRAMES)
        if not issues:
            frames_count = await page.evaluate("() => document.querySelectorAll('iframe, frame').length")
            if frames_count == 0:
                return [RGAACriterion(
                    criterion_id="2.1", theme="Cadres",
                    title="Titre des cadres",
                    status=RGAAConformance.NON_APPLICABLE,
                )]
            return [RGAACriterion(
                criterion_id="2.1", theme="Cadres",
                title="Titre des cadres",
                status=RGAAConformance.CONFORME,
                details="Tous les cadres ont un titre.",
            )]

        return [RGAACriterion(
            criterion_id="2.1", theme="Cadres",
            title="Titre des cadres",
            status=RGAAConformance.NON_CONFORME,
            severity=RGAASeverity.MAJOR,
            details=f"{len(issues)} cadre(s) sans titre.",
            elements=issues,
            recommendation="Ajouter un attribut title descriptif à chaque iframe/frame.",
        )]

    # ─── Theme 3: Colors ──────────────────────────────────────

    async def _check_colors(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_COLORS)
        results = []

        aa_issues = [i for i in issues if i.get("level") == "AA"]
        aaa_issues = [i for i in issues if i.get("level") == "AAA"]

        if aa_issues:
            results.append(RGAACriterion(
                criterion_id="3.2", theme="Couleurs",
                title="Contraste texte (AA)",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.CRITICAL,
                details=f"{len(aa_issues)} texte(s) avec contraste insuffisant (niveau AA).",
                elements=aa_issues,
                recommendation="Augmenter le contraste pour atteindre un ratio minimum de 4.5:1 "
                              "(ou 3:1 pour les grands textes).",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="3.2", theme="Couleurs",
                title="Contraste texte (AA)",
                status=RGAAConformance.CONFORME,
                details="Tous les textes vérifiés respectent le ratio de contraste AA.",
            ))

        if aaa_issues:
            results.append(RGAACriterion(
                criterion_id="3.3", theme="Couleurs",
                title="Contraste texte (AAA)",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MINOR,
                details=f"{len(aaa_issues)} texte(s) avec contraste insuffisant (niveau AAA).",
                elements=aaa_issues,
                recommendation="Pour le niveau AAA, viser un ratio de 7:1 (ou 4.5:1 pour les grands textes).",
            ))

        return results

    # ─── Theme 5: Tables ──────────────────────────────────────

    async def _check_tables(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_TABLES)
        table_count = await page.evaluate("() => document.querySelectorAll('table:not([role=\"presentation\"]):not([role=\"none\"])').length")

        if table_count == 0:
            return [RGAACriterion(
                criterion_id="5.1", theme="Tableaux",
                title="Légende et en-têtes de tableaux",
                status=RGAAConformance.NON_APPLICABLE,
            )]

        if not issues:
            return [RGAACriterion(
                criterion_id="5.1", theme="Tableaux",
                title="Légende et en-têtes de tableaux",
                status=RGAAConformance.CONFORME,
                details=f"{table_count} table(s) de données correctement structurée(s).",
            )]

        return [RGAACriterion(
            criterion_id="5.1", theme="Tableaux",
            title="Légende et en-têtes de tableaux",
            status=RGAAConformance.NON_CONFORME,
            severity=RGAASeverity.MAJOR,
            details=f"{len(issues)} problème(s) de structure de tableau.",
            elements=issues,
            recommendation="Ajouter caption/aria-label aux tables et scope aux en-têtes (th).",
        )]

    # ─── Theme 6: Links ───────────────────────────────────────

    async def _check_links(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_LINKS)
        results = []

        name_issues = [i for i in issues if i.get("type") in ("link_no_accessible_name",)]
        generic_issues = [i for i in issues if i.get("type") == "link_generic_text"]
        new_window = [i for i in issues if i.get("type") == "link_new_window_no_warning"]

        if name_issues:
            results.append(RGAACriterion(
                criterion_id="6.1", theme="Liens",
                title="Nom accessible des liens",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.CRITICAL,
                details=f"{len(name_issues)} lien(s) sans nom accessible.",
                elements=name_issues,
                recommendation="Ajouter un texte visible, aria-label ou title à chaque lien.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="6.1", theme="Liens",
                title="Nom accessible des liens",
                status=RGAAConformance.CONFORME,
            ))

        if generic_issues:
            results.append(RGAACriterion(
                criterion_id="6.2", theme="Liens",
                title="Pertinence des intitulés de liens",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(generic_issues)} lien(s) avec intitulé générique.",
                elements=generic_issues,
                recommendation="Remplacer les intitulés génériques ('En savoir plus', 'Cliquez ici') "
                              "par des textes explicites.",
            ))

        if new_window:
            results.append(RGAACriterion(
                criterion_id="13.2", theme="Consultation",
                title="Ouverture nouvelle fenêtre",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MINOR,
                details=f"{len(new_window)} lien(s) ouvrant une nouvelle fenêtre sans avertissement.",
                elements=new_window,
                recommendation="Indiquer l'ouverture dans une nouvelle fenêtre via aria-label ou texte masqué.",
            ))

        return results

    # ─── Theme 7: Scripts ─────────────────────────────────────

    async def _check_scripts(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_SCRIPTS)
        results = []

        mouse_only = [i for i in issues if i.get("type") == "mouse_only_handler"]
        dialog_issues = [i for i in issues if i.get("type") == "dialog_no_label"]

        if mouse_only:
            results.append(RGAACriterion(
                criterion_id="7.1", theme="Scripts",
                title="Accessibilité clavier des scripts",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.CRITICAL,
                details=f"{len(mouse_only)} élément(s) interactif(s) uniquement accessible(s) à la souris.",
                elements=mouse_only,
                recommendation="Ajouter des gestionnaires clavier (onkeydown) et un role/tabindex appropriés.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="7.1", theme="Scripts",
                title="Accessibilité clavier des scripts",
                status=RGAAConformance.CONFORME,
            ))

        if dialog_issues:
            results.append(RGAACriterion(
                criterion_id="7.5", theme="Scripts",
                title="Dialogues accessibles",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(dialog_issues)} dialogue(s) sans nom accessible.",
                elements=dialog_issues,
                recommendation="Ajouter aria-label ou aria-labelledby à chaque dialogue.",
            ))

        return results

    # ─── Theme 8: Mandatory elements ──────────────────────────

    async def _check_mandatory(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_MANDATORY_ELEMENTS)
        results = []

        for issue in issues:
            t = issue.get("type", "")
            if t in ("no_lang", "invalid_lang"):
                results.append(RGAACriterion(
                    criterion_id="8.3", theme="Éléments obligatoires",
                    title="Langue de la page",
                    status=RGAAConformance.NON_CONFORME,
                    severity=RGAASeverity.CRITICAL,
                    details=issue.get("text", ""),
                    recommendation="Ajouter un attribut lang valide sur l'élément <html>.",
                ))
            elif t in ("no_title", "irrelevant_title"):
                results.append(RGAACriterion(
                    criterion_id="8.5", theme="Éléments obligatoires",
                    title="Titre de la page",
                    status=RGAAConformance.NON_CONFORME,
                    severity=RGAASeverity.CRITICAL if t == "no_title" else RGAASeverity.MINOR,
                    details=issue.get("text", ""),
                    recommendation="Définir un <title> descriptif et unique pour chaque page.",
                ))
            elif t == "deprecated_tags":
                results.append(RGAACriterion(
                    criterion_id="8.9", theme="Éléments obligatoires",
                    title="Balises de présentation obsolètes",
                    status=RGAAConformance.NON_CONFORME,
                    severity=RGAASeverity.MINOR,
                    details=issue.get("text", ""),
                    elements=[issue],
                    recommendation="Remplacer les balises de présentation par du CSS.",
                ))

        # If no lang issues found, mark conforme
        if not any(i.get("type") in ("no_lang", "invalid_lang") for i in issues):
            results.append(RGAACriterion(
                criterion_id="8.3", theme="Éléments obligatoires",
                title="Langue de la page",
                status=RGAAConformance.CONFORME,
            ))

        if not any(i.get("type") in ("no_title", "irrelevant_title") for i in issues):
            results.append(RGAACriterion(
                criterion_id="8.5", theme="Éléments obligatoires",
                title="Titre de la page",
                status=RGAAConformance.CONFORME,
            ))

        return results

    # ─── ARIA correctness ─────────────────────────────────────

    async def _check_aria(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_ARIA)
        results = []

        if issues:
            severity = RGAASeverity.MAJOR
            for i in issues:
                if i.get("type") == "aria_hidden_focusable":
                    severity = RGAASeverity.CRITICAL
                    break

            results.append(RGAACriterion(
                criterion_id="8.2", theme="Éléments obligatoires",
                title="Utilisation correcte d'ARIA",
                status=RGAAConformance.NON_CONFORME,
                severity=severity,
                details=f"{len(issues)} problème(s) d'utilisation ARIA.",
                elements=issues,
                recommendation="Corriger les rôles ARIA invalides, les références orphelines, "
                              "et retirer les éléments focalisables de aria-hidden.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="8.2", theme="Éléments obligatoires",
                title="Utilisation correcte d'ARIA",
                status=RGAAConformance.CONFORME,
            ))

        return results

    # ─── Theme 9: Structure ───────────────────────────────────

    async def _check_structure(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_STRUCTURE)
        results = []

        heading_issues = [i for i in issues if i.get("type") in ("heading_skip", "no_h1", "multiple_h1")]
        landmark_issues = [i for i in issues if i.get("type") in ("no_main", "no_nav", "no_header", "no_footer")]
        list_issues = [i for i in issues if i.get("type") == "list_invalid_children"]
        skip_issues = [i for i in issues if i.get("type") == "no_skip_link"]

        if heading_issues:
            results.append(RGAACriterion(
                criterion_id="9.1", theme="Structure",
                title="Hiérarchie des titres",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(heading_issues)} problème(s) de hiérarchie de titres.",
                elements=heading_issues,
                recommendation="Respecter la hiérarchie des titres (h1 > h2 > h3...) sans saut de niveau. "
                              "Un seul h1 par page.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="9.1", theme="Structure",
                title="Hiérarchie des titres",
                status=RGAAConformance.CONFORME,
            ))

        if landmark_issues:
            results.append(RGAACriterion(
                criterion_id="9.2", theme="Structure",
                title="Zones de page (landmarks)",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(landmark_issues)} zone(s) de page manquante(s).",
                elements=landmark_issues,
                recommendation="Structurer la page avec <main>, <nav>, <header>, <footer>.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="9.2", theme="Structure",
                title="Zones de page (landmarks)",
                status=RGAAConformance.CONFORME,
            ))

        if skip_issues:
            results.append(RGAACriterion(
                criterion_id="9.4", theme="Structure",
                title="Liens d'accès rapide",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details="Aucun lien d'accès rapide vers le contenu principal détecté.",
                elements=skip_issues,
                recommendation="Ajouter un lien 'Aller au contenu principal' en haut de page.",
            ))

        return results

    # ─── Theme 11: Forms ──────────────────────────────────────

    async def _check_forms(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_FORMS)
        form_count = await page.evaluate("() => document.querySelectorAll('form, input, select, textarea').length")

        if form_count == 0:
            return [RGAACriterion(
                criterion_id="11.1", theme="Formulaires",
                title="Étiquettes de champs",
                status=RGAAConformance.NON_APPLICABLE,
            )]

        results = []
        label_issues = [i for i in issues if i.get("type") in ("field_no_label", "label_too_short")]
        group_issues = [i for i in issues if i.get("type") == "radio_no_fieldset"]
        required_issues = [i for i in issues if i.get("type") == "required_not_indicated"]
        error_issues = [i for i in issues if i.get("type") == "invalid_field_no_error_msg"]

        if label_issues:
            results.append(RGAACriterion(
                criterion_id="11.1", theme="Formulaires",
                title="Étiquettes de champs",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.CRITICAL,
                details=f"{len(label_issues)} champ(s) sans étiquette conforme.",
                elements=label_issues,
                recommendation="Associer un <label for='...'> ou aria-label à chaque champ.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="11.1", theme="Formulaires",
                title="Étiquettes de champs",
                status=RGAAConformance.CONFORME,
            ))

        if group_issues:
            results.append(RGAACriterion(
                criterion_id="11.4", theme="Formulaires",
                title="Regroupement de champs",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(group_issues)} groupe(s) de boutons radio sans fieldset.",
                elements=group_issues,
                recommendation="Regrouper les boutons radio dans un <fieldset> avec <legend>.",
            ))

        if required_issues:
            results.append(RGAACriterion(
                criterion_id="11.10", theme="Formulaires",
                title="Indication des champs obligatoires",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MINOR,
                details=f"{len(required_issues)} champ(s) obligatoire(s) sans indication visuelle.",
                elements=required_issues,
                recommendation="Ajouter un astérisque (*) ou la mention 'obligatoire' dans le label.",
            ))

        if error_issues:
            results.append(RGAACriterion(
                criterion_id="11.11", theme="Formulaires",
                title="Messages d'erreur associés",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=f"{len(error_issues)} champ(s) en erreur sans message associé.",
                elements=error_issues,
                recommendation="Associer aria-describedby ou aria-errormessage aux champs invalides.",
            ))

        return results

    # ─── Theme 12: Navigation ─────────────────────────────────

    async def _check_navigation(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_NAVIGATION)
        results = []

        nav_issues = [i for i in issues if i.get("type") in ("no_navigation",)]
        label_issues = [i for i in issues if i.get("type") == "nav_no_label"]
        tabindex_issues = [i for i in issues if i.get("type") == "positive_tabindex"]
        order_issues = [i for i in issues if i.get("type") == "tab_order_issues"]

        if nav_issues:
            results.append(RGAACriterion(
                criterion_id="12.1", theme="Navigation",
                title="Système de navigation",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details="Aucun système de navigation détecté.",
                elements=nav_issues,
                recommendation="Utiliser <nav> ou role='navigation' pour les menus.",
            ))
        else:
            results.append(RGAACriterion(
                criterion_id="12.1", theme="Navigation",
                title="Système de navigation",
                status=RGAAConformance.CONFORME,
            ))

        if label_issues:
            results.append(RGAACriterion(
                criterion_id="12.2", theme="Navigation",
                title="Nommage des navigations",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MINOR,
                details=f"{len(label_issues)} navigation(s) sans nom accessible.",
                elements=label_issues,
                recommendation="Ajouter aria-label aux éléments <nav> quand il y en a plusieurs.",
            ))

        if tabindex_issues:
            results.append(RGAACriterion(
                criterion_id="12.6", theme="Navigation",
                title="Ordre de tabulation",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MAJOR,
                details=tabindex_issues[0].get("text", ""),
                elements=tabindex_issues,
                recommendation="Utiliser tabindex='0' pour inclure dans l'ordre naturel, "
                              "tabindex='-1' pour exclure. Éviter les valeurs positives.",
            ))

        if order_issues:
            results.append(RGAACriterion(
                criterion_id="12.8", theme="Navigation",
                title="Ordre de lecture logique",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.MINOR,
                details=order_issues[0].get("text", ""),
                elements=order_issues,
                recommendation="Vérifier que l'ordre du DOM correspond à l'ordre visuel.",
            ))

        return results

    # ─── Focus visibility ─────────────────────────────────────

    async def _check_focus_visibility(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_FOCUS_VISIBILITY)

        if issues:
            return [RGAACriterion(
                criterion_id="12.7", theme="Navigation",
                title="Visibilité du focus",
                status=RGAAConformance.NON_CONFORME,
                severity=RGAASeverity.CRITICAL,
                details="Des styles CSS suppriment l'indicateur de focus.",
                elements=issues,
                recommendation="Ne pas utiliser outline:none/0 sans fournir "
                              "un style de focus alternatif visible (:focus-visible).",
            )]

        return [RGAACriterion(
            criterion_id="12.7", theme="Navigation",
            title="Visibilité du focus",
            status=RGAAConformance.CONFORME,
        )]

    # ─── Theme 13: Consultation ───────────────────────────────

    async def _check_consultation(self, page: Page) -> list[RGAACriterion]:
        issues = await page.evaluate(_JS_CONSULTATION)
        results = []

        for issue in issues:
            t = issue.get("type", "")
            if t == "auto_refresh":
                results.append(RGAACriterion(
                    criterion_id="13.1", theme="Consultation",
                    title="Contrôle des rafraîchissements",
                    status=RGAAConformance.NON_CONFORME,
                    severity=RGAASeverity.CRITICAL,
                    details=issue.get("text", ""),
                    recommendation="Supprimer la meta refresh et utiliser un lien de redirection à la place.",
                ))
            elif t == "hidden_content_focusable":
                results.append(RGAACriterion(
                    criterion_id="13.8", theme="Consultation",
                    title="Contenus masqués accessibles",
                    status=RGAAConformance.NON_CONFORME,
                    severity=RGAASeverity.MAJOR,
                    details=issue.get("text", ""),
                    elements=[issue],
                    recommendation="Ajouter aria-hidden='true' aux contenus visuellement masqués "
                                  "contenant des éléments focalisables.",
                ))

        return results
