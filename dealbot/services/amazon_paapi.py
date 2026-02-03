"""Amazon Product Advertising API integration."""

from typing import Dict, Optional

from amazon_paapi import AmazonApi
from amazon_paapi.sdk.models.get_items_resource import GetItemsResource
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Currency, PriceInfo
from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AmazonPAAPIService:
    """Amazon PA-API price validation service."""

    MARKETPLACE_MAP = {
        Currency.EUR: "ES",  # Spain
        Currency.GBP: "UK",
        Currency.USD: "US",
    }

    def __init__(self, config: Config) -> None:
        """Initialize Amazon PA-API client."""
        self.config = config
        self.access_key = config.require_env("AMAZON_PAAPI_ACCESS_KEY")
        self.secret_key = config.require_env("AMAZON_PAAPI_SECRET_KEY")
        self.associate_tag = config.affiliate_tag
        self._apis: dict[str, AmazonApi] = {}

    def _get_api(self, marketplace: str) -> AmazonApi:
        """Get or create API client for marketplace."""
        if marketplace not in self._apis:
            self._apis[marketplace] = AmazonApi(
                key=self.access_key,
                secret=self.secret_key,
                tag=self.associate_tag,
                country=marketplace,
            )
        return self._apis[marketplace]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def validate_price(
        self, asin: str, currency: Currency = Currency.EUR, stated_price: Optional[float] = None,
        source_pvp: Optional[float] = None, source_discount_pct: Optional[float] = None
    ) -> PriceInfo:
        """Validate product price via PA-API."""
        marketplace = self.MARKETPLACE_MAP.get(currency, "ES")
        api = self._get_api(marketplace)

        logger.info(f"Validating price for ASIN {asin} in {marketplace}")

        try:
            # Get item details
            # python-amazon-paapi automatically requests all available resources including customer reviews
            items = api.get_items([asin])

            if not items or len(items) == 0:
                logger.warning(f"No data returned for ASIN {asin}")
                
                # FALLBACK: Use stated price from TXT file when PA-API returns no data
                if stated_price:
                    logger.warning(f"No PA-API data for {asin}, using stated price from file: {currency}{stated_price}")
                    return PriceInfo(
                        asin=asin,
                        title=f"Product {asin}",
                        currency=currency,
                        current_price=stated_price,  # Use stated price as fallback
                        list_price=source_pvp,  # Use source PVP if available
                        savings_percentage=source_discount_pct,  # Use source discount
                        availability="Now",  # Assume available since we have a price in the file
                        needs_review=True,  # Mark for review since PA-API returned no data
                    )
                
                # No fallback available
                return PriceInfo(
                    asin=asin,
                    title=f"Product {asin}",
                    currency=currency,
                    needs_review=True,
                )

            item = items[0]

            # Extract current price and list price (PVP)
            current_price: Optional[float] = None
            list_price: Optional[float] = None
            savings_percentage: Optional[float] = None
            
            if hasattr(item, "offers") and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                
                # Current/sale price
                if hasattr(listing, "price") and listing.price:
                    current_price = float(listing.price.amount)
                    logger.info(f"Current price for {asin}: {current_price}")
                
                # Try to get list price from multiple possible fields
                # 1. Try saving_basis (common for discounted items)
                if hasattr(listing, "saving_basis") and listing.saving_basis:
                    list_price = float(listing.saving_basis.amount)
                    logger.info(f"Found list price (saving_basis) for {asin}: {list_price}")
                
                # 2. Try list_price directly from offers
                if not list_price and hasattr(item.offers, "listings") and item.offers.listings:
                    for listing_item in item.offers.listings:
                        if hasattr(listing_item, "list_price") and listing_item.list_price:
                            list_price = float(listing_item.list_price.amount)
                            logger.info(f"Found list price (listings.list_price) for {asin}: {list_price}")
                            break
                
                # 3. Check if offers has summaries with list price
                if not list_price and hasattr(item.offers, "summaries") and item.offers.summaries:
                    for summary in item.offers.summaries:
                        if hasattr(summary, "highest_price") and summary.highest_price:
                            list_price = float(summary.highest_price.amount)
                            logger.info(f"Found list price (summaries.highest_price) for {asin}: {list_price}")
                            break
                        elif hasattr(summary, "lowest_price") and summary.lowest_price:
                            # Sometimes lowest_price in summaries is actually the list price
                            potential_list = float(summary.lowest_price.amount)
                            if current_price and potential_list > current_price:
                                list_price = potential_list
                                logger.info(f"Found list price (summaries.lowest_price > current) for {asin}: {list_price}")
                                break
                
                # Calculate discount percentage
                if current_price and list_price and list_price > current_price:
                    savings_percentage = ((list_price - current_price) / list_price) * 100
                    logger.info(f"Discount found: {currency}{current_price} (was {currency}{list_price}) = -{savings_percentage:.0f}%")
            
            # Fallback: Use source PVP if PA-API didn't provide list price
            if not list_price and source_pvp and current_price:
                if source_pvp > current_price:
                    list_price = source_pvp
                    savings_percentage = source_discount_pct if source_discount_pct else ((list_price - current_price) / list_price) * 100
                    logger.info(f"Using source PVP: {currency}{list_price} (discount: -{savings_percentage:.0f}%)")

            # Extract title
            title = str(item.item_info.title.display_value) if item.item_info.title else asin

            # Extract image
            main_image_url: Optional[str] = None
            if hasattr(item, "images") and item.images and item.images.primary:
                main_image_url = str(item.images.primary.large.url)

            # Extract customer reviews/ratings from PA-API
            review_rating: Optional[float] = None
            review_count: Optional[int] = None
            
            logger.debug(f"Checking customer_reviews for {asin}: exists={hasattr(item, 'customer_reviews')}, value={getattr(item, 'customer_reviews', None)}")
            
            if hasattr(item, "customer_reviews") and item.customer_reviews:
                logger.debug(f"CustomerReviews object found for {asin}")
                
                if hasattr(item.customer_reviews, "star_rating") and item.customer_reviews.star_rating:
                    # Star rating comes as "4.5 out of 5 stars" or just a float
                    rating_value = getattr(item.customer_reviews.star_rating, "value", None)
                    if rating_value:
                        review_rating = float(rating_value)
                        logger.info(f"⭐ Found rating for {asin}: {review_rating}/5")
                
                if hasattr(item.customer_reviews, "count") and item.customer_reviews.count:
                    review_count = int(item.customer_reviews.count)
                    logger.info(f"📝 Found {review_count:,} reviews for {asin}")
                
                if review_rating:
                    logger.info(f"✅ Reviews extracted for {asin}: {review_rating}/5 ({review_count or 0} reviews)")
                else:
                    logger.warning(f"⚠️ CustomerReviews exists for {asin} but no rating found")
            else:
                logger.debug(f"ℹ️ No customer_reviews data available from PA-API for {asin}")

            # Initialize review flags
            discrepancy: Optional[float] = None
            needs_review = False

            # Extract availability and check if in stock
            availability: Optional[str] = None
            if hasattr(item, "offers") and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, "availability") and listing.availability:
                    availability_type = getattr(listing.availability, "type", None)
                    availability_message = getattr(listing.availability, "message", None)
                    
                    # Check if available for purchase
                    if availability_type:
                        availability = str(availability_type)
                        logger.info(f"Availability for {asin}: {availability}")
                    
                    # Only mark as unavailable if explicitly stated (not just missing "Now")
                    # Common availability_type values: "Now", "Backorder", "Preorder"
                    if availability_type and availability_type not in ["Now", "Backorder", "Preorder"]:
                        logger.warning(f"⚠️ Product {asin} may not be available: {availability_message or availability_type}")
                        needs_review = True
                    elif not availability_type and current_price:
                        # If we have a price but no availability info, assume available
                        availability = "Now"
                        logger.info(f"Assuming {asin} is available (has price, no explicit unavailability)")
                elif current_price:
                    # No availability object but has price - assume available
                    availability = "Now"
                    logger.info(f"Assuming {asin} is available (has price)")
            elif current_price:
                # No offers.listings but has price - assume available
                availability = "Now"
                logger.info(f"Assuming {asin} is available (has current price)")

            # If we still don't have a price, use stated_price as fallback
            if not current_price and stated_price:
                current_price = stated_price
                availability = "Now"  # Assume available if we have a stated price
                logger.info(f"Using stated price as fallback for {asin}: {currency}{current_price}")

            # Calculate discrepancy
            if stated_price and current_price:
                discrepancy = abs(current_price - stated_price) / stated_price
                threshold = self.config.price_discrepancy_threshold
                if discrepancy > threshold:
                    needs_review = True
                    logger.warning(
                        f"Price discrepancy for {asin}: "
                        f"stated={stated_price}, current={current_price}, "
                        f"diff={discrepancy:.1%}"
                    )

            price_info = PriceInfo(
                asin=asin,
                title=title,
                current_price=current_price,
                list_price=list_price,
                savings_percentage=savings_percentage,
                currency=currency,
                main_image_url=main_image_url,
                availability=availability,
                review_rating=review_rating,
                review_count=review_count,
                discrepancy=discrepancy,
                needs_review=needs_review,
            )

            logger.info(f"Validated {asin}: price={current_price} {currency}")
            return price_info

        except Exception as e:
            logger.error(f"PA-API error for {asin}: {e}")
            
            # FALLBACK: Use stated price from TXT file when PA-API fails
            if stated_price:
                logger.warning(f"PA-API failed for {asin}, using stated price from file: {currency}{stated_price}")
                return PriceInfo(
                    asin=asin,
                    title=f"Product {asin}",
                    currency=currency,
                    current_price=stated_price,  # Use stated price as fallback
                    list_price=source_pvp,  # Use source PVP if available
                    savings_percentage=source_discount_pct,  # Use source discount
                    availability="Now",  # Assume available since we have a price in the file
                    needs_review=True,  # Mark for review since PA-API failed
                )
            
            # No fallback available
            return PriceInfo(
                asin=asin,
                title=f"Product {asin}",
                currency=currency,
                needs_review=True,
            )
