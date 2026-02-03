"""Playwright-based Amazon scraper for fallback image/price extraction."""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PlaywrightProductInfo:
    """Product information scraped via Playwright."""
    asin: str
    image_url: Optional[str] = None
    current_price: Optional[float] = None
    list_price: Optional[float] = None
    discount_pct: Optional[float] = None
    delivery_cost: Optional[float] = None  # Mandatory delivery cost if any
    has_mandatory_delivery: bool = False  # True if delivery cost is mandatory
    success: bool = False
    error: Optional[str] = None


class PlaywrightScraper:
    """Fallback scraper using Playwright with stealth for Amazon product pages."""

    def __init__(self):
        self._browser = None
        self._context = None
        self._playwright = None

    async def _ensure_browser(self, marketplace: str = "es"):
        """Lazily initialize browser with stealth."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

            # Set locale based on marketplace
            locale_map = {
                "es": ("es-ES", "Europe/Madrid"),
                "uk": ("en-GB", "Europe/London"),
                "us": ("en-US", "America/New_York"),
                "de": ("de-DE", "Europe/Berlin"),
                "fr": ("fr-FR", "Europe/Paris"),
                "it": ("it-IT", "Europe/Rome"),
            }
            locale, timezone = locale_map.get(marketplace, ("es-ES", "Europe/Madrid"))

            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale=locale,
                timezone_id=timezone,
            )

            # Apply stealth to avoid bot detection
            stealth = Stealth()
            await stealth.apply_stealth_async(self._context)

        return self._context

    async def scrape_product(self, asin: str, marketplace: str = "es") -> PlaywrightProductInfo:
        """
        Scrape Amazon product page for image and price info.

        Args:
            asin: Amazon product ASIN
            marketplace: Amazon marketplace (es, uk, us, etc.)

        Returns:
            PlaywrightProductInfo with scraped data
        """
        domain_map = {
            "es": "amazon.es",
            "uk": "amazon.co.uk",
            "us": "amazon.com",
            "de": "amazon.de",
            "fr": "amazon.fr",
            "it": "amazon.it",
        }
        domain = domain_map.get(marketplace, "amazon.es")
        url = f"https://www.{domain}/dp/{asin}"

        logger.info(f"🎭 Playwright scraping: {url}")

        try:
            context = await self._ensure_browser(marketplace)
            page = await context.new_page()

            # Increased timeout from 30s to 90s to handle slow Amazon responses
            # Using "domcontentloaded" instead of "networkidle" for faster loading
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(3000)  # Let page settle and load images

            # Extract image URL
            image_url = await self._extract_image(page)

            # Extract prices
            current_price, list_price, discount_pct = await self._extract_prices(page)

            # Extract delivery costs
            delivery_cost, has_mandatory_delivery = await self._extract_delivery_cost(page)

            await page.close()

            # Log findings
            if image_url:
                logger.info(f"✅ Playwright found image for {asin}: {image_url[:60]}...")
            else:
                logger.warning(f"❌ Playwright could not find image for {asin}")

            if has_mandatory_delivery:
                logger.warning(f"⚠️ Mandatory delivery cost €{delivery_cost} for {asin}")

            return PlaywrightProductInfo(
                asin=asin,
                image_url=image_url,
                current_price=current_price,
                list_price=list_price,
                discount_pct=discount_pct,
                delivery_cost=delivery_cost,
                has_mandatory_delivery=has_mandatory_delivery,
                success=image_url is not None
            )

        except Exception as e:
            logger.error(f"Playwright scrape error for {asin}: {e}")
            return PlaywrightProductInfo(
                asin=asin,
                error=str(e),
                success=False
            )

    async def _extract_image(self, page) -> Optional[str]:
        """Extract main product image URL."""
        # Primary selector - landing image
        img = await page.query_selector("#landingImage")
        if img:
            # Try high-res first
            hires = await img.get_attribute("data-old-hires")
            if hires and hires.startswith("http"):
                return hires
            src = await img.get_attribute("src")
            if src and src.startswith("http") and "no-image" not in src.lower():
                return src

        # Alternative selectors
        for selector in ["#imgBlkFront", "#main-image", ".a-dynamic-image"]:
            try:
                element = await page.query_selector(selector)
                if element:
                    src = await element.get_attribute("src")
                    if src and src.startswith("http") and "no-image" not in src.lower():
                        return src
            except Exception:
                continue

        # Fallback: search in page source
        try:
            content = await page.content()
            patterns = [
                r'"hiRes":"(https://[^"]+\.jpg)"',
                r'"large":"(https://[^"]+\.jpg)"',
                r'data-old-hires="(https://[^"]+\.jpg)"',
            ]
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
        except Exception:
            pass

        return None

    async def _extract_prices(self, page) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Extract current price, list price, and discount percentage."""
        current_price = None
        list_price = None
        discount_pct = None

        # Current price
        price_el = await page.query_selector(".a-price .a-offscreen")
        if price_el:
            text = await price_el.text_content()
            current_price = self._parse_price(text)

        # List price (PVP) - try multiple selectors
        for selector in [".basisPrice .a-offscreen", ".a-text-price .a-offscreen"]:
            list_el = await page.query_selector(selector)
            if list_el:
                text = await list_el.text_content()
                list_price = self._parse_price(text)
                if list_price:
                    break

        # Discount percentage
        disc_el = await page.query_selector(".savingsPercentage")
        if disc_el:
            text = await disc_el.text_content()
            match = re.search(r'(\d+)', text)
            if match:
                discount_pct = float(match.group(1))

        # Calculate discount if we have both prices but no explicit discount
        if not discount_pct and current_price and list_price and list_price > current_price:
            discount_pct = round(((list_price - current_price) / list_price) * 100, 0)

        return current_price, list_price, discount_pct

    async def _extract_delivery_cost(self, page) -> tuple[Optional[float], bool]:
        """
        Extract mandatory delivery cost if present.
        Returns: (delivery_cost, has_mandatory_delivery)
        """
        delivery_cost = None
        has_mandatory_delivery = False

        try:
            # Check delivery message block
            delivery_selectors = [
                "#mir-layout-DELIVERY_BLOCK",
                "#deliveryMessageMirId",
                "#deliveryBlockMessage",
                "[data-csa-c-delivery-price]",
            ]

            for selector in delivery_selectors:
                el = await page.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text:
                        # Look for delivery cost patterns
                        # Spanish: "€2,99 de envío"
                        # English: "€2.99 delivery"
                        patterns = [
                            r'€\s*(\d+[,.]?\d*)\s*(?:de\s+)?(?:envío|entrega|delivery)',
                            r'(\d+[,.]?\d*)\s*€\s*(?:de\s+)?(?:envío|entrega|delivery)',
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                delivery_cost = self._parse_price(match.group(1))
                                # Only count as mandatory if it's not free
                                if delivery_cost and delivery_cost > 0:
                                    has_mandatory_delivery = True
                                    logger.info(f"Found delivery cost: €{delivery_cost}")
                                break
                    if has_mandatory_delivery:
                        break

        except Exception as e:
            logger.debug(f"Could not extract delivery cost: {e}")

        return delivery_cost, has_mandatory_delivery

    def _parse_price(self, text: str) -> Optional[float]:
        """Parse price from text like '€14.99' or '14,99 €'."""
        if not text:
            return None
        try:
            cleaned = re.sub(r'[€$£\s]', '', text)
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


def scrape_product_sync(asin: str, marketplace: str = "es", max_retries: int = 2) -> PlaywrightProductInfo:
    """
    Synchronous wrapper for scrape_product with retry logic.

    Args:
        asin: Amazon product ASIN
        marketplace: Amazon marketplace
        max_retries: Maximum number of retry attempts (default 2 = 3 total attempts)
    """
    import asyncio
    import time

    async def _scrape():
        scraper = PlaywrightScraper()
        try:
            return await scraper.scrape_product(asin, marketplace)
        finally:
            await scraper.close()

    # Retry logic for handling transient failures
    for attempt in range(max_retries + 1):
        try:
            result = asyncio.run(_scrape())
            if result.success or attempt == max_retries:
                return result
            # Retry if failed (but not on last attempt)
            logger.warning(f"🔄 Playwright attempt {attempt + 1} failed for {asin}, retrying...")
            time.sleep(2 * (attempt + 1))  # Exponential backoff: 2s, 4s
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"❌ Playwright failed after {max_retries + 1} attempts for {asin}: {e}")
                return PlaywrightProductInfo(asin=asin, error=str(e), success=False)
            logger.warning(f"🔄 Playwright attempt {attempt + 1} exception for {asin}, retrying: {e}")
            time.sleep(2 * (attempt + 1))

    return PlaywrightProductInfo(asin=asin, error="Max retries exceeded", success=False)
