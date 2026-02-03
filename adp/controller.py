"""Main controller orchestrating the deal processing pipeline."""

from pathlib import Path
from typing import Optional

from .models import Deal, DealStatus, ProcessedDeal, PublishResult
from .parsers.txt_parser import TxtParser
from .services.affiliates import AffiliateService
from .services.amazon_paapi import AmazonPAAPIService
from .services.interstitial import InterstitialServer
from .services.pricing import PricingService
from .services.ratings import RatingsService
from .services.scrapula import ScrapulaService
from .services.shortlinks import ShortLinkService
from .services.whapi import WhapiService
from .storage.db import Database
from .ui.whatsapp_format import WhatsAppFormatter
from .utils.config import Config
from .utils.logging import get_logger

logger = get_logger(__name__)


class DealController:
    """Orchestrates the deal processing pipeline."""

    def __init__(self, config: Config) -> None:
        """Initialize controller with all services."""
        self.config = config

        # Initialize services
        self.parser = TxtParser()
        self.amazon_api = AmazonPAAPIService(config)
        self.pricing = PricingService(config)
        self.affiliates = AffiliateService(config)
        
        # Shortlinks service (optional)
        try:
            self.shortlinks = ShortLinkService(config)
        except ValueError as e:
            logger.warning(f"Shortlinks disabled: {e}")
            self.shortlinks = None  # type: ignore
        
        self.ratings = RatingsService(config)
        self.whapi = WhapiService(config)
        self.formatter = WhatsAppFormatter()
        self.db = Database()
        
        # Initialize Scrapula service if enabled
        self.scrapula: Optional[ScrapulaService] = None
        if config.get("scrapula", {}).get("enabled", False):
            try:
                api_key = config.env("SCRAPULA_API_KEY")
                if not api_key:
                    raise ValueError("SCRAPULA_API_KEY not found in environment")
                service_name = config.get("scrapula", {}).get("service_name", "amazon_products_service_v2")
                self.scrapula = ScrapulaService(api_key, service_name=service_name)
                logger.info("Scrapula service initialized")
            except Exception as e:
                logger.warning(f"Scrapula disabled: {e}")
                self.scrapula = None

        # Initialize interstitial server if enabled
        self.interstitial_server: Optional[InterstitialServer] = None
        if config.interstitial_enabled:
            self.interstitial_server = InterstitialServer(config)
            self.interstitial_server.start()
        
        # Cache for Scrapula enrichment data
        self._scrapula_cache = {}

    def parse_file(self, file_path: str | Path) -> list[Deal]:
        """Parse deals from TXT file."""
        logger.info(f"Parsing file: {file_path}")
        deals = self.parser.parse_file(file_path)
        logger.info(f"Parsed {len(deals)} deals")
        
        # Enrich with Scrapula data if enabled
        if self.scrapula and deals:
            logger.info(f"Enriching {len(deals)} deals with Scrapula data...")
            self._enrich_with_scrapula(deals)
        
        return deals
    
    def _enrich_with_scrapula(self, deals: list[Deal]) -> None:
        """Enrich deals with Scrapula product data (images, ratings, etc.)."""
        # Collect ASINs from deals
        asins = [deal.asin for deal in deals if deal.asin]
        
        if not asins:
            logger.warning("No ASINs found in deals, skipping Scrapula enrichment")
            return
        
        try:
            # Get marketplace from config
            marketplace = self.config.get("scrapula", {}).get("marketplace", "es")
            max_wait = self.config.get("scrapula", {}).get("max_wait_seconds", 60)
            
            # Fetch batch product data
            logger.info(f"Fetching Scrapula data for {len(asins)} products...")
            scrapula_data = self.scrapula.get_batch_product_data(
                asins=asins,
                marketplace=marketplace,
                max_wait_seconds=max_wait
            )
            
            # Cache the data for use in process_deal
            self._scrapula_cache = scrapula_data
            
            # Log success rate
            successful = sum(1 for data in scrapula_data.values() if data.success)
            logger.info(f"Scrapula enrichment: {successful}/{len(asins)} products retrieved successfully")
            
        except Exception as e:
            logger.error(f"Failed to enrich deals with Scrapula: {e}")
            self._scrapula_cache = {}

    def process_deal(self, deal: Deal) -> ProcessedDeal:
        """Process a single deal through the pipeline."""
        logger.info(f"Processing deal: {deal.title[:50]}...")

        # Step 1: Validate price via Amazon PA-API
        if not deal.asin:
            logger.warning(f"Deal has no ASIN, skipping PA-API validation")
            # Create basic price info
            from .models import PriceInfo

            price_info = PriceInfo(
                asin="unknown",
                title=deal.title,
                currency=deal.currency,
                current_price=deal.stated_price,
                needs_review=True,
            )
        else:
            price_info = self.amazon_api.validate_price(
                deal.asin, deal.currency, deal.stated_price,
                source_pvp=deal.source_pvp, source_discount_pct=deal.source_discount_pct
            )
            
            # Merge Scrapula data if available
            if deal.asin in self._scrapula_cache:
                scrapula_info = self._scrapula_cache[deal.asin]
                if scrapula_info.success:
                    # Use Scrapula image if available and PA-API didn't provide one
                    if not price_info.main_image_url and scrapula_info.image_url:
                        price_info.main_image_url = scrapula_info.image_url
                        logger.info(f"Added Scrapula image for {deal.asin}")
                    
                    # Use Scrapula rating/reviews if PA-API didn't provide them
                    if not price_info.review_rating and scrapula_info.rating:
                        price_info.review_rating = scrapula_info.rating
                        logger.info(f"Added Scrapula rating for {deal.asin}")
                    
                    if not price_info.review_count and scrapula_info.review_count:
                        price_info.review_count = scrapula_info.review_count

        deal.status = DealStatus.VALIDATED

        # Step 2: Apply price adjustment
        if price_info.current_price:
            adjusted_price = self.pricing.adjust_price(price_info.current_price)
        elif deal.stated_price:
            adjusted_price = self.pricing.adjust_price(deal.stated_price)
        else:
            logger.warning("No price available, using 0.0")
            adjusted_price = 0.0

        # Step 3: Ensure affiliate tag
        final_url = self.affiliates.ensure_affiliate_tag(deal.url)
        deal.url = final_url

        # Step 4: Create short link (to interstitial or directly to Amazon)
        if self.shortlinks:
            if self.interstitial_server:
                # Create interstitial URL
                interstitial_url = self.interstitial_server.get_interstitial_url(deal.deal_id)
                short_link = self.shortlinks.create_short_link(interstitial_url)
            else:
                # Link directly to Amazon
                short_link = self.shortlinks.create_short_link(final_url)
        else:
            # No shortlinks service - use direct Amazon URL
            from .models import ShortLink
            short_link = ShortLink(
                short_url=final_url,
                long_url=final_url,
                provider="direct",
            )

        # Step 5: Get ratings (optional, non-blocking)
        rating = None
        if deal.asin:
            marketplace = {"EUR": "ES", "GBP": "UK", "USD": "US"}.get(
                deal.currency.value, "ES"
            )
            rating = self.ratings.get_rating(deal.asin, marketplace)

        # Create processed deal
        processed = ProcessedDeal(
            deal=deal,
            price_info=price_info,
            adjusted_price=adjusted_price,
            short_link=short_link,
            rating=rating,
            interstitial_url=(
                self.interstitial_server.get_interstitial_url(deal.deal_id)
                if self.interstitial_server
                else None
            ),
        )

        logger.info(f"Deal processed: {deal.title[:50]}...")
        return processed

    def publish_to_whatsapp(
        self, processed: ProcessedDeal, to_group: bool = False
    ) -> "PublishResult":
        """Publish processed deal to WhatsApp. Returns PublishResult."""
        result = self.publish_deal(processed, include_group=to_group)
        return result.publish_result if result.publish_result else PublishResult(
            deal_id=processed.deal.deal_id,
            success=False,
            error="Failed to publish",
            destinations=[],
            message_ids={},
        )

    def publish_deal(
        self, processed: ProcessedDeal, include_group: bool = False
    ) -> ProcessedDeal:
        """Publish deal to WhatsApp."""
        logger.info(f"Publishing deal: {processed.deal.title[:50]}...")

        # Check if product is available for purchase
        if processed.price_info:
            # Skip if no current price (means product unavailable or restricted)
            if not processed.price_info.current_price:
                logger.error(f"❌ SKIPPING - No price available for {processed.deal.asin} (likely out of stock or unavailable)")
                processed.deal.status = DealStatus.FAILED
                from .models import PublishResult
                processed.publish_result = PublishResult(
                    deal_id=processed.deal.deal_id,
                    success=False,
                    error="No current price available (product likely out of stock)",
                    destinations=[],
                    message_ids={},
                )
                return processed
            
            # Check availability status
            availability = processed.price_info.availability
            if availability and availability != "Now":
                logger.error(f"❌ SKIPPING - Product is OUT OF STOCK: {processed.deal.asin} (availability: {availability})")
                processed.deal.status = DealStatus.FAILED
                from .models import PublishResult
                processed.publish_result = PublishResult(
                    deal_id=processed.deal.deal_id,
                    success=False,
                    error=f"Product out of stock (availability: {availability})",
                    destinations=[],
                    message_ids={},
                )
                return processed
            
            # If needs_review for other reasons (e.g., price discrepancy), log warning but continue
            if processed.price_info.needs_review:
                logger.warning(f"⚠️ Deal needs review but will publish: {processed.deal.asin}")

        # Get recipients
        recipients = self.whapi.get_recipients(include_group=include_group)

        if not recipients:
            logger.error("No recipients configured")
            processed.deal.status = DealStatus.FAILED
            return processed

        # Format message
        message = self.formatter.format_message(processed)

        # Get image URL from price info (from Amazon PA-API)
        image_url = processed.price_info.main_image_url if processed.price_info else None

        # Send via Whapi (with image if available)
        try:
            result = self.whapi.send_message(
                recipients, 
                message, 
                processed.deal.deal_id,
                image_url=image_url
            )
            processed.publish_result = result

            if result.success:
                processed.deal.status = DealStatus.PUBLISHED
                logger.info(f"Deal published successfully: {processed.deal.deal_id}")
            else:
                processed.deal.status = DealStatus.FAILED
                logger.error(f"Failed to publish deal: {result.error}")

        except Exception as e:
            logger.error(f"Error publishing deal: {e}")
            processed.deal.status = DealStatus.FAILED

        # Save to database
        self.db.save_deal(processed)

        # Log event
        self.db.log_event(
            processed.deal.deal_id,
            "published" if processed.publish_result and processed.publish_result.success else "failed",
            {
                "recipients": recipients,
                "success": (
                    processed.publish_result.success if processed.publish_result else False
                ),
            },
        )

        return processed

    def process_and_publish_batch(
        self, deals: list[Deal], include_group: bool = False
    ) -> list[ProcessedDeal]:
        """Process and publish a batch of deals."""
        processed_deals: list[ProcessedDeal] = []

        for deal in deals:
            try:
                processed = self.process_deal(deal)
                processed = self.publish_deal(processed, include_group=include_group)
                processed_deals.append(processed)
            except Exception as e:
                logger.error(f"Failed to process deal {deal.title}: {e}")

        return processed_deals

    def shutdown(self) -> None:
        """Clean up resources."""
        if self.interstitial_server:
            self.interstitial_server.stop()
        self.db.close()
        logger.info("Controller shutdown complete")
