"""
Performance Analyzer — Lighthouse integration for web performance auditing.
Runs audits, compares reports, extracts optimisation opportunities.
"""

import asyncio
import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ScoreCard:
    """Performance score summary."""
    performance: int = 0
    accessibility: int = 0
    best_practices: int = 0
    seo: int = 0

    def to_dict(self) -> dict:
        return {
            "performance": self.performance,
            "accessibility": self.accessibility,
            "best_practices": self.best_practices,
            "seo": self.seo,
        }

    @property
    def overall(self) -> int:
        scores = [self.performance, self.accessibility, self.best_practices, self.seo]
        return round(sum(scores) / len(scores))


@dataclass
class Opportunity:
    """Performance optimisation opportunity from Lighthouse."""
    title: str
    description: str
    score: Optional[float] = None
    savings_ms: float = 0
    savings_bytes: float = 0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "score": self.score,
            "savings_ms": self.savings_ms,
            "savings_bytes": self.savings_bytes,
        }


@dataclass
class AuditConfig:
    """Configuration for a Lighthouse audit."""
    categories: list[str] = field(default_factory=lambda: [
        "performance", "accessibility", "best-practices", "seo"
    ])
    form_factor: str = "desktop"  # "desktop" or "mobile"
    throttling: bool = True
    max_wait_for_load: int = 45_000
    output_format: str = "json"


class PerfAnalyzer:
    """Runs and interprets Lighthouse performance audits."""

    LIGHTHOUSE_CMD = "lighthouse"

    async def run_audit(
        self, url: str, config: Optional[AuditConfig] = None
    ) -> dict:
        """Run a Lighthouse audit and return the raw JSON report."""
        cfg = config or AuditConfig()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_path = tmp.name

        categories_flags = " ".join(
            f"--only-categories={cat}" for cat in cfg.categories
        )

        cmd = (
            f"{self.LIGHTHOUSE_CMD} {url} "
            f"--output=json "
            f"--output-path={output_path} "
            f"--chrome-flags='--headless --no-sandbox --disable-gpu' "
            f"--form-factor={cfg.form_factor} "
            f"--max-wait-for-load={cfg.max_wait_for_load} "
            f"{categories_flags} "
            f"--quiet"
        )

        if not cfg.throttling:
            cmd += " --throttling-method=provided"

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        try:
            report_path = Path(output_path)
            report = json.loads(report_path.read_text())
            report_path.unlink(missing_ok=True)
            return report
        except Exception as e:
            return {
                "error": str(e),
                "stderr": stderr.decode() if stderr else "",
            }

    def extract_scores(self, report: dict) -> ScoreCard:
        """Extract the category scores from a Lighthouse report."""
        categories = report.get("categories", {})
        return ScoreCard(
            performance=self._score(categories.get("performance")),
            accessibility=self._score(categories.get("accessibility")),
            best_practices=self._score(categories.get("best-practices")),
            seo=self._score(categories.get("seo")),
        )

    def extract_opportunities(self, report: dict) -> list[Opportunity]:
        """Extract optimisation opportunities from the audit."""
        audits = report.get("audits", {})
        opportunities = []

        for key, audit in audits.items():
            score = audit.get("score")
            if score is not None and score < 1:
                details = audit.get("details", {})
                savings = details.get("overallSavingsMs", 0)
                savings_bytes = details.get("overallSavingsBytes", 0)

                if savings > 0 or savings_bytes > 0 or (score is not None and score < 0.5):
                    opportunities.append(
                        Opportunity(
                            title=audit.get("title", key),
                            description=audit.get("description", ""),
                            score=score,
                            savings_ms=savings,
                            savings_bytes=savings_bytes,
                            details=details,
                        )
                    )

        opportunities.sort(key=lambda o: o.savings_ms, reverse=True)
        return opportunities

    def extract_metrics(self, report: dict) -> dict:
        """Extract Core Web Vitals and other key metrics."""
        audits = report.get("audits", {})
        metrics = {}

        metric_keys = {
            "largest-contentful-paint": "LCP",
            "first-contentful-paint": "FCP",
            "cumulative-layout-shift": "CLS",
            "total-blocking-time": "TBT",
            "speed-index": "SI",
            "interactive": "TTI",
            "server-response-time": "TTFB",
        }

        for key, label in metric_keys.items():
            audit = audits.get(key, {})
            metrics[label] = {
                "value": audit.get("numericValue", 0),
                "unit": audit.get("numericUnit", ""),
                "score": audit.get("score", 0),
                "display": audit.get("displayValue", ""),
            }

        return metrics

    def compare_reports(
        self, before: dict, after: dict
    ) -> dict:
        """Compare two Lighthouse reports and return deltas."""
        before_scores = self.extract_scores(before)
        after_scores = self.extract_scores(after)
        before_metrics = self.extract_metrics(before)
        after_metrics = self.extract_metrics(after)

        score_deltas = {
            "performance": after_scores.performance - before_scores.performance,
            "accessibility": after_scores.accessibility - before_scores.accessibility,
            "best_practices": after_scores.best_practices - before_scores.best_practices,
            "seo": after_scores.seo - before_scores.seo,
        }

        metric_deltas = {}
        for key in after_metrics:
            if key in before_metrics:
                before_val = before_metrics[key].get("value", 0)
                after_val = after_metrics[key].get("value", 0)
                metric_deltas[key] = {
                    "before": before_val,
                    "after": after_val,
                    "delta": round(after_val - before_val, 2),
                    "improved": after_val < before_val,  # Lower is better for timing
                }

        return {
            "score_deltas": score_deltas,
            "metric_deltas": metric_deltas,
            "before_scores": before_scores.to_dict(),
            "after_scores": after_scores.to_dict(),
        }

    def generate_score_card(self, report: dict) -> ScoreCard:
        """Generate a ScoreCard from a report."""
        return self.extract_scores(report)

    # --- Private ---

    @staticmethod
    def _score(category: Optional[dict]) -> int:
        if not category:
            return 0
        return round((category.get("score", 0) or 0) * 100)
