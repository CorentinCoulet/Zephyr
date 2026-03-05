"""
Zephyr Core Analysis Engine.
"""

from core.browser_engine import BrowserEngine, Viewport, VIEWPORTS
from core.dom_extractor import DOMExtractor
from core.console_capture import ConsoleCapture
from core.screenshot_manager import ScreenshotManager
from core.perf_analyzer import PerfAnalyzer
from core.visual_diff import VisualDiff, DiffResult
from core.interaction_runner import InteractionRunner
from core.rgaa_auditor import RGAAAuditor, RGAAReport, RGAACriterion
from core.rgpd_auditor import RGPDAuditor, RGPDReport, RGPDCheck

__all__ = [
    "BrowserEngine",
    "Viewport",
    "VIEWPORTS",
    "DOMExtractor",
    "ConsoleCapture",
    "ScreenshotManager",
    "PerfAnalyzer",
    "VisualDiff",
    "DiffResult",
    "InteractionRunner",
    "RGAAAuditor",
    "RGAAReport",
    "RGAACriterion",
    "RGPDAuditor",
    "RGPDReport",
    "RGPDCheck",
]
