"""Short link creation service (Bitly + Cloudflare Workers)."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import ShortLink
from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ShortLinkProvider(ABC):
    """Abstract base class for short link providers."""

    @abstractmethod
    def create_short_link(self, long_url: str, slug: Optional[str] = None) -> ShortLink:
        """Create a short link for the given URL."""
        pass


class BitlyProvider(ShortLinkProvider):
    """Bitly short link provider with branded domain."""

    API_BASE = "https://api-ssl.bitly.com/v4"

    def __init__(self, config: Config) -> None:
        """Initialize Bitly provider."""
        self.config = config
        self.token = config.env("BITLY_TOKEN")
        if not self.token:
            raise ValueError("BITLY_TOKEN not set in environment")
        self.domain = config.shortlink_domain

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def create_short_link(self, long_url: str, slug: Optional[str] = None) -> ShortLink:
        """Create Bitly short link with branded domain."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload: dict[str, str] = {
            "long_url": long_url,
            "domain": self.domain,
        }

        if slug:
            payload["title"] = slug

        response = requests.post(
            f"{self.API_BASE}/bitlinks",
            headers=headers,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        short_url = data["link"]
        link_id = data["id"]

        logger.info(f"Created Bitly short link: {short_url}")

        return ShortLink(
            short_url=short_url,
            long_url=long_url,
            provider="bitly",
            link_id=link_id,
        )


class CloudflareProvider(ShortLinkProvider):
    """Cloudflare Workers + KV short link provider."""

    def __init__(self, config: Config) -> None:
        """Initialize Cloudflare provider."""
        self.config = config
        self.account_id = config.env("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = config.env("CLOUDFLARE_API_TOKEN")
        self.domain = config.shortlink_domain

        if not self.account_id or not self.api_token:
            raise ValueError("Cloudflare credentials not set in environment")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def create_short_link(self, long_url: str, slug: Optional[str] = None) -> ShortLink:
        """Create short link via Cloudflare Workers API."""
        if not slug:
            # Generate slug from URL hash
            slug = hashlib.md5(long_url.encode()).hexdigest()[:8]

        # POST to Worker's /shorten endpoint
        worker_url = f"https://{self.domain}/shorten"
        
        payload = {
            "url": long_url,
            "slug": slug,
        }
        
        try:
            response = requests.post(
                worker_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            short_url = data["short_url"]
            
            logger.info(f"Created Cloudflare short link: {short_url}")
            
            return ShortLink(
                short_url=short_url,
                long_url=long_url,
                provider="cloudflare",
                link_id=slug,
            )
        except Exception as e:
            logger.error(f"Failed to create Cloudflare short link: {e}")
            # Fallback: construct URL directly
            short_url = f"https://{self.domain}/{slug}"
            logger.warning(f"Using fallback URL: {short_url}")
            
            return ShortLink(
                short_url=short_url,
                long_url=long_url,
                provider="cloudflare",
                link_id=slug,
            )


class ShortLinkService:
    """Short link creation service manager."""

    def __init__(self, config: Config) -> None:
        """Initialize short link service."""
        self.config = config
        provider_name = config.shortlink_provider

        # Initialize provider based on configuration
        if provider_name == "bitly":
            try:
                self.provider: ShortLinkProvider = BitlyProvider(config)
            except ValueError as e:
                logger.warning(f"Bitly not configured: {e}, falling back to Cloudflare")
                self.provider = CloudflareProvider(config)
        elif provider_name == "cloudflare":
            self.provider = CloudflareProvider(config)
        else:
            raise ValueError(f"Unknown short link provider: {provider_name}")

    def create_short_link(self, long_url: str, slug: Optional[str] = None) -> ShortLink:
        """Create short link using configured provider."""
        return self.provider.create_short_link(long_url, slug)
