"""Core data models for DealBot."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class Currency(str, Enum):
    """Supported currencies."""

    EUR = "EUR"
    GBP = "GBP"
    USD = "USD"


class DealStatus(str, Enum):
    """Deal processing status."""

    PARSED = "parsed"
    VALIDATED = "validated"
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"
    FAILED = "failed"


class Deal(BaseModel):
    """Represents a parsed deal from input."""

    deal_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    title: str
    url: str
    asin: Optional[str] = None
    stated_price: Optional[float] = None
    source_pvp: Optional[float] = None  # PVP from source TXT file
    source_discount_pct: Optional[float] = None  # Discount % from source TXT file
    currency: Currency = Currency.EUR
    notes: Optional[str] = None
    status: DealStatus = DealStatus.PARSED
    language_flag: Optional[str] = None  # ES/EN


class PriceInfo(BaseModel):
    """Amazon PA-API price validation result."""

    asin: str
    title: str
    current_price: Optional[float] = None
    list_price: Optional[float] = None  # PVP (original price)
    savings_percentage: Optional[float] = None  # Discount %
    currency: Currency = Currency.EUR
    main_image_url: Optional[str] = None
    availability: Optional[str] = None
    review_rating: Optional[float] = None  # Customer rating (e.g., 4.5)
    review_count: Optional[int] = None  # Number of reviews
    discrepancy: Optional[float] = None  # Percentage difference from stated price
    needs_review: bool = False


class Rating(BaseModel):
    """Product rating information."""

    value: float  # e.g., 4.4
    count: int  # Number of ratings
    stars: str  # e.g., "★★★★☆"

    @staticmethod
    def render_stars(value: float) -> str:
        """Render star rating from float value."""
        full_stars = int(value)
        half_star = 1 if (value - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star

        stars = "★" * full_stars
        if half_star:
            stars += "☆"
        stars += "☆" * empty_stars

        return stars


class ShortLink(BaseModel):
    """Short link creation result."""

    short_url: str
    long_url: str
    provider: str  # "bitly" | "cloudflare"
    link_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class PublishResult(BaseModel):
    """WhatsApp publishing result."""

    deal_id: str
    destinations: list[str]  # Channel/group JIDs
    message_ids: dict[str, str]  # destination -> message_id
    sent_at: datetime = Field(default_factory=datetime.now)
    success: bool
    error: Optional[str] = None


class ProcessedDeal(BaseModel):
    """Fully processed deal ready for publishing."""

    deal: Deal
    price_info: PriceInfo
    adjusted_price: float
    short_link: ShortLink
    rating: Optional[Rating] = None
    interstitial_url: Optional[str] = None
    publish_result: Optional[PublishResult] = None
    is_duplicate: bool = False  # Recently published within 48h
    last_published: Optional[str] = None  # Timestamp of last publish
