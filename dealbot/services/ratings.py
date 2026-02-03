"""Product ratings service (Keepa, Rainforest, SerpAPI)."""

from abc import ABC, abstractmethod
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Rating
from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RatingsProvider(ABC):
    """Abstract base class for ratings providers."""

    @abstractmethod
    def get_rating(self, asin: str, marketplace: str = "ES") -> Optional[Rating]:
        """Get product rating for ASIN."""
        pass


class KeepaProvider(RatingsProvider):
    """Keepa API ratings provider."""

    API_BASE = "https://api.keepa.com"

    def __init__(self, config: Config) -> None:
        """Initialize Keepa provider."""
        self.config = config
        self.api_key = config.env("KEEPA_API_KEY")
        if not self.api_key:
            raise ValueError("KEEPA_API_KEY not set in environment")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=False,
    )
    def get_rating(self, asin: str, marketplace: str = "ES") -> Optional[Rating]:
        """Get rating from Keepa API."""
        # Keepa domain codes: 1=US, 3=DE, 4=FR, 5=JP, 6=UK, 8=ES, 9=IT
        domain_map = {"ES": 8, "UK": 6, "US": 1}
        domain = domain_map.get(marketplace, 8)

        try:
            response = requests.get(
                f"{self.API_BASE}/product",
                params={"key": self.api_key, "domain": domain, "asin": asin, "stats": 1},
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            if not data.get("products"):
                return None

            product = data["products"][0]
            rating_value = product.get("csv", [None] * 17)[16]  # Rating is at index 16

            if rating_value and rating_value != -1:
                rating_value = rating_value / 10  # Keepa stores ratings * 10
                # Keepa doesn't provide review count in basic endpoint
                return Rating(
                    value=rating_value, count=0, stars=Rating.render_stars(rating_value)
                )

            return None

        except Exception as e:
            logger.warning(f"Keepa API error for {asin}: {e}")
            return None


class RainforestProvider(RatingsProvider):
    """Rainforest API ratings provider."""

    API_BASE = "https://api.rainforestapi.com/request"

    def __init__(self, config: Config) -> None:
        """Initialize Rainforest provider."""
        self.config = config
        self.api_key = config.env("RAINFOREST_API_KEY")
        if not self.api_key:
            raise ValueError("RAINFOREST_API_KEY not set in environment")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=False,
    )
    def get_rating(self, asin: str, marketplace: str = "ES") -> Optional[Rating]:
        """Get rating from Rainforest API."""
        try:
            response = requests.get(
                self.API_BASE,
                params={
                    "api_key": self.api_key,
                    "type": "product",
                    "asin": asin,
                    "amazon_domain": f"amazon.{marketplace.lower()}",
                },
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            product = data.get("product", {})
            rating_value = product.get("rating")
            rating_count = product.get("ratings_total", 0)

            if rating_value:
                return Rating(
                    value=rating_value, count=rating_count, stars=Rating.render_stars(rating_value)
                )

            return None

        except Exception as e:
            logger.warning(f"Rainforest API error for {asin}: {e}")
            return None


class SerpAPIProvider(RatingsProvider):
    """SerpAPI fallback ratings provider."""

    API_BASE = "https://serpapi.com/search"

    def __init__(self, config: Config) -> None:
        """Initialize SerpAPI provider."""
        self.config = config
        self.api_key = config.env("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not set in environment")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=False,
    )
    def get_rating(self, asin: str, marketplace: str = "ES") -> Optional[Rating]:
        """Get rating from SerpAPI."""
        try:
            response = requests.get(
                self.API_BASE,
                params={
                    "api_key": self.api_key,
                    "engine": "amazon_product",
                    "asin": asin,
                    "amazon_domain": f"amazon.{marketplace.lower()}",
                },
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            product = data.get("product_results", {})
            rating_value = product.get("rating")
            rating_count = product.get("ratings_total", 0)

            if rating_value:
                return Rating(
                    value=rating_value, count=rating_count, stars=Rating.render_stars(rating_value)
                )

            return None

        except Exception as e:
            logger.warning(f"SerpAPI error for {asin}: {e}")
            return None


class RatingsService:
    """Ratings service manager."""

    def __init__(self, config: Config) -> None:
        """Initialize ratings service."""
        self.config = config
        self.enabled = config.ratings_enabled

        if not self.enabled:
            logger.info("Ratings service disabled in configuration")
            self.provider: Optional[RatingsProvider] = None
            return

        provider_name = config.ratings_provider

        # Initialize provider based on configuration
        try:
            if provider_name == "keepa":
                self.provider = KeepaProvider(config)
            elif provider_name == "rainforest":
                self.provider = RainforestProvider(config)
            elif provider_name == "serpapi":
                self.provider = SerpAPIProvider(config)
            else:
                logger.warning(f"Unknown ratings provider: {provider_name}, disabling ratings")
                self.provider = None
        except ValueError as e:
            logger.warning(f"Ratings provider not configured: {e}, disabling ratings")
            self.provider = None

    def get_rating(self, asin: str, marketplace: str = "ES") -> Optional[Rating]:
        """Get product rating."""
        if not self.enabled or not self.provider:
            return None

        try:
            return self.provider.get_rating(asin, marketplace)
        except Exception as e:
            logger.warning(f"Failed to fetch rating for {asin}: {e}")
            return None
