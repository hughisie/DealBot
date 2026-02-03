"""Configuration management for DealBot."""

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    """Application configuration manager."""

    def __init__(self, config_path: str | Path = "config.yaml") -> None:
        """Initialize configuration from YAML and environment variables."""
        self.config_path = self._find_config(config_path)
        self._config: dict[str, Any] = {}
        self.load()

    def _find_config(self, config_path: str | Path) -> Path:
        """Find config file in multiple locations."""
        search_paths = []
        
        # Check if running from macOS app bundle
        # Toga apps have structure: DealBot.app/Contents/MacOS/DealBot (executable)
        # Resources are at: DealBot.app/Contents/Resources/
        exe_path = Path(sys.executable)
        if "DealBot.app" in str(exe_path):
            # We're in the app bundle
            resources_dir = exe_path.parent.parent / "Resources"
            if resources_dir.exists():
                search_paths.append(resources_dir / config_path)
                search_paths.append(resources_dir / "app" / config_path)
        
        # Add standard search locations
        search_paths.extend([
            Path(config_path),  # Explicit path
            Path.cwd() / config_path,  # Current directory
            Path.home() / ".dealbot" / "config.yaml",  # User config
            Path(__file__).parent.parent.parent / config_path,  # Project root
        ])
        
        for path in search_paths:
            if path.exists():
                return path
        
        # If not found, return the default path (will error later with helpful message)
        return Path(config_path)

    def load(self) -> None:
        """Load configuration from YAML file and environment."""
        # Find and load .env file from same directory as config.yaml
        env_path = self.config_path.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try loading from current directory as fallback
            load_dotenv()

        # Load YAML config
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please check config.yaml and .env"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split(".")
        value: Any = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    def env(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable."""
        return os.getenv(key, default)

    def require_env(self, key: str) -> str:
        """Get required environment variable, raise if missing."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        return value

    @property
    def default_source_dir(self) -> str:
        """Get default source directory for deal files."""
        return str(self.get("default_source_dir", ""))

    @property
    def price_multiplier(self) -> float:
        """Get price adjustment multiplier."""
        return float(self.get("price_adjustment.multiplier", 1.0))

    @property
    def price_additive(self) -> float:
        """Get price adjustment additive."""
        return float(self.get("price_adjustment.additive", 0.0))

    @property
    def affiliate_tag(self) -> str:
        """Get Amazon affiliate tag from environment."""
        return self.require_env("AMAZON_ASSOCIATE_TAG")

    @property
    def whatsapp_channel(self) -> str:
        """Get WhatsApp channel ID."""
        return str(self.get("whatsapp.recipients.channel", ""))

    @property
    def whatsapp_group(self) -> str:
        """Get WhatsApp group ID."""
        return str(self.get("whatsapp.recipients.group", ""))

    @property
    def send_to_group(self) -> bool:
        """Check if should send to WhatsApp group."""
        return bool(self.get("whatsapp.send_to_group", False))

    def set_send_to_group(self, value: bool) -> None:
        """Update send_to_group setting."""
        if "whatsapp" not in self._config:
            self._config["whatsapp"] = {}
        self._config["whatsapp"]["send_to_group"] = value

    @property
    def shortlink_provider(self) -> str:
        """Get short link provider."""
        return str(self.get("shortlinks.provider", "bitly"))

    @property
    def shortlink_domain(self) -> str:
        """Get short link domain."""
        return str(self.get("shortlinks.domain", "amzon.fyi"))

    @property
    def ratings_enabled(self) -> bool:
        """Check if ratings are enabled."""
        return bool(self.get("ratings.enabled", True))

    @property
    def ratings_provider(self) -> str:
        """Get ratings provider."""
        return str(self.get("ratings.provider", "keepa"))

    @property
    def interstitial_enabled(self) -> bool:
        """Check if interstitial pages are enabled."""
        return bool(self.get("interstitial.enabled", True))

    @property
    def interstitial_countdown(self) -> int:
        """Get interstitial countdown seconds."""
        return int(self.get("interstitial.countdown_seconds", 2))

    @property
    def price_discrepancy_threshold(self) -> float:
        """Get price discrepancy threshold for warnings."""
        return float(self.get("price_validation.discrepancy_threshold", 0.15))
