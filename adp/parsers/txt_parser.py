"""TXT file parser for Amazon deals."""

import re
from pathlib import Path
from typing import Optional

from ..models import Currency, Deal
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TxtParser:
    """Parse deal records from TXT files."""

    # Regex patterns
    ASIN_PATTERN = re.compile(r"/dp/([A-Z0-9]{10})")
    # Updated to handle "Precio/Price: €X.XX" format
    PRICE_PATTERN = re.compile(r"(?:Precio/Price:|Price:|Precio:)?\s*[€£$]?\s*(\d+[.,]\d{1,2})\s*[€£$]?", re.IGNORECASE)
    URL_PATTERN = re.compile(r"https?://[^\s]+")
    # Support emoji flags (🇪🇸, 🇬🇧) and text flags (ES, EN)
    LANGUAGE_FLAG_PATTERN = re.compile(r"(?:🇪🇸|🇬🇧|\b(?:ES|EN|UK|GB)\b)")

    def __init__(self) -> None:
        """Initialize parser."""
        pass

    def parse_file(self, file_path: str | Path) -> list[Deal]:
        """Parse deals from a TXT file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content)

    def parse_content(self, content: str) -> list[Deal]:
        """Parse deals from text content."""
        deals: list[Deal] = []

        # Split by separator lines (━━━━━) or deal headers (#1, #2, etc)
        separator_pattern = re.compile(r'^[━─]+\s*$|^🎯\s*#\d+')
        
        lines = content.strip().split("\n")
        current_block: list[str] = []
        blocks: list[str] = []

        for line in lines:
            stripped = line.strip()
            
            # Skip header lines (CHOLLOS AMAZON, date, etc)
            if '🔥' in stripped or '📅' in stripped:
                continue
            
            # Check if this is a separator or new deal header
            if separator_pattern.search(stripped):
                # Save the current block if it has content
                if current_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
                continue
            
            # Add line to current block
            if stripped:
                current_block.append(line)

        # Don't forget the last block
        if current_block:
            blocks.append("\n".join(current_block))

        # Parse each block
        for block in blocks:
            deal = self._parse_block(block)
            if deal:
                deals.append(deal)

        logger.info(f"Parsed {len(deals)} deals from content")
        return deals

    def _parse_block(self, block: str) -> Optional[Deal]:
        """Parse a single deal block."""
        # Extract URL
        url_match = self.URL_PATTERN.search(block)
        if not url_match:
            logger.warning(f"No URL found in block: {block[:50]}...")
            return None

        url = url_match.group(0)

        # Extract ASIN
        asin_match = self.ASIN_PATTERN.search(url)
        asin = asin_match.group(1) if asin_match else None

        # Extract price - look specifically for Precio/Price line first
        stated_price: Optional[float] = None
        source_pvp: Optional[float] = None
        source_discount_pct: Optional[float] = None
        
        price_lines = [line for line in block.split('\n') if 'Precio' in line or 'Price:' in line or '💰' in line]
        
        if price_lines:
            # Search for price in the price-specific line
            price_line = price_lines[0]
            # Look for pattern like "€0.01" or "11.99"
            price_pattern = re.compile(r'[€£$]\s*(\d+[.,]\d{1,2})|(\d+[.,]\d{1,2})\s*[€£$]')
            price_match = price_pattern.search(price_line)
            if price_match:
                # Get whichever group matched
                price_str = price_match.group(1) or price_match.group(2)
                price_str = price_str.replace(",", ".")
                try:
                    stated_price = float(price_str)
                except ValueError:
                    logger.warning(f"Failed to parse price: {price_str}")
            
            # Extract PVP (original price) from format like "€18.59 (PVP:€28.49)"
            pvp_pattern = re.compile(r'\(PVP:\s*[€£$]?\s*(\d+[.,]\d{1,2})\s*[€£$]?\)', re.IGNORECASE)
            pvp_match = pvp_pattern.search(price_line)
            if pvp_match:
                pvp_str = pvp_match.group(1).replace(",", ".")
                try:
                    source_pvp = float(pvp_str)
                    logger.info(f"Extracted source PVP: €{source_pvp}")
                except ValueError:
                    logger.warning(f"Failed to parse PVP: {pvp_str}")
        
        # Extract discount from lines like "💸 Descuento/Discount: -€9.90 (-35%)"
        discount_lines = [line for line in block.split('\n') if 'Descuento' in line or 'Discount:' in line or '💸' in line]
        if discount_lines:
            discount_line = discount_lines[0]
            # Look for percentage like "(-35%)" or "-35%"
            discount_pattern = re.compile(r'\(?-(\d+)%\)?')
            discount_match = discount_pattern.search(discount_line)
            if discount_match:
                try:
                    source_discount_pct = float(discount_match.group(1))
                    logger.info(f"Extracted source discount: -{source_discount_pct}%")
                except ValueError:
                    logger.warning(f"Failed to parse discount: {discount_match.group(1)}")
        
        # Fallback to searching entire block if no price line found
        if stated_price is None:
            price_match = self.PRICE_PATTERN.search(block)
            if price_match:
                price_str = price_match.group(1).replace(",", ".")
                try:
                    stated_price = float(price_str)
                except ValueError:
                    logger.warning(f"Failed to parse price: {price_str}")

        # Determine currency from symbols or context
        currency = Currency.EUR  # Default
        if "£" in block or "GBP" in block.upper():
            currency = Currency.GBP
        elif "$" in block or "USD" in block.upper():
            currency = Currency.USD

        # Extract language flag
        lang_match = self.LANGUAGE_FLAG_PATTERN.search(block)
        language_flag = lang_match.group(0) if lang_match else None

        # Extract title from bilingual format (prefer English 🇬🇧 or Spanish 🇪🇸)
        lines = block.split('\n')
        title = ""
        
        # Look for flag-prefixed titles
        for line in lines:
            if '🇬🇧' in line or 'UK' in line.upper():
                # Prefer English title
                title = line.replace('🇬🇧', '').replace('UK', '').strip()
                break
            elif '🇪🇸' in line or line.strip().startswith('ES'):
                # Fallback to Spanish
                if not title:
                    title = line.replace('🇪🇸', '').replace('ES', '').strip()
        
        # If no flag-based title found, extract from cleaned block
        if not title:
            title = block.strip()
            title = self.URL_PATTERN.sub("", title)
            title = re.sub(r"Precio/Price:.*", "", title, flags=re.IGNORECASE)
            title = re.sub(r"Descuento/Discount:.*", "", title, flags=re.IGNORECASE)
            title = re.sub(r"[\n\r]+", " ", title)
            title = re.sub(r"\s+", " ", title)
            title = title.strip()
        
        # Remove emojis and clean up
        title = re.sub(r"[🔥📅💰💸🛒🎯━─]+", "", title)
        title = re.sub(r"#\d+\s*-\s*\d+°?", "", title)  # Remove deal numbers
        title = title.strip()[:200]  # Limit title length
        title = " ".join(title.split())  # Normalize whitespace

        if not title:
            title = f"Deal {asin or 'Unknown'}"

        deal = Deal(
            title=title,
            url=url,
            asin=asin,
            stated_price=stated_price,
            source_pvp=source_pvp,
            source_discount_pct=source_discount_pct,
            currency=currency,
            language_flag=language_flag,
        )

        logger.debug(f"Parsed deal: {deal.title[:50]}...")
        return deal
