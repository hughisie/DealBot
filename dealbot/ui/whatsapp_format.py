"""WhatsApp message formatting."""

from typing import Optional

from ..models import Currency, ProcessedDeal, Rating


class WhatsAppFormatter:
    """Format deals for WhatsApp publishing."""

    CURRENCY_SYMBOLS = {
        Currency.EUR: "€",
        Currency.GBP: "£",
        Currency.USD: "$",
    }

    @staticmethod
    def format_message(deal: ProcessedDeal) -> str:
        """Format a processed deal for WhatsApp."""
        lines = []

        # Spanish title (use title_es if available, otherwise fall back to primary title)
        spanish_title = deal.deal.title_es if deal.deal.title_es else deal.deal.title
        lines.append(f"🇪🇸 {spanish_title}")
        lines.append("")

        # AI-generated Spanish review (if available)
        if deal.ai_review_es:
            lines.append(f"📋 {deal.ai_review_es}")
            lines.append("")

        # English title (use title_en if available, otherwise fall back to primary title)
        english_title = deal.deal.title_en if deal.deal.title_en else deal.deal.title
        lines.append(f"🇬🇧 {english_title}")
        lines.append("")

        # AI-generated English review (if available)
        if deal.ai_review_en:
            lines.append(f"📋 {deal.ai_review_en}")
            lines.append("")

        # Rating (if available)
        if deal.rating:
            rating_line = f"⭐ {deal.rating.stars} {deal.rating.value}/5"
            if deal.rating.count > 0:
                rating_line += f" ({deal.rating.count:,}+)"
            lines.append(rating_line)
            lines.append("")

        # Price with PVP and discount
        currency_symbol = WhatsAppFormatter.CURRENCY_SYMBOLS.get(
            deal.price_info.currency, "€"
        )
        
        # Get PVP and discount from any available source (PA-API or source TXT file)
        pvp_price = deal.price_info.list_price if deal.price_info.list_price and deal.price_info.list_price > 0 else None
        discount_pct = deal.price_info.savings_percentage if deal.price_info.savings_percentage and deal.price_info.savings_percentage > 0 else None

        # Fallback to source data if PA-API didn't provide it
        if not pvp_price and deal.deal.source_pvp and deal.deal.source_pvp > 0:
            pvp_price = deal.deal.source_pvp
        if not discount_pct and deal.deal.source_discount_pct and deal.deal.source_discount_pct > 0:
            discount_pct = deal.deal.source_discount_pct

        # ALWAYS show PVP and discount if we have them (required for all deals)
        if pvp_price and discount_pct:
            price_line = (
                f"💰 Precio/Price: {currency_symbol}{deal.adjusted_price:.2f} / "
                f"PVP {currency_symbol}{pvp_price:.2f} "
                f"(-{discount_pct:.0f}%)"
            )
        else:
            # This should not happen as daemon validation requires PVP/discount
            price_line = f"💰 Precio/Price: {currency_symbol}{deal.adjusted_price:.2f}"
        
        lines.append(price_line)
        lines.append("")

        # Short URL
        lines.append(f"🛒 {deal.short_link.short_url}")

        return "\n".join(lines)

    @staticmethod
    def format_preview(deal: ProcessedDeal) -> str:
        """Format a shorter preview for GUI display."""
        currency_symbol = WhatsAppFormatter.CURRENCY_SYMBOLS.get(
            deal.price_info.currency, "€"
        )
        rating_str = f"{deal.rating.value}/5 ★" if deal.rating else "N/A"

        preview = (
            f"{deal.deal.title[:60]}...\n"
            f"Price: {currency_symbol}{deal.adjusted_price:.2f}\n"
            f"Rating: {rating_str}\n"
            f"Link: {deal.short_link.short_url}"
        )
        return preview
