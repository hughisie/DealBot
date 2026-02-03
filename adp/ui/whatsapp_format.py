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

        # Spanish title (if available, else English)
        lines.append(f"🇪🇸 {deal.deal.title}")
        lines.append("")
        
        # English title - for bilingual posting
        lines.append(f"🇬🇧 {deal.deal.title}")
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
        
        # If we have list price (PVP), show discount
        if deal.price_info.list_price and deal.price_info.savings_percentage:
            price_line = (
                f"💰 Precio/Price: {currency_symbol}{deal.adjusted_price:.2f} / "
                f"PVP {currency_symbol}{deal.price_info.list_price:.2f} "
                f"(-{deal.price_info.savings_percentage:.0f}%)"
            )
        else:
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
