"""Main controller orchestrating the deal processing pipeline."""

from pathlib import Path
from typing import Optional

from .models import Deal, DealStatus, ProcessedDeal, PublishResult
from .parsers.txt_parser import TxtParser
from .services.affiliates import AffiliateService
from .services.amazon_paapi import AmazonPAAPIService
from .services.pricing import PricingService
from .services.ratings import RatingsService
from .services.scrapula import ScrapulaService
from .services.shortlinks import ShortLinkService
from .services.whapi import WhapiService
from .storage.db import Database
from .ui.whatsapp_format import WhatsAppFormatter
from .utils.config import Config
from .utils.logging import get_logger

# Optional interstitial server (only for GUI)
try:
    from .services.interstitial import InterstitialServer
except ImportError:
    InterstitialServer = None  # type: ignore

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

        # Initialize AI validator if enabled
        self.ai_validator = None
        if config.get("ai_validation", {}).get("enabled", False):
            try:
                from .services.ai_validator import AIValidator
                ai_key = config.env("DEEPSEEK_API_KEY")
                if not ai_key:
                    raise ValueError("DEEPSEEK_API_KEY not found in environment")
                model = config.get("ai_validation", {}).get("model", "deepseek-chat")
                self.ai_validator = AIValidator(ai_key, model=model)
                logger.info("AI validator initialized with DeepSeek")
            except Exception as e:
                logger.warning(f"AI validation disabled: {e}")
                self.ai_validator = None

        # Initialize interstitial server if enabled and available
        self.interstitial_server: Optional[InterstitialServer] = None  # type: ignore
        if config.interstitial_enabled and InterstitialServer is not None:
            self.interstitial_server = InterstitialServer(config)
            self.interstitial_server.start()
        
        # Cache for Scrapula enrichment data
        self._scrapula_cache = {}

    def parse_file(self, file_path: str | Path) -> list[Deal]:
        """Parse deals from TXT file."""
        logger.info(f"Parsing file: {file_path}")
        deals = self.parser.parse_file(file_path)
        logger.info(f"Parsed {len(deals)} deals")
        
        # Skip Scrapula enrichment during initial file load to avoid 60s delay
        # Images will be added via fallback during publish instead
        # if self.scrapula and deals:
        #     logger.info(f"Enriching {len(deals)} deals with Scrapula data...")
        #     self._enrich_with_scrapula(deals)
        
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

    def _generate_fallback_reviews(self, title: str, discount_pct: Optional[float] = None) -> tuple[str, str]:
        """
        Generate descriptive template-based reviews when AI service is unavailable.

        Args:
            title: Product title
            discount_pct: Discount percentage (optional)

        Returns:
            Tuple of (spanish_review, english_review)
        """
        title_lower = title.lower()

        # Categorize product and create appropriate review
        # Gaming & Consoles
        if any(word in title_lower for word in ['controller', 'mando', 'gamepad', 'joystick', 'joycon']):
            spanish_review = "Mando ergonómico con respuesta precisa. Perfecto para largas sesiones de juego."
            english_review = "Ergonomic controller with precise response. Perfect for long gaming sessions."
        elif any(word in title_lower for word in ['console', 'xbox', 'playstation', 'nintendo', 'switch', 'ps5', 'ps4']):
            spanish_review = "Consola de última generación para gaming inmersivo. Horas de diversión garantizadas."
            english_review = "Latest generation console for immersive gaming. Hours of fun guaranteed."
        elif any(word in title_lower for word in ['gaming keyboard', 'mechanical keyboard', 'teclado gaming']):
            spanish_review = "Teclado gaming mecánico con respuesta táctil. Ideal para jugadores competitivos."
            english_review = "Mechanical gaming keyboard with tactile response. Ideal for competitive gamers."
        elif any(word in title_lower for word in ['gaming mouse', 'ratón gaming']):
            spanish_review = "Ratón de alta precisión para gaming profesional. DPI ajustable y diseño ergonómico."
            english_review = "High precision mouse for professional gaming. Adjustable DPI and ergonomic design."

        # Electronics & Tech
        elif any(word in title_lower for word in ['monitor', 'tv', 'screen', 'display', 'televisor']):
            spanish_review = "Pantalla de alta calidad con colores vivos y gran nitidez. Ideal para cine y gaming."
            english_review = "High quality display with vivid colors and sharp clarity. Ideal for movies and gaming."
        elif any(word in title_lower for word in ['laptop', 'notebook', 'macbook', 'portátil']):
            spanish_review = "Portátil potente y ligero. Perfecto para trabajo, estudios y entretenimiento."
            english_review = "Powerful and lightweight laptop. Perfect for work, studies and entertainment."
        elif any(word in title_lower for word in ['phone', 'smartphone', 'móvil', 'iphone', 'samsung']):
            spanish_review = "Smartphone de última generación con cámara avanzada y gran rendimiento."
            english_review = "Latest generation smartphone with advanced camera and great performance."
        elif any(word in title_lower for word in ['headphone', 'auricular', 'earbuds', 'airpods', 'cascos']):
            spanish_review = "Auriculares premium con cancelación de ruido y sonido envolvente."
            english_review = "Premium headphones with noise cancellation and surround sound."
        elif any(word in title_lower for word in ['charger', 'cargador', 'cable', 'adapter', 'adaptador']):
            spanish_review = "Carga rápida y fiable para tus dispositivos. Compatible con múltiples modelos."
            english_review = "Fast and reliable charging for your devices. Compatible with multiple models."

        # Home & Kitchen
        elif any(word in title_lower for word in ['vacuum', 'aspirador', 'robot', 'roomba']):
            spanish_review = "Aspirador potente con tecnología avanzada. Limpieza eficiente sin esfuerzo."
            english_review = "Powerful vacuum with advanced technology. Effortless efficient cleaning."
        elif any(word in title_lower for word in ['coffee', 'café', 'nespresso', 'cafetera', 'espresso']):
            spanish_review = "Cafetera de calidad profesional. Prepara el café perfecto cada mañana."
            english_review = "Professional quality coffee maker. Brew the perfect coffee every morning."
        elif any(word in title_lower for word in ['air fryer', 'freidora', 'cooker', 'olla', 'cookware']):
            spanish_review = "Electrodoméstico versátil para cocinar de forma saludable. Fácil y rápido."
            english_review = "Versatile appliance for healthy cooking. Easy and fast."
        elif any(word in title_lower for word in ['thermostat', 'termostato', 'smart home', 'alexa', 'google home']):
            spanish_review = "Dispositivo inteligente para controlar tu hogar. Ahorro energético y comodidad."
            english_review = "Smart device to control your home. Energy savings and convenience."

        # Health & Beauty
        elif any(word in title_lower for word in ['cream', 'crema', 'lotion', 'serum', 'moisturizer']):
            spanish_review = "Cuidado de la piel con ingredientes de calidad. Hidratación y protección diarias."
            english_review = "Skincare with quality ingredients. Daily hydration and protection."
        elif any(word in title_lower for word in ['perfume', 'fragrance', 'cologne', 'eau de toilette']):
            spanish_review = "Fragancia sofisticada con notas elegantes. Aroma persistente todo el día."
            english_review = "Sophisticated fragrance with elegant notes. Lasting scent all day long."
        elif any(word in title_lower for word in ['deodorant', 'desodorante', 'roll-on']):
            spanish_review = "Protección duradera contra el olor. Frescura que dura hasta 48 horas."
            english_review = "Long-lasting odor protection. Freshness that lasts up to 48 hours."

        # Food & Beverages
        elif any(word in title_lower for word in ['beer', 'cerveza', 'lager', 'ale']):
            spanish_review = "Cerveza refrescante con sabor auténtico. Ideal para compartir con amigos."
            english_review = "Refreshing beer with authentic flavor. Ideal for sharing with friends."
        elif any(word in title_lower for word in ['wine', 'vino', 'reserva', 'rioja']):
            spanish_review = "Vino selecto con carácter único. Perfecto para acompañar tus comidas."
            english_review = "Select wine with unique character. Perfect to accompany your meals."
        elif any(word in title_lower for word in ['chocolate', 'candy', 'snack', 'biscuit', 'cookie']):
            spanish_review = "Snack delicioso para esos momentos especiales. Sabor que conquista."
            english_review = "Delicious snack for those special moments. Flavor that wins you over."

        # Books & Media
        elif any(word in title_lower for word in ['book', 'libro', 'novel', 'novela']):
            spanish_review = "Lectura cautivadora que te transportará. Perfecto para amantes de la literatura."
            english_review = "Captivating read that will transport you. Perfect for literature lovers."
        elif any(word in title_lower for word in ['blu-ray', 'dvd', 'trilogy', 'collection', 'series']):
            spanish_review = "Colección imprescindible en alta calidad. Horas de entretenimiento garantizadas."
            english_review = "Essential collection in high quality. Hours of guaranteed entertainment."

        # Sports & Outdoors
        elif any(word in title_lower for word in ['backpack', 'mochila', 'bag', 'bolsa']):
            spanish_review = "Mochila resistente y espaciosa. Perfecta para viajes, deporte o uso diario."
            english_review = "Durable and spacious backpack. Perfect for travel, sports or daily use."
        elif any(word in title_lower for word in ['watch', 'reloj', 'smartwatch', 'fitness']):
            spanish_review = "Reloj inteligente con funciones avanzadas. Monitoriza tu salud y actividad."
            english_review = "Smart watch with advanced features. Monitor your health and activity."

        # Fashion
        elif any(word in title_lower for word in ['shirt', 'camisa', 'camiseta', 't-shirt']):
            spanish_review = "Prenda versátil y cómoda para cualquier ocasión. Tejido de calidad superior."
            english_review = "Versatile and comfortable garment for any occasion. Superior quality fabric."
        elif any(word in title_lower for word in ['pants', 'pantalon', 'jeans', 'trousers']):
            spanish_review = "Pantalón con corte moderno y ajuste perfecto. Comodidad durante todo el día."
            english_review = "Pants with modern cut and perfect fit. All-day comfort."
        elif any(word in title_lower for word in ['shoes', 'zapatos', 'sneakers', 'zapatillas']):
            spanish_review = "Calzado cómodo y elegante. Diseño que combina estilo y funcionalidad."
            english_review = "Comfortable and elegant footwear. Design that combines style and functionality."

        # Generic fallback - NO LONGER mentions discount percentage
        else:
            # Try to extract brand or key feature
            if 'pro' in title_lower or 'premium' in title_lower:
                spanish_review = "Producto premium con características profesionales. Calidad excepcional."
                english_review = "Premium product with professional features. Exceptional quality."
            elif 'kit' in title_lower or 'set' in title_lower or 'pack' in title_lower:
                spanish_review = "Pack completo con todo lo necesario. Excelente relación calidad-precio."
                english_review = "Complete pack with everything you need. Excellent value for money."
            else:
                spanish_review = "Producto de calidad con buenas valoraciones. Opción fiable y recomendable."
                english_review = "Quality product with good ratings. Reliable and recommended option."

        return spanish_review, english_review

    def _fallback_validation(
        self,
        title: str,
        current_price: float,
        list_price: Optional[float],
        discount_pct: Optional[float]
    ) -> bool:
        """
        Fallback validation when AI service is unavailable.
        Uses basic sanity checks to prevent obviously bad deals.

        Returns:
            True if deal passes basic sanity checks, False otherwise
        """
        # Rule 1: Minimum price thresholds based on product category
        title_lower = title.lower()

        # Electronics and tech products - must be > €20
        tech_keywords = [
            'monitor', 'laptop', 'tablet', 'phone', 'camera', 'smartwatch',
            'headphone', 'keyboard', 'mouse', 'speaker', 'console', 'gaming',
            'tv', 'display', 'processor', 'graphics card', 'ssd', 'hard drive'
        ]
        if any(keyword in title_lower for keyword in tech_keywords):
            if current_price < 20:
                logger.warning(f"❌ Fallback: Tech product price too low (€{current_price} < €20)")
                return False

        # Gaming monitors specifically - must be > €50
        if 'monitor' in title_lower and ('gaming' in title_lower or 'hz' in title_lower):
            if current_price < 50:
                logger.warning(f"❌ Fallback: Gaming monitor price too low (€{current_price} < €50)")
                return False

        # Rule 2: Price must be reasonable relative to PVP
        if list_price and list_price > 0:
            # Current price shouldn't be more than 90% off (likely error)
            if current_price < (list_price * 0.10):
                logger.warning(f"❌ Fallback: Discount too extreme (>90%): €{current_price} vs PVP €{list_price}")
                return False

            # PVP shouldn't be more than 10x the current price (likely inflated PVP)
            if list_price > (current_price * 10):
                logger.warning(f"❌ Fallback: PVP seems inflated (>10x): €{list_price} vs €{current_price}")
                return False

        # Rule 3: Discount must be reasonable
        if discount_pct:
            # Discount shouldn't be more than 90% (likely error or fake PVP)
            if discount_pct > 90:
                logger.warning(f"❌ Fallback: Discount too high ({discount_pct}%)")
                return False

        # All checks passed
        logger.info(f"✅ Fallback validation passed for {title[:50]}... (€{current_price})")
        return True

    def process_deal(self, deal: Deal, for_preview: bool = True) -> ProcessedDeal:
        """Process a single deal through the pipeline.
        
        Args:
            deal: The deal to process
            for_preview: If True, skips expensive operations (shortlinks, ratings) to prevent crashes
        """
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
                    
                    # Use Scrapula list_price (PVP) if PA-API didn't provide it
                    if not price_info.list_price and scrapula_info.list_price:
                        price_info.list_price = scrapula_info.list_price
                        # Calculate discount percentage
                        if price_info.current_price and scrapula_info.list_price > price_info.current_price:
                            discount = ((scrapula_info.list_price - price_info.current_price) / scrapula_info.list_price) * 100
                            price_info.savings_percentage = round(discount, 0)
                        logger.info(f"Added Scrapula PVP €{scrapula_info.list_price} and discount -{price_info.savings_percentage}% for {deal.asin}")
                    
                    # Use Scrapula rating/reviews if PA-API didn't provide them
                    if not price_info.review_rating and scrapula_info.rating:
                        price_info.review_rating = scrapula_info.rating
                        logger.info(f"Added Scrapula rating for {deal.asin}")
                    
                    if not price_info.review_count and scrapula_info.review_count:
                        price_info.review_count = scrapula_info.review_count

        # Playwright fallback: If still no image, try scraping directly
        playwright_delivery_cost = None
        playwright_has_delivery = False
        if not price_info.main_image_url and deal.asin:
            try:
                from .services.playwright_scraper import scrape_product_sync
                logger.info(f"🎭 Trying Playwright fallback for {deal.asin}...")
                pw_result = scrape_product_sync(deal.asin, self.config.get("scrapula", {}).get("marketplace", "es"))
                if pw_result.success and pw_result.image_url:
                    price_info.main_image_url = pw_result.image_url
                    logger.info(f"✅ Playwright found image for {deal.asin}")
                    # Also use PVP/discount if missing
                    if not price_info.list_price and pw_result.list_price:
                        price_info.list_price = pw_result.list_price
                    if not price_info.savings_percentage and pw_result.discount_pct:
                        price_info.savings_percentage = pw_result.discount_pct
                    # Store delivery cost info
                    playwright_delivery_cost = pw_result.delivery_cost
                    playwright_has_delivery = pw_result.has_mandatory_delivery
                else:
                    logger.warning(f"❌ Playwright could not find image for {deal.asin}")
            except Exception as e:
                logger.error(f"Playwright fallback error for {deal.asin}: {e}")

        # Log comprehensive price info for debugging
        logger.info(
            f"💰 Price sources for {deal.asin}: "
            f"Current=€{price_info.current_price} "
            f"List/PVP=€{price_info.list_price} "
            f"Discount={price_info.savings_percentage}% "
            f"| Source: Stated=€{deal.stated_price} PVP=€{deal.source_pvp} Disc={deal.source_discount_pct}%"
        )

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
        if for_preview:
            short_link = None  # Skip shortlink creation during preview
        elif self.shortlinks:
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
        if self.ratings and not for_preview:
            try:
                rating = self.ratings.get_rating(deal.asin)
            except Exception as e:
                logger.warning(f"Failed to get rating for {deal.asin}: {e}")

        # Step 6: AI validation and review generation (optional)
        ai_review_es = None
        ai_review_en = None
        ai_approved = True  # Default to approved if AI disabled

        if self.ai_validator and not for_preview:
            try:
                from .services.ai_validator import get_cached_or_validate
                ai_result = get_cached_or_validate(
                    self.ai_validator,
                    deal.asin or "unknown",
                    deal.title,
                    price_info.current_price or adjusted_price,
                    price_info.list_price or deal.source_pvp,
                    price_info.savings_percentage or deal.source_discount_pct,
                    playwright_delivery_cost
                )
                # If AI service error, use fallback validation (basic sanity checks)
                if ai_result.error:
                    logger.warning(f"AI validation error for {deal.asin}, using fallback validation: {ai_result.error}")
                    ai_approved = self._fallback_validation(
                        deal.title,
                        price_info.current_price or adjusted_price,
                        price_info.list_price or deal.source_pvp,
                        price_info.savings_percentage or deal.source_discount_pct
                    )
                    if not ai_approved:
                        logger.warning(f"❌ Fallback validation rejected: {deal.title[:50]}")
                    else:
                        # Generate fallback reviews for deals that passed validation
                        logger.info(f"📝 Generating fallback reviews for {deal.asin}")
                        ai_review_es, ai_review_en = self._generate_fallback_reviews(
                            deal.title,
                            price_info.savings_percentage or deal.source_discount_pct
                        )
                else:
                    ai_approved = ai_result.approved
                    if ai_result.review:
                        ai_review_es = ai_result.review.spanish
                        ai_review_en = ai_result.review.english
            except Exception as e:
                logger.error(f"AI validation exception for {deal.asin}: {e}")
                # Use fallback validation on exception
                ai_approved = self._fallback_validation(
                    deal.title,
                    price_info.current_price or adjusted_price,
                    price_info.list_price or deal.source_pvp,
                    price_info.savings_percentage or deal.source_discount_pct
                )
                if ai_approved:
                    # Generate fallback reviews for deals that passed validation
                    logger.info(f"📝 Generating fallback reviews for {deal.asin} (exception fallback)")
                    ai_review_es, ai_review_en = self._generate_fallback_reviews(
                        deal.title,
                        price_info.savings_percentage or deal.source_discount_pct
                    )

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
            delivery_cost=playwright_delivery_cost,
            has_mandatory_delivery=playwright_has_delivery,
            ai_review_es=ai_review_es,
            ai_review_en=ai_review_en,
            ai_approved=ai_approved,
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

    def enrich_deals_before_publish(self, deals: list[Deal]) -> None:
        """Enrich deals with Scrapula data before publishing (to get PVP/discounts/images)."""
        if not self.scrapula or not deals:
            return
        
        # Only enrich deals that aren't already in cache
        asins_to_fetch = [deal.asin for deal in deals if deal.asin and deal.asin not in self._scrapula_cache]
        
        if not asins_to_fetch:
            logger.info("All deals already enriched with Scrapula data")
            return
        
        logger.info(f"Enriching {len(asins_to_fetch)} deals with Scrapula data (for PVP/discounts/images)...")
        self._enrich_with_scrapula([d for d in deals if d.asin in asins_to_fetch])

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
            
            # Check availability status - but ONLY if we have availability data
            # If availability is None/empty and we have a price, assume it's available
            availability = processed.price_info.availability
            if availability and availability not in ["Now", None, ""]:
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

        # Get image URL from price info (from Amazon PA-API or Scrapula)
        image_url = processed.price_info.main_image_url if processed.price_info else None
        
        # Fallback: Try to extract image AND PVP/discount from Amazon page if missing
        if (not image_url or not processed.price_info.list_price) and processed.deal.asin:
            try:
                import requests
                import re
                
                # Fetch Amazon product page
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                response = requests.get(
                    f"https://www.amazon.es/dp/{processed.deal.asin}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Extract image URL if still missing
                    if not image_url:
                        image_patterns = [
                            r'"hiRes":"(https://[^"]+\.jpg)"',
                            r'"large":"(https://[^"]+\.jpg)"',
                            r'data-old-hires="(https://[^"]+\.jpg)"',
                            r'data-a-dynamic-image="[^"]*?(https://m\.media-amazon\.com/images/I/[^"]+\.jpg)',
                        ]
                        
                        for pattern in image_patterns:
                            match = re.search(pattern, html)
                            if match:
                                image_url = match.group(1)
                                logger.info(f"Extracted image URL from Amazon page for {processed.deal.asin}")
                                break
                    
                    # Extract PVP/list price if missing
                    if not processed.price_info.list_price:
                        # Look for patterns like: "listPrice":{"amount":75.0,"currency":"EUR"}
                        pvp_patterns = [
                            r'"listPrice":\s*{\s*"amount":\s*([0-9.]+)',
                            r'"list_price":\s*{\s*"amount":\s*([0-9.]+)',
                            r'<span[^>]*class="[^"]*a-price[^"]*a-text-price[^"]*"[^>]*>[^€]*€\s*([0-9.,]+)',
                            r'data-a-strike="true"[^>]*>[^€]*€\s*([0-9.,]+)',
                        ]
                        
                        for pattern in pvp_patterns:
                            match = re.search(pattern, html)
                            if match:
                                pvp_str = match.group(1).replace(',', '.')
                                try:
                                    list_price = float(pvp_str)
                                    # Only use if it's higher than current price
                                    if list_price > processed.price_info.current_price:
                                        processed.price_info.list_price = list_price
                                        # Calculate discount
                                        discount = ((list_price - processed.price_info.current_price) / list_price) * 100
                                        processed.price_info.savings_percentage = round(discount, 0)
                                        logger.info(f"Extracted PVP €{list_price} and discount -{processed.price_info.savings_percentage}% from Amazon page for {processed.deal.asin}")
                                        break
                                except ValueError:
                                    continue
                            
            except Exception as e:
                logger.warning(f"Failed to extract from Amazon page for {processed.deal.asin}: {e}")
        
        # If still no image, skip image (send text-only to avoid 400 errors)
        if not image_url:
            logger.warning(f"No valid image URL found for {processed.deal.asin}, sending text-only message")

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
