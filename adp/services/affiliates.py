"""Affiliate tag management service."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AffiliateService:
    """Ensure Amazon affiliate tag is present in URLs."""

    def __init__(self, config: Config) -> None:
        """Initialize affiliate service."""
        self.config = config
        self.tag = config.affiliate_tag
        self.tag_param = config.get("affiliates.tag_param", "tag")
        self.ensure_tag = config.get("affiliates.ensure_tag", True)

    def ensure_affiliate_tag(self, url: str) -> str:
        """Ensure affiliate tag is present in URL, append if missing."""
        if not self.ensure_tag:
            return url

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Check if tag already exists
        existing_tag = query_params.get(self.tag_param, [None])[0]

        if existing_tag == self.tag:
            logger.debug(f"Affiliate tag already present: {url}")
            return url

        # Add or replace tag
        query_params[self.tag_param] = [self.tag]

        # Rebuild query string
        new_query = urlencode(query_params, doseq=True)

        # Rebuild URL
        new_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

        logger.info(f"Added affiliate tag to URL: {self.tag}")
        return new_url

    def clean_url(self, url: str, keep_params: list[str] | None = None) -> str:
        """Clean URL by removing tracking parameters except specified ones."""
        if keep_params is None:
            keep_params = [self.tag_param]

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Keep only specified parameters
        cleaned_params = {k: v for k, v in query_params.items() if k in keep_params}

        new_query = urlencode(cleaned_params, doseq=True)

        cleaned_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

        return cleaned_url
