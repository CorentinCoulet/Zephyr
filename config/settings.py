"""
Global configuration for Zephyr Intelligence Platform.
Reads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from enum import Enum


class ZephyrTheme(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class ZephyrVersion(int, Enum):
    MASCOT = 1
    SPIRIT = 2
    MINIMAL = 3
    FUTURISTIC = 4


class AgentMode(str, Enum):
    DEV = "dev"
    USER = "user"
    AUTO = "auto"


class Settings(BaseSettings):
    """Main application settings."""

    # --- App ---
    app_name: str = "Zephyr Intelligence Platform"
    app_version: str = "0.4.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    ws_port: int = 8001

    # --- Target ---
    target_url: str = Field(
        default="http://host.docker.internal:3000",
        description="Default URL of the project to analyze",
    )

    # --- Zephyr UI ---
    zephyr_theme: ZephyrTheme = ZephyrTheme.DARK
    zephyr_version: ZephyrVersion = ZephyrVersion.MASCOT
    default_mode: AgentMode = AgentMode.AUTO

    # --- Browser ---
    browser_headless: bool = True
    browser_ignore_https_errors: bool = True  # Set False when TLS matters
    browser_max_pages: int = 3
    browser_timeout: int = 30_000  # ms
    default_viewports: list[dict] = Field(default=[
        {"name": "mobile_s", "width": 320, "height": 568},
        {"name": "mobile_m", "width": 375, "height": 812},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "desktop", "width": 1440, "height": 900},
    ])

    # --- Paths ---
    screenshots_dir: str = "reports/screenshots"
    baselines_dir: str = "baselines"
    reports_dir: str = "reports"

    # --- Widget SDK ---
    widget_api_key: str = ""  # API key for widget auth (empty = no auth)
    widget_base_url: str = ""  # Public URL for widget (empty = auto)
    widget_allowed_origins: list[str] = Field(default=["*"])

    # --- Session ---
    session_timeout: int = 1800  # 30 min in seconds
    max_sessions: int = 10

    model_config = {"env_prefix": "ZEPHYR_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
